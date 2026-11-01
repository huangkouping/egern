#!/usr/bin/env python3
"""Mirror the official DualSubs YouTube release YAML without adapting upstream scripts."""
import argparse,concurrent.futures,hashlib,json,re,subprocess,sys,tempfile,urllib.request
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
from youtube_parameter_ui import apply_ui,UI_VERSION
ROOT=Path(__file__).resolve().parents[1]
UPSTREAM='https://github.com/DualSubs/YouTube/releases/latest/download/DualSubs.YouTube.yaml'
MODULE=ROOT/'youtube-subtitles-translation.yaml'
META=ROOT/'youtube-subtitles-sync-status.json'
def fetch(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'Egern-Official-Release-Sync/1.0','Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=40) as response:
        data=response.read(limit+1);resolved=response.geturl()
    if len(data)>limit:raise ValueError('Upstream resource exceeds size limit')
    return data,resolved
def validate_module(text):
    obj=yaml.safe_load(text)
    if not isinstance(obj,dict) or not isinstance(obj.get('compat_arguments'),dict):raise ValueError('Invalid official module')
    rows=obj.get('scriptings',[])
    if len(rows)<7 or not obj.get('mitm'):raise ValueError('Incomplete official module')
    urls=set();types=set()
    for row in rows:
        if not isinstance(row,dict) or len(row)!=1:raise ValueError('Invalid scripting entry')
        kind,s=next(iter(row.items()));types.add(kind)
        if not isinstance(s,dict):raise ValueError('Invalid scripting configuration')
        re.compile(s['match'])
        url=s['script_url']
        if not url.startswith('https://github.com/'):raise ValueError('Unexpected official script host')
        urls.add(url)
    if not {'http_request','http_response'}.issubset(types):raise ValueError('Missing request/response hooks')
    for row in obj.get('map_locals',[]):
        re.compile(row['match'])
        if not row['to'].startswith('https://github.com/'):raise ValueError('Unexpected settings resource')
        urls.add(row['to'])
    for row in obj.get('rules',[]):
        if 'url_regex' in row:re.compile(row['url_regex']['match'])
    return obj,sorted(urls)
def validate_dependency(item):
    url,data,resolved=item
    if not data or data.lstrip().startswith((b'<!DOCTYPE',b'<html',b'404: Not Found')):raise ValueError('Unreadable official dependency')
    text=data.decode('utf-8')
    if url.split('?')[0].endswith('.js'):
        if len(text)<100:raise ValueError('Unexpected script size')
        with tempfile.NamedTemporaryFile(suffix='.mjs',mode='w') as f:
            f.write(text);f.flush()
            p=subprocess.run(['node','--check',f.name],capture_output=True,timeout=20)
            if p.returncode:raise ValueError('Official script syntax check failed')
    else:
        value=json.loads(text)
        if not isinstance(value,(dict,list)):raise ValueError('Invalid preference pane resource')
    return {'url':url,'resolved_url':resolved,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'content_text':text}
def download_dependency(url):
    data,resolved=fetch(url,8000000)
    return validate_dependency((url,data,resolved))
def description(meta,upstream_description):
    status='官方发布版同步正常' if meta['status']=='ok' else '官方同步失败，保留上次有效版本'
    return f"官方版本：{meta.get('upstream_version','未知')}；更新时间：{meta.get('last_updated','未知')}\n{upstream_description}\n同步状态：{status}；最近检查：{meta['last_checked']}"
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-file',type=Path);parser.add_argument('--skip-download',action='store_true',help='Offline structural validation only; never writes output');args=parser.parse_args()
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old=json.loads(META.read_text()) if META.exists() else {}
    try:
        if args.source_file:data=args.source_file.read_bytes();resolved=UPSTREAM
        else:data,resolved=fetch(UPSTREAM,1000000)
        module,urls=validate_module(data.decode('utf-8'))
        if args.skip_download:
            print(f'Official YAML structure valid: {len(module["scriptings"])} hooks, {len(urls)} dependencies');return 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:dependencies=list(pool.map(download_dependency,urls))
        match=re.search(r'/releases/download/(v[^/]+)/DualSubs.YouTube.yaml',resolved)
        if not match:
            match=re.search(r'/DualSubs/YouTube/releases/download/(v[^/]+)/',json.dumps(module))
        if not match:raise ValueError('Official release version missing')
        version=match.group(1);sha=hashlib.sha256(data).hexdigest()
        sources={item['url']:item['content_text'] for item in dependencies}
        ui_outputs,ui_sources=apply_ui(module,sources,'subtitles')
        for item in dependencies:item.pop('content_text',None)
        with tempfile.TemporaryDirectory() as stage:
            for name,code in ui_outputs.items():
                file=Path(stage)/name;file.write_text(code)
                if subprocess.run(['node','--check',str(file)],capture_output=True,timeout=20).returncode:raise ValueError('Parameter adapter syntax failed')
            subprocess.run(['node',str(ROOT/'tests/test-youtube-parameter-runtime.mjs'),'subtitles',stage],check=True,capture_output=True,timeout=20)
        subprocess.run(['node',str(ROOT/'tests/test-youtube-parameter-ui.mjs'),str(ROOT/'scripts/youtube-parameter-wrapper.js')],check=True,capture_output=True,timeout=20)
        previous_dependencies={d['url']:d['sha256'] for d in old.get('dependencies',[])}
        changed=old.get('ui_sources')!=ui_sources or old.get('upstream_sha256')!=sha or old.get('mode')!='official-release-yaml' or previous_dependencies!={d['url']:d['sha256'] for d in dependencies}
        meta={'status':'ok','mode':'official-release-yaml','last_checked':checked,'last_success':checked,
              'last_updated':checked if changed else old.get('last_updated',checked),'upstream_url':UPSTREAM,
              'resolved_url':resolved,'upstream_version':version,'upstream_sha256':sha,'dependencies':dependencies,
              'upstream_description':module.get('description',''),
              'ui_version':UI_VERSION,'ui_sources':ui_sources,'scope':'Official release rules and original script bodies retained; Chinese native parameter UI and priority selection added.'}
        module['name']='YouTube双语翻译🅗'
        module['description']=description(meta,meta['upstream_description'])
        # Official rules and original script bodies retained; local Chinese controls are wired by the wrapper.
        for name,code in ui_outputs.items():(ROOT/name).write_text(code)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
        META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print(f'Official DualSubs {version}: YAML and {len(dependencies)} remote dependencies verified')
        return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text())
            module['description']=description(meta,old.get('upstream_description','YouTube 字幕及歌词翻译'))
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000))
            META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Official subtitle sync failed; last good module retained:',str(error),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
