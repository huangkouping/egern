#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

UPSTREAM = "https://kelee.one/Tool/Loon/Lsr/AI.lsr"
OUTPUT = Path("ai.list")

MUSE_RULES = [
    "DOMAIN-SUFFIX,meta.ai",
    "DOMAIN-SUFFIX,ai.meta.com",
    "DOMAIN-SUFFIX,muse.com",
    "DOMAIN-SUFFIX,muse.ai",
    "DOMAIN,api.meta.ai",
    "DOMAIN,graph.meta.ai",
    "DOMAIN,www.meta.ai",
    "DOMAIN-KEYWORD,meta-ai",
    "DOMAIN-KEYWORD,metaai",
]

req = Request(UPSTREAM, headers={
    "User-Agent": "Loon/852 CFNetwork/3860.300.31 Darwin/25.2.0",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://kelee.one/",
    "Cache-Control": "no-cache",
})
with urlopen(req, timeout=30) as resp:
    raw = resp.read().decode("utf-8-sig")

upstream_rules = []
seen = set()
for line in raw.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if line not in seen:
        seen.add(line)
        upstream_rules.append(line)

custom_rules = []
for rule in MUSE_RULES:
    if rule not in seen:
        seen.add(rule)
        custom_rules.append(rule)

now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")

lines = [
    "# AI 服务代理规则集（含 Muse）",
    "# 本文件由 GitHub Actions 自动同步生成，请勿直接编辑",
    f"# 规则内容更新时间（北京时间）：{now}",
    f"# 上游来源：{UPSTREAM}",
    '# 使用方法：在 Egern 中订阅本文件，并将策略设置为“AI”',
    "# 同步策略：完整同步上游 AI 规则，并自动合并 Muse 自定义规则",
    "",
    "# ===== AI 服务（上游同步） =====",
    *upstream_rules,
    "",
    "# ===== Muse 自定义补充规则 =====",
    *custom_rules,
    "",
]
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"已生成 {OUTPUT}：上游 {len(upstream_rules)} 条，Muse 新增 {len(custom_rules)} 条")
