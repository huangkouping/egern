#!/usr/bin/env python3
"""Back up the readable XiaojukejiCharge mirror; retain last-good output on failure."""
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
URL = 'https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/XiaojukejiCharge_remove_ads/kelee_XiaojukejiCharge_remove_ads.js'
MODULE = ROOT / 'xiaojukeji-charge-adblock.yaml'
SCRIPT = ROOT / 'xiaojukeji-charge-adblock.js'
META = ROOT / 'xiaojukeji-charge-sync-status.json'

def adapt(source):
    if not 1000000 < len(source) < 5000000:
        raise ValueError('Unexpected page bundle size')
    if any(token not in source for token in ['__webpack_modules__', '__webpack_require__(69592)', 'Vue', 'people']):
        raise ValueError('Page bundle signature missing')
    if any(token in source[:2000] for token in ['<!DOCTYPE', '<html', '404: Not Found']):
        raise ValueError('Unexpected upstream content')
    if 'kelee.one' in source:
        raise ValueError('Unexpected additional Kelee dependency')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as handle:
        handle.write(source)
        handle.flush()
        check = subprocess.run(['node', '--check', handle.name], capture_output=True, text=True, timeout=30)
        if check.returncode:
            raise ValueError('JavaScript syntax check failed')
    return source

def description(meta):
    state = '脚本镜像同步正常' if meta['status'] == 'ok' else '脚本镜像同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '移除横幅、弹窗及搜索推荐，替换我的页面资源。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def build(version):
    template = (ROOT / 'scripts/xiaojukeji-charge-base.yaml').read_text()
    url = 'https://raw.githubusercontent.com/huangkouping/egern/main/xiaojukeji-charge-adblock.js?v=' + version
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
                source = response.read(5000001).decode('utf-8')
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
                'source_url': URL, 'source_version': '公开整包镜像，未标注脚本版本',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync the full replacement page bundle, never execute it as a proxy script; local module rules are maintained separately.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('XiaojukejiCharge script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('XiaojukejiCharge sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
