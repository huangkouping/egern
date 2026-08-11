#!/usr/bin/env python3
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUTPUT = Path("custom-direct.list")
FETCH_ATTEMPTS = 4
RETRY_DELAYS = (3, 8, 15)

CUSTOM_RULES = [
    "DOMAIN-KEYWORD,localhost",
    "DOMAIN-KEYWORD,icsignx",
    "DOMAIN-SUFFIX,wuchuyun.com",
    "DOMAIN-SUFFIX,sentry.io",
    "DOMAIN-SUFFIX,snssdk.com",
]

# 这里只同步用户明确指定的“防去广告误杀”直连来源。
# 不要为了补全 App 分流而加入普通业务、广告、统计或推广域名。
SOURCES = [
    (
        "微信防误杀规则（blackmatrix7）",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/WeChat/WeChat.list",
    ),
    (
        "抖音防误杀规则（fmz200）",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/Douyin.list",
    ),
    (
        "抖音 PCDN 防误杀规则（takoyakiwhite）",
        "https://raw.githubusercontent.com/takoyakiwhite/asoul_mirror/main/douyin_pcdn.list",
    ),
    (
        "小红书防误杀规则（blackmatrix7）",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/XiaoHongShu/XiaoHongShu.list",
    ),
]


def download_text(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "custom-direct-rule-sync/2.0",
                    "Accept": "text/plain,*/*",
                },
            )
            with urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt == FETCH_ATTEMPTS:
                break
            delay = RETRY_DELAYS[attempt - 1]
            print(f"下载失败（{attempt}/{FETCH_ATTEMPTS}）：{url}；{delay} 秒后重试：{error}")
            time.sleep(delay)

    raise RuntimeError(
        f"上游连续 {FETCH_ATTEMPTS} 次下载失败，保留现有输出文件：{url}"
    ) from last_error


def fetch_rules(url: str) -> list[str]:
    text = download_text(url)
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
        raise RuntimeError(f"上游规则为空，保留现有输出文件：{url}")
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
        "# Egern 防去广告误杀直连规则集",
        "# 本文件由 GitHub Actions 自动生成，请勿直接编辑生成内容",
        "# 用途：让被去广告规则误拦的正常内容恢复显示",
        "# 在 Egern 中订阅本文件，并将策略统一设置为 DIRECT",
        "# 不以补全 App 分流为目标，不主动收录广告、统计或推广域名",
        "# 相同规则按首次出现位置保留，后续分组中的重复项自动忽略",
        "",
    ]
    seen: set[str] = set()
    output.extend(section("自定义防误杀规则", unique_rules(CUSTOM_RULES, seen)))

    for title, url in SOURCES:
        rules = unique_rules(fetch_rules(url), seen)
        output.extend(section(title, rules, url))

    # 只有全部上游成功后才覆盖，任何一个来源失败都会保留旧文件。
    OUTPUT.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
