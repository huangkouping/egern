"""Offline regression: official core fields, native UI and failure retention."""
import contextlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('youtube_official',ROOT/'scripts/sync-youtube-subtitles.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
upstream=yaml.safe_load((ROOT/'youtube-subtitles-translation.yaml').read_text())
meta=json.loads((ROOT/'youtube-subtitles-sync-status.json').read_text())
for row in upstream['scriptings']:
    entry=next(iter(row.values()))
    for filename,info in meta.get('ui_sources',{}).items():
        if ('/'+filename+'?') in entry['script_url']:entry['script_url']=info['upstream_url']
upstream.pop('env_schema',None)
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);source=root/'official.yaml';source.write_text(yaml.safe_dump(upstream,allow_unicode=True))
    (root/'scripts').symlink_to(ROOT/'scripts',target_is_directory=True)
    (root/'tests').symlink_to(ROOT/'tests',target_is_directory=True)
    mod.ROOT=root;mod.MODULE=root/'youtube-subtitles-translation.yaml';mod.META=root/'youtube-subtitles-sync-status.json'
    bodies={}
    for filename,info in meta.get('ui_sources',{}).items():
        code=(ROOT/filename).read_text()
        body=code.split('  (function ($argument, globalThis, $done) {\n',1)[1].rsplit('\n  })(argument,proxy,finish);',1)[0]
        bodies[info['upstream_url']]=body
    mod.download_dependency=lambda url:{'url':url,'resolved_url':url,'sha256':'fixture','bytes':1000,'content_text':bodies.get(url,'/* fixture */\n$done({});\n')}
    sys.argv=['sync','--source-file',str(source)]
    with contextlib.redirect_stdout(io.StringIO()):assert mod.main()==0
    generated=yaml.safe_load(mod.MODULE.read_text())
    assert len(generated['env_schema'])==7
    assert generated['compat_arguments']['Storage']=='Argument'
    for key in ['rules','mitm','map_locals','open_url']:assert generated[key]==upstream[key]
    for before,after in zip(upstream['scriptings'],generated['scriptings']):
        a=next(iter(before.values()));b=next(iter(after.values()));assert a['match']==b['match']
        if a['script_url'].endswith('/api.js'):assert a['script_url']==b['script_url']
        else:assert '/youtube-subtitles-ui-' in b['script_url']
    previous=generated.copy();previous.pop('description')
    def fail(_):raise ValueError('fixture unavailable')
    mod.download_dependency=fail
    with contextlib.redirect_stderr(io.StringIO()):assert mod.main()==1
    retained=yaml.safe_load(mod.MODULE.read_text());retained.pop('description');assert retained==previous
    assert json.loads(mod.META.read_text())['status']=='failed'
print('PASS: official core retained; Chinese controls wired; failed dependency retains effective fields')
