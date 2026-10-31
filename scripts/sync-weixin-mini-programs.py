#!/usr/bin/env python3
"""Sync all 12 public script mirrors plus the replacement image as one validated set."""
import argparse, hashlib, json, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts/weixin-mini-programs-base.yaml'
MANIFEST=ROOT/'scripts/weixin-mini-programs-manifest.json'
MODULE=ROOT/'weixin-mini-programs-adblock.yaml'
SCRIPT=ROOT/'weixin-mini-programs-adblock.js'
IMAGE=ROOT/'weixin-mini-programs-cyys1.jpg'
META=ROOT/'weixin-mini-programs-sync-status.json'
SOURCE='https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/WexinMiniPrograms_Remove_ads/kelee_'
IMAGE_URL='https://raw.githubusercontent.com/Moli-X/Other/main/Backups/KeLee/Resource/Script/WexinMiniPrograms/chayanyuese/cyys1.jpg'
OLD_IMAGE='https://kelee.one/Resource/Script/WexinMiniPrograms/chayanyuese/cyys1.jpg'
OWN='https://raw.githubusercontent.com/huangkouping/egern/main/'
def fetch(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'Egern-Public-Mirror-Sync/1.0'})
    with urllib.request.urlopen(req,timeout=30) as response:data=response.read(limit+1)
    if len(data)>limit:raise ValueError('Mirror too large')
    return data
def description(meta):
    state='全部脚本及图片同步正常' if meta['status']=='ok' else '同步失败，保留上次完整版本'
    return f"更新时间：{meta.get('last_updated','未知')}\n收录常用小程序去广告，保留原模块全部功能。\n同步状态：{state}；最近检查：{meta['last_checked']}"
def build_script(manifest,sources,image_sha):
    parts=[]
    for entry in manifest:
        name=entry['filename'];source=sources[name]
        if not 30<len(source)<100000 or 'JSON.parse' not in source or '$done' not in source:raise ValueError('Invalid script: '+name)
        if any(t in source for t in ['404: Not Found','<html','eval(','$httpClient','$task.fetch','import(']):raise ValueError('Unexpected script content: '+name)
        if name=='chayanyuese_remove_ads.js':
            if source.count(OLD_IMAGE)!=1:raise ValueError('Image dependency changed')
            source=source.replace(OLD_IMAGE,OWN+IMAGE.name+'?v='+image_sha[:12])
        urls=re.findall(r'https?://[^\s"\']+',source)
        if any(not u.startswith(OWN+IMAGE.name+'?v=') for u in urls):raise ValueError('Untracked dependency: '+name)
        parts.append('if (new RegExp('+json.dumps(entry['pattern'])+', "i").test($request.url)) {\n'
            '// '+entry['name']+'; source '+SOURCE+name+'\n'
            '(function () {\n'+source+'\n})();\nreturn {body: typeof result?.body === "string" ? result.body : original};\n}\n')
    output='''/* 可莉公开模块全部12个脚本的 Egern 原生适配，保留各自处理逻辑。 */
export default async function(ctx) {
let original;
try {
if (!ctx.request || !ctx.response) return;
original = await ctx.response.text();
const $request = {url:ctx.request.url,headers:ctx.request.headers};
const $response = {body:original};
let result;
function $done(value) { result=value; }
'''+''.join(parts)+'''
return {body:original};
} catch (_) { return original === undefined ? undefined : {body:original}; }
}
'''
    with tempfile.NamedTemporaryFile(suffix='.mjs',mode='w') as f:
        f.write(output);f.flush()
        checked=subprocess.run(['node','--check',f.name],capture_output=True,timeout=15)
        if checked.returncode:raise ValueError('JavaScript syntax check failed')
    return output
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources-file',type=Path);parser.add_argument('--image-file',type=Path)
    args=parser.parse_args()
    old=json.loads(META.read_text()) if META.exists() else {}
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    try:
        manifest=json.loads(MANIFEST.read_text())
        if len(manifest)!=12:raise ValueError('Unexpected dependency count')
        fixture=json.loads(args.sources_file.read_text()) if args.sources_file else None
        sources={e['filename']:fixture[e['filename']] if fixture is not None else fetch(SOURCE+e['filename'],100000).decode('utf-8') for e in manifest}
        image=args.image_file.read_bytes() if args.image_file else fetch(IMAGE_URL,3000000)
        if not 1000<len(image)<3000000 or image[:3]!=b'\xff\xd8\xff' or image[-2:]!=b'\xff\xd9':raise ValueError('Invalid replacement JPEG')
        image_sha=hashlib.sha256(image).hexdigest()
        script=build_script(manifest,sources,image_sha)
        sha=hashlib.sha256(script.encode()).hexdigest()
        module=yaml.safe_load(BASE.read_text().replace('SOURCE_SCRIPT',OWN+SCRIPT.name+'?v='+sha[:12]))
        changed=not SCRIPT.exists() or SCRIPT.read_text()!=script or not IMAGE.exists() or IMAGE.read_bytes()!=image
        if MODULE.exists():
            previous=yaml.safe_load(MODULE.read_text());previous.pop('description',None)
            changed=changed or previous!=module
        meta={'status':'ok','last_checked':checked,'last_success':checked,'last_updated':checked if changed else old.get('last_updated',checked),
              'sources':{name:{'url':SOURCE+name,'sha256':hashlib.sha256(text.encode()).hexdigest()} for name,text in sources.items()},
              'image':{'url':IMAGE_URL,'sha256':image_sha},'script_sha256':sha,
              'scope':'Sync all 12 public scripts and image together; local module rules maintained separately.'}
        module['description']=description(meta)
        # Nothing is written until every dependency and the adapter is validated.
        SCRIPT.write_text(script);IMAGE.write_bytes(image)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
        META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Weixin mini programs: 12 scripts and image synchronized')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text());module['description']=description(meta)
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
            META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Mini program sync failed; complete last good set retained:',str(error),file=sys.stderr)
        return 1
if __name__=='__main__':sys.exit(main())
