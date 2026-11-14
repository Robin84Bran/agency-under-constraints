"""Immutable offline freeze and read-only separate-clone GitHub attestation."""
import argparse
import datetime as dt
from pathlib import Path
import subprocess
from od_core import ROOT,sha,schedule,render,reserve
from od_io import Stop,read,save,save_bytes,now,lock
from od_provenance import REPOSITORY,push_record,receipt_gate,timestamp,active_path

A1_CHANGED=frozenset(('od_collect.py','od_validation.py','od_analysis.py','od_freeze.py','od_provenance.py',
    'tests/test_integrity.py','tests/test_validation.py','RUN.md','PROJECT_STATE.md'))


def inputs(root):
    root=Path(root);names=[]
    for p in root.iterdir():
        if p.suffix in ('.py','.md'): names.append(p.name)
    for folder in ('config','tests','fixtures','evidence','deviations'):
        for p in (root/folder).rglob('*'):
            if '__pycache__' in p.parts: continue
            if p.is_file(): names.append(p.relative_to(root).as_posix())
    for p in (root/'offline').iterdir():
        if p.is_file() and (p.name.endswith('.tar.gz') or p.name.endswith('.json')): names.append(p.relative_to(root).as_posix())
    return sorted(names)


def verify(root=ROOT):
    root=Path(root);path=active_path(root)
    if path.is_symlink(): raise Stop('symlink freeze')
    f=read(path)
    if path.name=='freeze-a1.json':
        parent=root/'freeze.json'
        if parent.is_symlink() or sha(parent.read_bytes())!=f['parent_freeze_sha256']: raise Stop('A1 parent freeze mismatch')
        original=read(parent)
        if f['revision']!='A1' or set(f['changed_originals'])!=A1_CHANGED: raise Stop('A1 amendment scope mismatch')
        if any(f.get(k)!=v for k,v in original.items() if k not in ('revision','kind','created_at','files')): raise Stop('A1 original metadata drift')
        for name,h in original['files'].items():
            if name in A1_CHANGED:
                archived='deviations/a1/original/'+name
                if f['files'].get(archived)!=h: raise Stop('A1 original archive mismatch: '+name)
            elif f['files'].get(name)!=h: raise Stop('A1 changed frozen science/evidence: '+name)
        if timestamp(f['created_at'])<=timestamp(original['created_at']): raise Stop('A1 must follow parent freeze')
    if set(f['files'])!=set(inputs(root)): raise Stop('freeze input set drift')
    for name,h in f['files'].items():
        p=root/name
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h: raise Stop('frozen input changed: '+name)
    if read(root/'config/episodes.json')!=schedule(): raise Stop('schedule drift')
    sizing=read(root/'config/sizing.json');total=sum(reserve(render(e))['micro_usd'] for e in schedule() if e['actor']=='claude')
    if f['frontier_reservation_micro_usd']!=total or sizing['frontier_micro_usd']!=total or total+1000000>25000000: raise Stop('frozen reservation mismatch')
    from od_identity import identity
    identity(root)
    return sha(path.read_bytes())


def freeze_a1(root=ROOT):
    root=Path(root)
    if (root/'collection').exists(): raise Stop('A1 revision must precede attestation/collection')
    original=read(root/'freeze.json')
    files={n:sha((root/n).read_bytes()) for n in inputs(root)}
    for name,h in original['files'].items():
        if name in A1_CHANGED:
            if files.get('deviations/a1/original/'+name)!=h: raise Stop('missing exact A1 original: '+name)
        elif files.get(name)!=h: raise Stop('A1 forbidden original change: '+name)
    save(root/'freeze-a1.json',dict(original,revision='A1',kind='pre-registration revision; no push or model calls',created_at=now(),
        parent_freeze_sha256=sha((root/'freeze.json').read_bytes()),changed_originals=sorted(A1_CHANGED),files=files))
    return verify(root)


def freeze(root=ROOT):
    root=Path(root)
    if (root/'collection').exists(): raise Stop('freeze must precede collection')
    total=read(root/'config/sizing.json')['frontier_micro_usd']
    save(root/'freeze.json',{'study':'One Door, Many Hands','revision':'v0.1-r1','kind':'pre-inference offline freeze','created_at':now(),
      'files':{n:sha((root/n).read_bytes()) for n in inputs(root)},'planned_episodes':3720,'local_episodes':3600,'frontier_episodes':120,
      'frontier_reservation_micro_usd':total,'protected_reserve_micro_usd':1000000,'model_calls_made_by_builder':0,
      'delegating_reviewer':'Claude','Robin_project_review':False,'runtime_status':'UNKNOWN','push_status_at_freeze':'UNKNOWN'})
    return verify(root)


def attest(root,event_file,commit,clone_root,repo_path):
    root=Path(root);freeze_hash=verify(root);clone=Path(clone_root)
    source=Path(event_file).read_bytes();event=read(event_file);ref,s=push_record(event,commit)
    if timestamp(s)<=timestamp(read(active_path(root))['created_at']): raise Stop('push predates freeze')
    if not repo_path or repo_path.startswith('/') or any(p in ('..','.git') for p in Path(repo_path).parts) or ':' in repo_path: raise Stop('invalid repo path')
    def git(*args): return subprocess.check_output(['git',*args],cwd=clone,timeout=40)
    if git('rev-parse','HEAD').decode().strip()!=commit: raise Stop('clone HEAD mismatch')
    origin=git('remote','get-url','origin').decode().strip()
    if origin not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git','git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git'): raise Stop('repository origin mismatch')
    # Bind every frozen source blob, not just the manifest's asserted hashes.
    committed=dict(read(active_path(root))['files'],**{'freeze.json':sha((root/'freeze.json').read_bytes())})
    if active_path(root).name=='freeze-a1.json': committed['freeze-a1.json']=freeze_hash
    for name,h in committed.items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=h: raise Stop('committed package mismatch: '+name)
    if not any(line.split()==[commit,ref] for line in git('ls-remote','origin',ref).decode().splitlines()): raise Stop('remote ref mismatch')
    with lock(root/'collection'):
        if (root/'collection/episodes').exists(): raise Stop('attestation must precede starts')
        save_bytes(root/'collection/push-event.json',source)
        save(root/'collection/push.json',{'freeze_sha256':freeze_hash,'repo':REPOSITORY,'commit':commit,'repo_path':repo_path,
          'remote_ref':ref,'pushed_at':s,'server_event_id':event['id'],'event_sha256':sha(source),'source_api':'/repos/'+REPOSITORY+'/activity'})
    return freeze_hash


def push_gate(root):
    h=verify(root);receipt_gate(root);return h

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','freeze-a1','verify','attest']);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--event',type=Path);p.add_argument('--commit');p.add_argument('--clone-root',type=Path);p.add_argument('--repo-path',default='one-door-many-hands');a=p.parse_args()
    if a.command=='attest':
        if not all((a.event,a.commit,a.clone_root)): p.error('attest requires --event --commit --clone-root')
        print(attest(a.root,a.event,a.commit,a.clone_root,a.repo_path))
    else: print({'freeze':freeze,'freeze-a1':freeze_a1,'verify':verify}[a.command](a.root))
