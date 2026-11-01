#!/usr/bin/env python3
"""Sync three Sparkle JS builds (adapter identifiers auto-derived per build) and two JQ dependencies as a validated set."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
URL='https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/Bilibili_remove_ads/kelee_'
SPARKLE='https://raw.githubusercontent.com/kokoryh/Sparkle/master/dist/'
NAMES={'request':'Bilibili_proto_request_kokoryh.js','response':'Bilibili_proto_response_kokoryh.js','json':'Bilibili_json_kokoryh.js','tab':'tab_Bilibili_remove_ads.jq','mine':'mine_Bilibili_remove_ads.jq'}
URLS={'request':SPARKLE+'bilibili.protobuf.request.js','response':SPARKLE+'bilibili.protobuf.response.js','json':SPARKLE+'bilibili.json.js','tab':URL+NAMES['tab'],'mine':URL+NAMES['mine']}
MODULE=ROOT/'bilibili-adblock.yaml'
META=ROOT/'bilibili-sync-status.json'
def replace_once(source,old,new):
    if source.count(old)!=1:raise ValueError('Upstream adapter signature changed')
    return source.replace(old,new,1)
IDENT=r'[A-Za-z_$][\w$]*'
def derive(source):
    # Minified identifiers change on every upstream rebuild; recover them from
    # stable structural anchors instead of hardcoding per-build names. Any
    # anchor that is missing or ambiguous aborts the sync (last good retained).
    def one(pattern,label):
        found=re.findall(pattern,source)
        if len(found)!=1:raise ValueError('Cannot auto-derive '+label+' ('+str(len(found))+' candidates)')
        return found[0]
    parent=one(r'return new ('+IDENT+r')\}request;response;state=','platform class')
    inst,base,compose=one(r'let ('+IDENT+r')=('+IDENT+r')\.createInstance\(\);('+IDENT+r')\(this\.middleware\)','script engine')
    runner=one(r'var ('+IDENT+r')=new '+IDENT+r';\1\.use\(','app runner')
    logger=one(r'('+IDENT+r')=class\{static level=\d+;static setLevel','logger class')
    gz=re.findall(r'function ('+IDENT+r')\(('+IDENT+r')\)\{return \$utils\.ungzip\(\2\)\}',source)
    if len(gz)>1:raise ValueError('Cannot auto-derive gunzip helper')
    gunzip,arg=gz[0] if gz else (None,None)
    return parent,inst,base,compose,runner,logger,gunzip,arg
def adapt(source,kind):
    if not 1000<len(source)<500000 or 'createInstance' not in source:raise ValueError('Invalid JS mirror')
    if any(t in source[:1000] for t in ['404: Not Found','<html']):raise ValueError('Invalid JS mirror')
    parent,inst,base,compose,runner,logger,gunzip,arg=derive(source)
    source=replace_once(source,'return new '+parent+'}','return new EgernAdapter}')
    source=replace_once(source,'let '+inst+'='+base+'.createInstance();'+compose+'(this.middleware)','let '+inst+'='+base+'.createInstance();return '+compose+'(this.middleware)')
    if gunzip:
        source=replace_once(source,'function '+gunzip+'('+arg+'){return $utils.ungzip('+arg+')}','async function '+gunzip+'('+arg+'){const bytes=await ctx.compress.gunzip('+arg+');if(!bytes)throw new Error("gzip failed");return bytes}')
        count=source.count('?'+gunzip+'(')
        if count<1:raise ValueError('gRPC framing code changed')
        source=source.replace('?'+gunzip+'(','?await '+gunzip+'(')
    native='''
class EgernAdapter extends PARENT {
 createRequest(e){return Object.defineProperty({...e},"bodyBytes",{get(){return this.body},set(v){this.body=v}});}
 createResponse(e){return this.createRequest(e);}
 async fetch(opts){
   const method=String(opts.method||"GET").toLowerCase();
   const response=await ctx.http[method](opts.url,{headers:opts.headers,body:opts.body,timeout:(opts.timeout??5)*1000});
   return this.createResponse({status:response.status,headers:headers(response.headers),
     body:opts["binary-mode"]===false?await response.text():new Uint8Array(await response.arrayBuffer())});
 }
}
'''.replace('PARENT',parent)
    # The JSON SponsorBlock API needs text, while gRPC redispatch needs raw bytes.
    native=native.replace('opts["binary-mode"]===false','!(opts.body instanceof Uint8Array)')
    source=replace_once(source,runner+'.run();',native+'\n'+logger+'.setLevel(String(ctx.env?.logLevel||"off"));await '+runner+'.run();')
    wrapper=(ROOT/'scripts/bilibili-adapter.js').read_text()
    result=wrapper.replace('SCRIPT_KIND',json.dumps(kind)).replace('SOURCE_CODE',source)
    with tempfile.NamedTemporaryFile(suffix='.mjs',mode='w') as f:
        f.write(result);f.flush()
        p=subprocess.run(['node','--check',f.name],capture_output=True,timeout=20)
        if p.returncode:raise ValueError('Invalid adapted JS')
    return result
def desc(meta):
    state='全部JS及jq镜像同步正常' if meta['status']=='ok' else '同步失败，保留上次完整版本'
    return f"更新时间：{meta.get('last_updated','未知')}\n过滤广告、精简页面，保留可选空降助手等原功能。\n同步状态：{state}；最近检查：{meta['last_checked']}"
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path);args=parser.parse_args()
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M');old=json.loads(META.read_text()) if META.exists() else {}
    try:
        sources={}
        for key,name in NAMES.items():
            if args.source_dir:text=(args.source_dir/name).read_text()
            else:
                req=urllib.request.Request(URLS[key],headers={'User-Agent':'Egern-Public-Mirror-Sync/1.0'})
                with urllib.request.urlopen(req,timeout=30) as response:text=response.read(500001).decode('utf-8')
            sources[key]=text
        outputs={}
        for key in ['request','response','json']:outputs['bilibili-'+key+'.js']=adapt(sources[key],key)
        for key in ['tab','mine']:
            text=sources[key]
            if not 50<len(text)<50000 or '404: Not Found' in text:raise ValueError('Invalid JQ mirror')
            p=subprocess.run(['jq','-n','def verify: '+text+'; empty'],capture_output=True,timeout=15)
            if p.returncode:raise ValueError('Invalid JQ syntax')
            outputs['bilibili-'+key+'.jq']=text
        with tempfile.TemporaryDirectory() as stage:
            for name,text in outputs.items():(Path(stage)/name).write_text(text)
            test=subprocess.run(['node',str(ROOT/'tests/test-bilibili.mjs')],env=dict(os.environ,BILI_DIR=stage),capture_output=True,text=True,timeout=30)
            if test.returncode:raise ValueError('Bilibili functional tests failed')
        module=yaml.safe_load((ROOT/'scripts/bilibili-base.yaml').read_text())
        for row in module['rewrites']:
            for action in row['actions']:
                jq=action.get('response_body',{}).get('jq')
                if isinstance(jq,dict):
                    kind='tab' if jq['source_file']==NAMES['tab'] else 'mine'
                    action['response_body']['jq']=sources[kind]
                elif isinstance(jq,str):
                    p=subprocess.run(['jq','-n','def verify: '+jq+'; empty'],capture_output=True,timeout=15)
                    if p.returncode:raise ValueError('Invalid inline JQ')
        for row in module['scriptings']:
            entry=next(iter(row.values()));token=entry['script_url'];key=token.removeprefix('SOURCE_').lower()
            content=outputs['bilibili-'+key+'.js'];sha=hashlib.sha256(content.encode()).hexdigest()
            entry['script_url']='https://raw.githubusercontent.com/huangkouping/egern/main/bilibili-'+key+'.js?v='+sha[:12]
        changed=any(not (ROOT/name).exists() or (ROOT/name).read_text()!=text for name,text in outputs.items())
        if MODULE.exists():
            previous=yaml.safe_load(MODULE.read_text());previous.pop('description',None);changed=changed or previous!=module
        meta={'status':'ok','last_checked':checked,'last_success':checked,'last_updated':checked if changed else old.get('last_updated',checked),
              'sources':{k:{'url':URLS[k],'sha256':hashlib.sha256(v.encode()).hexdigest()} for k,v in sources.items()},
              'scope':'Sync 3 JS from kokoryh/Sparkle dist (original author) and 2 JQ mirrors; module rules and native adapter separately maintained.',
              'external_services':['https://bsbsb.top','https://github.com/kokoryh/chronos']}
        module['description']=desc(meta)
        for name,text in outputs.items():(ROOT/name).write_text(text)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Bilibili: all 3 JS and 2 JQ dependencies synchronized')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text());module['description']=desc(meta)
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Bilibili sync failed; complete last good set retained:',str(error),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
