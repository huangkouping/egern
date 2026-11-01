#!/usr/bin/env python3
"""Sync the multi-engine search module (Baidu/Bing/Google) built on limbopro/Adblock4limbo (original repo); retain last-good on failure.

Only the three Baidu rules are extracted from the upstream mega-conf;
Bing/Google get static injector rules (the userscript's own @match list
covers their search pages) plus the local multi-engine auto-pager:
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
PAGER = ROOT / 'baidu-autopager.js'
META = ROOT / 'baidu-search-sync-status.json'
RAW_BASE = 'https://raw.githubusercontent.com/huangkouping/egern/main/'
FUNCTION_JS_PATTERN = r'(?i)^https?://[^/]+/Adguard/Adblock4limbo\.function\.js'
BING_MATCH = r'^https?://(www|cn)\.bing\.com/search\?'
GOOGLE_MATCH = r'^https?://www\.google\.com(\.hk)?/search'
GOOGLE_CN_PATTERN = r'^https?://(www\.)?(g|google)\.cn(/.*)?$'
GOOGLE_CN_LOCATION = 'https://www.google.com$3'

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
    result = ('/* limbopro 百度搜索去广告注入器备份（源自 limbopro/Adblock4limbo 的 Adguard/Adblock4limbo.js）；源逻辑保持，补充异常透传与单次完成。\n'
              ' * Source: ' + INJECTOR_URL + '\n */\n'
              '(function (complete) {\nlet finished = false;\n'
              'const $done = value => { if (!finished) { finished = true; complete(value); } };\n'
              'try {\n'
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
    state = '上游同步正常' if meta['status'] == 'ok' else '上游同步失败，保留上次有效规则'
    return (f"更新时间：{meta.get('last_updated', '未知')}\n"
            '去除百度、Bing、Google 的搜索广告（limbo 毒奶脚本的搜索引擎部分），三家结果页均带自动翻页。\n'
            f"同步状态：{state}；最近检查：{meta['last_checked']}")


def validate_pager(text):
    """The auto-pager is a local hand-maintained file (not synced from upstream);
    the sync only references it by hash. Verify it parses and injects correctly."""
    for marker in ['searchAutoPagerPage', 'new-nextpage-only', 'sb_pagN', 'pnnext']:
        if marker not in text:
            raise ValueError('Auto-pager signature missing: ' + marker)
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(text)
        path = handle.name
    check = subprocess.run(['node', '--check', path], capture_output=True, text=True, timeout=15)
    if check.returncode:
        raise ValueError('Auto-pager syntax check failed')
    smoke = r'''
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
global.$request = { url: "https://www.baidu.com/s?wd=test", headers: {} };
global.$response = { headers: { "Content-Type": "text/html; charset=utf-8" }, body: "<html><body><div id=\"results\"></div></body></html>" };
let out = null;
global.$done = v => { out = v; };
eval(src);
if (!out || typeof out.body !== "string" || !out.body.includes("__searchAutopager")) throw new Error("pager not injected");
console.log("pager smoke ok");
'''
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as handle:
        handle.write(smoke)
        smoke_path = handle.name
    run = subprocess.run(['node', smoke_path, path], capture_output=True, text=True, timeout=15)
    if run.returncode or 'pager smoke ok' not in run.stdout:
        raise ValueError('Auto-pager smoke test failed: ' + (run.stderr or run.stdout)[:200])


def build(version, patterns, pager_version):
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
        raise ValueError('Results pattern missing; cannot attach auto-pager')
    scriptings.append({'http_response': {
        'name': '百度搜索结果自动翻页', 'match': results_pattern,
        'script_url': RAW_BASE + 'baidu-autopager.js?v=' + pager_version,
        'body_required': True, 'timeout': 20}})
    injector_url = RAW_BASE + 'baidu-search-adblock.js?v=' + version
    pager_url = RAW_BASE + 'baidu-autopager.js?v=' + pager_version
    for name, match in [('必应搜索去广告', BING_MATCH), ('谷歌搜索去广告', GOOGLE_MATCH)]:
        scriptings.append({'http_response': {
            'name': name, 'match': match, 'script_url': injector_url,
            'body_required': True, 'timeout': 20}})
        scriptings.append({'http_response': {
            'name': name.replace('去广告', '自动翻页'), 'match': match, 'script_url': pager_url,
            'body_required': True, 'timeout': 20}})
    return {
        'name': '搜索去广告&自动翻页©️',
        'author': 'limbopro[https://github.com/limbopro/Adblock4limbo]',
        'homepage': 'https://github.com/huangkouping/egern',
        'icon': 'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/Baidu.png',
        'compat_arguments_desc': ('【使用说明】\n启用模块，确认 MitM 已开启且证书受信任，然后重新打开浏览器访问百度、Bing 或 Google。\n'
            '本模块只摘取 limbopro/Adblock4limbo 合集中的搜索引擎部分，不含其数百个其他站点规则。百度走合集原规则（知道、搜索首页、搜索结果 3 条）；Bing、Google 用同一注入器运行 limbopro 用户脚本自带的搜索引擎逻辑（去广告与内容农场结果过滤，其脚本 @match 本就包含这两家）。\n'
            '注入器镜像自 limbopro 原仓库，每 6 小时自动检查上游更新，失败时保留上次有效版本；页面脚本与分域名 CSS 运行时由 limbopro.com 加载（作者分发方式）。\n'
            '已按作者在脚本头注明的官方方法，拦截 Adblock4limbo.function.js：右下角导航按钮、导航面板及其附带功能（沉浸式翻译、划词搜索等）全部禁用，只保留纯去广告。\n'
            '自动翻页为自维护脚本（与 limbopro 上游无关，不受其更新影响）：百度已按实测结构验证；Bing 分页变体生效，若页面是官方渐进加载变体则自动不干预；Google 为通用实现，待实机验证。\n'
            '另含谷歌域名重定向（源 DivineEngine）：google.cn / g.cn 自动跳转 google.com，并保留路径与搜索词。NobyDa 的人机验证增强依赖 Surge/QX 的代理策略 API，Egern 不支持，未并入。\n'
            '若某个搜索页面异常，先停用本模块排查。'),
        'dns': {},
        'scriptings': scriptings,
        'url_rewrites': [{'match': FUNCTION_JS_PATTERN, 'location': 'http://reject-dict/'},
                         {'match': GOOGLE_CN_PATTERN, 'location': GOOGLE_CN_LOCATION, 'status_code': 302}],
        'mitm': {'hostnames': {'includes': ['www.baidu.com', 'm.baidu.com', 'zhidao.baidu.com',
                                            'www.bing.com', 'cn.bing.com',
                                            'www.google.com', 'www.google.com.hk',
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
        pager_text = PAGER.read_text()
        validate_pager(pager_text)
        pager_sha = hashlib.sha256(pager_text.encode()).hexdigest()
        sha = hashlib.sha256(script.encode()).hexdigest()
        module = build(sha[:12], patterns, pager_sha[:12])
        changed = not SCRIPT.exists() or SCRIPT.read_text() != script
        if MODULE.exists():
            previous = yaml.safe_load(MODULE.read_text())
            previous.pop('description', None)
            changed = changed or previous != module
        meta = {'status': 'ok', 'last_checked': checked, 'last_success': checked,
                'last_updated': checked if changed else old.get('last_updated', checked),
                'source_conf': CONF_URL, 'source_injector': INJECTOR_URL,
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'script_sha256': sha,
                'pager_sha256': pager_sha,
                'counts': {'scriptings': len(module['scriptings']), 'url_rewrites': 2},
                'scope': 'Search-engine slice of limbopro/Adblock4limbo: Baidu 3 response rules + mirrored injector, plus Bing/Google injector rules running the userscript built-in search-engine logic; Adblock4limbo.function.js rejected to disable the navigation panel per the author-documented switch; plus a local hand-maintained multi-engine auto-pager (baidu-autopager.js, referenced by hash, never overwritten by sync); plus a DivineEngine google.cn/g.cn -> google.com 302 redirect preserving path and query; auto-sync every 6h via Muse cron; last-good retained on failure.'}
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
