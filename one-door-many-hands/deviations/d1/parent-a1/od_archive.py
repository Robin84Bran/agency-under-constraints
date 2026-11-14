"""Safe portable fake-evidence archives; no transports or network."""
from pathlib import Path
import tarfile
from od_core import sha
from od_io import save,read,Stop

def archive(source,target):
    source=Path(source);target=Path(target)
    if target.exists(): raise Stop('archive exists')
    manifest={p.relative_to(source).as_posix():sha(p.read_bytes()) for p in sorted(source.rglob('*')) if p.is_file()}
    save(target.with_suffix('').with_suffix('.manifest.json'),manifest)
    # Normalized metadata; individual retained record bytes remain exact.
    with target.open('xb') as out:
        import gzip
        with gzip.GzipFile(fileobj=out,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w') as t:
                for name in manifest:
                    p=source/name;info=t.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                    with p.open('rb') as f:t.addfile(info,f)


def verify_archive(target):
    target=Path(target);manifest=read(target.with_suffix('').with_suffix('.manifest.json'))
    with tarfile.open(target,'r:gz') as t:
        members=t.getmembers()
        if len({m.name for m in members})!=len(members) or set(m.name for m in members)!=set(manifest): raise Stop('archive set mismatch')
        for m in members:
            if not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts: raise Stop('unsafe archive')
            if sha(t.extractfile(m).read())!=manifest[m.name]: raise Stop('archive content mismatch')
    return len(manifest)

