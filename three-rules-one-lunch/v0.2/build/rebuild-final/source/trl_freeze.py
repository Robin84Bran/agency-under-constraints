"""Create-once v0.2 freeze and exact-commit activity-API attestation; never pushes."""
import argparse
import datetime as dt
from pathlib import Path
import re
import subprocess
from trl_core import ROOT, canonical, sha, strict_load
from trl_io import Stop, lock, now, read, save, timestamp, syncdir
from trl_journal import prefix, verify_prefix, Journal

REPO='Robin84Bran/research'
ORIGINS=('git@github.com:Robin84Bran/research.git','https://github.com/Robin84Bran/research.git',
         'https://github.com/Robin84Bran/research','ssh://git@github.com/Robin84Bran/research.git')
LEDGERS=('collection/dispatch.jsonl','collection/time-local.jsonl')


def inputs(root):
    out={}
    for p in sorted(Path(root).rglob('*')):
        rel=p.relative_to(root)
        if any(x in ('build','collection','__pycache__','.git','.agents','.codex','.aws') or x.startswith('.') for x in rel.parts) or rel.as_posix()=='freeze.json': continue
        if p.is_symlink(): raise Stop('symlink frozen input')
        if p.is_file(): out[rel.as_posix()]=sha(p.read_bytes())
    return out


def tested_inputs(root):
    return {n:h for n,h in inputs(root).items() if n.endswith('.py') or n.startswith(('config/','fixtures/','reuse/')) or n=='evidence/toy-model.mjs'}


def freeze(root):
    root=Path(root);report=read(root/'evidence/test-report.json');dry=read(root/'evidence/offline.json')
    if report['status']!='PASS' or report['failures'] or report['errors'] or report['skipped'] or report['tested_files']!=tested_inputs(root):
        raise Stop('current passing tests without skips required')
    if (dry['status']!='PASS' or dry['local_episodes']!=900 or dry['model_calls']!=0 or
        dry.get('tested_files')!=tested_inputs(root)):
        raise Stop('complete fake-only offline verification required')
    if list((root/'collection/episodes').glob('*')): raise Stop('freeze must precede v0.2 collection')
    files=inputs(root)
    f={'study':'three-rules-one-lunch','protocol_revision':'v0.2','created_at':now(),
       'kind':'pre-inference offline freeze','files':files,'content_sha256':sha(canonical(files).encode()),
       'planned_local_episodes':900,'maximum_local_calls':8400,'reused_v01_claude_episodes':60,
       'new_frontier_calls':0,'model_calls_made_by_builder':0,'push_status':'UNKNOWN',
       'ledger_prefixes':{n:prefix(root/n) for n in LEDGERS},'stop_after':'v0.2'}
    save(root/'freeze.json',f);return verify(root)


def verify(root):
    root=Path(root);f=read(root/'freeze.json')
    actual=inputs(root)
    if f['files']!=actual or f['content_sha256']!=sha(canonical(actual).encode()): raise Stop('frozen input inventory/hash mismatch')
    if f['protocol_revision']!='v0.2' or f['new_frontier_calls']!=0 or f['stop_after']!='v0.2': raise Stop('version/scope mismatch')
    for n in LEDGERS: verify_prefix(root/n,f['ledger_prefixes'][n])
    Journal(root/'collection/dispatch.jsonl')
    return sha((root/'freeze.json').read_bytes())


def push_record(event,commit):
    if type(commit) is not str or not re.fullmatch('[0-9a-f]{40}',commit) or type(event) is not dict:
        raise Stop('full commit and activity record required')
    if event.get('activity_type')!='push' or event.get('after')!=commit:
        raise Stop('activity API exact push commit required')
    ref,when=event.get('ref'),event.get('timestamp')
    if type(ref) is not str or not re.fullmatch(r'refs/heads/[A-Za-z0-9_][A-Za-z0-9._/-]*',ref): raise Stop('branch ref required')
    try: pushed=timestamp(when)
    except (ValueError,TypeError,AttributeError): raise Stop('server timestamp required') from None
    if pushed>=dt.datetime.now(dt.timezone.utc) or type(event.get('id')) not in (str,int) or not str(event['id']):
        raise Stop('past server time/id required')
    return ref,when


def select_event(events_file,commit,out):
    pages=read(events_file)
    if type(pages) is not list: raise Stop('activity API array/pages required')
    if pages and type(pages[0]) is list: pages=[e for page in pages for e in page]
    matches=[]
    for e in pages:
        try: push_record(e,commit)
        except Stop: continue
        matches.append(e)
    if not matches: raise Stop('no activity record for exact commit; retain response and wait')
    save(out,max(matches,key=lambda e:timestamp(push_record(e,commit)[1])));return str(out)


