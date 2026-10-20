#!/usr/bin/env python3
"""Sync domestic DNS domains from Loon rulesets and local regex domains."""
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCES = {
    "DouYin": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/DouYin/DouYin.list",
    "China": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/China/China.list",
    "China_Domain": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/China/China_Domain.list",
    "Direct": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Direct/Direct.list",
}
LOCAL_DOMAINS = [
    "mzstatic.com", "cdn-apple.com", "apps.apple.com", "itunes.apple.com",
    "douyin.com", "douyinpic.com", "douyinstatic.com", "douyinvod.com",
    "iesdouyin.com", "snssdk.com", "amemv.com", "bytecdn.com",
    "bytedance.com", "ibyteimg.com", "ibytedtos.com", "muscdn.com",
    "ixigua.com", "volcvideo.com", "volcgslb.com", "toutiaocloud.com",
]
OUTPUT = Path("dns-cn.list")
ALLOWED = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
EXCLUDED_RULES = {
    "DOMAIN-SUFFIX,ms",
    "DOMAIN-SUFFIX,windows.net",
    "DOMAIN-KEYWORD,microsoft",
    "DOMAIN-KEYWORD,icloud.com",
    "DOMAIN-KEYWORD,trip.com",
}
excluded = []
seen = set()
sections = []

def add(rule, target):
    if rule.upper() in EXCLUDED_RULES:
        excluded.append(rule)
        return
    key = rule.replace(" ", "").lower()
    if key not in seen:
        seen.add(key)
        target.append(rule)

local = []
for domain in LOCAL_DOMAINS:
    add("DOMAIN-SUFFIX," + domain, local)
sections.append(("本地正则转换（包含全部子域名）", local))

for name, url in SOURCES.items():
    req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"})
    with urlopen(req, timeout=40) as response:
        data = response.read().decode("utf-8-sig")
    rules = []
    for raw in data.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if name == "China_Domain":
            if line.startswith("."):
                add("DOMAIN-SUFFIX," + line[1:], rules)
            elif "." in line and " " not in line and "," not in line:
                add("DOMAIN," + line, rules)
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0].upper() in ALLOWED and parts[1]:
            add(parts[0].upper() + "," + parts[1], rules)
    if not rules and name != "Direct":
        raise RuntimeError(f"{name} yielded no DNS-compatible domain rules")
    sections.append((name + " 上游规则", rules))

now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
lines = [
    "# 国内 DNS 规则集©️",
    "# 自动同步生成；供 Egern DNS forward 的 proxy_rule_set 使用",
    f"# 规则内容更新时间（北京时间）：{now}",
    "# 原始正则已转为 DOMAIN-SUFFIX，主域名及子域名均匹配",
    "# 仅保留 DNS 可匹配的域名类规则，排除 IP-CIDR / GEOIP 等",
    "# 上游：" + " | ".join(SOURCES.values()),
    "# 已排除宽泛规则：" + ", ".join(sorted(EXCLUDED_RULES)),
    "",
]
for name, rules in sections:
    lines += [f"# ===== {name}（{len(rules)} 条） =====", *rules, ""]
assert len(seen) > 3000, "Unexpectedly small domestic ruleset"
assert not any(r in seen for r in EXCLUDED_RULES)
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated {OUTPUT}: {sum(len(x[1]) for x in sections)} unique rules")
