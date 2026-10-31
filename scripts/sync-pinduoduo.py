#!/usr/bin/env python3
"""Sync both public PDD pickup dependencies; keep the existing application rules."""
import argparse
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
MAIN = 'https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/PinDuoDuo_remove_ads/kelee_PinDuoDuo_remove_ads.js'
CHUNK = 'https://raw.githubusercontent.com/darkings/lat3ncy-proxy-configs/main/loon/vendor/pinduoduo/9410-b8806e870a26db7d.js'
CDN = 'https://pfile.pddpic.com/mdkd/mdkd/_next/static/chunks/9410-b8806e870a26db7d.js'
MODULE = ROOT / 'pinduoduo-adblock.yaml'
SCRIPT = ROOT / 'pinduoduo-pickup.js'
META = ROOT / 'pinduoduo-sync-status.json'

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent':'Egern-Public-Mirror-Sync/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(300001)
        if len(data) > 300000:
            raise ValueError('Source exceeds size limit')
        return data.decode('utf-8')

def check_js(source):
    if not source.strip() or any(x in source.lower() for x in ['<!doctype','<html','404: not found']):
        raise ValueError('Invalid JavaScript mirror')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as f:
        f.write(source); f.flush()
        result = subprocess.run(['node','--check',f.name],capture_output=True,text=True,timeout=15)
        if result.returncode:
            raise ValueError('JavaScript syntax check failed')

def adapt(main, chunk):
    check_js(main); check_js(chunk)
    if 'removeGifContainer' not in main or 'trimNextData' not in main or CDN not in main:
        raise ValueError('Pickup script structure changed; review needed')
    if 'webpackChunk_N_E' not in chunk or '[9410]' not in chunk:
        raise ValueError('Pickup chunk structure changed')
    for source in [main, chunk]:
        if any(x in source for x in ['$httpClient', '$task.fetch', 'eval(', 'fetch(', 'XMLHttpRequest']):
            raise ValueError('Unexpected network or dynamic code')
    main, count = re.subn(r'const newChunk = "[^"]+";', 'const newChunk = oldChunk;', main, count=1)
    if count != 1:
        raise ValueError('Chunk replacement boundary changed')
    # Keep the original CDN URL and replace its response locally. Loading a raw
    # GitHub URL as a browser script would risk text/plain / nosniff rejection.
    script = ('/* PDD pickup: public KeLee mirror + darkings vendored chunk.\n'
              ' * Main: '+MAIN+'\n * Chunk: '+CHUNK+'\n */\n'
              '(function(complete){let finished=false;const $done=value=>{if(!finished){finished=true;complete(value);}};try{\n'
              'const url=String($request.url||"");\n'
              'if(url.split("?")[0]==='+json.dumps(CDN)+')return $done({status:200,headers:{"Content-Type":"application/javascript; charset=utf-8","Cache-Control":"no-store"},body:'+json.dumps(chunk,ensure_ascii=False)+'});\n'
              'if(!/^https:\\/\\/m\\.pinduoduo\\.net\\/mdkd\\/package\\?from_app_scan/i.test(url)||typeof $response.body!=="string")return $done({});\n'
              + main + '\n}catch(_){$done({});}})($done);\n')
    check_js(script)
    return script

def describe(meta):
    status = '扫码脚本镜像同步正常' if meta['status']=='ok' else '扫码脚本镜像同步失败，保留上次有效规则'
    return f"更新时间：{meta.get('last_updated','未知')}\n去除广告及推广，精简页面，含扫码取件页清理。\n同步状态：{status}；最近检查：{meta['last_checked']}"

def build(base, script):
    module = yaml.safe_load(base)
    url = 'https://raw.githubusercontent.com/huangkouping/egern/main/pinduoduo-pickup.js?v='+hashlib.sha256(script.encode()).hexdigest()[:12]
    module['rewrites'].extend([
        {'name':'扫码取件页清理','match':r'(?i)^https://m\.pinduoduo\.net/mdkd/package\?from_app_scan',
         'actions':[{'response_script':{'name':'扫码取件页清理','url':url,'timeout':20,'body_required':True}}]},
        {'name':'扫码取件页组件替换','match':r'^https://pfile\.pddpic\.com/mdkd/mdkd/_next/static/chunks/9410-b8806e870a26db7d\.js(?:\?|$)',
         'actions':[{'response_script':{'name':'扫码取件页组件替换','url':url,'timeout':20,'body_required':True}}]}
    ])
    hosts=module['mitm']['hostnames']['includes']
    for host in ['m.pinduoduo.net','pfile.pddpic.com']:
        if host not in hosts: hosts.append(host)
    module['compat_arguments_desc'] = '【使用说明】\n启用后重新打开拼多多；扫码取件页需重新扫码或刷新。请关闭其他同类拼多多模块。\n原有应用内规则保持不变，补全扫码取件页 HTML 清理和页面组件替换。\n两个依赖已合并备份到本仓库，不再访问可莉脚本地址。\n每 6 小时检查两个公开镜像；失败保留上次有效版本。\n镜像源码标注 2026-07-11，未必与可莉服务器当前版本一致，App 效果待实测。'
    return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path);args=parser.parse_args()
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old=json.loads(META.read_text()) if META.exists() else {}
    try:
        main_source=(args.source_dir/'pinduoduo-main.js').read_text() if args.source_dir else fetch(MAIN)
        chunk=(args.source_dir/'pinduoduo-chunk.js').read_text() if args.source_dir else fetch(CHUNK)
        script=adapt(main_source,chunk)
        module=build((ROOT/'scripts/pinduoduo-base.yaml').read_text(),script)
        changed=not SCRIPT.exists() or SCRIPT.read_text()!=script
        if MODULE.exists():
            previous=yaml.safe_load(MODULE.read_text());previous.pop('description',None)
            changed=changed or previous!=module
        meta={'status':'ok','last_checked':checked,'last_success':checked,
              'last_updated':checked if changed else old.get('last_updated',checked),
              'source_urls':[MAIN,CHUNK], 'source_versions':['2026-07-11','2026-07-11'],
              'source_sha256':[hashlib.sha256(s.encode()).hexdigest() for s in [main_source,chunk]],
              'scope':'Only pickup-page dependencies are synchronized; existing application rules are maintained locally.'}
        module['description']=describe(meta)
        SCRIPT.write_text(script)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
        META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('PDD: both pickup dependencies synchronized; existing rules retained');return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text());module['description']=describe(meta)
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
            META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('PDD sync failed; last good module retained:',type(error).__name__,file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
