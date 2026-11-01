#!/usr/bin/env python3
"""Sync the NeteaseCloudMusic source script (Keywos wyres.js) directly; retain last-good output on failure."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://raw.githubusercontent.com/Keywos/rule/main/script/wy/js/wyres.js'
MODULE = ROOT / 'netease-cloudmusic-adblock.yaml'
SCRIPT = ROOT / 'netease-cloudmusic-adblock.js'
META = ROOT / 'netease-cloudmusic-sync-status.json'

def adapt(source):
    if not 1000 < len(source) < 100000:
        raise ValueError('Unexpected source size')
    transforms = [
        ('(()=>{', 'await (async()=>{'),
        ('function fe(f)', 'async function fe(f)'),
        ('$utils.ungzip(h)', '(await ctx.compress.gunzip(h))'),
        ('s=fe($response.body)', 's=await fe($response.body)'),
        ('function de(f){f=N.AES.encrypt(JSON.stringify(f)).ciphertext;', 'async function de(f){if(ne){f=await ctx.compress.gzip(new TextEncoder().encode(JSON.stringify(f)));if(!f)throw new Error("gzip failed");f=N.lib.WordArray.create(f)}else f=JSON.stringify(f);f=N.AES.encrypt(f).ciphertext;'),
        ('ee={body:de(s)}', 'ee={body:await de(s)}'),
        ('case"homepage/block/page":', 'case"/homepage/block/page":')
    ]
    for old, new in transforms:
        if source.count(old) != 1:
            raise ValueError('Upstream structure changed: adapter review required')
        source = source.replace(old, new, 1)
    if any(token in source for token in ['404: Not Found', '<html', '$httpClient', '$task.fetch', 'eval(', 'import(']):
        raise ValueError('Unexpected upstream content or network dependency')
    result = (ROOT / 'scripts/netease-cloudmusic-adapter.js').read_text()
    result = result.replace('SOURCE_URL', URL).replace('SOURCE_CODE', source)
    with tempfile.NamedTemporaryFile(suffix='.mjs', mode='w') as handle:
        handle.write(result)
        handle.flush()
        check = subprocess.run(['node', '--check', handle.name], capture_output=True, text=True, timeout=15)
        if check.returncode:
            raise ValueError('JavaScript syntax check failed')
    return result

def description(meta):
    state = '源脚本同步正常' if meta['status'] == 'ok' else '源脚本同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '过滤开屏、页面推广及评论区广告，支持界面开关。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def build(version):
    template = (ROOT / 'scripts/netease-cloudmusic-base.yaml').read_text()
    url = 'https://raw.githubusercontent.com/huangkouping/egern/main/netease-cloudmusic-adblock.js?v=' + version
    return yaml.safe_load(template.replace('SOURCE_SCRIPT', url))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file', type=Path)
    args = parser.parse_args()
    checked = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old = json.loads(META.read_text()) if META.exists() else {}
    try:
        if args.source_file:
            source = args.source_file.read_text()
        else:
            req = urllib.request.Request(URL, headers={'User-Agent': 'Egern-Public-Mirror-Sync/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                source = response.read(100001).decode('utf-8')
        script = adapt(source)
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12])
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_url': URL, 'source_version': '2025-02-19',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync the Keywos source JavaScript (wyres.js) directly, without the Kelee mirror; local module rules are maintained separately.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('NeteaseCloudMusic script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('NeteaseCloudMusic sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
