#!/usr/bin/env python3
"""Convert upstream Quantumult X TxvideoAD snippet into Egern YAML without changing its rules."""
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
script_url = "https://raw.githubusercontent.com/huangkouping/egern/main/txvideo-adblock.js"
icon = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/icons/apps/TencentVideo.png"

def quote(s):
    return "'" + s.replace("'", "''") + "'"

lines = [
    "name: 腾讯视频去广告🅗",
    "description: |-",
    "  原作者 ZenmoFeiShi/Qx；按上游 Quantumult X 模块自动转换，保持原始规则与脚本逻辑。",
    "  每 6 小时检查上游变化；转换失败保留上一版本。",
    "icon: " + icon,
    "open_url: https://apps.apple.com/app/id458318329",
    "author: ZenmoFeiShi[https://github.com/ZenmoFeiShi/Qx]",
    "homepage: https://github.com/huangkouping/egern",
    "dns: {}",
]
domains, scripts, hosts = [], [], []
for raw in source.splitlines():
    line = raw.strip()
    if not line or line.startswith("#!"):
        continue
    if line.startswith("hostname"):
        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError("Invalid hostname: " + line)
        hosts.extend(x.strip() for x in value.split(",") if x.strip())
    elif line.startswith("host,"):
        m = re.fullmatch(r"host,\s*([^,\s]+),\s*reject", line, re.I)
        if not m:
            raise ValueError("Unsupported host rule: " + line)
        domains.append(m.group(1))
    elif " url " in line:
        m = re.fullmatch(r"(\S+)\s+url\s+(script-request-body|script-response-body)\s+(https?://\S+)", line)
        if not m:
            raise ValueError("Unsupported rewrite: " + line)
        regex, action, url = m.groups()
        if "Txvideoad.js" not in url:
            raise ValueError("Unknown upstream script: " + url)
        # Quantumult X uses \/ to escape literal slashes; Egern regex needs only /.
        regex = regex.replace(r"\/", "/")
        re.compile(regex)
        scripts.append((regex, "http_request" if action == "script-request-body" else "http_response"))
    else:
        raise ValueError("Unrecognized upstream directive: " + line)
if not domains or not scripts or not hosts:
    raise ValueError("Upstream missing required rules; refusing to overwrite")
lines.append("rules:")
for domain in domains:
    lines.extend(["  - domain:", "      match: " + quote(domain), "      policy: REJECT"])
lines.append("scriptings:")
for idx, (regex, kind) in enumerate(scripts, 1):
    lines.extend([
        "  - " + kind + ":",
        "      name: 腾讯视频上游规则" + str(idx),
        "      match: " + quote(regex),
        "      script_url: " + script_url,
        "      body_required: true",
        "      timeout: 20",
    ])
lines.extend(["mitm:", "  hostnames:", "    includes:"])
for host in dict.fromkeys(hosts):
    lines.append("      - " + quote(host))
Path(sys.argv[2]).write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Converted {len(domains)} reject rules, {len(scripts)} script rules, {len(hosts)} MITM hosts")
