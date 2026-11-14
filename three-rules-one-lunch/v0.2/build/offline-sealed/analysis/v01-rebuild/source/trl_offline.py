"""Fake-only dry run and portable evidence rebuild; never constructs a live provider."""
import argparse
import gzip
import io
from pathlib import Path
import tarfile
import tempfile
from trl_core import ROOT, canonical, sha
from trl_io import read, save, lock, Stop
from trl_budget import Ledger, ActiveTime
from trl_collect import episode
from trl_transport import Fake
from trl_analysis import analyze


def dry_run(root,out):
    root,out = Path(root),Path(out)
    out.mkdir(parents=True,exist_ok=False)
    base = out/'collection'
    selected = [e for e in read(root/'config/episodes.json') if e['seed'] in (0,19)]
    with lock(base/'collector.lock'):
        ledger = Ledger(base/'cost.jsonl')
        timer = ActiveTime(base/'time-fake.jsonl',43200)
        timer.begin('offline-fixture')
        try:
            for ep in selected:
                episode(ep,Fake(),base,ledger,timer,'FAKE-NO-PUSH-NO-MODEL')
        finally:
            timer.end()
    summary = analyze(root,base,out/'analysis')
    save(out/'run.json',{'kind':'FAKE','episodes':len(selected),'calls':sum(len(list(p.glob('*.start.json'))) for p in (base/'episodes').iterdir()),
        'model_calls':0,'paid_calls':0,'ledger_settled_micro_usd':ledger.spent,'scientific_result':False})
    return summary


def archive(out,target):
    out,target = Path(out),Path(target)
    manifest = {p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}
    save(target.with_suffix('.manifest.json'),manifest)
    # Stable archive metadata; variable timestamps within evidence are retained verbatim.
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as z:
            with tarfile.open(fileobj=z,mode='w') as tar:
                for name in sorted(manifest):
                    data = (out/name).read_bytes()
                    info = tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
                    tar.addfile(info,io.BytesIO(data))


def rebuild(root,archive_path,out):
    root,archive_path,out = Path(root),Path(archive_path),Path(out)
    manifest = read(archive_path.with_suffix('.manifest.json'))
    with tempfile.TemporaryDirectory(prefix='trl-rebuild-') as temp:
        temp = Path(temp)
        with tarfile.open(archive_path,'r:gz') as tar:
            members = tar.getmembers()
            if len({m.name for m in members})!=len(members) or set(m.name for m in members)!=set(manifest):
                raise Stop('archive member inventory mismatch')
            for member in members:
                p = Path(member.name)
                if p.is_absolute() or '..' in p.parts or not member.isfile():
                    raise Stop('unsafe archive member')
                data = tar.extractfile(member).read()
                if sha(data)!=manifest[member.name]:
                    raise Stop('archive hash mismatch')
                dest = temp/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        result = analyze(root,temp/'collection',out)
        if result!=read(temp/'analysis/summary.json') or read(out/'episodes.json')!=read(temp/'analysis/episodes.json') or any((out/name).read_bytes()!=(temp/'analysis'/name).read_bytes() for name in ('tables.csv','tables.md','frontier-seeds.csv')):
            raise Stop('fresh offline rebuild differs from saved analysis')
        return {'status':'PASS','episodes':960,'kind':'FAKE','summary_sha256':sha((out/'summary.json').read_bytes())}


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=['dry-run','archive','rebuild']);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--archive',type=Path)
    a = p.parse_args()
    if a.command=='dry-run':
        dry_run(a.root,a.out)
        print(read(a.out/'run.json'))
    elif a.command=='archive':
        archive(a.out,a.archive)
    else:
        print(rebuild(a.root,a.archive or a.root/'evidence/offline-dryrun.tar.gz',a.out))

if __name__=='__main__':
    main()
