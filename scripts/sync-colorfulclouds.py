#!/usr/bin/env python3
"""Sync ddgksf2013 Caiyun upstream with independent local patches and safe publishing."""
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
# 同步源：墨鱼原生彩云天气净化脚本
URL = 'https://raw.githubusercontent.com/ddgksf2013/Scripts/master/caiyun_json.js'
MODULE = ROOT / 'colorfulclouds-adblock.yaml'
SCRIPT = ROOT / 'colorfulclouds-adblock.js'
META = ROOT / 'colorfulclouds-sync-status.json'
BASE = ROOT / 'scripts/colorfulclouds-sync-base.js'
YAML_BASE = ROOT / 'scripts/colorfulclouds-sync-base.yaml'

class EgernSafeDumper(yaml.SafeDumper):
    """Custom YAML Dumper to preserve raw regex backslashes using single quotes."""
    pass

def _str_representer(dumper, data):
    if '\\' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

EgernSafeDumper.add_representer(str, _str_representer)

def safe_dump_yaml(data):
    return yaml.dump(data, Dumper=EgernSafeDumper, allow_unicode=True, sort_keys=False, width=1000)

# Local behavior is independently maintained and reapplied to every upstream release.
from colorfulclouds_local_patches import adapt

def description(meta):
    state = '同步成功' if meta['status'] == 'ok' else '同步失败'
    updated = meta.get('module_updated_at') or meta.get('last_updated', '未知')
    return ('去开屏、首页推广、底栏小助手及右侧悬浮入口。\n'
            f"更新时间：{updated}（{state}）")

