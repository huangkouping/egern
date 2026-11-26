#!/usr/bin/env python3
"""Sync the multi-engine search module (Baidu/Bing/Google) built on limbopro/Adblock4limbo (original repo); retain last-good on failure.

Only the three Baidu rules are extracted from the upstream mega-conf;
Bing/Google get static injector rules (the userscript's own @match list
covers their search pages) with the independent Baidu targets:
zhidao search, Baidu homepage, Baidu results. The mirrored injector
(Adguard/Adblock4limbo.js) loads limbopro's runtime assets; the module
additionally rejects Adblock4limbo.function.js, which is the author's own
documented switch to disable the navigation button/panel and its attached
features globally (see the header notes of Adblock4limbo.user.js), while the
ad-removal userscript and per-domain CSS keep working.
Any upstream shape change aborts the sync instead of emitting a partial module.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONF_URL = 'https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adblock4limbo.conf'
INJECTOR_URL = 'https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adguard/Adblock4limbo.js'
MODULE = ROOT / 'baidu-search-adblock.yaml'
SCRIPT = ROOT / 'baidu-search-adblock.js'
META = ROOT / 'baidu-search-sync-status.json'
RAW_BASE = 'https://raw.githubusercontent.com/huangkouping/egern/main/'
FUNCTION_JS_PATTERN = r'(?i)^https?://[^/]+/Adguard/Adblock4limbo\.function\.js'
BING_MATCH = r'^https?://(www|cn)\.bing\.com/search\?'
GOOGLE_MATCH = r'^https?://www\.google\.com(\.hk|\.tw)?/search'
GOOGLE_CN_PATTERN = r'^https?://(www\.)?(g|google)\.cn(/.*)?$'
GOOGLE_CN_LOCATION = 'https://www.google.com$3'

BAIDU_CARD_FILTER = r"""
(() => {
  // Search-result cards only. Ordinary enterprise listings and snippets can mention ads.
  const ids = '#results, #content_left';
  const card = ':is(.c-result,.result,.result-op,.c-container)';
  const marker = '[data-tuiguang], [data-module="ad"], .ec-tuiguang, .ecfc-tuiguang, .ec-result, .ecom-result, .ec_wise_ad, [data-lp][data-placeid]';
  const flag = 'data-egern-baidu-sponsored';
  const norm = text => (text || '').replace(/[\s\u200b-\u200d\ufeff]/g, '');
  const badgeText = /^(广告|商业推广|赞助广告)$/;
  const style = document.createElement('style');
  style.textContent = '[' + flag + ']{display:none!important}';
  (document.head || document.documentElement).appendChild(style);
  const label = 'span,small,i,em,div,a,button,[aria-label]';
  function inFooter(node, item) {
    // Accept the exact disclosure only in card chrome, not a result title or snippet.
    if (node.closest('h1,h2,h3,h4,p,summary,[role="heading"]')) return false;
    for (let el = node; el && el !== item; el = el.parentElement) {
      if (el.matches('footer,[role="contentinfo"]') ||
          /(?:^|[\s_-])(?:foot(?:er)?|ad[-_]?label|ad[-_]?tag|disclaimer|disclosure|source|site|origin)(?:$|[\s_-])/i.test(el.className || '')) return true;
      if (el.parentElement === item && el === item.lastElementChild && el !== node &&
          !el.querySelector('h1,h2,h3,h4,p,article,summary,[role="heading"]') &&
          norm(el.textContent).length <= 80 && item.children.length > 1 &&
          [...el.children].some(s => s !== node && !s.contains(node) && norm(s.textContent).length > 2)) return true;
    }
    return false;
  }
  function scan() {
    for (const root of document.querySelectorAll(ids)) {
      for (const item of root.children) {
        if (item.tagName !== 'DIV' && item.tagName !== 'ARTICLE') continue;
        if (item.hasAttribute(flag)) continue;
        // Do not promote a nested result's ad marker into a hide of an entire results list.
        const candidate = item.matches(card) || item.matches(marker);
        if (!candidate || item.querySelector(ids)) continue;
        if (item.matches(marker) ||
          [...item.querySelectorAll(marker)].some(el => !el.closest('h1,h2,h3,h4,p,summary'))) {
          item.setAttribute(flag, '');
          continue;
        }
        for (const node of item.querySelectorAll(label)) {
          if (node.children.length || !inFooter(node, item)) continue;
          if (badgeText.test(norm(node.textContent)) ||
              badgeText.test(norm(node.getAttribute('aria-label')))) {
            item.setAttribute(flag, '');
            break;
          }
          if (!norm(node.textContent) && /(?:ad|tag|tip|label|badge|tuiguang)/i.test(node.className || '') &&
              ['::before','::after'].some(p => badgeText.test(norm(getComputedStyle(node,p).content).replace(/^['"]|['"]$/g,'')))) {
            item.setAttribute(flag, '');
            break;
          }
        }
      }
    }
  }
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; scan(); });
  };
  scan();
  new MutationObserver(schedule).observe(document.documentElement, {childList:true,subtree:true,characterData:true});
})();
"""

RULE_NAMES = [
    ('zhidao', '百度知道去广告'),
    ('from=', '百度搜索结果去广告'),
    ('(/$|', '百度搜索首页去广告'),
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Egern-Public-Mirror-Sync/1.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(400001).decode('utf-8')


def parse_conf(text):
    patterns = []
    for raw in text.splitlines():
        line = raw.strip()
        if 'baidu' not in line or 'script-response-body' not in line:
            continue
        m = re.fullmatch(r'(\S+)\s+url\s+script-response-body\s+(\S+)', line)
        if not m:
            raise ValueError('Unrecognized Baidu rule line: ' + line[:80])
        if m.group(2) != INJECTOR_URL:
            raise ValueError('Unexpected Baidu script URL: ' + m.group(2))
        patterns.append(m.group(1).replace('\\/', '/'))
    if len(patterns) != 3:
        raise ValueError(f'Expected 3 Baidu rules, got {len(patterns)}')
    joined = ' '.join(patterns)
    for probe in ['zhidao', 'from=', 'www|m']:
        if probe not in joined:
            raise ValueError('Baidu rule set changed shape; missing ' + probe)
    return patterns


def adapt(source):
    if len(source) < 2000 or len(source) > 100000:
        raise ValueError('Unexpected injector size')
    for marker in ['Adblock4limbo.user.js', 'Adblock4limbo.function.js', 'limbopro.com/CSS/', '$response', '$done']:
        if marker not in source:
            raise ValueError('Injector signature missing: ' + marker)
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    patch = '<script id="egern-baidu-card-filter">' + BAIDU_CARD_FILTER + '</script>'
    wrapper = r"""
const localPatch = __LOCAL_PATCH__;
const $done = value => {
    if (finished) return;
    finished = true;
    try {
        if (value && typeof value.body === 'string' &&
            /^https?:\/\/(?:m|www)\.baidu\.com\/(?:s\?|from=[^?#]*\/(?:s\?|s(?:\/|$)|tc\?))/i.test($request.url) &&
            !value.body.includes('id="egern-baidu-card-filter"')) {
            const body = value.body;
            const tag = /<\/body\s*>/i;
            if (tag.test(body)) value = {...value, body: body.replace(tag, m => localPatch + m)};
        }
    } catch (_) { /* Leave upstream result untouched if the local overlay fails. */ }
    complete(value);
};
""".replace('__LOCAL_PATCH__', json.dumps(patch, ensure_ascii=False))
    result = ('/* limbopro 百度搜索去广告注入器镜像；含 huangkouping 百度搜索推广卡片补充过滤。\n'
              ' * Source: ' + INJECTOR_URL + '\n */\n'
              '(function (complete) {\nlet finished = false;\n'
              + wrapper + 'try {\n'
              + source + '\n} catch (_) { $done({}); }\n})($done);\n')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(result)
        path = handle.name
    check = subprocess.run(['node', '--check', path], capture_output=True, text=True, timeout=15)
    if check.returncode:
        raise ValueError('JavaScript syntax check failed')
    smoke = r'''
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
const html = "<html><head><title>t</title></head><body>results</body></html>";
global.$request = { url: "https://www.baidu.com/s?wd=test", headers: {} };
global.$response = { headers: { "Content-Type": "text/html; charset=utf-8" }, body: html };
let out = null;
global.$done = v => { out = v; };
eval(src);
if (!out || typeof out.body !== "string") throw new Error("no body returned");
if (!out.body.includes("Adblock4limbo.user.js")) throw new Error("userscript not injected");
if (!out.body.includes("limbopro.com/CSS/baidu.com.css")) throw new Error("baidu css not injected");
if (!out.body.includes('id="egern-baidu-card-filter"')) throw new Error("local Baidu filter not injected");
if (!out.body.includes("Adblock4limbo.function.js")) throw new Error("function.js tag missing (reject rule would be moot)");
console.log("smoke ok");
'''
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(smoke)
        smoke_path = handle.name
    run = subprocess.run(['node', smoke_path, path], capture_output=True, text=True, timeout=15)
    if run.returncode or 'smoke ok' not in run.stdout:
        raise ValueError('Smoke test failed: ' + (run.stderr or run.stdout)[:200])
    return result


def description(meta):
    suffix = '（同步失败）' if meta['status'] != 'ok' else ''
    return ('去除百度、Bing、Google 搜索广告。\n'
            f"更新时间：{meta.get('last_updated', '未知')}{suffix}")


def build(version, patterns):
    scriptings = []
    results_pattern = None
    for pattern in patterns:
        name = next((n for key, n in RULE_NAMES if key in pattern), '百度搜索去广告')
        if 'from=' in pattern:
            results_pattern = pattern
        scriptings.append({'http_response': {
            'name': name, 'match': pattern,
            'script_url': RAW_BASE + 'baidu-search-adblock.js?v=' + version,
            'body_required': True, 'timeout': 20}})
    if results_pattern is None:
        raise ValueError('Baidu results pattern missing')
    injector_url = RAW_BASE + 'baidu-search-adblock.js?v=' + version
    for name, match in [('必应搜索去广告', BING_MATCH), ('谷歌搜索去广告', GOOGLE_MATCH)]:
        scriptings.append({'http_response': {
            'name': name, 'match': match, 'script_url': injector_url,
            'body_required': True, 'timeout': 20}})
    return {
        'name': '搜索去广告🅗',
        'author': 'limbopro[https://github.com/limbopro/Adblock4limbo], huangkouping',
        'homepage': 'https://github.com/huangkouping/egern',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/Baidu.png',
        'compat_arguments_desc': '请启用 MitM 并信任证书。',
        'dns': {},
        'scriptings': scriptings,
        'url_rewrites': [{'match': FUNCTION_JS_PATTERN, 'location': 'http://reject-dict/'},
                         {'match': GOOGLE_CN_PATTERN, 'location': GOOGLE_CN_LOCATION, 'status_code': 302}],
        'mitm': {'hostnames': {'includes': ['www.baidu.com', 'm.baidu.com', 'zhidao.baidu.com',
                                            'www.bing.com', 'cn.bing.com',
                                            'www.google.com', 'www.google.com.hk', 'www.google.com.tw',
                                            'google.cn', 'www.google.cn', 'g.cn', 'www.g.cn',
                                            'limbopro.com']}}}


def main():
    checked = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old = json.loads(META.read_text()) if META.exists() else {}
    try:
        conf = fetch(CONF_URL)
        source = fetch(INJECTOR_URL)
        patterns = parse_conf(conf)
        script = adapt(source)
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12], patterns)
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_conf': CONF_URL, 'source_injector': INJECTOR_URL,
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'counts': {'scriptings': len(module['scriptings']), 'url_rewrites': 2},
                'scope': 'Search ads only; local Baidu card filter, mirrored upstream injector and unchanged Google redirect. Auto-paging is independent.'}
        module['description'] = description(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Baidu search module sync OK; changed =', changed)
        return 0
    except Exception as error:
        if MODULE.exists():
            meta = dict(old, status='failed', last_checked=checked, error=type(error).__name__)
            module = yaml.safe_load(MODULE.read_text())
            module['description'] = description(meta)
            MODULE.write_text(yaml.safe_dump(module, allow_unicode=True, sort_keys=False, width=1000))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print('Baidu search sync failed; last good rules retained:', type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
