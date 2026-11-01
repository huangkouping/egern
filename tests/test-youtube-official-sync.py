"""Offline regression: exact official fields, all-or-nothing failure retention."""
import contextlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('youtube_official',ROOT/'scripts/sync-youtube-subtitles.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
upstream=yaml.safe_load((ROOT/'youtube-subtitles-translation.yaml').read_text())
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);source=root/'official.yaml';source.write_text(yaml.safe_dump(upstream,allow_unicode=True))
    mod.ROOT=root;mod.MODULE=root/'youtube-subtitles-translation.yaml';mod.META=root/'youtube-subtitles-sync-status.json'
    mod.download_dependency=lambda url:{'url':url,'resolved_url':url,'sha256':'verified-fixture','bytes':1000}
    sys.argv=['sync','--source-file',str(source)]
    with contextlib.redirect_stdout(io.StringIO()):assert mod.main()==0
    generated=yaml.safe_load(mod.MODULE.read_text())
    for key in upstream:
        if key not in ['name','description']:assert generated[key]==upstream[key],key
    previous=generated.copy();previous.pop('description')
    def fail(_):raise ValueError('fixture upstream unavailable')
    mod.download_dependency=fail
    with contextlib.redirect_stderr(io.StringIO()):assert mod.main()==1
    retained=yaml.safe_load(mod.MODULE.read_text());retained.pop('description')
    assert retained==previous
    assert json.loads(mod.META.read_text())['status']=='failed'
print('PASS: official configuration preserved; failed dependency retained all effective fields')