def build(version):
    empty = {'respond': {'status': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{}'}}
    script_url = 'https://raw.githubusercontent.com/huangkouping/egern/main/colorfulclouds-adblock.js?v=' + version

    return {
        'name': '彩云天气去广告(同步优化版) 🅥',
        'author': 'ddgksf2013, huangkouping',
        'homepage': 'https://github.com/huangkouping/egern',
        'open_url': 'https://apps.apple.com/app/id847764912',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/ColorfulClouds.png',
        'compat_arguments_desc': '开启 MitM 并信任证书，更新后彻底关闭 App 再打开。',
        'dns': {},
        # 网络层直接拦截广告与日志上报
        'rules': [{'domain': {'match': domain, 'policy': 'REJECT'}} for domain in
                  ['abyss.cyapi.cn', 'ad.cyapi.cn', 'gather.colorfulclouds.net', 'log.caiyunapp.com', 'adx.caiyunapp.com']],
        # 静态广告接口直接置空（秒开且不耗电）
        'rewrites': [
            {'match': r'(?i)^https?://ad\.cyapi\.cn/v\d+', 'actions': [empty]}
        ],
        # 核心净化脚本（包含移除底栏小助手与各模块清洗）
        'scriptings': [
            {
                'http_response': {
                    'name': '彩云天气移除底栏小助手',
                    'match': r'(?i)^https?://biz\.cyapi\.cn/(api/)?v\d+/user(_detail)?',
                    'script_url': script_url,
                    'body_required': True,
                    'timeout': 10,
                    'update_interval': 3600
                }
            },
            {
                'http_response': {
                    'name': '彩云天气活动清洗',
                    'match': r'(?i)^https?://(wrapper\.cyapi\.cn|api\.caiyunapp\.com|cdn-w\.caiyunapp\.com)/v\d+/activity',
                    'script_url': script_url,
                    'body_required': True,
                    'timeout': 10,
                    'update_interval': 3600
                }
            },
            {
                'http_response': {
                    'name': '彩云天气首页卡片与浮窗清理',
                    'match': r'(?i)^https?://starplucker\.cyapi\.cn/v\d+/(operation/(homefeatures|feeds|banners|features)|notification/message_center|config/cypage|campaigns)',
                    'script_url': script_url,
                    'body_required': True,
                    'timeout': 10,
                    'update_interval': 3600
                }
            }
        ],
        'mitm': {
            'hostnames': {
                'includes': [
                    'biz.cyapi.cn',
                    'starplucker.cyapi.cn',
                    'wrapper.cyapi.cn',
                    'api.caiyunapp.com',
                    'cdn-w.caiyunapp.com',
                    'ad.cyapi.cn'
                ]
            }
        }
    }

_MISSING = object()

def merge_value(base, local, incoming, path='root'):
    """Recursive three-way merge; local edits win when both sides change."""
    if local is _MISSING:
        return _MISSING if base is not _MISSING else incoming
    if base is _MISSING and isinstance(local, dict) and isinstance(incoming, dict):
        return merge_value({}, local, incoming, path)
    if incoming is _MISSING:
        return local if local != base else _MISSING
    if local == base:
        return incoming
    if incoming == base or local == incoming:
        return local
    if isinstance(base, dict) and isinstance(local, dict) and isinstance(incoming, dict):
        result = {}
        for key in dict.fromkeys([*base, *local, *incoming]):
            value = merge_value(base.get(key, _MISSING), local.get(key, _MISSING),
                                incoming.get(key, _MISSING), path + '.' + str(key))
            if value is not _MISSING:
                result[key] = value
        return result
    if isinstance(local, list) and isinstance(incoming, list):
        if path.endswith('.includes') or path.endswith('.rules'):
            result = [v for v in local]
            for item in incoming:
                if item not in result and (not isinstance(base, list) or item not in base):
                    result.append(item)
            return result
        if path.endswith('.scriptings') or path.endswith('.rewrites'):
            def key(item):
                if not isinstance(item, dict):
                    return repr(item)
                if 'http_response' in item:
                    response = item['http_response']
                    return ('response', response.get('name', response.get('match')))
                return ('rewrite', item.get('match', repr(item)))
            bmap = {key(v): v for v in base} if isinstance(base, list) else {}
            lmap = {key(v): v for v in local}
            imap = {key(v): v for v in incoming}
            keys = list(dict.fromkeys([*lmap, *imap]))
            result = []
            for k in keys:
                value = merge_value(bmap.get(k, _MISSING), lmap.get(k, _MISSING),
                                    imap.get(k, _MISSING), path + '.' + str(k))
                if value is not _MISSING:
                    result.append(value)
            return result
    # Concurrent edits of a scalar: local value is authoritative.
    return local

def validate_module(module):
    if not isinstance(module, dict) or not isinstance(module.get('scriptings'), list):
        raise ValueError('Invalid Egern module structure')
    if not isinstance(module.get('mitm', {}).get('hostnames', {}).get('includes'), list):
        raise ValueError('Invalid MitM host list')
    if not any('小助手' in str(item) for item in module['scriptings']):
        raise ValueError('Critical local assistant fix is missing')
    if not any('activity' in str(item) for item in module['scriptings']):
        raise ValueError('Critical activity handler is missing')

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
                source = response.read(200001).decode('utf-8')
        incoming = adapt(source)
        script = incoming
        if SCRIPT.exists() and BASE.exists():
            with tempfile.TemporaryDirectory() as temp:
                current_file = Path(temp) / 'local.js'
                base_file = Path(temp) / 'base.js'
                incoming_file = Path(temp) / 'incoming.js'
                current_file.write_text(SCRIPT.read_text())
                base_file.write_text(BASE.read_text())
                incoming_file.write_text(incoming)
                merge = subprocess.run(['git', 'merge-file', '-p', str(current_file), str(base_file), str(incoming_file)], capture_output=True, text=True, timeout=20)
                if merge.returncode != 0:
                    raise ValueError('Conflicting JS changes require review; last good version retained')
                script = merge.stdout
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as check_file:
            check_file.write(script)
            check_file.flush()
            syntax = subprocess.run(['node', '--check', check_file.name], capture_output=True, text=True, timeout=15)
            if syntax.returncode:
                raise ValueError('Merged JavaScript syntax check failed')
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12])
        # Alias-free YAML is easier to inspect and compatible with Egern.
        for rule in module['rewrites']:
            rule['actions'] = json.loads(json.dumps(rule['actions']))
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        generated_module = json.loads(json.dumps(module))
        if MODULE.exists():
            original = yaml.safe_load(MODULE.read_text()) or {}
            previous_base = yaml.safe_load(YAML_BASE.read_text()) if YAML_BASE.exists() else original
            for item in (original, previous_base):
                item.pop('description', None)
                item.pop('compat_arguments_desc', None)
            module = merge_value(previous_base, original, module)
        validate_module(module)
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text()) or {}
            for field in ('description', 'compat_arguments_desc'):
                previous.pop(field, None)
            comparable = dict(module)
            for field in ('description', 'compat_arguments_desc'):
                comparable.pop(field, None)
            changed = changed or previous != comparable
        module_updated_at = checked if changed else (old.get('module_updated_at') or old.get('last_updated', checked))
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'module_updated_at': module_updated_at,
                'last_updated': module_updated_at,
                'source_url': URL, 'source_version': 'ddgksf2013-latest',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync ddgksf2013 caiyun_json.js; remove assistant bar and feeds/banners.'}
        module['description'] = description(meta)
        module['compat_arguments_desc'] = module['description']
        # Only publish after script validation and module merge have succeeded.
        if changed:
            SCRIPT.write_text(script)
        BASE.write_text(incoming)
        YAML_BASE.write_text(safe_dump_yaml(generated_module))
        # 使用自定义的 safe_dump_yaml 生成，避免破坏合法转义
        MODULE.write_text(safe_dump_yaml(module))
        
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds ddgksf2013 script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            # A failed sync does not modify the published module's behavior.
            # Keep its visible last-modified timestamp unchanged.
            meta['module_updated_at'] = old.get('module_updated_at') or old.get('last_updated', checked)
            module['description'] = description(meta)
            module['compat_arguments_desc'] = module['description']
            MODULE.write_text(safe_dump_yaml(module))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
