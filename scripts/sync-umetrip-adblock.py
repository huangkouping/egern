#!/usr/bin/env python3
"""Synchronize the ddgksf2013 Umetrip ad-block source for Egern."""

import re
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

CONFIG_URL = "https://ddgksf2013.top/rewrite/UmetripAds.conf"
CONFIG_SNAPSHOT = Path("upstreams/umetrip-ddgksf.conf")
SCRIPT_OUTPUT = Path("umetrip-adblock.js")
MODULE_OUTPUT = Path("umetrip-adblock.yaml")
RULE_UPDATED_PREFIX = "  规则更新时间："
CHECKED_PREFIX = "  同步检查："
SOURCE_STATUS_PREFIX = "  墨鱼源："
RETRIES = 4


def fetch(url: str, user_agents: tuple[str, ...]) -> tuple[str | None, str | None]:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        for user_agent in user_agents:
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/plain,*/*",
                        "Referer": "https://ddgksf2013.top/",
                    },
                )
                with urlopen(request, timeout=45) as response:
                    text = response.read().decode("utf-8-sig")
                if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
                    raise ValueError("服务器返回了网页而不是规则文件")
                return text, None
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
                last_error = error
        if attempt < RETRIES:
            delay = (3, 8, 15)[attempt - 1]
            print(f"下载失败（{attempt}/{RETRIES}）：{url}；{delay} 秒后重试：{last_error}")
            time.sleep(delay)
    return None, str(last_error or "未知错误")


def validate_config(text: str) -> None:
    required = ("hostname =", "script-response-body", "umetrip.ads.js")
    if not all(token in text for token in required):
        raise RuntimeError("墨鱼版配置校验失败")


def validate_script(text: str) -> None:
    if len(text) < 500 or "$done" not in text or "cleanDocument" not in text:
        raise RuntimeError("墨鱼版脚本校验失败")


def parse_hosts(text: str) -> list[str]:
    hosts: set[str] = set()
    for line in text.splitlines():
        if re.match(r"^\s*hostname\s*=", line, re.I):
            hosts.update(value.strip() for value in line.split("=", 1)[1].split(",") if value.strip())
    return sorted(hosts)


def find_script_url(text: str) -> str:
    match = re.search(r"script-response-body\s+(https?://\S+)", text)
    if not match:
        raise RuntimeError("未在墨鱼版配置中找到响应脚本地址")
    return match.group(1)


def parse_rejects(text: str) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", ";")):
            continue
        match = re.match(r"^(\^\S+?)(?:\s+url)?\s+(reject(?:-img|-dict|-array|-200|-video)?)\b", stripped, re.I)
        if not match:
            continue
        pattern, action = match.group(1), match.group(2).lower()
        location = {
            "reject": "http://reject/",
            "reject-img": "http://reject-img/",
            "reject-dict": "http://reject-dict/",
            "reject-array": "http://reject-array/",
            "reject-200": "http://reject-200/",
            "reject-video": "http://reject-video/",
        }[action]
        key = (pattern, location)
        if key not in seen:
            seen.add(key)
            rules.append(key)
    return rules


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def without_runtime_status(text: str) -> str:
    prefixes = (RULE_UPDATED_PREFIX, CHECKED_PREFIX, SOURCE_STATUS_PREFIX, "  Kelee源：")
    return "\n".join(line for line in text.splitlines() if not line.startswith(prefixes)).rstrip() + "\n"


def old_rule_timestamp(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith(RULE_UPDATED_PREFIX):
            return line.removeprefix(RULE_UPDATED_PREFIX).removesuffix("（北京时间）")
    return fallback


def short_error(error: str) -> str:
    http_error = re.search(r"HTTP Error (\d+)", error)
    if http_error:
        return f"HTTP {http_error.group(1)}"
    return error.replace("\n", " ")[:48]


def snapshot_date(text: str) -> str:
    match = re.search(r"(?im)^\s*//\s*@UpdateTime\s+([^\r\n]+)", text)
    return match.group(1).strip() if match else "最近有效版本"


