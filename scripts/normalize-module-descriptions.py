#!/usr/bin/env python3
"""Normalize Egern module metadata and description timestamps after upstream syncs."""
from pathlib import Path
import re
import sys
import yaml

HOME = "https://github.com/huangkouping/egern"
# Preserve verified upstream credits; never infer an author from a filename.
STAMP = re.compile(r"^更新时间[：:]\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}.*$")
KEY = re.compile(r"^[A-Za-z_][\w-]*:")
paths = map(Path, sys.argv[1:]) if len(sys.argv) > 1 else sorted(Path(".").glob("*.yaml"))
for path in paths:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    # Insert homepage without reserializing YAML, preserving all functional rules.
    if not re.search(r"^homepage\s*:", original, re.M):
        insertion = next((i + 1 for i, line in enumerate(lines) if re.match(r"^author\s*:", line)), None)
        if insertion is None:
            insertion = next((i + 1 for i, line in enumerate(lines) if re.match(r"^name\s*:", line)), 0)
        lines.insert(insertion, f"homepage: {HOME}\n")
    else:
        lines = [re.sub(r"^homepage\s*:.*$", f"homepage: {HOME}", line) if re.match(r"^homepage\s*:", line) else line for line in lines]
    # Existing upstream author credits are kept, and repository maintainer appended once.
    for i, line in enumerate(lines):
        m = re.match(r"^author:\s*(.*?)\s*$", line)
        if m and m.group(1) and "huangkouping" not in m.group(1).lower():
            value = yaml.safe_load(line).get('author')
            if not isinstance(value, str):
                continue
            lines[i] = yaml.safe_dump({'author': value + ', huangkouping'}, allow_unicode=True, width=1000)
            break
    if not any(re.match(r"^author\s*:", line) for line in lines):
        name = next((line.split(":", 1)[1] for line in lines if line.startswith("name:")), "")
        # Only explicitly marked self-authored modules get sole credit.
        if "🅗" in name:
            idx = next((i for i, line in enumerate(lines) if line.startswith("name:")), -1)
            lines.insert(idx + 1, "author: huangkouping\n")

    start = next((i for i, line in enumerate(lines) if line.startswith("description:")), None)
    if start is None:
        changed = "".join(lines)
        if changed != original:
            path.write_text(changed, encoding="utf-8")
            print("Normalized:", path)
        continue
    end = start + 1
    while end < len(lines) and not KEY.match(lines[end]):
        end += 1
    try:
        description = yaml.safe_load("".join(lines[start:end]))["description"]
    except (yaml.YAMLError, TypeError, KeyError):
        continue
    if not isinstance(description, str):
        changed = "".join(lines)
        if changed != original:
            path.write_text(changed, encoding="utf-8")
        continue
    content = [s.strip() for s in re.split(r'\\n(?=\s*更新时间[：:])|\r?\n', description) if s.strip()]
    clean, timestamps = [], []
    for line in content:
        if STAMP.match(line):
            timestamps.append(line)
            continue
        prefix, sep, stamp = line.rpartition("；")
        if sep and STAMP.match(stamp.strip()):
            if prefix.strip():
                clean.append(prefix.strip())
            timestamps.append(stamp.strip())
        else:
            clean.append(line)
    if not timestamps:
        changed = "".join(lines)
        if changed != original:
            path.write_text(changed, encoding="utf-8")
            print("Normalized:", path)
        continue
    clean.append(timestamps[-1])
    replacement = ["description: |-\n"] + ["  " + s + "\n" for s in clean]
    changed = "".join(lines[:start] + replacement + lines[end:])
    if changed != original:
        path.write_text(changed, encoding="utf-8")
        print("Normalized:", path)
