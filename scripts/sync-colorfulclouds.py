#!/usr/bin/env python3
"""Sync the ColorfulClouds script from Kelee official distribution (Moli-X/Tool); retain last-good output on failure."""
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

def adapt(source):
    if len(source) < 100 or len(source) > 200000:
        raise ValueError('Unexpected source size')
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', 'eval(', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    result = ('/* 墨鱼 ddgksf2013 彩云天气去广告脚本镜像；补充异常透传与单次完成包装。\n'
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
    state = '墨鱼脚本同步正常' if meta['status'] == 'ok' else '脚本同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '彻底移除开屏广告、首页信息流卡片(feeds)、轮播横幅(banners)及底栏小助手。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def build(version):
    empty = {'respond': {'status': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{}'}}
    script_url = 'https://raw.githubusercontent.com/huangkouping/egern/main/colorfulclouds-adblock.js?v=' + version

    return {
        'name': '彩云天气去广告🅥 (墨鱼优化版)',
        'author': 'ddgksf2013, huangkouping',
        'homepage': 'https://github.com/huangkouping/egern',
        'open_url': 'https://apps.apple.com/app/id847764912',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/ColorfulClouds.png',
        'compat_arguments_desc': '【使用说明】\n开启 MitM 并信任证书，启用后彻底划掉彩云天气重新打开。\n基于墨鱼(ddgksf2013)逻辑，彻底清空底栏小助手、首页 feeds/banners 卡片及活动推广。',
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
        script = adapt(source)
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12])
        # Alias-free YAML is easier to inspect and compatible with Egern.
        for rule in module['rewrites']:
            rule['actions'] = json.loads(json.dumps(rule['actions']))
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_url': URL, 'source_version': 'ddgksf2013-latest',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync ddgksf2013 caiyun_json.js; remove assistant bar and feeds/banners.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        # 使用自定义的 safe_dump_yaml 生成，避免破坏合法转义
        MODULE.write_text(safe_dump_yaml(module))
        
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds ddgksf2013 script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(safe_dump_yaml(module))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
