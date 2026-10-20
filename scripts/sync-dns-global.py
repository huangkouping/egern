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
DOMESTIC = Path("dns-cn.list")
# DNS conflict policy: domestic exact rules win; overseas-specific rules stay abroad.
# The large GMOogway proxy list must not override known domestic DNS rules.
def domestic_keys():
    if not DOMESTIC.is_file():
        raise RuntimeError("Missing dns-cn.list; cannot safely audit cross-list conflicts")
    keys = set()
    for line in DOMESTIC.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,")):
            keys.add(line.lower())
    if len(keys) < 1000:
        raise RuntimeError("Domestic DNS file unexpectedly small; refusing unsafe update")
    return keys

DOMESTIC_KEYS = domestic_keys()
excluded = []
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
        if key in DOMESTIC_KEYS:
            excluded.append((name, rule))
            continue
        # .cn is intentionally handled by the local Egern domestic wildcard.
        if parts[0].upper() in {"DOMAIN", "DOMAIN-SUFFIX"} and parts[1].lower().endswith(".cn"):
            excluded.append((name, rule))
            continue
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
    "# 冲突处理：完全相同的国内域名规则及 .cn 域名归国内 DNS；保留其他海外规则",
    f"# 本次跨文件排除：{len(excluded)} 条（含不同上游重复排除记录）",
    "# 注意：关键词、父子域名等隐性重叠需结合 Egern 实际匹配顺序验证",
    "",
]
for name, rules in sections:
    lines.extend([f"# ===== {name}（{len(rules)} 条） =====", *rules, ""])
# Guard against missing critical foreign services or accidental reintroduction
# of exact domestic overlaps. Other parent/child overlaps are intentionally
# retained because deleting them would break region-specific subdomains.
critical = {
    "DOMAIN-SUFFIX,openai.com",
    "DOMAIN-SUFFIX,google.com",
    "DOMAIN-SUFFIX,telegram.org",
    "DOMAIN-SUFFIX,tiktok.com",
}
missing = critical - seen
if missing:
    raise RuntimeError(f"Missing critical overseas DNS rules: {sorted(missing)}")
if seen & DOMESTIC_KEYS:
    raise RuntimeError("Exact domestic/foreign DNS overlap detected")
if len(seen) < 10000:
    raise RuntimeError("Overseas DNS rules unexpectedly small")
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated {OUTPUT}: {len(seen)} rules from {len(SOURCES)} sources; excluded {len(excluded)} domestic conflicts")
