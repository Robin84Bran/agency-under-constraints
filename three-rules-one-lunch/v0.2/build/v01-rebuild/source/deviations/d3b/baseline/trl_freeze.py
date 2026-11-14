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
        if any(part in EXCLUDED or part.startswith('.') for part in rel.parts) or rel.as_posix() in ('freeze.json','freeze-d1.json','freeze-d2.json','freeze-d3.json'):
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
    p = Path(root)/'freeze-d3.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d3.json'
    p = Path(root)/'freeze-d2.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d2.json'
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
    if f.get('deviation') in ('D1','D2','D3'):
        expected.add('freeze.json')
    if f.get('deviation') in ('D2','D3'):
        expected.add('freeze-d1.json')
    if f.get('deviation')=='D3':
        expected.add('freeze-d2.json')
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
    if name=='freeze-d2.json':
        d2_scope(root,f)
    if name=='freeze-d3.json':
        d3_scope(root,f)
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


D1_FREEZE_SHA256 = 'f1985141e400d843ecd24f95f30445f85d67b45bd7e9e4a5b1b29f150ee6bb2b'
D2_CHANGED = {'DEVIATIONS.md','trl_freeze.py','trl_collect.py','trl_validation.py','trl_io.py',
              'tests/test_transport.py','tests/test_d1.py'}
D2_ADDED = {'trl_d2.py','tests/test_d2.py','RUN-d2.md','PROJECT_STATE-d2.md',
            'deviations/d2/clearance.json','evidence/test-report-d2.json','evidence/rebuild-d2.json'} | {
                'deviations/d2/baseline/'+n for n in D2_CHANGED}


def d2_scope(root,f):
    root = Path(root)
    p = root/'freeze-d1.json'
    if p.is_symlink() or sha(p.read_bytes())!=D1_FREEZE_SHA256:
        raise Stop('D2 D1 freeze identity mismatch')
    parent = read(p)
    d1_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D2_CHANGED or
        added!=D2_ADDED|{'freeze-d1.json'} or files.get('freeze-d1.json')!=D1_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D1_FREEZE_SHA256 or f.get('deviation')!='D2' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D2 parent binding or permitted scope mismatch')
    for n in D2_CHANGED:
        if files.get('deviations/d2/baseline/'+n)!=parent['files'][n]:
            raise Stop('D2 baseline differs from D1: '+n)
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D2 changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D2 predates D1')


def freeze_d2(root):
    from trl_test import tested_inputs
    from trl_d2 import stop_gate
    root = Path(root)
    if (root/'freeze-d2.json').exists():
        raise FileExistsError('freeze-d2.json is create-once')
    stop_gate(root)
    test = read(root/'evidence/test-report-d2.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D2 tests for current inputs required')
    parent = read(root/'freeze-d1.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':D1_FREEZE_SHA256})
    f = {**parent,'created_at':now(),'kind':'pre-analysis harness amendment',
         'deviation':'D2','parent_freeze_sha256':D1_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D2 clears only the bound local output-length STOP. Historical D1 starts remain bound to their original push; future starts require a fresh D2 push attestation.'}
    d2_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d2.json',f)
    return verify(root)


D2_FREEZE_SHA256 = 'c0869906324152f8d9fcc4cf48413b2da9f33aab360a42236142cd2e83e4f5a3'
D3_CHANGED = {'DEVIATIONS.md','trl_d2.py','trl_collect.py','trl_validation.py','trl_freeze.py',
              'trl_io.py','tests/test_d2.py'}
D3_ADDED = {'trl_d3.py','tests/test_d3.py','RUN-d3.md','PROJECT_STATE-d3.md',
            'deviations/d3/clearance.json','deviations/d3/scan.json',
            'evidence/test-report-d3.json','evidence/rebuild-d3.json'} | {
                'deviations/d3/baseline/'+n for n in D3_CHANGED}


def d3_scope(root,f):
    root = Path(root)
    p = root/'freeze-d2.json'
    if p.is_symlink() or sha(p.read_bytes())!=D2_FREEZE_SHA256:
        raise Stop('D3 D2 freeze identity mismatch')
    parent = read(p)
    d2_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D3_CHANGED or
        added!=D3_ADDED|{'freeze-d2.json'} or files.get('freeze-d2.json')!=D2_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D2_FREEZE_SHA256 or f.get('deviation')!='D3' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D3 parent binding or permitted scope mismatch')
    for n in D3_CHANGED:
        if files.get('deviations/d3/baseline/'+n)!=parent['files'][n]:
            raise Stop('D3 baseline differs from D2: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D3 must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D3 changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D3 predates D2')


def freeze_d3(root):
    from trl_test import tested_inputs
    from trl_d3 import stop_gate
    root = Path(root)
    if (root/'freeze-d3.json').exists():
        raise FileExistsError('freeze-d3.json is create-once')
    stop_gate(root)
    test = read(root/'evidence/test-report-d3.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D3 tests for current inputs required')
    parent = read(root/'freeze-d2.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':D1_FREEZE_SHA256,
                  'freeze-d2.json':D2_FREEZE_SHA256})
    f = {**parent,'created_at':now(),'kind':'pre-analysis harness amendment',
         'deviation':'D3','parent_freeze_sha256':D2_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D3 preserves ledger prefixes and clears only the bound local incomplete-envelope STOP. All historical starts retain their D1/D2 pushes; new starts need a fresh D3 push.'}
    d3_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d3.json',f)
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
        d3 = active_freeze(root)=='freeze-d3.json'
        d2 = active_freeze(root)=='freeze-d2.json'
        if d3:
            from trl_d3 import stop_gate
            from trl_collect import push_gate
            c = stop_gate(root)
            push_gate(root,historical=True)
            if any(p.relative_to(root).as_posix() not in c['preserved_files'] for p in (root/'collection/episodes').glob('*/*.start.json')):
                raise Stop('D3 attestation must precede all D3 starts')
        elif d2:
            from trl_d2 import stop_gate
            from trl_collect import push_gate
            c = stop_gate(root)
            push_gate(root,historical=True)
            if any(p.relative_to(root).as_posix() not in c['preserved_files'] for p in (root/'collection/episodes').glob('*/*.start.json')):
                raise Stop('D2 attestation must precede all D2 starts')
        elif list((root/'collection/episodes').glob('*/*.start.json')):
            raise Stop('push attestation cannot be recorded after starts')
        suffix = '-d3' if d3 else ('-d2' if d2 else '')
        path = root/('collection/push-event'+suffix+'.raw.json')
        receipt = root/('collection/push'+suffix+'.json')
        if path.exists() or receipt.exists():
            raise FileExistsError('push evidence is create-once')
        with path.open('xb') as f:
            f.write(raw_event);f.flush();__import__('os').fsync(f.fileno())
        __import__('trl_io').syncdir(path.parent)
        save(receipt,{'freeze_sha256':digest,'freeze_file':active_freeze(root),
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
    p = argparse.ArgumentParser();p.add_argument('command',choices=['freeze','freeze-d1','freeze-d2','clear-d2','freeze-d3','clear-d3','verify','attest','select-event'])
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
    elif a.command in ('clear-d2','clear-d3'):
        if a.command=='clear-d3':
            from trl_d3 import record_clearance
        else:
            from trl_d2 import record_clearance
        with lock(a.root/'collection/collector.lock'):
            c = record_clearance(a.root)
        print(c['disposition'])
    else:
        print({'freeze':freeze,'freeze-d1':freeze_d1,'freeze-d2':freeze_d2,'freeze-d3':freeze_d3,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
