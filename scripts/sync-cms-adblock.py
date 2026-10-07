#!/usr/bin/env python3
"""Convert Yswag CMS rules for Egern, with all remote playback parsing disabled."""
import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'https://raw.githubusercontent.com/Yswag/for-own-use/main/loon-plugin/cmsAdblock.plugin'
SCRIPT = 'https://raw.githubusercontent.com/Yswag/for-own-use/main/js/cmsAdblock.js'
MODULE = ROOT / 'attract-adblock.yaml'
META = ROOT / 'cms-adblock-source.json'
PREFIX = 'CMS 插播过滤'

def stamp():
    return datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')

def adapt_script(source):
    source, n = re.subn(r'async function fetchJxResult\(\) \{[\s\S]*?\nfunction getArg\(\)',
        'async function fetchJxResult() { return; }\n\nfunction getArg()', source, count=1)
    if n != 1 or '$.http.get(' in source or '$.http.post(' in source:
        raise ValueError('Upstream network behavior changed; manual review required')
    if "let arg = getArg()" not in source or "let isMsg = arg.toLowerCase() === 'true'" not in source:
        raise ValueError('Upstream argument format changed; manual review required')
    source = source.replace('let arg = getArg()', 'let arg = String(getArg())', 1)
    source = source.replace("let isMsg = arg.toLowerCase() === 'true'", 'let isMsg = false', 1)
    old_case = "case url.includes('hmrvideo'):\n      await fetchJxResult()\n      break"
    if old_case not in source:
        raise ValueError('Upstream HMR branch changed; manual review required')
    source = source.replace(old_case, "case url.includes('hmrvideo'):\n    case url.includes('heimuertv'):\n      filterAds(hmrvideo)\n      break", 1)
    source = source.replace('const hostname = line.match(regex)[1]',
        'const matchedHost = line.match(regex);\n      if (!matchedHost) return;\n      const hostname = matchedHost[1]', 1)
    source = source.replace('})()\n\nfunction filterAds',
        '})().catch(function () { $.done({}); })\n\nfunction filterAds', 1)
    return ('/* Adapted from Yswag/for-own-use cmsAdblock.js. Remote parsing disabled. */\n'
        '(function () {\nconst complete = $done; let finished = false;\n'
        '(function ($done) {\n'
        'if (typeof $response === "undefined" || typeof $response.body !== "string" || !$response.body.includes("#EXTM3U") || /#EXT-X-(?:STREAM-INF|I-FRAME-STREAM-INF)/.test($response.body)) return $done({});\n'
        'const $httpClient = {get: function(o, cb) {cb("Remote parsing disabled");}, post: function(o, cb) {cb("Remote parsing disabled");}};\n'
        + source + '\n})(function (r) {if (!finished) {finished = true; complete(r);}});\n})();\n')

def build(plugin, source, updated):
    data = yaml.safe_load(MODULE.read_text())
    js = adapt_script(source)
    version = hashlib.sha256(js.encode()).hexdigest()[:12]
    rules = []
    section = ''
    hosts = []
    rewrite = None
    for raw in plugin.splitlines():
        line = raw.strip()
        if line.startswith('['):
            section = line
        elif section == '[Script]' and line.startswith('http-response '):
            m = re.fullmatch(r'http-response (\S+) script-path=(\S+), requires-body=true, tag=(.+)', line)
            if not m or m[2] != SCRIPT:
                raise ValueError('Unsupported upstream script rule')
            re.compile(m[1])
            rules.append({'http_response': {'name': PREFIX + '｜' + m[3].split('｜')[-1],
                'match': m[1], 'script_url': 'https://raw.githubusercontent.com/huangkouping/egern/main/cms-adblock.js?v=' + version,
                'body_required': True, 'timeout': 10, 'update_interval': 3600}})
        elif section == '[MITM]' and line.startswith('hostname = '):
            hosts = [h.strip() for h in line.split('=', 1)[1].split(',')]
        elif section == '[Rewrite]' and line and not line.startswith('#'):
            m = re.fullmatch(r'(\S+) (\S+) 302', line)
            if not m or rewrite:
                raise ValueError('Unsupported upstream rewrite')
            rewrite = {'match': m[1], 'actions': [{'redirect': {'url': m[2], 'status_code': 302}}]}
    if len(rules) < 10 or not hosts or not rewrite:
        raise ValueError('Incomplete upstream plugin')
    # Use established Egern legacy rewrites rather than guessing unified action fields.
    match = rewrite['match']; location = rewrite['actions'][0]['redirect']['url']
    data['scriptings'] = [r for r in data.get('scriptings', []) if not r.get('http_response', {}).get('name', '').startswith(PREFIX)] + rules
    old = json.loads(META.read_text()) if META.exists() else {}
    own = [h for h in data['mitm']['hostnames']['includes'] if h not in old.get('hostnames', [])]
    data['mitm']['hostnames']['includes'] = list(dict.fromkeys(own + hosts))
    data['url_rewrites'] = [r for r in data.get('url_rewrites', []) if r.get('match') not in [old.get('rewrite_match'), match]]
    data['url_rewrites'].append({'match': match, 'location': location, 'status_code': 302})
    data['name'] = '小羞片网站去广告©️'
    data['description'] = '屏蔽网页及视频插播广告。\n更新时间：' + updated + '（CMS 同步正常）'
    meta = {'plugin_url': PLUGIN, 'script_url': SCRIPT,
        'plugin_sha256': hashlib.sha256(plugin.encode()).hexdigest(),
        'script_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'hostnames': hosts, 'rewrite_match': match, 'remote_parsing': False}
    return data, js, meta

def sync(plugin, source, updated):
    data, js, meta = build(plugin, source, updated)
    old = json.loads(META.read_text()) if META.exists() else {}
    if old == meta and 'CMS 同步正常' in MODULE.read_text() and (ROOT / 'cms-adblock.js').read_text() == js:
        print('CMS source unchanged; kept file update time')
        return
    MODULE.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000))
    (ROOT / 'cms-adblock.js').write_text(js)
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    print('CMS rules synchronized:', len([r for r in data['scriptings'] if r['http_response']['name'].startswith(PREFIX)]))

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode('utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin-file'); parser.add_argument('--script-file'); parser.add_argument('--updated-at')
    args = parser.parse_args()
    try:
        p = Path(args.plugin_file).read_text() if args.plugin_file else fetch(PLUGIN)
        s = Path(args.script_file).read_text() if args.script_file else fetch(SCRIPT)
        sync(p, s, args.updated_at or stamp())
    except Exception as error:
        # Keep the last working script/rules if downloading or validation fails.
        data = yaml.safe_load(MODULE.read_text())
        data['description'] = '屏蔽网页及视频插播广告。\n更新时间：' + (args.updated_at or stamp()) + '（CMS 同步失败，沿用现有规则）'
        MODULE.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000))
        print('CMS sync failed:', type(error).__name__)
        raise SystemExit(1)