def build_module(config_text: str, rule_stamp: str, checked_stamp: str, source_status: str, cache_key: str) -> str:
    hosts = parse_hosts(config_text)
    response_hosts = [host for host in hosts if host != "oss.umetrip.com"]
    domain_parts = [re.escape(host) for host in response_hosts]
    response_match = rf"^https?://(?:{'|'.join(domain_parts)})/gateway/api/umetrip/native(?:\\?.*)?$"

    lines = [
        "name: 航旅纵横去广告",
        "description: |-",
        "  屏蔽开屏、首页及应用内广告。",
        f"{RULE_UPDATED_PREFIX}{rule_stamp}（北京时间）",
        f"{CHECKED_PREFIX}{checked_stamp}（北京时间）",
        f"{SOURCE_STATUS_PREFIX}{source_status}",
        "author: ddgksf2013 / huangkouping",
        "icon: airplane",
        "homepage: https://github.com/huangkouping/egern",
        "",
        "url_rewrites:",
    ]
    for pattern, location in parse_rejects(config_text):
        lines.extend([f"  - match: {yaml_quote(pattern)}", f"    location: {yaml_quote(location)}"])
    lines.extend(
        [
            "",
            "scriptings:",
            "  - http_response:",
            "      name: 航旅纵横广告净化",
            f"      match: {yaml_quote(response_match)}",
            f"      script_url: https://raw.githubusercontent.com/huangkouping/egern/main/umetrip-adblock.js?v={cache_key}",
            "      body_required: true",
            "      timeout: 15",
            "      update_interval: 3600",
            "",
            "mitm:",
            "  hostnames:",
            "    includes:",
        ]
    )
    lines.extend(f"      - {host}" for host in hosts)
    return "\n".join(lines) + "\n"


def main() -> None:
    downloaded_config, config_error = fetch(CONFIG_URL, ("Surge", "Quantumult X"))
    if downloaded_config is not None:
        validate_config(downloaded_config)
        config_text = downloaded_config
    elif CONFIG_SNAPSHOT.exists():
        config_text = CONFIG_SNAPSHOT.read_text(encoding="utf-8")
        validate_config(config_text)
    else:
        raise RuntimeError("墨鱼源不可用且仓库中没有有效配置快照")

    script_url = find_script_url(config_text)
    downloaded_script, script_error = fetch(script_url, ("Quantumult X", "Surge"))
    if downloaded_script is not None:
        validate_script(downloaded_script)
        script_text = downloaded_script
    elif SCRIPT_OUTPUT.exists():
        script_text = SCRIPT_OUTPUT.read_text(encoding="utf-8")
        validate_script(script_text)
    else:
        raise RuntimeError("墨鱼源脚本不可用且仓库中没有有效脚本快照")

    errors = [short_error(error) for error in (config_error, script_error) if error]
    if errors:
        source_status = f"失败（{', '.join(dict.fromkeys(errors))}，使用快照 {snapshot_date(config_text)}）"
    else:
        source_status = "成功"

    old_script = SCRIPT_OUTPUT.read_text(encoding="utf-8") if SCRIPT_OUTPUT.exists() else ""
    script_changed = old_script != script_text
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    stamp = now.strftime("%Y-%m-%d %H:%M")
    cache_key = now.strftime("%Y%m%d%H%M")
    old_module = MODULE_OUTPUT.read_text(encoding="utf-8") if MODULE_OUTPUT.exists() else ""
    if old_module and not script_changed:
        old_cache_key = re.search(r"umetrip-adblock\.js\?v=(\d+)", old_module)
        if old_cache_key:
            cache_key = old_cache_key.group(1)

    candidate = build_module(config_text, stamp, stamp, source_status, cache_key)
    if old_module and not script_changed and without_runtime_status(old_module) == without_runtime_status(candidate):
        rule_stamp = old_rule_timestamp(old_module, stamp)
        candidate = build_module(config_text, rule_stamp, stamp, source_status, cache_key)
        print("有效规则没有变化，保留原规则更新时间；刷新同步状态")

    CONFIG_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    if downloaded_config is not None:
        CONFIG_SNAPSHOT.write_text(config_text.rstrip() + "\n", encoding="utf-8")
    SCRIPT_OUTPUT.write_text(script_text.rstrip() + "\n", encoding="utf-8")
    MODULE_OUTPUT.write_text(candidate, encoding="utf-8")


if __name__ == "__main__":
    main()
