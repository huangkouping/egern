#!/usr/bin/env python3
"""Keep Egern module update time as the last description line."""
from pathlib import Path
import re
import yaml

STAMP = re.compile(r"^更新时间[：:]\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}.*$")
KEY = re.compile(r"^[A-Za-z_][\w-]*:")
for path in sorted(Path(".").glob("*.yaml")):
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("description:")), None)
    if start is None:
        continue
    end = start + 1
    while end < len(lines) and not KEY.match(lines[end]):
        end += 1
    try:
        description = yaml.safe_load("".join(lines[start:end]))["description"]
    except (yaml.YAMLError, TypeError, KeyError):
        continue
    if not isinstance(description, str):
        continue
    content = [s.strip() for s in description.splitlines() if s.strip()]
    timestamps = [s for s in content if STAMP.match(s)]
    if not timestamps:
        continue
    clean = [s for s in content if not STAMP.match(s)]
    clean.append(timestamps[-1])
    replacement = ["description: |-\n"] + ["  " + s + "\n" for s in clean]
    changed = "".join(lines[:start] + replacement + lines[end:])
    if changed != original:
        path.write_text(changed, encoding="utf-8")
        print("Normalized:", path)
