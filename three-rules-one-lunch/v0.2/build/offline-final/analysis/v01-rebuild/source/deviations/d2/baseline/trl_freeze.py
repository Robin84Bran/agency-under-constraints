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
        if any(part in EXCLUDED or part.startswith('.') for part in rel.parts) or rel.as_posix() in ('freeze.json','freeze-d1.json'):
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


ORIGINAL_FREEZE_SHA256 = '85d2dcc527e3c9fb37868109106939a1fe8eb4e24dbc4d03f3cbc8280253e6aa'
D1_CHANGED = {'trl_freeze.py','trl_collect.py','trl_transport.py','trl_validation.py',
              'tests/test_harness_analysis.py'}
D1_ADDED = {'DEVIATIONS.md','ERRATA.md','RUN-d1.md','PROJECT_STATE-d1.md',
            'tests/test_d1.py','evidence/test-report-d1.json','evidence/rebuild-d1.json'} | {
                'deviations/d1/baseline/'+name for name in D1_CHANGED}


def active_freeze(root):
    p = Path(root)/'freeze-d1.json'
    return 'freeze-d1.json' if p.exists() or p.is_symlink() else 'freeze.json'


def d1_scope(root, f):
    p = Path(root)/'freeze.json'
    if p.is_symlink() or sha(p.read_bytes())!=ORIGINAL_FREEZE_SHA256:
        raise Stop('D1 original freeze identity mismatch')
    parent = read(p)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D1_CHANGED or
            added!=D1_ADDED|{'freeze.json'} or files.get('freeze.json')!=ORIGINAL_FREEZE_SHA256 or
            f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or f.get('deviation')!='D1'):
        raise Stop('D1 parent binding or permitted scope mismatch')
    for name in D1_CHANGED:
        if files.get('deviations/d1/baseline/'+name)!=parent['files'][name]:
            raise Stop('D1 baseline differs from original: '+name)
    mutable = {'files','content_sha256','created_at','kind','frontier_readiness','dispatch_note'}
    for key in set(parent)-mutable:
        if f.get(key)!=parent[key]:
            raise Stop('D1 changed scientific freeze metadata: '+key)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D1 predates original freeze')


def verify_manifest(root, f):
    files = f['files']
    expected = set(inputs(root))
    if f.get('deviation')=='D1':
        expected.add('freeze.json')
    if not files or set(files)!=expected or f['content_sha256']!=sha(canonical(files).encode()):
        raise Stop('freeze input set/content manifest changed')
    for name,digest in files.items():
        p = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=digest:
            raise Stop('frozen input changed: '+name)
    if f['frontier_reservation_micro_usd']!=read(root/'config/sizing.json')['frontier_micro_usd']:
        raise Stop('reservation mismatch')


def verify(root):
    root = Path(root)
    name = active_freeze(root)
    if (root/name).is_symlink():
        raise Stop('symlink freeze')
    f = read(root/name)
    if name=='freeze-d1.json':
        d1_scope(root,f)
    verify_manifest(root,f)
    return sha((root/name).read_bytes())


