#!/usr/bin/env python3
"""Validate and back up all four DualSubs scripts; preserve a complete last-good set."""
import argparse,hashlib,json,os,subprocess,sys,tempfile,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
PREFIX='https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/YouTubeSubtitlesTranslation/kelee_'
NAMES={'request':'YouTube_Subtitles_request.js','response':'YouTube_Subtitles_response.js','composite':'YouTube_Composite_Subtitles_response.js','translate':'YouTube_Subtitles_Translate_response.js'}
MODULE=ROOT/'youtube-subtitles-translation.yaml'
META=ROOT/'youtube-subtitles-sync-status.json'
def replace(source,old,new,count):
    if source.count(old)!=count:raise ValueError('Adapter signature changed; review required')
    return source.replace(old,new)
def adapt(source,kind):
    if not 10000<len(source)<1500000 or 'Database=' not in source or '$done' not in source:
        raise ValueError('Invalid public source')
    if any(t in source[:1000] for t in ['404: Not Found','<!DOCTYPE','<html']):raise ValueError('Invalid public source')
    if kind=='request':
        source=replace(source,'a.set(URL,"query.subtype","Translate")','xe.searchParams.set("subtype","Translate")',1)
        source=replace(source,'a.set(URL,"query.subtype","External")','xe.searchParams.set("subtype","External")',1)
        source=replace(source,'o?.playbackContext&&','n.AutoCC&&o?.playbackContext&&',2)
    wrapper=(ROOT/'scripts/youtube-subtitles-adapter.js').read_text()
    result=wrapper.replace('SCRIPT_KIND',json.dumps(kind)).replace('SOURCE_CODE',source)
    with tempfile.NamedTemporaryFile(suffix='.mjs',mode='w') as f:
        f.write(result);f.flush()
        p=subprocess.run(['node','--check',f.name],capture_output=True,timeout=20)
        if p.returncode:raise ValueError('Invalid JavaScript syntax')
    return result
def desc(meta):
    state='全部4个字幕脚本同步正常' if meta['status']=='ok' else '同步失败，保留上次完整版本'
    return f"更新时间：{meta.get('last_updated','未知')}\n字幕增强、双语合成及YouTube Music歌词翻译。\n同步状态：{state}；最近检查：{meta['last_checked']}"
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path);args=parser.parse_args()
    old=json.loads(META.read_text()) if META.exists() else {}
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    try:
        sources={};outputs={}
        for kind,name in NAMES.items():
            if args.source_dir:source=(args.source_dir/name).read_text()
            else:
                req=urllib.request.Request(PREFIX+name,headers={'User-Agent':'Egern-Public-Mirror-Sync/1.0'})
                with urllib.request.urlopen(req,timeout=30) as response:source=response.read(1500001).decode('utf-8')
            sources[kind]=source;outputs['youtube-subtitles-'+kind+'.js']=adapt(source,kind)
        with tempfile.TemporaryDirectory() as stage:
            for name,text in outputs.items():(Path(stage)/name).write_text(text)
            test=subprocess.run(['node',str(ROOT/'tests/test-youtube-subtitles.mjs')],env=dict(os.environ,YT_SUBTITLES_DIR=stage),capture_output=True,text=True,timeout=40)
            if test.returncode:raise ValueError('Subtitle functional validation failed')
        template=(ROOT/'scripts/youtube-subtitles-base.yaml').read_text()
        for kind in NAMES:
            filename='youtube-subtitles-'+kind+'.js';sha=hashlib.sha256(outputs[filename].encode()).hexdigest()
            template=template.replace('SOURCE_'+kind.upper(),'https://raw.githubusercontent.com/huangkouping/egern/main/'+filename+'?v='+sha[:12])
        module=yaml.safe_load(template)
        changed=any(not (ROOT/name).exists() or (ROOT/name).read_text()!=text for name,text in outputs.items())
        if MODULE.exists():
            previous=yaml.safe_load(MODULE.read_text());previous.pop('description',None);changed=changed or previous!=module
        meta={'status':'ok','last_checked':checked,'last_success':checked,'last_updated':checked if changed else old.get('last_updated',checked),
              'sources':{k:{'url':PREFIX+NAMES[k],'sha256':hashlib.sha256(v.encode()).hexdigest()} for k,v in sources.items()},
              'scope':'Sync 4 complete public JS mirrors; adapter and module rules separately maintained.',
              'services':'YouTube official subtitles; translation provider from DualSubs settings (Google by default).'}
        module['description']=desc(meta)
        # Publish only after all sources compile and functional checks pass.
        for name,text in outputs.items():(ROOT/name).write_text(text)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('YouTube subtitles: all four scripts synchronized and verified')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text());module['description']=desc(meta)
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('YouTube subtitle sync failed; last complete set retained:',str(error),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
