"""Immutable offline freeze and read-only separate-clone GitHub attestation."""
import argparse
import datetime as dt
from pathlib import Path
import subprocess
from od_core import ROOT,sha,schedule,render,reserve
from od_io import Stop,read,save,save_bytes,now,lock
from od_provenance import REPOSITORY,push_record,receipt_gate,timestamp


def inputs(root):
    root=Path(root);names=[]
    for p in root.iterdir():
        if p.suffix in ('.py','.md'): names.append(p.name)
    for folder in ('config','tests','fixtures','evidence'):
        for p in (root/folder).rglob('*'):
            if '__pycache__' in p.parts: continue
            if p.is_file(): names.append(p.relative_to(root).as_posix())
    for p in (root/'offline').iterdir():
        if p.is_file() and (p.name.endswith('.tar.gz') or p.name.endswith('.json')): names.append(p.relative_to(root).as_posix())
    return sorted(names)


def verify(root=ROOT):
    root=Path(root);path=root/'freeze.json'
    if path.is_symlink(): raise Stop('symlink freeze')
    f=read(path)
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
    if timestamp(s)<=timestamp(read(root/'freeze.json')['created_at']): raise Stop('push predates freeze')
    if not repo_path or repo_path.startswith('/') or any(p in ('..','.git') for p in Path(repo_path).parts) or ':' in repo_path: raise Stop('invalid repo path')
    def git(*args): return subprocess.check_output(['git',*args],cwd=clone,timeout=40)
    if git('rev-parse','HEAD').decode().strip()!=commit: raise Stop('clone HEAD mismatch')
    origin=git('remote','get-url','origin').decode().strip()
    if origin not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git','git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git'): raise Stop('repository origin mismatch')
    # Bind every frozen source blob, not just the manifest's asserted hashes.
    for name,h in dict(read(root/'freeze.json')['files'],**{'freeze.json':freeze_hash}).items():
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
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','attest']);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--event',type=Path);p.add_argument('--commit');p.add_argument('--clone-root',type=Path);p.add_argument('--repo-path',default='one-door-many-hands');a=p.parse_args()
    if a.command=='attest':
        if not all((a.event,a.commit,a.clone_root)): p.error('attest requires --event --commit --clone-root')
        print(attest(a.root,a.event,a.commit,a.clone_root,a.repo_path))
    else: print({'freeze':freeze,'verify':verify}[a.command](a.root))
