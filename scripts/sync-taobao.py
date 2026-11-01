#!/usr/bin/env python3
"""淘宝去广告模块同步脚本。

同步源（可莉官方 GitHub 分发仓 Moli-X/Tool，作者 RuCu6）：
- 插件：Loon/Plugin/Kelee/Taobao_remove_ads.plugin（[Rule]/[Rewrite]/[Script]/[MitM]）
- 脚本：Loon/Plugin/Kelee/Script/Taobao_remove_ads.js（开屏处理，原文镜像加安全包装）

本地转换：DOMAIN->rules、reject_dict->[Rewrite]->respond {} 重写、[Script]->scriptings、[MitM]->mitm。
嫁接项（Thelongdarkorg 插件独有，写死在本脚本，上游同步不覆盖）：
- 闲鱼开屏 mtop.taobao.idlecommerce.splash.ads、菜鸟 mtop.cainiao.adx.flyad.getad 两条 respond {}
- 3 条 alicdn 广告图直链 url_rewrites（reject-dict），并为其补 gw.alicdn.com 的 MITM
AMDC 拦截不加（用户 2026-11-01 确认：通用调度通道，有误伤可能的一律跳过）。
上游出现无法识别的行时中止同步、保留上次有效版本并以非零码退出。
"""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_URL = "https://raw.githubusercontent.com/Moli-X/Tool/main/Loon/Plugin/Kelee/Taobao_remove_ads.plugin"
JS_URL = "https://raw.githubusercontent.com/Moli-X/Tool/main/Loon/Plugin/Kelee/Script/Taobao_remove_ads.js"
YAML_FILE = ROOT / "taobao-adblock.yaml"
JS_FILE = ROOT / "taobao-adblock.js"
STATUS_FILE = ROOT / "taobao-sync-status.json"
CST = timezone(timedelta(hours=8))

