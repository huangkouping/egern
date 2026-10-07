#!/usr/bin/env python3
"""Merge the supplied Pornhub template and safely check its script source."""
import argparse
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'attract-adblock.yaml'
META = ROOT / 'pornhub-adblock-source.json'
SOURCE = 'https://ddgksf2013.top/scripts/pornhub.ads.js'
API_MATCH = r'^https?:\/\/(cn|www)\.pornhub\.com\/_xa\/ads'
PAGE_MATCH = r'^https?://(?:cn|www)\.pornhub\.com/(?!(?:.*(?:api|login|cdn-cgi|verify|auth|captch|\.(?:js|css|jpg|jpeg|png|webp|gif|zip|woff|woff2|m3u8|mp4|mov|m4v|avi|mkv|flv|rmvb|wmv|rm|asf|asx|mp3|json|ico|otf|ttf))))'
NAME = 'Pornhub 网页过滤'

def validate(source):
    if not source.strip() or re.search(r'<!doctype|<html\b|<head\b', source[:1500], re.I):
        raise ValueError('source_is_html')
    if '$response' not in source or not re.search(r'\$done\b|\$\.done\(', source):
        raise ValueError('requires_compatibility_review')
    if '$task' in source or '$prefs' in source:
        raise ValueError('requires_compatibility_review')
    check = subprocess.run(['node', '--check'], input=source, text=True, capture_output=True)
    if check.returncode:
        raise ValueError('invalid_javascript')

def sync(source=None, error=None, updated=None):
    before = MODULE.read_text()
    data = yaml.safe_load(before)
    old = json.loads(META.read_text()) if META.exists() else {}
    rules = data.setdefault('rewrites', [])
    rules[:] = [r for r in rules if r.get('match') != API_MATCH]
    rules.append({'match': API_MATCH, 'actions': [{'respond': {'status': 200,
        'headers': {'Content-Type': 'application/json'}, 'body': '{}'}}]})
    hosts = data['mitm']['hostnames']['includes']
    for host in ['cn.pornhub.com', 'www.pornhub.com']:
        if host not in hosts: hosts.append(host)
    digest = old.get('script_sha256')
    if source is not None:
        try:
            validate(source)
        except ValueError as exc:
            error = str(exc)
        else:
            digest = hashlib.sha256(source.encode()).hexdigest()
            (ROOT / 'pornhub-adblock.js').write_text(source)
            error = None
    has_script = bool(digest and (ROOT / 'pornhub-adblock.js').exists())
    data['scriptings'] = [r for r in data.get('scriptings', []) if r.get('http_response', {}).get('name') != NAME]
    if has_script:
        data['scriptings'].append({'http_response': {'name': NAME, 'match': PAGE_MATCH,
            'script_url': 'https://raw.githubusercontent.com/huangkouping/egern/main/pornhub-adblock.js?v=' + digest[:12],
            'max_size': -1, 'timeout': 60, 'body_required': True, 'update_interval': 3600}})
    status = 'Pornhub 同步正常' if not error else ('Pornhub 源异常，沿用旧脚本' if has_script else 'Pornhub 源异常，仅基础规则')
    if error == 'requires_compatibility_review': status = 'Pornhub 脚本待适配'
    cms = re.search(r'CMS[^；）\n]+', data.get('description', ''))
    states = (cms[0] + '；' if cms else '') + status
    previous_time = re.search(r'更新时间：([^（\n]+)', data.get('description', ''))
    oldtime = previous_time[1].strip() if previous_time else '未知'
    data['description'] = '屏蔽网页及视频插播广告。\n更新时间：' + oldtime + '（' + states + '）'
    meta = {'script_url': SOURCE, 'script_sha256': digest, 'status': status, 'error': error,
        'template': 'User-provided Pornhub Egern configuration', 'api_match': API_MATCH}
    olddata = yaml.safe_load(before)
    if olddata != data or old != meta:
        now = updated or datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
        data['description'] = '屏蔽网页及视频插播广告。\n更新时间：' + now + '（' + states + '）'
        MODULE.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    print(status)
    return bool(error)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file'); parser.add_argument('--updated-at')
    args = parser.parse_args()
    source, error = None, None
    try:
        if args.source_file:
            source = Path(args.source_file).read_text()
        else:
            request = urllib.request.Request(SOURCE, headers={'User-Agent': 'surge'})
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.geturl().split('?', 1)[0] != SOURCE:
                    error = 'redirected_away_from_script'
                else:
                    source = response.read().decode('utf-8')
    except Exception:
        error = 'download_failed'
    raise SystemExit(1 if sync(source, error, args.updated_at) else 0)
