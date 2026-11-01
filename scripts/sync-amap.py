#!/usr/bin/env python3
"""Sync public Amap JQ mirrors, keeping the last good module on any failure."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = 'ifflagged/Romeo'
SOURCES = {
    'updatable.jq': 'Modules/JavaScript/Kelee/Amap_remove_ads/kelee_updatable.jq',
    'search_poi_detail.jq': 'Modules/JavaScript/Kelee/Amap_remove_ads/kelee_search_poi_detail.jq',
}
MODULE = ROOT / 'amap-adblock.yaml'
STATUS = ROOT / 'amap-sync-status.json'

def stamp():
    return datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Egern-Amap-Public-Mirror-Sync/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError('Upstream HTTP status: ' + str(response.status))
        data = response.read(500001)
        if len(data) > 500000:
            raise ValueError('Upstream file exceeds size limit')
        return data.decode('utf-8')

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def validate_jq(code):
    if not isinstance(code, str) or not code.strip() or len(code) > 500000:
        raise ValueError('Missing or oversized jq code')
    if any(s in code.lower() for s in ['<!doctype', '<html', '404: not found']):
        raise ValueError('Upstream returned an error page')
    # Compile without executing the filter or requiring a particular response shape.
    result = subprocess.run(['jq', '-n', 'if false then (\n' + code + '\n) else null end'],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError('jq compilation failed: ' + result.stderr[:120])

def render_description(meta):
    state = 'JQ镜像同步正常' if meta['status'] == 'ok' else 'JQ镜像同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '开屏、首页及地点推广过滤，精简页面。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def dump_yaml(data):
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000)

def build(base, sources):
    module = yaml.safe_load(base)
    if len(module['rewrites']) != 27:
        raise ValueError('Unexpected base rule count')
    replacements = set()
    for rule in module['rewrites']:
        re.compile(rule['match'])
        for action in rule['actions']:
            response = action.get('response_body', {})
            code = response.get('jq')
            if isinstance(code, dict):
                name = code['url'].rsplit('/', 1)[-1]
                if name not in SOURCES or name in replacements:
                    raise ValueError('Unexpected external dependency')
                response['jq'] = sources[name]
                replacements.add(name)
            if 'jq' in response:
                validate_jq(response['jq'])
    if replacements != set(SOURCES):
        raise ValueError('Incomplete dependency replacement')
    return module

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path)
    parser.add_argument('--upstream-ref')
    args = parser.parse_args()
    checked = stamp()
    old = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    try:
        base = (ROOT / 'scripts/amap-base.yaml').read_text()
        if args.source_dir:
            ref = args.upstream_ref or 'local-validation'
            sources = {name: (args.source_dir / name).read_text() for name in SOURCES}
        else:
            ref = json.loads(fetch(f'https://api.github.com/repos/{REPO}/commits/main'))['sha']
            if not re.fullmatch(r'[0-9a-f]{40}', ref):
                raise ValueError('Invalid upstream commit')
            sources = {name: fetch(f'https://raw.githubusercontent.com/{REPO}/{ref}/{path}')
                       for name, path in SOURCES.items()}
        module = build(base, sources)
        hashes = {name: digest(code) for name, code in sources.items()}
        changed = hashes != old.get('source_sha256') or digest(base) != old.get('base_sha256')
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'upstream_repository': REPO, 'upstream_commit': ref,
                'source_paths': SOURCES, 'source_sha256': hashes, 'base_sha256': digest(base),
                'scope': 'Only the two public JQ mirror dependencies; base rules are maintained locally.'}
        module['description'] = render_description(meta)
        # All dependencies and filters are validated before touching any good output.
        for name, code in sources.items():
            (ROOT / ('amap-' + name)).write_text(code.rstrip() + '\n')
        MODULE.write_text(dump_yaml(module))
        STATUS.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Amap: 23 rules, 2 inline JQ dependencies; sync OK')
        return 0
    except Exception as error:
        if not MODULE.exists():
            print('Initial Amap sync failed:', type(error).__name__, file=sys.stderr)
            return 1
        meta = dict(old, status='failed', last_checked=checked,
                    error=type(error).__name__ + ': ' + str(error)[:180])
        module = yaml.safe_load(MODULE.read_text())
        module['description'] = render_description(meta)
        MODULE.write_text(dump_yaml(module))
        STATUS.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Amap sync failed; kept last good rules:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
