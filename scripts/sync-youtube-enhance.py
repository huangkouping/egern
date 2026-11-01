#!/usr/bin/env python3
"""Convert the original Maasea module to Egern, keeping original script bodies untouched."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import yaml
from youtube_parameter_ui import apply_ui,UI_VERSION
ROOT=Path(__file__).resolve().parents[1]
REPO='Maasea/sgmodule'
MODULE_PATH='YouTube.Enhance.sgmodule'
SOURCE_URL='https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule'
SCRIPTS=['Script/Youtube/youtube.response.js','Script/Youtube/youtube.request.js']
MODULE=ROOT/'youtube-enhance.yaml'
META=ROOT/'youtube-enhance-sync-status.json'
def fetch(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'Egern-Maasea-Upstream-Sync/1.0'})
    with urllib.request.urlopen(req,timeout=40) as r:data=r.read(limit+1)
    if len(data)>limit:raise ValueError('Oversized upstream resource')
    return data.decode('utf-8')
def convert(text,revision):
    if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Invalid upstream revision')
    m=re.search(r'^#!arguments=(.*)$',text,re.M)
    if not m:raise ValueError('Upstream arguments missing')
    arguments=dict(item.split(':',1) for item in m[1].strip().split(','))
    rows=[]
    for line in text.splitlines():
        if ' = type=http-' not in line:continue
        name,spec=line.split(' = ',1);parts={}
        # Split only at known directive boundaries; nested regexp/JSON commas remain intact.
        for part in re.split(r',(?=(?:type|pattern|requires-body|max-size|binary-body-mode|script-path|argument)=)',spec):
            key,value=part.split('=',1);parts[key]=value
        path=parts['script-path'];prefix='https://raw.githubusercontent.com/Maasea/sgmodule/master/'
        if not path.startswith(prefix) or path[len(prefix):] not in SCRIPTS:raise ValueError('New upstream script dependency: review required')
        pattern=parts['pattern'];re.compile(pattern)
        arg=parts.get('argument','')
        if arg.startswith('"') and arg.endswith('"'):arg=arg[1:-1]
        entry={'name':name,'match':pattern,'script_url':path.replace('/master/','/'+revision+'/'),
               'body_required':parts.get('requires-body')=='1','binary_body':parts.get('binary-body-mode')=='1',
               'max_size':int(parts.get('max-size','1048576')),'update_interval':21600,
               'env':{'_compat.$argument':arg}}
        if not arg:entry.pop('env')
        kind={'http-request':'http_request','http-response':'http_response'}[parts['type']]
        rows.append({kind:entry})
    if len(rows)!=3:raise ValueError('Upstream route count changed')
    mitm=re.search(r'^hostname\s*=\s*%APPEND%\s*(.*)$',text,re.M)
    if not mitm:raise ValueError('Upstream MITM missing')
    hosts=[v.strip() for v in mitm[1].split(',')]
    original_desc=re.search(r'^#!arguments-desc=(.*)$',text,re.M)
    instructions=(original_desc[1].replace('\\n','\n') if original_desc else '')
    instructions+='\n\n使用说明：开启HTTPS解密并信任证书，确保HTTP/2可解密及QUIC回退。放在YouTube双语字幕模块之前，避免两边重复启用字幕/歌词翻译；原版captionLang默认off。原作者脚本还包含画中画、后台播放、界面及播放配置处理，保留原逻辑。initplayback按原版使用init-stream.maasea.workers.dev，依赖原作者服务。每6小时跟随原仓库，固定到同一提交校验配置与两个JS，原脚本主体不修改，外层仅适配中文参数；任一检查失败保留上次有效配置。兼容性与实际效果需实机验证。'
    return {'name':'YouTube去广告🅗','description':'','author':'Maasea[https://github.com/Maasea]',
            'homepage':'https://github.com/Maasea/sgmodule/blob/master/YouTube.Enhance.sgmodule',
            'open_url':'https://apps.apple.com/app/id544007664',
            'icon':'https://raw.githubusercontent.com/luestr/IconResource/main/App_icon/120px/YouTube.png',
            'compat_arguments':arguments,'compat_arguments_desc':instructions,'dns':{},
            'scriptings':rows,'mitm':{'hostnames':{'includes':hosts}}}
def desc(meta):
    state='Maasea原版同步正常' if meta['status']=='ok' else '同步失败，保留上次有效配置'
    return f"更新时间：{meta.get('last_updated','未知')}\n同步Maasea原版，过滤YouTube及Music广告并保留原功能。\n同步状态：{state}；最近检查：{meta['last_checked']}"
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path);parser.add_argument('--revision');args=parser.parse_args()
    checked=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old=json.loads(META.read_text()) if META.exists() else {}
    try:
        revision=args.revision if args.source_dir else json.loads(fetch('https://api.github.com/repos/'+REPO+'/commits/master',1000000))['sha']
        if not revision:raise ValueError('Revision required for offline mode')
        prefix='https://raw.githubusercontent.com/'+REPO+'/'+revision+'/'
        source=(args.source_dir/MODULE_PATH).read_text() if args.source_dir else fetch(prefix+MODULE_PATH,100000)
        module=convert(source,revision);scripts={}
        for path in SCRIPTS:
            code=(args.source_dir/Path(path).name).read_text() if args.source_dir else fetch(prefix+path,2000000)
            if len(code)<1000 or '404: Not Found' in code[:1000] or '$done' not in code:raise ValueError('Invalid original JS')
            scripts[Path(path).name]=code
        with tempfile.TemporaryDirectory() as stage:
            for name,code in scripts.items():
                f=Path(stage)/name;f.write_text(code)
                p=subprocess.run(['node','--check',str(f)],capture_output=True,timeout=20)
                if p.returncode:raise ValueError('Original JS syntax check failed')
            test=subprocess.run(['node',str(ROOT/'tests/test-youtube-enhance.mjs')],env=dict(os.environ,YOUTUBE_ENHANCE_DIR=stage),capture_output=True,text=True,timeout=20)
            if test.returncode:raise ValueError('Original script regression failed')
        source_map={prefix+path:scripts[Path(path).name] for path in SCRIPTS}
        ui_outputs,ui_sources=apply_ui(module,source_map,'enhance')
        with tempfile.TemporaryDirectory() as stage:
            for name,code in ui_outputs.items():
                file=Path(stage)/name;file.write_text(code)
                if subprocess.run(['node','--check',str(file)],capture_output=True,timeout=20).returncode:raise ValueError('Parameter adapter syntax failed')
            subprocess.run(['node',str(ROOT/'tests/test-youtube-parameter-runtime.mjs'),'enhance',stage],check=True,capture_output=True,timeout=20)
        subprocess.run(['node',str(ROOT/'tests/test-youtube-parameter-ui.mjs'),str(ROOT/'scripts/youtube-parameter-wrapper.js')],check=True,capture_output=True,timeout=20)
        changed=old.get('upstream_commit')!=revision or old.get('ui_sources')!=ui_sources
        if MODULE.exists():
            previous=yaml.safe_load(MODULE.read_text());previous.pop('description',None)
            candidate=dict(module);candidate.pop('description',None);changed=changed or previous!=candidate
        meta={'status':'ok','last_checked':checked,'last_success':checked,'last_updated':checked if changed else old.get('last_updated',checked),
              'upstream_url':SOURCE_URL,'upstream_commit':revision,'config_sha256':hashlib.sha256(source.encode()).hexdigest(),
              'scripts':{path:{'url':prefix+path,'sha256':hashlib.sha256(scripts[Path(path).name].encode()).hexdigest()} for path in SCRIPTS},
              'ui_version':UI_VERSION,'ui_sources':ui_sources,'scope':'Chinese native parameter UI wraps original code unchanged; sync the same verified original commit.'}
        module['description']=desc(meta)
        for name,code in ui_outputs.items():(ROOT/name).write_text(code)
        MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('YouTube Enhance: original module and 2 unmodified scripts verified at '+revision[:12]);return 0
    except Exception as error:
        if MODULE.exists():
            meta=dict(old,status='failed',last_checked=checked,error=type(error).__name__)
            module=yaml.safe_load(MODULE.read_text());module['description']=desc(meta)
            MODULE.write_text(yaml.safe_dump(module,allow_unicode=True,sort_keys=False,width=1000));META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        print('Maasea sync failed; last good configuration retained:',str(error),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
