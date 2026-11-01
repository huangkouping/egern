#!/usr/bin/env python3
"""Sync the Meituan adblock module from ZenmoFeiShi/Qx (MT.snippet + MT.js); retain last-good output on failure.

The QX snippet is converted to Egern-native structures:
- host rejects            -> rules: domain REJECT
- host-wildcard reject    -> rules: url_regex REJECT (scoped to that host pattern)
- ip-cidr / ip6-cidr      -> rules: ip_cidr REJECT (no_resolve)
- url reject lines        -> rules: url_regex REJECT
- script-response-body    -> scriptings: http_response running the mirrored MT.js
- hostname list           -> mitm hostnames
Any unrecognized snippet line aborts the sync so a changed upstream format
never silently produces a partial module.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
SNIPPET_URL = 'https://raw.githubusercontent.com/ZenmoFeiShi/Qx/refs/heads/main/MT.snippet'
JS_URL = 'https://raw.githubusercontent.com/ZenmoFeiShi/Qx/refs/heads/main/MT.js'
MODULE = ROOT / 'meituan-adblock.yaml'
SCRIPT = ROOT / 'meituan-adblock.js'
META = ROOT / 'meituan-sync-status.json'
RAW_BASE = 'https://raw.githubusercontent.com/huangkouping/egern/main/'

SCRIPT_NAMES = [
    ('aggroup/indexTab', '美团首页Tab过滤'),
    ('lycoris/scene', '美团信息流过滤'),
    ('usercenter/display', '美团个人中心过滤'),
    ('searchpage/defaultword', '美团搜索默认词过滤'),
    ('hotrecommend', '美团热搜推荐过滤'),
    ('getAppClientHornConfig', '美团小喇叭通知过滤'),
    ('shoppingCartEntry', '美团购物车入口过滤'),
    ('startupPicture', '美团开屏图过滤'),
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Egern-Public-Mirror-Sync/1.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(200001).decode('utf-8')


def parse_snippet(text):
    meta = {}
    domains, ips, url_rules, scripts, mitm = [], [], [], [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#!'):
            key, _, value = line[2:].partition('=')
            meta[key.strip()] = value.strip()
            continue
        if line.startswith('#'):
            continue
        m = re.fullmatch(r'host,\s*([^,]+),\s*reject', line)
        if m:
            domains.append(m.group(1).strip())
            continue
        m = re.fullmatch(r'host-wildcard,\s*([^,]+),\s*reject', line)
        if m:
            pattern = m.group(1).strip()
            host_re = '^https?://' + re.escape(pattern).replace(r'\*', r'[^./]+') + r'(?:[:/]|$)'
            url_rules.append(host_re)
            continue
        m = re.fullmatch(r'ip6?-cidr,\s*([^,]+),\s*reject', line)
        if m:
            ips.append(m.group(1).strip())
            continue
        m = re.fullmatch(r'(\S+)\s+url\s+reject', line)
        if m:
            url_rules.append(m.group(1).replace('\\/', '/'))
            continue
        m = re.fullmatch(r'(\S+)\s+url\s+script-response-body\s+(\S+)', line)
        if m:
            if m.group(2) != JS_URL:
                raise ValueError('Unexpected script URL: ' + m.group(2))
            scripts.append(m.group(1).replace('\\/', '/'))
            continue
        m = re.fullmatch(r'hostname\s*=\s*(.+)', line)
        if m:
            mitm = [h.strip() for h in m.group(1).split(',') if h.strip()]
            continue
        raise ValueError('Unrecognized snippet line: ' + line[:80])
    if len(domains) < 10 or len(ips) < 20 or len(scripts) != 8 or len(mitm) < 5:
        raise ValueError(f'Unexpected snippet shape: domains={len(domains)} ips={len(ips)} scripts={len(scripts)} mitm={len(mitm)}')
    return meta, domains, ips, url_rules, scripts, mitm


def adapt(source):
    if len(source) < 500 or len(source) > 100000:
        raise ValueError('Unexpected MT.js size')
    if 'mtqx' not in source or '$done' not in source or '$response' not in source:
        raise ValueError('MT.js signature missing')
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', 'eval(', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    result = ('/* ZenmoFeiShi 美团去广告脚本备份（源自 ZenmoFeiShi/Qx MT.js）；源逻辑保持，补充异常透传与单次完成。\n'
              ' * Source: ' + JS_URL + '\n */\n'
              '(function (complete) {\nlet finished = false;\n'
              'const $done = value => { if (!finished) { finished = true; complete(value); } };\n'
              'try {\nif (typeof $response === "undefined" || typeof $response.body !== "string") return $done({});\n'
              + source + '\n} catch (_) { $done({}); }\n})($done);\n')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(result)
        path = handle.name
    check = subprocess.run(['node', '--check', path], capture_output=True, text=True, timeout=15)
    if check.returncode:
        raise ValueError('JavaScript syntax check failed')
    smoke = r'''
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
function run(url, bodyObj) {
  return new Promise(resolve => {
    global.$request = { url };
    global.$response = { body: JSON.stringify(bodyObj) };
    global.$done = v => resolve(v);
    eval(src);
  });
}
(async () => {
  const tab = await run("https://apimobile.meituan.com/aggroup/indexTab",
    { data: { resource: { tabArea: [{ tabName: "homepage" }, { tabName: "video" }, { tabName: "mine" }] } } });
  const names = JSON.parse(tab.body).data.resource.tabArea.map(t => t.tabName);
  if (names.join(",") !== "homepage,mine") throw new Error("indexTab smoke failed: " + names);
  const feed = await run("https://feedguess.meituan.com/lycoris/scene/gwc_feed1_2265?x=1",
    { data: [{ a: 1 }, { a: 2 }] });
  if (JSON.parse(feed.body).data.length !== 0) throw new Error("feed smoke failed");
  console.log("smoke ok");
})().catch(e => { console.error(e.message); process.exit(1); });
'''
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(smoke)
        smoke_path = handle.name
    run = subprocess.run(['node', smoke_path, path], capture_output=True, text=True, timeout=15)
    if run.returncode or 'smoke ok' not in run.stdout:
        raise ValueError('Smoke test failed: ' + (run.stderr or run.stdout)[:200])
    return result


def description(meta):
    state = '上游同步正常' if meta['status'] == 'ok' else '上游同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '去除美团开屏、首页Tab、搜索热词、个人中心等广告与推广。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")


def build(version, parsed):
    meta, domains, ips, url_rules, scripts, mitm = parsed
    rules = [{'domain': {'match': d, 'policy': 'REJECT'}} for d in domains]
    rules += [{'ip_cidr': {'match': ip, 'policy': 'REJECT', 'no_resolve': True}} for ip in ips]
    rules += [{'url_regex': {'match': p, 'policy': 'REJECT'}} for p in url_rules]
    scriptings = []
    for pattern in scripts:
        name = next((n for key, n in SCRIPT_NAMES if key in pattern), '美团去广告脚本')
        scriptings.append({'http_response': {
            'name': name, 'match': pattern,
            'script_url': RAW_BASE + 'meituan-adblock.js?v=' + version,
            'body_required': True, 'timeout': 20}})
    app = meta.get('name', '美团')
    return {
        'name': '美团去广告©️',
        'author': 'ZenmoFeiShi[https://github.com/ZenmoFeiShi/Qx]',
        'homepage': 'https://github.com/huangkouping/egern',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/1024px/%E7%BE%8E%E5%9B%A2.png',
        'compat_arguments_desc': ('【使用说明】\n启用模块，确认 MitM 已开启且证书受信任，然后重新打开美团。\n关闭其他美团去广告模块，避免重复处理。\n'
            f'规则与脚本镜像自 ZenmoFeiShi/Qx（MT.snippet / MT.js），上游标注适用 {app}；JS 已备份到本仓库，每 6 小时自动检查上游更新，失败时保留上次有效版本。\n'
            '拦截层包含 shark 广告域名、美团 HTTPDNS 域名及上游维护的广告服务器 IP 名单；若美团出现加载慢、定位异常，先停用本模块验证是否为 HTTPDNS 拦截所致。\n'
            'QX 的 host-wildcard（mquic-*）与两条 url reject 已等价转换为 url_regex 规则；当前效果待实机验证。'),
        'dns': {},
        'rules': rules,
        'scriptings': scriptings,
        'mitm': {'hostnames': {'includes': mitm}}}


def main():
    checked = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old = json.loads(META.read_text()) if META.exists() else {}
    try:
        snippet = fetch(SNIPPET_URL)
        source = fetch(JS_URL)
        parsed = parse_snippet(snippet)
        script = adapt(source)
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12], parsed)
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_snippet': SNIPPET_URL, 'source_script': JS_URL,
                'source_update': parsed[0].get('update'), 'source_name': parsed[0].get('name'),
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'counts': {'domains': len(parsed[1]), 'ip_cidr': len(parsed[2]),
                           'url_regex': len(parsed[3]), 'scriptings': len(parsed[4])},
                'scope': 'Mirror ZenmoFeiShi/Qx MT.snippet rules (converted to Egern rules) and MT.js; auto-sync every 6h via Muse cron; last-good retained on failure.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Meituan module sync OK; changed =', changed)
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Meituan sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
