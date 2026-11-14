"""Immutable manifest and GitHub server-event attestation. Never pushes."""
import argparse
import datetime as dt
from pathlib import Path
import re
import subprocess
from trl_core import ROOT, canonical, sha, strict_load
from trl_io import Stop, lock, now, read, save, timestamp

EXCLUDED = {'build','collection','__pycache__','.git','.agents','.codex','.aws'}


def inputs(root):
    result = []
    for p in Path(root).rglob('*'):
        rel = p.relative_to(root)
        if any(part in EXCLUDED or part.startswith('.') for part in rel.parts) or rel.as_posix()=='freeze.json':
            continue
        if p.is_symlink():
            raise Stop('symlink input forbidden: '+str(rel))
        if p.is_file():
            result.append(rel.as_posix())
    return sorted(result)


def freeze(root):
    root = Path(root)
    test = read(root/'evidence/test-report.json')
    if test['status']!='PASS' or test['failures'] or test['errors']:
        raise Stop('passing test evidence required')
    sizing = read(root/'config/sizing.json')
    if sizing['frontier_micro_usd']!=18083840 or sizing['including_protected_reserve_micro_usd']>25000000:
        raise Stop('reservation mismatch')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    if any(files.get(name)!=digest for name,digest in test.get('tested_files',{}).items()):
        raise Stop('tested inputs changed after verification')
    value = {'study':'three-rules-one-lunch','protocol_revision':'v0.1-build-r1','created_at':now(),
        'kind':'pre-inference offline freeze','files':files,'content_sha256':sha(canonical(files).encode()),
        'planned_episodes':960,'planned_calls':8960,'frontier_reservation_micro_usd':sizing['frontier_micro_usd'],
        'protected_reserve_micro_usd':1000000,'calls_made_by_builder':0,'push_status':'UNKNOWN',
        'frontier_readiness':read(root/'evidence/cli-contract.json')['readiness'],
        'dispatch_note':'Both cohorts HOLD before inference pending reviewed transport/budget readiness amendment and new freeze. No runtime override.'}
    save(root/'freeze.json',value)
    return verify(root)


def verify(root):
    root = Path(root)
    f = read(root/'freeze.json')
    files = f['files']
    if not files or set(files)!=set(inputs(root)) or f['content_sha256']!=sha(canonical(files).encode()):
        raise Stop('freeze input set/content manifest changed')
    for name,digest in files.items():
        p = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=digest:
            raise Stop('frozen input changed: '+name)
    if f['frontier_reservation_micro_usd']!=read(root/'config/sizing.json')['frontier_micro_usd']:
        raise Stop('reservation mismatch')
    return sha((root/'freeze.json').read_bytes())


def attest(root,event_file,commit,repo_path):
    root = Path(root)
    digest = verify(root)
    raw_event = Path(event_file).read_bytes()
    event = strict_load(raw_event.decode())
    if not re.fullmatch('[0-9a-f]{40}',commit):
        raise Stop('full Git commit required')
    if event.get('type')!='PushEvent' or event.get('repo',{}).get('name')!='Robin84Bran/research' or event.get('payload',{}).get('head',event.get('payload',{}).get('after'))!=commit:
        raise Stop('server PushEvent does not identify this repository/commit')
    if not timestamp(read(root/'freeze.json')['created_at'])<=timestamp(event['created_at'])<dt.datetime.now(dt.timezone.utc):
        raise Stop('invalid server timestamp')
    if Path(repo_path).is_absolute() or '..' in Path(repo_path).parts or not repo_path:
        raise Stop('invalid repository path')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=root)
    if git('rev-parse','HEAD').decode().strip()!=commit:
        raise Stop('checkout differs from pushed commit')
    for name,expected in dict(read(root/'freeze.json')['files'],**{'freeze.json':digest}).items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=expected:
            raise Stop('pushed commit omits or changes frozen file: '+name)
    ref = event['payload']['ref']
    if not re.fullmatch(r'refs/heads/(codex|claude)/[A-Za-z0-9._/-]+',ref):
        raise Stop('research task branch required')
    remote = git('remote','get-url','origin').decode().strip()
    if remote not in ('git@github.com:Robin84Bran/research.git','https://github.com/Robin84Bran/research.git'):
        raise Stop('unexpected origin')
    remotes = git('ls-remote','origin',ref).decode()
    if not any(line.split()==[commit,ref] for line in remotes.splitlines()):
        raise Stop('remote ref does not match server event')
    with lock(root/'collection/collector.lock'):
        if list((root/'collection/episodes').glob('*/*.start.json')):
            raise Stop('push attestation cannot be recorded after starts')
        path = root/'collection/push-event.raw.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:
            f.write(raw_event);f.flush();__import__('os').fsync(f.fileno())
        save(root/'collection/push.json',{'freeze_sha256':digest,'commit':commit,'repo':'Robin84Bran/research',
            'pushed_at':event['created_at'],'server_event_id':event['id'],'event_sha256':sha(raw_event),
            'repo_path':repo_path,'remote_ref':ref,'origin':remote})
    return digest


def select_event(events_file,commit,out):
    events = read(events_file)
    if type(events) is not list:
        raise Stop('expected saved GitHub events array/pages')
    if events and type(events[0]) is list:
        events = [e for page in events for e in page]
    matches = [e for e in events if e.get('type')=='PushEvent' and e.get('repo',{}).get('name')=='Robin84Bran/research' and e.get('payload',{}).get('head',e.get('payload',{}).get('after'))==commit]
    if not matches:
        raise Stop('no server event for exact pushed commit; retain response and wait for real evidence')
    save(out,max(matches,key=lambda e:e['created_at']))
    return str(out)


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','attest','select-event'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--event',type=Path);p.add_argument('--events',type=Path);p.add_argument('--out',type=Path);p.add_argument('--commit');p.add_argument('--repo-path',default='three-rules-one-lunch')
    a = p.parse_args()
    if a.command=='select-event':
        if not a.events or not a.commit or not a.out:
            p.error('select-event requires --events, --commit, --out')
        print(select_event(a.events,a.commit,a.out))
    elif a.command=='attest':
        if not a.event or not a.commit:
            p.error('attest requires --event and --commit')
        print(attest(a.root,a.event,a.commit,a.repo_path))
    else:
        print({'freeze':freeze,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
