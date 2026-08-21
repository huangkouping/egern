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

# 用户根据 Egern 实际连接日志确认：以下 4 个 Apple 域名不纳入直连，
# 统一加入“苹果服务”代理策略。与上游 AppleService 规则分开维护，避免后续同步丢失。
CUSTOM_PROXY_RULES = [
    (
        "iTunes 服务入口（用户确认：走苹果服务）",
        "DOMAIN,itunes.com",
    ),
    (
        "iPhone 信息提交服务（用户确认：走苹果服务）",
        "DOMAIN,iphonesubmissions.apple.com",
    ),
    (
        "Apple Key Transparency 服务（用户确认：走苹果服务）",
        "DOMAIN,kt-prod.ess.apple.com",
    ),
    (
        "Apple 后台服务（公开用途不明确；用户确认：走苹果服务）",
        "DOMAIN,humb.apple.com",
    ),
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
        "# 使用方法：在 Egern 中订阅本文件，并将策略设置为“苹果服务”",
        "# iCloud 过滤策略：自动排除 icloud.com 及其全部子域名，继续由直连规则处理",
        f"# 本次过滤的 iCloud 规则：{', '.join(excluded) if excluded else '无'}",
        "",
        "# ===== Apple 地区受限服务（代理） =====",
        *rules,
        "",
        "# ===== 用户确认的 Apple 服务（代理） =====",
        "# 以下 4 个域名来自用户实际连接日志，均曾因未命中规则而走兜底香港节点。",
        "# 用户明确指定：不走直连，统一交给 Egern 的“苹果服务”策略。",
    ]

    for title, rule in CUSTOM_PROXY_RULES:
        output.append(f"# {title}")
        output.append(rule)
        output.append("")

    new_content = "\n".join(output)

    if OUTPUT.exists():
        old_content = OUTPUT.read_text(encoding="utf-8")
        if UPDATED_PREFIX in old_content and without_updated_at(old_content) == without_updated_at(new_content):
            print("规则内容没有变化，保留原更新时间")
            return

    OUTPUT.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    main()
