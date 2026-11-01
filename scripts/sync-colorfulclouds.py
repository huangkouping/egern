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
URL = 'https://raw.githubusercontent.com/Moli-X/Tool/X/Loon/Plugin/Kelee/Script/ColorfulClouds_remove_ads.js'
MODULE = ROOT / 'colorfulclouds-adblock.yaml'
SCRIPT = ROOT / 'colorfulclouds-adblock.js'
META = ROOT / 'colorfulclouds-sync-status.json'

def adapt(source):
    if len(source) < 100 or len(source) > 100000:
        raise ValueError('Unexpected source size')
    if '/api.caiyunapp.com/v1/activity' not in source or '$done' not in source:
        raise ValueError('Source signature missing')
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', 'eval(', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    result = ('/* 可莉官方脚本备份（活动推广逻辑源自 RuCu6）；源逻辑保持，补充异常透传与单次完成。\n'
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
    state = '官方脚本同步正常' if meta['status'] == 'ok' else '官方脚本同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '过滤首页推广、弹窗及部分页面广告。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")

def build(version):
    empty = {'respond': {'status': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{}'}}
    return {
        'name': '彩云天气去广告🅥', 'author': 'RuCu6[https://github.com/RuCu6]',
        'homepage': 'https://github.com/huangkouping/egern',
        'open_url': 'https://apps.apple.com/app/id847764912',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/ColorfulClouds.png',
        'compat_arguments_desc': '【使用说明】\n启用模块，确认 MitM 已开启且证书受信任，然后重新打开彩云天气。\n关闭其他彩云去广告模块，避免重复处理。\nJS 已备份到本仓库，每 6 小时检查可莉官方脚本；失败时保留上次有效版本。\n原规则为用户提供的可莉配置，JS 直连可莉官方分发（Moli-X/Tool），标注版本 2024-09-05；活动推广处理逻辑源自 RuCu6。不采用 RuCu6 原版：原版是会员破解脚本，会注入他人账号 token 并伪造 SVIP，与去广告无关且有安全风险。\n保留源处理逻辑，仅增加异常透传；当前 App 效果待实测。',
        'dns': {},
        'rules': [{'domain': {'match': domain, 'policy': 'REJECT'}} for domain in
                  ['abyss.cyapi.cn', 'ad.cyapi.cn', 'gather.colorfulclouds.net']],
        'rewrites': [
            {'match': r'(?i)^https://biz\.cyapi\.cn/(p/v1/entries|p/v1/trial_card/info|v2/product)', 'actions': [empty]},
            {'match': r'(?i)^https://starplucker\.cyapi\.cn/v3/(config/cypage/\w+/conditions|notification/message_center|operation/homefeatures)', 'actions': [empty]},
            {'name': '彩云天气去广告', 'match': r'(?i)^https://(wrapper\.cyapi\.cn|api\.caiyunapp\.com|cdn-w\.caiyunapp\.com)/v1/activity\?',
             'actions': [{'response_script': {'name': '彩云天气去广告',
                  'url': 'https://raw.githubusercontent.com/huangkouping/egern/main/colorfulclouds-adblock.js?v=' + version,
                  'timeout': 20, 'body_required': True}}]}],
        'mitm': {'hostnames': {'includes': ['biz.cyapi.cn', 'starplucker.cyapi.cn',
                 'wrapper.cyapi.cn', 'api.caiyunapp.com', 'cdn-w.caiyunapp.com']}}}

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
        # Alias-free YAML is easier to inspect and compatible with Egern.
        for rule in module['rewrites'][:2]:
            rule['actions'] = json.loads(json.dumps(rule['actions']))
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_url': URL, 'source_version': '2024-09-05',
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'scope': 'Sync the Kelee official JavaScript (Moli-X/Tool) directly, without the ifflagged mirror; local module rules are maintained separately.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds script mirror sync OK')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('ColorfulClouds sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
