#!/usr/bin/env python3
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE = "https://raw.githubusercontent.com/Bwy999/Surge/master/Ruleset/AppleService.list"
OUTPUT = Path("apple-service-proxy.list")
UPDATED_PREFIX = "# 规则内容更新时间（北京时间）："
FETCH_ATTEMPTS = 4
RETRY_DELAYS = (3, 8, 15)

# Apple 官方列出的 Apple Intelligence、Siri 与 Private Cloud Compute 端点。
APPLE_INTELLIGENCE_RULES = [
    "DOMAIN,guzzoni.apple.com",
    "DOMAIN,apple-relay.cloudflare.com",
    "DOMAIN,apple-relay.fastly-edge.com",
    "DOMAIN,cp4.cloudflare.com",
    "DOMAIN,apple-relay.apple.com",
]


def download_text() -> str:
    last_error: Exception | None = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            request = Request(
                SOURCE,
                headers={
                    "User-Agent": "apple-service-proxy-sync/1.0",
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
            print(f"下载失败（{attempt}/{FETCH_ATTEMPTS}），{delay} 秒后重试：{error}")
            time.sleep(delay)
    raise RuntimeError("AppleService 上游下载失败，保留现有输出文件") from last_error


def is_icloud_rule(line: str) -> bool:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 2:
        return False
    rule_type = parts[0].upper()
    value = parts[1].lower().rstrip(".")
    return rule_type in {"DOMAIN", "DOMAIN-SUFFIX"} and (
        value == "icloud.com" or value.endswith(".icloud.com")
    )


def without_updated_at(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.startswith(UPDATED_PREFIX)
    ).rstrip() + "\n"


def main() -> None:
    rules: list[str] = []
    seen: set[str] = set()
    excluded: list[str] = []

    for raw_line in download_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if "," in line:
            rule_type, value = line.split(",", 1)
            line = f"{rule_type.strip().upper()},{value.strip()}"
        if is_icloud_rule(line):
            excluded.append(line)
            continue
        key = line.lower()
        if key not in seen:
            seen.add(key)
            rules.append(line)

    if not rules:
        raise RuntimeError("过滤后的 AppleService 规则为空，保留现有输出文件")

    updated_at = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    output = [
        "# Apple 地区受限服务代理规则集（排除 iCloud）",
        "# 本文件由 GitHub Actions 自动同步生成，请勿直接编辑生成内容",
        f"{UPDATED_PREFIX}{updated_at}",
        f"# 上游来源：{SOURCE}",
        "# 使用方法：在 Egern 中订阅本文件，并选择合适的境外代理策略",
        "# iCloud 过滤策略：自动排除 icloud.com 及其全部子域名，继续由直连规则处理",
        f"# 本次过滤的 iCloud 规则：{', '.join(excluded) if excluded else '无'}",
        "",
        "# ===== Apple 地区受限服务（代理） =====",
        *rules,
        "",
        "# ===== Apple Intelligence / Siri / Private Cloud Compute（代理） =====",
        "# 来源：https://support.apple.com/101555",
        *[rule for rule in APPLE_INTELLIGENCE_RULES if rule.lower() not in seen],
        "",
    ]
    new_content = "\n".join(output)

    if OUTPUT.exists():
        old_content = OUTPUT.read_text(encoding="utf-8")
        if UPDATED_PREFIX in old_content and without_updated_at(old_content) == without_updated_at(new_content):
            print("规则内容没有变化，保留原更新时间")
            return

    OUTPUT.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    main()
