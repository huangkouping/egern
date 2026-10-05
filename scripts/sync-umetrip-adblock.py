#!/usr/bin/env python3
"""Merge the ddgksf2013 and Kelee Umetrip ad-block sources for Egern."""

import re
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

DD_CONFIG_URL = "https://ddgksf2013.top/rewrite/UmetripAds.conf"
KELEE_URL = "https://kelee.one/Tool/Loon/Lpx/Umetrip_remove_ads.lpx"
DD_SNAPSHOT = Path("upstreams/umetrip-ddgksf.conf")
KELEE_SNAPSHOT = Path("upstreams/umetrip-kelee.lpx")
SCRIPT_OUTPUT = Path("umetrip-adblock.js")
MODULE_OUTPUT = Path("umetrip-adblock.yaml")
RULE_UPDATED_PREFIX = "  规则更新时间："
CHECKED_PREFIX = "  同步检查："
DD_STATUS_PREFIX = "  墨鱼源："
KELEE_STATUS_PREFIX = "  Kelee源："
RETRIES = 4
LAST_FETCH_ERRORS: dict[str, str] = {}


def fetch(url: str, user_agents: tuple[str, ...], required: bool = True) -> str | None:
    last_error: Exception | None = None
    attempts = RETRIES if required else 2
    for attempt in range(1, attempts + 1):
        for user_agent in user_agents:
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/plain,*/*",
                        "Referer": "https://ddgksf2013.top/" if "ddgksf2013" in url else "https://kelee.one/",
                    },
                )
                with urlopen(request, timeout=45) as response:
                    text = response.read().decode("utf-8-sig")
                if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
                    raise ValueError("服务器返回了网页而不是规则文件")
                LAST_FETCH_ERRORS.pop(url, None)
                return text
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
                last_error = error
        if attempt < attempts:
            delay = (3, 8, 15)[attempt - 1]
            print(f"下载失败（{attempt}/{attempts}）：{url}；{delay} 秒后重试：{last_error}")
            time.sleep(delay)
    if required:
        raise RuntimeError(f"必需上游下载失败，保留现有文件：{url}") from last_error
    LAST_FETCH_ERRORS[url] = str(last_error or "未知错误")
    print(f"警告：暂时无法读取 {url}，继续使用仓库中的最近有效快照：{last_error}")
    return None


def validate_dd_config(text: str) -> None:
    required = ("hostname =", "script-response-body", "umetrip.ads.js")
    if not all(token in text for token in required):
        raise RuntimeError("墨鱼版配置校验失败，拒绝覆盖现有文件")


def validate_script(text: str) -> None:
    if len(text) < 500 or "$done" not in text or "cleanDocument" not in text:
        raise RuntimeError("墨鱼版脚本校验失败，拒绝覆盖现有文件")


def validate_kelee(text: str) -> None:
    if "umetrip" not in text.lower() or not any(token in text for token in ("[Rewrite]", "[Script]", "hostname")):
        raise RuntimeError("Kelee 配置校验失败，拒绝覆盖最近有效快照")


def parse_hosts(*texts: str) -> list[str]:
    hosts: set[str] = set()
    for text in texts:
        for line in text.splitlines():
            if re.match(r"^\s*hostname\s*=", line, re.I):
                values = line.split("=", 1)[1]
                hosts.update(value.strip() for value in values.split(",") if value.strip())
    hosts.update({"discardrp.umetrip.com", "114.115.217.129"})
    return sorted(hosts, key=lambda value: (value.replace(".", "").isdigit(), value))


def find_dd_script_url(text: str) -> str:
    match = re.search(r"script-response-body\s+(https?://\S+)", text)
    if not match:
        raise RuntimeError("未在墨鱼版配置中找到响应脚本地址")
    return match.group(1)


def parse_rejects(dd_text: str, kelee_text: str) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in (dd_text + "\n" + kelee_text).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", ";")):
            continue
        match = re.match(r"^(\^\S+?)(?:\s+url)?\s+(reject(?:-img|-dict|-array|-200|-video)?)\b", stripped, re.I)
        if not match:
            continue
        pattern, action = match.group(1), match.group(2).lower()
        # Kelee 的旧规则写成了 http?，转换到 Egern 时修正为同时匹配 HTTP/HTTPS。
        pattern = pattern.replace("^http?:", "^https?:", 1)
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
    prefixes = (RULE_UPDATED_PREFIX, CHECKED_PREFIX, DD_STATUS_PREFIX, KELEE_STATUS_PREFIX)
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
    match = re.search(r"(?im)^\s*(?:#!date=|//\s*@UpdateTime\s+)([^\r\n]+)", text)
    return match.group(1).strip() if match else "最近有效版本"


def build_module(
    dd_text: str,
    kelee_text: str,
    rule_stamp: str,
    checked_stamp: str,
    dd_status: str,
    kelee_status: str,
    cache_key: str,
) -> str:
    hosts = parse_hosts(dd_text, kelee_text)
    response_hosts = [host for host in hosts if host not in {"oss.umetrip.com", "startup.umetrip.com", "discardrp.umetrip.com"}]
    domain_parts = [re.escape(host) for host in response_hosts]
    response_match = rf"^https?://(?:{'|'.join(domain_parts)})/gateway/api/umetrip/native(?:\\?.*)?$"
    rejects = parse_rejects(dd_text, kelee_text)

    lines = [
        "name: 航旅纵横去广告",
        "description: |-",
        "  屏蔽开屏、首页及应用内广告。",
        f"{RULE_UPDATED_PREFIX}{rule_stamp}（北京时间）",
        f"{CHECKED_PREFIX}{checked_stamp}（北京时间）",
        f"{DD_STATUS_PREFIX}{dd_status}",
        f"{KELEE_STATUS_PREFIX}{kelee_status}",
        "author: ddgksf2013 / Kelee / huangkouping",
        "icon: https://gitlab.com/lodepuly/iconlibrary/-/raw/main/App_icon/120px/Umetrip.png",
        "homepage: https://github.com/huangkouping/egern",
        "",
        "url_rewrites:",
    ]
    for pattern, location in rejects:
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
    dd_text = fetch(DD_CONFIG_URL, ("Surge", "Quantumult X"), required=True)
    assert dd_text is not None
    validate_dd_config(dd_text)

    dd_script_url = find_dd_script_url(dd_text)
    script_text = fetch(dd_script_url, ("Quantumult X", "Surge"), required=True)
    assert script_text is not None
    validate_script(script_text)

    kelee_download = fetch(KELEE_URL, ("Loon", "Surge", "Mozilla/5.0"), required=False)
    if kelee_download is not None:
        validate_kelee(kelee_download)
        kelee_text = kelee_download
        kelee_status = "成功"
    elif KELEE_SNAPSHOT.exists():
        kelee_text = KELEE_SNAPSHOT.read_text(encoding="utf-8")
        validate_kelee(kelee_text)
        error = short_error(LAST_FETCH_ERRORS.get(KELEE_URL, "连接失败"))
        kelee_status = f"失败（{error}，使用快照 {snapshot_date(kelee_text)}）"
    else:
        raise RuntimeError("Kelee 上游不可用且仓库中没有有效快照")

    old_script = SCRIPT_OUTPUT.read_text(encoding="utf-8") if SCRIPT_OUTPUT.exists() else ""
    script_changed = old_script != script_text
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    stamp = now.strftime("%Y-%m-%d %H:%M")
    cache_key = now.strftime("%Y%m%d%H%M")
    if MODULE_OUTPUT.exists() and not script_changed:
        old_module = MODULE_OUTPUT.read_text(encoding="utf-8")
        old_cache_key = re.search(r"umetrip-adblock\.js\?v=(\d+)", old_module)
        if old_cache_key:
            cache_key = old_cache_key.group(1)
    candidate = build_module(dd_text, kelee_text, stamp, stamp, "成功", kelee_status, cache_key)

    if MODULE_OUTPUT.exists() and not script_changed:
        if without_runtime_status(old_module) == without_runtime_status(candidate):
            rule_stamp = old_rule_timestamp(old_module, stamp)
            candidate = build_module(dd_text, kelee_text, rule_stamp, stamp, "成功", kelee_status, cache_key)
            print("合并后的有效规则没有变化，保留原规则更新时间；刷新同步状态")

    DD_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    DD_SNAPSHOT.write_text(dd_text.rstrip() + "\n", encoding="utf-8")
    if kelee_download is not None:
        KELEE_SNAPSHOT.write_text(kelee_text.rstrip() + "\n", encoding="utf-8")
    SCRIPT_OUTPUT.write_text(script_text.rstrip() + "\n", encoding="utf-8")
    MODULE_OUTPUT.write_text(candidate, encoding="utf-8")


if __name__ == "__main__":
    main()