def freeze_d1(root):
    root = Path(root)
    if (root/'freeze-d1.json').exists():
        raise FileExistsError('freeze-d1.json is create-once')
    if any((root/'collection/episodes').glob('*/*.start.json')):
        raise Stop('D1 must precede inference')
    from trl_test import tested_inputs
    test = read(root/'evidence/test-report-d1.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
            not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D1 tests for current inputs required')
    parent = read(root/'freeze.json')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    files['freeze.json'] = ORIGINAL_FREEZE_SHA256
    f = {**parent,'created_at':now(),'kind':'pre-inference operational amendment',
         'deviation':'D1','original_freeze_sha256':ORIGINAL_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'frontier_readiness':'UNKNOWN',
         'dispatch_note':'D1 replaces advance transport certainty with empirical accounting and first scheduled Claude envelope verification; fresh push attestation still required.'}
    d1_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d1.json',f)
    return verify(root)


def push_record(event, commit):
    """Same two GitHub server evidence forms accepted by Receipt Gap D1."""
    if type(event) is not dict or type(commit) is not str or not re.fullmatch('[0-9a-f]{40}',commit):
        raise Stop('invalid server record or full commit')
    if event.get('type')=='PushEvent':
        payload, repo = event.get('payload'),event.get('repo')
        if (type(payload) is not dict or type(repo) is not dict or
                repo.get('name')!='Robin84Bran/research' or payload.get('head',payload.get('after'))!=commit):
            raise Stop('server PushEvent repository/commit mismatch')
        ref, when = payload.get('ref'),event.get('created_at')
    elif event.get('activity_type')=='push':
        if event.get('after')!=commit:
            raise Stop('server activity commit mismatch')
        ref, when = event.get('ref'),event.get('timestamp')
    else:
        raise Stop('server PushEvent or push activity required')
    if type(ref) is not str or not re.fullmatch(r'refs/heads/[A-Za-z0-9_][A-Za-z0-9._/-]*',ref):
        raise Stop('server branch ref required')
    try:
        pushed = timestamp(when)
    except (ValueError,TypeError,AttributeError):
        raise Stop('invalid server timestamp') from None
    if pushed>=dt.datetime.now(dt.timezone.utc) or type(event.get('id')) not in (str,int) or not str(event['id']):
        raise Stop('invalid server timestamp or id')
    return ref,when


def attest(root,event_file,commit,repo_path,clone_root=None):
    root = Path(root)
    digest = verify(root)
    raw_event = Path(event_file).read_bytes()
    event = strict_load(raw_event.decode())
    ref,when = push_record(event,commit)
    if not timestamp(read(root/active_freeze(root))['created_at'])<=timestamp(when):
        raise Stop('push must follow active freeze')
    if Path(repo_path).is_absolute() or '..' in Path(repo_path).parts or not repo_path or ':' in repo_path:
        raise Stop('invalid repository path')
    clone_root = Path(clone_root) if clone_root is not None else root
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=clone_root)
    if git('rev-parse','HEAD').decode().strip()!=commit:
        raise Stop('checkout differs from pushed commit')
    remote = git('remote','get-url','origin').decode().strip()
    if remote not in ('git@github.com:Robin84Bran/research.git','https://github.com/Robin84Bran/research.git',
                      'https://github.com/Robin84Bran/research','ssh://git@github.com/Robin84Bran/research.git'):
        raise Stop('unexpected origin')
    # Bind both freeze blobs and every active input in the committed package.
    committed = dict(read(root/active_freeze(root))['files'])
    committed['freeze.json'] = sha((root/'freeze.json').read_bytes())
    committed[active_freeze(root)] = digest
    for name,expected in committed.items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=expected:
            raise Stop('pushed commit omits or changes frozen file: '+name)
    remotes = git('ls-remote','origin',ref).decode()
    if not any(line.split()==[commit,ref] for line in remotes.splitlines()):
        raise Stop('remote ref does not match server event')
    with lock(root/'collection/collector.lock'):
        if list((root/'collection/episodes').glob('*/*.start.json')):
            raise Stop('push attestation cannot be recorded after starts')
        path = root/'collection/push-event.raw.json'
        if path.exists() or (root/'collection/push.json').exists():
            raise FileExistsError('push evidence is create-once')
        with path.open('xb') as f:
            f.write(raw_event);f.flush();__import__('os').fsync(f.fileno())
        __import__('trl_io').syncdir(path.parent)
        save(root/'collection/push.json',{'freeze_sha256':digest,'freeze_file':active_freeze(root),
            'original_freeze_sha256':sha((root/'freeze.json').read_bytes()),'commit':commit,'repo':'Robin84Bran/research',
            'pushed_at':when,'server_event_id':event['id'],'event_sha256':sha(raw_event),
            'source_api':'/repos/Robin84Bran/research/'+('events' if event.get('type')=='PushEvent' else 'activity'),
            'repo_path':repo_path,'remote_ref':ref,'origin':remote})
    return digest


def select_event(events_file,commit,out):
    events = read(events_file)
    if type(events) is not list:
        raise Stop('expected saved GitHub events array/pages')
    if events and type(events[0]) is list:
        events = [e for page in events for e in page]
    matches = []
    for e in events:
        try:
            push_record(e,commit)
        except Stop:
            continue
        matches.append(e)
    if not matches:
        raise Stop('no server event for exact pushed commit; retain response and wait for real evidence')
    save(out,max(matches,key=lambda e:timestamp(push_record(e,commit)[1])))
    return str(out)


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=['freeze','freeze-d1','verify','attest','select-event'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--event',type=Path);p.add_argument('--events',type=Path);p.add_argument('--out',type=Path);p.add_argument('--commit');p.add_argument('--repo-path',default='three-rules-one-lunch')
    p.add_argument('--clone-root',type=Path,help='separate research clone; Git checks only, no writes')
    a = p.parse_args()
    if a.command=='select-event':
        if not a.events or not a.commit or not a.out:
            p.error('select-event requires --events, --commit, --out')
        print(select_event(a.events,a.commit,a.out))
    elif a.command=='attest':
        if not a.event or not a.commit or not a.clone_root:
            p.error('attest requires --event, --commit and --clone-root')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root))
    else:
        print({'freeze':freeze,'freeze-d1':freeze_d1,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