def attest(root,event_file,commit,repo_path,clone_root):
    root=Path(root);digest=verify(root);f=read(root/'freeze.json')
    raw=Path(event_file).read_bytes();event=strict_load(raw.decode());ref,when=push_record(event,commit)
    if timestamp(when)<timestamp(f['created_at']): raise Stop('push predates freeze')
    if not repo_path or Path(repo_path).is_absolute() or '..' in Path(repo_path).parts or ':' in repo_path: raise Stop('invalid repository path')
    def git(*args): return subprocess.check_output(['git',*args],cwd=clone_root)
    if git('rev-parse','HEAD').decode().strip()!=commit: raise Stop('checkout commit mismatch')
    origin=git('remote','get-url','origin').decode().strip()
    if origin not in ORIGINS: raise Stop('unexpected origin')
    for name,h in dict(f['files'],**{'freeze.json':digest}).items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=h: raise Stop('committed blob mismatch: '+name)
    if not any(line.split()==[commit,ref] for line in git('ls-remote','origin',ref).decode().splitlines()): raise Stop('remote ref mismatch')
    with lock(root/'collection/collector.lock'):
        if verify(root)!=digest: raise Stop('freeze changed during attestation')
        if list((root/'collection/episodes').rglob('start.json')) or Journal(root/'collection/dispatch.jsonl').events:
            raise Stop('attestation must precede all v0.2 starts')
        if (root/'collection/push.json').exists() or (root/'collection/push-event.raw.json').exists(): raise Stop('attestation is create-once')
        p=root/'collection/push-event.raw.json'
        with p.open('xb') as stream:
            stream.write(raw);stream.flush();__import__('os').fsync(stream.fileno())
        syncdir(p.parent)
        save(root/'collection/push.json',{'freeze_sha256':digest,'commit':commit,'repo':REPO,'repo_path':repo_path,
            'origin':origin,'source_api':'/repos/'+REPO+'/activity','server_event_id':event['id'],
            'pushed_at':when,'attested_at':now(),'event_sha256':sha(raw),'remote_ref':ref,
            'ledger_prefixes':{n:prefix(root/n) for n in LEDGERS}})
    return digest


def push_gate(root):
    root=Path(root);digest=verify(root);f=read(root/'freeze.json');a=read(root/'collection/push.json')
    raw=(root/'collection/push-event.raw.json').read_bytes();event=strict_load(raw.decode());ref,when=push_record(event,a['commit'])
    if (a['freeze_sha256']!=digest or a['event_sha256']!=sha(raw) or a['repo']!=REPO or
        a['source_api']!='/repos/'+REPO+'/activity' or a['server_event_id']!=event['id'] or a['origin'] not in ORIGINS or
        a['remote_ref']!=ref or a['pushed_at']!=when or
        not timestamp(f['created_at'])<=timestamp(when)<=timestamp(a['attested_at'])<dt.datetime.now(dt.timezone.utc)):
        raise Stop('push attestation mismatch')
    for n in LEDGERS: verify_prefix(root/n,a['ledger_prefixes'][n])
    for p in (root/'collection/episodes').rglob('start.json'):
        s=read(p)
        if s['freeze_sha256']!=digest or timestamp(s['started_at'])<=timestamp(a['attested_at']): raise Stop('start predates attestation/wrong freeze')
    for e in Journal(root/'collection/dispatch.jsonl').events:
        if timestamp(e['time'])<=timestamp(a['attested_at']) or (e['event']=='start' and e['freeze_sha256']!=digest): raise Stop('journal start predates attestation/wrong freeze')
    return digest


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','select-event','attest'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--events',type=Path);p.add_argument('--commit');p.add_argument('--out',type=Path)
    p.add_argument('--event',type=Path);p.add_argument('--repo-path',default='three-rules-one-lunch/v0.2');p.add_argument('--clone-root',type=Path)
    a=p.parse_args()
    if a.command=='freeze': print(freeze(a.root))
    elif a.command=='verify': print(verify(a.root))
    elif a.command=='select-event':
        if not all((a.events,a.commit,a.out)): p.error('--events --commit --out required')
        print(select_event(a.events,a.commit,a.out))
    else:
        if not all((a.event,a.commit,a.clone_root)): p.error('--event --commit --clone-root required')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root))

if __name__=='__main__': main()
