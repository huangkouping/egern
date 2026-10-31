#!/usr/bin/env python3
"""Back up the readable AliYunDrive mirror; retain last-good output on failure."""
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
URL = 'https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/AliYunDrive_remove_ads/kelee_AliYunDrive_remove_ads.js'
MODULE = ROOT / 'aliyundrive-adblock.yaml'
SCRIPT = ROOT / 'aliyundrive-adblock.js'
META = ROOT / 'aliyundrive-sync-status.json'

def adapt(source):
    if len(source) < 100 or len(source) > 100000:
        raise ValueError('Unexpected source size')
    if '/v1/users/onboard_list' not in source or '$done' not in source:
        raise ValueError('Source signature missing')
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', 'eval(', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    result = ('/* RuCu6 / 可莉公开镜像备份；源逻辑保持，补充异常透传与单次完成。\n'
              ' * Source: ' + URL + '\n */\n'
              '(function (complete) {\nlet finished = false;\n'
              'const $done = value => { if (!finished) { finished = true; complete(value); } };\n'
              'try {\nif (typeof $response === "undefined" || typeof $response.body !== "string") return $done({});\n'
              + source + '\n} catch (_) { $done({}); }\n})($done);\n')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as handle:
        handle.write(result)
        handle.flush()
        check = subprocess.run(['node', '--check', handle.name], capture_output=True, text=True, timeout=15)
        if check.returncode:
            raise ValueError('JavaScript syntax check failed')
    return result

def description(meta):
    state = '脚本镜像同步正常' if meta['status'] == 'ok' else '脚本镜像同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '移除首页广告横幅、弹窗和顶部奖励。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def build(version):
    template = (ROOT / 'scripts/aliyundrive-base.yaml').read_text()
    url = 'https://raw.githubusercontent.com/huangkouping/egern/main/aliyundrive-adblock.js?v=' + version
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
                'source_url': URL, 'source_version': '2024-07-15',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync the public JavaScript mirror; local module rules are maintained separately.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('AliYunDrive script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('AliYunDrive sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
