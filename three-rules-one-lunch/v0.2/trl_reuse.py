"""Portable immutable v0.1 source/evidence replay, with no provider imports in analysis."""
from pathlib import Path
import subprocess
import sys
import tarfile
from trl_core import ROOT, sha
from trl_io import Stop, read, save


def extract(root, target):
    root,target=Path(root),Path(target)
    target.mkdir(parents=True,exist_ok=False)
    manifest=read(root/'reuse/manifest.json')
    with tarfile.open(root/'reuse/v01.tar.gz','r:gz') as tar:
        members=tar.getmembers()
        if len(members)!=len(manifest) or {m.name for m in members}!=set(manifest):
            raise Stop('v0.1 archive inventory mismatch')
        for m in members:
            rel=Path(m.name)
            if not m.isfile() or rel.is_absolute() or '..' in rel.parts:
                raise Stop('unsafe v0.1 archive member')
            data=tar.extractfile(m).read()
            if sha(data)!=manifest[m.name]: raise Stop('v0.1 archived bytes changed')
            p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return target


def rebuild(root, out, legacy_tests=False):
    root,out=Path(root),Path(out)
    source=extract(root,out/'source')
    commands=[[sys.executable,'-B','trl_freeze.py','verify'],
              [sys.executable,'-B','trl_analysis.py','--out','../analysis']]
    if legacy_tests:
        commands.append([sys.executable,'-B','trl_test.py','--out','build/v02-reuse-tests.json'])
    for i,cmd in enumerate(commands):
        with (out/f'rebuild-{i}.log').open('x') as log:
            subprocess.run(cmd,cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
    files={}
    for name in ('episodes.json','summary.json','tables.csv','tables.md','frontier-seeds.csv'):
        a,b=(root/'reuse'/('v01-'+name)).read_bytes(),(out/'analysis'/name).read_bytes()
        if a!=b: raise Stop('v0.1 raw replay differs: '+name)
        files[name]=sha(a)
    result={'status':'PASS','source_files':len(read(root/'reuse/manifest.json')),
            'byte_identical_outputs':files,'model_calls':0,'network_calls':0,
            'legacy_tests':read(source/'build/v02-reuse-tests.json') if legacy_tests else None}
    save(out/'verification.json',result)
    return result