GRAFT_RESPOND = [
    r"(?i)^https://acs\.m\.taobao\.com/gw/mtop\.taobao\.idlecommerce\.splash\.ads",
    r"(?i)^https://guide-acs\.m\.taobao\.com/gw/mtop\.cainiao\.adx\.flyad\.getad",
]
GRAFT_URL_REWRITES = [
    r"(?i)^https://heic\.alicdn\.com/imgextra/i\d/[A-Za-z0-9_!]+-\d+-tps-\d+-\d+\.png_\d+x\d+q\d+\.jpg_\.heic$",
    r"(?i)^https://heic\.alicdn\.com/imgextra/i\d/[A-Za-z0-9_!]+-\d+-tps-\d+-\d+\.jpg_\d+x\d+q\d+\.jpg_\.heic$",
    r"(?i)^https://gw\.alicdn\.com/imgextra/i\d+/[^/]+_!!\d+-\d+-tps-(?:720-1280|1080-1920|1125-1602|1242-2208)\.(?:jpg|png|jpeg)_[^/]+\.webp",
]
EXTRA_MITM = ["gw.alicdn.com"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fail(msg):
    status = {
        "module": "taobao-adblock",
        "synced_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "error": msg,
    }
    try:
        old = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {}
        old.update(status)
        status = old
    except Exception:
        pass
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def conv_regex(raw):
    # Loon 插件正则以 \/ 转义斜杠、结尾 /i 表示忽略大小写；转成 Egern 的 (?i) 内联形式
    return "(?i)" + raw.replace("\\/", "/")


def parse_plugin(text):
    date_m = re.search(r"^#!date=(.+)$", text, re.M)
    upstream_date = date_m.group(1).strip() if date_m else ""
    sections = {}
    current = None
    for line in text.splitlines():
        s = line.strip()
        hm = re.match(r"^\[(.+)\]$", s)
        if hm:
            current = hm.group(1)
            sections.setdefault(current, [])
            continue
        if current and s and not s.startswith("#"):
            sections[current].append(s)

    domains, rewrites, scriptings, mitm = [], [], [], []
    for line in sections.get("Rule", []):
        m = re.match(r"^DOMAIN,\s*([^,]+),\s*REJECT$", line)
        if not m:
            fail(f"无法识别的 Rule 行: {line}")
        domains.append(m.group(1).strip())
    for line in sections.get("Rewrite", []):
        m = re.match(r"^request if \$\{url\} ~= /(.+)/i then reject_dict\(200\)$", line)
        if not m:
            fail(f"无法识别的 Rewrite 行: {line}")
        rewrites.append(conv_regex(m.group(1)))
    for line in sections.get("Script", []):
        m = re.match(
            r'^response if \$\{url\} ~= /(.+)/i then script\("([^"]+)"\) with tag="([^"]*)", requires_body=true$',
            line,
        )
        if not m:
            fail(f"无法识别的 Script 行: {line}")
        pattern, script_url = conv_regex(m.group(1)), m.group(2)
        if not script_url.endswith("/Taobao_remove_ads.js"):
            fail(f"Script 行指向了意料外的脚本: {script_url}")
        name = "淘宝开屏活动弹窗处理" if "poplayer" in pattern else "淘宝开屏视频与开屏图处理"
        scriptings.append((name, pattern))
    for line in sections.get("MitM", []):
        m = re.match(r"^hostname\s*=\s*(.+)$", line)
        if not m:
            fail(f"无法识别的 MitM 行: {line}")
        mitm = [h.strip() for h in m.group(1).split(",") if h.strip()]
    if len(domains) < 1 or len(rewrites) < 5 or len(scriptings) < 1 or len(mitm) < 1:
        fail(f"上游结构异常: domains={len(domains)} rewrites={len(rewrites)} scriptings={len(scriptings)} mitm={len(mitm)}")
    return upstream_date, domains, rewrites, scriptings, mitm


def yaml_quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_yaml(domains, rewrites, scriptings, mitm, js_hash):
    out = []
    out.append("name: 淘宝去广告🅥")
    out.append("description: |-")
    out.append("  过滤淘宝开屏广告（图片/视频/活动弹窗）与广告下发接口，含闲鱼欢迎页与开屏。")
    out.append("  纯规则加一个开屏处理脚本，脚本仅把开屏素材清空、等待时长归零，不改其他数据。")
    out.append("open_url: https://apps.apple.com/app/id387682726")
    out.append("author: RuCu6[https://github.com/RuCu6]")
    out.append("homepage: https://hub.kelee.one")
    out.append("icon: https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/Taobao.png")
    out.append("")
    out.append("# 同步自可莉官方 GitHub 分发仓 Moli-X/Tool 的 RuCu6 淘宝插件，由 scripts/sync-taobao.py 每 6 小时自动转换；开屏脚本镜像至本仓库。")
    out.append("# 本地嫁接（Thelongdarkorg 插件独有，同步时保留）：闲鱼开屏、菜鸟广告两条接口空回应，及 3 条广告图直链 reject，并为其补 gw.alicdn.com 的 MITM。")
    out.append("# AMDC 调度拦截不加：通用配置通道，有误伤可能（用户 2026-11-01 确认跳过）。")
    out.append("dns: {}")
    out.append("rules:")
    for d in domains:
        out.append("- domain:")
        out.append(f"    match: {d}")
        out.append("    policy: REJECT")
    out.append("rewrites:")
    for p in rewrites + GRAFT_RESPOND:
        out.append(f"- match: {yaml_quote(p)}")
        out.append("  actions:")
        out.append("  - respond:")
        out.append("      status: 200")
        out.append('      headers: {"Content-Type":"application/json"}')
        out.append('      body: "{}"')
    out.append("url_rewrites:")
    for p in GRAFT_URL_REWRITES:
        out.append(f"- match: {yaml_quote(p)}")
        out.append("  location: http://reject-dict/")
    out.append("scriptings:")
    for name, pattern in scriptings:
        out.append("- http_response:")
        out.append(f"    name: {name}")
        out.append(f"    match: {yaml_quote(pattern)}")
        out.append(f"    script_url: https://raw.githubusercontent.com/huangkouping/egern/main/taobao-adblock.js?v={js_hash}")
        out.append("    body_required: true")
        out.append("    timeout: 20")
    out.append("mitm:")
    out.append("  hostnames:")
    out.append("    includes:")
    hosts = list(mitm)
    for h in EXTRA_MITM:
        if h not in hosts:
            hosts.append(h)
    for h in hosts:
        out.append(f"    - {h}")
    return "\n".join(out) + "\n"


def build_js(src):
    return f"""/* RuCu6 淘宝去广告脚本（经可莉分发，脚本头注引用 RuCu6/QuanX myBlockAds.js，2024-01-12）；由 scripts/sync-taobao.py 自可莉官方 GitHub 分发仓 Moli-X/Tool 同步，源逻辑保持，仅补充单次完成与异常透传包装。
 * Source: https://raw.githubusercontent.com/Moli-X/Tool/main/Loon/Plugin/Kelee/Script/Taobao_remove_ads.js
 * 处理：开屏视频（时长归零/资源清空）、开屏图（等待归零/时间推至 2090 年/素材清空）、开屏活动弹窗（素材清空/停用）。
 */
(function (complete) {{
let finished = false;
const $done = value => {{ if (!finished) {{ finished = true; complete(value); }} }};
try {{
if (typeof $response === "undefined" || typeof $response.body !== "string") return $done({{}});
{src}
}} catch (_) {{ $done({{}}); }}
}})($done);
"""


def main():
    try:
        plugin = fetch(PLUGIN_URL)
        js_src = fetch(JS_URL)
    except Exception as e:
        fail(f"下载上游失败: {e}")
    upstream_date, domains, rewrites, scriptings, mitm = parse_plugin(plugin)
    if "taobao-splash" not in js_src or "poplayer" not in js_src:
        fail("上游脚本内容异常（缺少 taobao-splash/poplayer 关键逻辑），保留上次有效版本")
    js_hash = hashlib.sha256(js_src.encode()).hexdigest()[:10]
    yaml_text = build_yaml(domains, rewrites, scriptings, mitm, js_hash)
    js_text = build_js(js_src)
    try:
        import yaml as _yaml
        parsed = _yaml.safe_load(yaml_text)
        assert parsed["name"] == "淘宝去广告🅥"
    except Exception as e:
        fail(f"生成的 YAML 校验失败: {e}")
    YAML_FILE.write_text(yaml_text)
    JS_FILE.write_text(js_text)
    status = {
        "module": "taobao-adblock",
        "upstream": {
            "plugin_url": PLUGIN_URL,
            "js_url": JS_URL,
            "upstream_date": upstream_date,
            "plugin_sha256": hashlib.sha256(plugin.encode()).hexdigest(),
            "js_sha256": hashlib.sha256(js_src.encode()).hexdigest(),
        },
        "counts": {
            "rules": len(domains),
            "rewrites": len(rewrites) + len(GRAFT_RESPOND),
            "grafted_rewrites": len(GRAFT_RESPOND),
            "url_rewrites": len(GRAFT_URL_REWRITES),
            "scriptings": len(scriptings),
        },
        "synced_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "error": None,
    }
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(f"OK upstream_date={upstream_date} rules={len(domains)} rewrites={len(rewrites)}+{len(GRAFT_RESPOND)} scriptings={len(scriptings)} js_hash={js_hash}")


if __name__ == "__main__":
    main()
