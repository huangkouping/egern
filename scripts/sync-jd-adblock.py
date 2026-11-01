#!/usr/bin/env python3
"""Sync JD v2 upstream while preserving the Egern wrapper and custom YAML rules."""
from pathlib import Path
import hashlib
import re
import urllib.request
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://raw.githubusercontent.com/zbsdsb/loon-adblock-plugins/main/JD_remove_ads_v2.js"
PLUGIN = "https://raw.githubusercontent.com/zbsdsb/loon-adblock-plugins/main/JD_remove_ads_v2.lpx"
local = (ROOT / "jd-adblock.js").read_text()
yaml = (ROOT / "jd-adblock.yaml").read_text()
assert "queryMaterialAdverts" in yaml and "jddebug" in yaml and "jd-adblock.js" in yaml, "Custom JD rules missing"
with urllib.request.urlopen(SOURCE, timeout=30) as f:
    upstream = f.read().decode("utf-8-sig")
with urllib.request.urlopen(PLUGIN, timeout=30) as f:
    plugin = f.read().decode("utf-8-sig")
assert "JD_remove_ads_v2.js" in plugin and "api" in plugin, "Upstream plugin changed; manual review needed"
assert upstream.startswith("/*") and "const url = $request.url;" in upstream and "$done(" in upstream, "Upstream structure changed"
assert local.startswith("/* zbsdsb") and "const $done = value =>" in local, "Local wrapper changed"
start = local.index("/*\n * 京东去广告 v2")
end_marker = "\n} catch (_) { $done({}); }\n})($done);"
assert local.endswith(end_marker + "\n"), "Local wrapper tail changed"
current = local[start:-len(end_marker + "\n")].rstrip("\n")
# No-op if upstream is identical; update only the embedded upstream block.
if current != upstream.rstrip("\n"):
    new = local[:start] + upstream.rstrip("\n") + "\n" + end_marker + "\n"
    assert new.startswith(local[:start]) and new.endswith(end_marker + "\n")
    (ROOT / "jd-adblock.js").write_text(new)
    print("Updated upstream JD logic; preserved local wrapper and YAML.")
else:
    print("Upstream JD logic unchanged; local customization preserved.")
subprocess.run(["node", "--check", str(ROOT / "jd-adblock.js")], check=True)
print("Upstream SHA256:", hashlib.sha256(upstream.encode()).hexdigest())
