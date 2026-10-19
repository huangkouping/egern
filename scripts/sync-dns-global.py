#!/usr/bin/env python3
"""Merge DNS-compatible foreign domain rules from upstream sources."""
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCES = [
 ("TikTok", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/TikTok/TikTok.list"),
 ("Ai&US", "https://raw.githubusercontent.com/huangkouping/egern/main/us.list"),
 ("Crypto", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Crypto/Crypto.list"),
 ("Binance", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Binance/Binance.list"),
 ("Telegram", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Telegram/Telegram.list"),
 ("YouTube", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/YouTube/YouTube.list"),
 ("Instagram", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Instagram/Instagram.list"),
 ("Twitter", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Twitter/Twitter.list"),
 ("Google", "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Google/Google.list"),
 ("GMOogway", "https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_proxy_list.module"),
]
OUTPUT = Path("dns-global.list")
ALLOWED = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
seen = set()
sections = []

def fetch(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"})
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8-sig")

for name, url in SOURCES:
    raw = fetch(url)
    rules = []
    for rawline in raw.splitlines():
        line = rawline.strip()
        if not line or line.startswith(("#", ";", "//", "[", "!")):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2 or parts[0].upper() not in ALLOWED or not parts[1]:
            continue
        rule = parts[0].upper() + "," + parts[1]
        key = rule.lower()
        if key not in seen:
            seen.add(key)
            rules.append(rule)
    if not rules:
        raise RuntimeError(f"No compatible domain rules found in {name}: {url}")
    sections.append((name, rules))
now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
lines = [
    "# 国外 DNS 规则集©️",
    "# GitHub Actions 自动同步生成；供 Egern DNS forward 的 proxy_rule_set 使用",
    f"# 规则内容更新时间（北京时间）：{now}",
    "# 已剔除代理策略字段、IP-CIDR/GEOIP 等非域名规则，按规则类型及内容排重",
    "# 注意：此规则集不等于代理分流规则；请将国外 DNS 规则置于国内兜底规则之前",
    "",
]
for name, rules in sections:
    lines.extend([f"# ===== {name}（{len(rules)} 条） =====", *rules, ""])
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated {OUTPUT}: {len(seen)} rules from {len(SOURCES)} sources")
