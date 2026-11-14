from pathlib import Path
import gzip,hashlib,io,json,tarfile
root=Path(__file__).resolve().parents[1];base=root/'build/offline-tail'
names=[p.relative_to(base).as_posix() for p in sorted((base/'collection').rglob('*')) if p.is_file() and not p.name.endswith('.lock')]
names += ['run.json']+['analysis/'+n for n in ('episodes.json','summary.json','tables.csv','tables.md','frontier-seeds.csv','baselines.csv','headline.svg')]
manifest={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}
target=root/'build/offline-tail.tar.gz'
with target.open('xb') as raw:
    with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
        with tarfile.open(fileobj=gz,mode='w') as tar:
            for n in sorted(manifest)+['MANIFEST.json']:
                data=(base/n).read_bytes() if n!='MANIFEST.json' else (json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode()
                info=tarfile.TarInfo(n);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
report=json.loads((base/'run.json').read_text())
report['portable_rebuild']='evidence/portable-rebuild.json'
report['archive']={'path':'evidence/offline-v02.tar.gz','sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'files':len(manifest),'manifest':'MANIFEST.json inside archive'}
with (root/'build/offline-tail-report.json').open('x') as out: out.write(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
print('PASS: archived',len(manifest),'fake evidence files,',target.stat().st_size,'bytes')
