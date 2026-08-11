#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen

OUTPUT = Path("custom-direct.list")

CUSTOM_RULES = [
    "DOMAIN-KEYWORD,localhost",
    "DOMAIN-KEYWORD,icsignx",
    "DOMAIN-SUFFIX,wuchuyun.com",
    "DOMAIN-SUFFIX,sentry.io",
    "DOMAIN-SUFFIX,snssdk.com",
]

SOURCES = [
    (
        "微信规则（blackmatrix7）",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/WeChat/WeChat.list",
    ),
    (
        "抖音规则（fmz200）",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/Douyin.list",
    ),
    (
        "抖音补充规则（blackmatrix7）",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/DouYin/DouYin.list",
    ),
    (
        "抖音 PCDN 规则（takoyakiwhite）",
        "https://raw.githubusercontent.com/takoyakiwhite/asoul_mirror/main/douyin_pcdn.list",
    ),
    (
        "小红书规则（blackmatrix7）",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/XiaoHongShu/XiaoHongShu.list",
    ),
]


def fetch_rules(url: str) -> list[str]:
    request = Request(url, headers={"User-Agent": "custom-direct-rule-sync/1.0"})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8-sig")

    rules = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if "," in line:
            rule_type, value = line.split(",", 1)
            line = f"{rule_type.strip().upper()},{value.strip()}"
        rules.append(line)
    if not rules:
        raise RuntimeError(f"上游规则为空，停止覆盖输出文件：{url}")
    return rules


def unique_rules(rules: list[str], seen: set[str]) -> list[str]:
    unique = []
    for rule in rules:
        key = rule.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(rule)
    return unique


def section(title: str, rules: list[str], source: str | None = None) -> list[str]:
    lines = [f"# ===== {title} ====="]
    if source:
        lines.append(f"# 来源：{source}")
    lines.extend(rules)
    lines.append("")
    return lines


def main() -> None:
    output = [
        "# Egern 自定义直连规则集",
        "# 本文件由 GitHub Actions 自动生成，请勿直接编辑生成内容",
        "# 在 Egern 中订阅本文件，并将策略统一设置为 DIRECT",
        "# 相同规则按首次出现位置保留，后续分组中的重复项自动忽略",
        "",
    ]
    seen: set[str] = set()
    output.extend(section("自定义规则", unique_rules(CUSTOM_RULES, seen)))

    for title, url in SOURCES:
        rules = unique_rules(fetch_rules(url), seen)
        output.extend(section(title, rules, url))

    OUTPUT.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
