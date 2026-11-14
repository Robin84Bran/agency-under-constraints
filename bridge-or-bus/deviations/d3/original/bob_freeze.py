"""Portable immutable manifest and real-push attestation gates."""
import datetime as dt
from pathlib import Path, PurePosixPath
import re
import subprocess

from bob_core import canonical,sha,strict_load,schedule,sizing
from bob_collect import Stop,now,read,save

ORIGINAL_FREEZE_SHA256='3353d538c1e27f5759e08ff11179ed20c65c4822c4366859ebb16de6cf9d458b'
REPOSITORY='Robin84Bran/research'
D1_CHANGED={'bob.py','bob_freeze.py','bob_collect.py','tests/test_freeze.py','tests/test_collect.py'}
D1_ADDED={'DEVIATIONS.md','ERRATA.md','RUN-d1.md','PROJECT_STATE-d1.md',
          'tests/test_d1.py','evidence/d1-cost-basis.json'}
TRANSPORT_POLICY='empirical-reservations-first-call-envelope'


def active_freeze(root):
    p=Path(root)/'freeze-d2.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d2.json'
    p=Path(root)/'freeze-d1.json'
    return 'freeze-d1.json' if p.exists() or p.is_symlink() else 'freeze.json'


def d1_parent(root):
    p=Path(root)/'freeze.json'
    if p.is_symlink() or sha(p.read_bytes())!=ORIGINAL_FREEZE_SHA256:
        raise Stop('D1 original freeze binding mismatch')
    return read(p)


def d1_scope(root,files):
    parent=d1_parent(root)
    archives={'deviations/d1/original/'+n for n in D1_CHANGED}
    if set(files)!=set(parent['files'])|D1_ADDED|archives:
        raise Stop('D1 inventory outside declared amendment')
    for name,expected in parent['files'].items():
        if name not in D1_CHANGED and files.get(name)!=expected:
            raise Stop('D1 changed scientific/frozen input: '+name)
        if name in D1_CHANGED and files.get('deviations/d1/original/'+name)!=expected:
            raise Stop('D1 original code archive mismatch: '+name)
    # Restrict collector changes to transport release, fatal envelope handling and
    # additional amendment provenance. Accounting, tools and requests stay frozen.
    import ast
    def unaffected(raw):
        tree=ast.parse(raw)
        tree.body=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) or
                   n.name not in ('frontier_gate','run_episode')]
        return ast.dump(tree,include_attributes=False)
    old=Path(root)/'deviations/d1/original/bob_collect.py'
    if unaffected(old.read_bytes())!=unaffected((Path(root)/'bob_collect.py').read_bytes()):
        raise Stop('D1 changed unrelated collector mechanism')
    return parent


def inventory(root):
    root=Path(root)
    files={}
    for p in sorted(root.rglob('*')):
        relative=p.relative_to(root)
        if any(s in ('.git','.agents','.codex','__pycache__','.pytest_cache') for s in relative.parts) or relative.parts[0] in ('build','collection','_releases') or str(relative) in ('freeze.json','freeze-d1.json','freeze-d2.json'):
            continue
        if p.is_symlink():
            raise Stop('symlink in frozen source: '+str(relative))
        if p.is_file():
            files[relative.as_posix()]=sha(p.read_bytes())
    return files


def verify(root):
    root=Path(root)
    name=active_freeze(root)
    if (root/name).is_symlink():
        raise Stop('symlink freeze')
    record=read(root/name)
    files=record['files']
    if not files or record.get('format')!=1 or sha(canonical(files).encode())!=record.get('content_sha256'):
        raise Stop('invalid freeze manifest')
    for filename in files:
        rel=PurePosixPath(filename)
        if rel.is_absolute() or '..' in rel.parts:
            raise Stop('unsafe freeze path')
    if files!=inventory(root):
        raise Stop('source/fixture/freeze drift; no collection')
    if name=='freeze-d2.json':
        from bob_d2 import verify_d2
        verify_d2(root,record)
    if name=='freeze-d1.json':
        parent=d1_scope(root,files)
        if record.get('deviation')!='D1' or record.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or record.get('transport_policy')!=TRANSPORT_POLICY:
            raise Stop('invalid D1 binding/policy')
        for key in ('format','local_episodes','frontier_episodes','maximum_generations','new_model_calls','new_usd',
                    'frontier_reservation_micro_usd','protected_reserve_micro_usd'):
            if record.get(key)!=parent[key]:
                raise Stop('D1 changed scientific/budget metadata: '+key)
    if read(root/'config/order.json')!=schedule() or read(root/'config/sizing.json')!=sizing():
        raise Stop('frozen design/sizing mismatch')
    return record


def freeze_d1(root):
    root=Path(root)
    if (root/'freeze-d1.json').exists() or (root/'freeze-d1.json').is_symlink():
        raise Stop('D1 freeze exists; never overwrite')
    if any((root/'collection').rglob('*.json')) or (root/'collection/cost.jsonl').exists():
        raise Stop('D1 requires pre-inference state; inspect existing collection')
    files=inventory(root)
    parent=d1_scope(root,files)
    report=read(root/'build/test-report.json')
    if report.get('status')!='PASS' or report.get('tests',0)<1 or report.get('source_sha256')!=sha(canonical(files).encode()):
        raise Stop('passing tests must bind exact D1 source')
    record=dict(parent,files=files,content_sha256=sha(canonical(files).encode()),frozen_utc=now(),
                deviation='D1',original_freeze_sha256=ORIGINAL_FREEZE_SHA256,
                transport_policy=TRANSPORT_POLICY,tests=report['tests'],
                test_counts=dict(python=report['python_tests'],toy=report['toy_tests']),
                unresolved=['real D1 push attestation','local runtime identity/context/capacity',
                            'first frozen Claude call must verify structured_output; unknown usage stops',
                            'current rates and hard token bounds remain UNKNOWN; empirical admission/actual settlement'])
    save(root/'freeze-d1.json',record)
    verify(root)
    return dict(freeze_file='freeze-d1.json',freeze_sha256=sha((root/'freeze-d1.json').read_bytes()),
                original_freeze_sha256=ORIGINAL_FREEZE_SHA256,tests=report['tests'])


def create(root):
    root=Path(root)
    if (root/'freeze.json').exists():
        raise Stop('freeze exists; never overwrite')
    report=read(root/'build/test-report.json')
    if report.get('status')!='PASS' or report.get('tests',0)<1 or report.get('source_sha256')!=sha(canonical(inventory(root)).encode()):
        raise Stop('passing tests must bind the exact current source inventory')
    files=inventory(root)
    record=dict(format=1,frozen_utc=now(),files=files,content_sha256=sha(canonical(files).encode()),
                status='FROZEN_OFFLINE_NO_INFERENCE',push_status='UNKNOWN',runtime_status='UNKNOWN',
                frontier_dispatch_status='UNKNOWN',new_model_calls=0,new_usd=0,
                local_episodes=1200,frontier_episodes=80,maximum_generations=8960,
                tests=report['tests'],test_counts=dict(python=report.get('python_tests',report['tests']),toy=report.get('toy_tests',0)),frontier_reservation_micro_usd=sizing()['frontier_micro_usd'],
                protected_reserve_micro_usd=2000000,
                unresolved=['Claude complete structured-output path with real tools disabled','one generation and no internal retries','enforced total charged output <=512','current rates/accounting','local runtime identity/context','real push attestation'])
    save(root/'freeze.json',record)
    verify(root)
    return dict(freeze_sha256=sha((root/'freeze.json').read_bytes()),**{k:record[k] for k in ('status','tests','frontier_reservation_micro_usd')})


def parsed_time(value):
    x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if x.tzinfo is None:
        raise Stop('timezone required')
    return x


def check_push(root,freeze,push):
    root=Path(root)
    if freeze.get('deviation')=='D2':
        from bob_d2 import check_d2_push
        return check_d2_push(root,freeze,push)
    if freeze.get('deviation')=='D1':
        return check_d1_push(root,freeze,push)
    if push.get('freeze_sha256')!=sha((root/'freeze.json').read_bytes()):
        raise Stop('push does not bind freeze')
    if re.fullmatch('[0-9a-f]{40}',push.get('commit','')) is None:
        raise Stop('full pushed commit required')
    if not push.get('remote') or not push.get('server_timestamp_source') or not push.get('evidence_file'):
        raise Stop('real remote/server evidence required')
    path=PurePosixPath(push['evidence_file'])
    if path.is_absolute() or '..' in path.parts or not str(path).startswith('collection/push-evidence/'):
        raise Stop('push evidence must be project-local collection/push-evidence')
    evidence=(root/str(path))
    if evidence.is_symlink() or not evidence.is_file() or sha(evidence.read_bytes())!=push.get('evidence_sha256'):
        raise Stop('push evidence missing/changed')
    supplied=github_evidence(root,push['remote'],push['evidence_file'])
    if any(push.get(key)!=supplied[value] for key,value in (('github_time','github_time'),('commit','commit'),('server_timestamp_source','source'))):
        raise Stop('push attestation differs from actual saved server response')
    frozen,pushed=parsed_time(freeze['frozen_utc']),parsed_time(push['github_time'])
    if not frozen<=pushed<=dt.datetime.now(dt.timezone.utc):
        raise Stop('push time must follow freeze and precede now')
    for start in (root/'collection/starts').glob('*.json'):
        if parsed_time(read(start)['started'])<pushed:
            raise Stop('push must precede every call')
    return push


def git_proof(root,commit):
    """Read-only Git verifies the attested commit contains the exact frozen bytes."""
    root=Path(root).resolve()
    def git(*args):
        p=subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True)
        return p.stdout
    top=Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()
    # Prohibit collection from canonical RobinOS2 tree; separate project clone only.
    if top.name=='RobinOS2' or root!=top:
        raise Stop('use a separate project-root research clone for attestation/collection')
    if git('rev-parse','HEAD').decode().strip()!=commit:
        raise Stop('attested commit must be checkout HEAD')
    frozen=read(root/'freeze.json')
    for name,expected in dict(frozen['files'],**{'freeze.json':sha((root/'freeze.json').read_bytes())}).items():
        if sha(git('show',commit+':'+name))!=expected:
            raise Stop('attested commit missing/different frozen source: '+name)


def record_push(root,github_time,commit,remote,source,evidence):
    root=Path(root)
    freeze=verify(root)
    if freeze.get('deviation') in ('D1','D2'):
        raise Stop('D1/D2 requires attest with a GitHub push server record')
    git_proof(root,commit)
    rel=Path(evidence)
    if rel.is_absolute():
        rel=rel.relative_to(root.resolve())
    ev=root/rel
    push=dict(github_time=github_time,commit=commit,remote=remote,
              server_timestamp_source=source,evidence_file=rel.as_posix(),evidence_sha256=sha(ev.read_bytes()),
              freeze_sha256=sha((root/'freeze.json').read_bytes()),recorded_utc=now())
    check_push(root,freeze,push)
    save(root/'collection/push.json',push)
    return push


def push_gate(root,freeze):
    root=Path(root)
    push=check_push(root,freeze,read(root/('collection/push-d2.json' if freeze.get('deviation')=='D2' else 'collection/push.json')))
    if freeze.get('deviation') not in ('D1','D2'):
        git_proof(root,push['commit'])
    return push


def push_record(event,commit):
    """Exact GitHub /events or /activity record, as in Receipt Gap D1."""
    if type(event) is not dict or type(commit) is not str or re.fullmatch('[0-9a-f]{40}',commit) is None:
        raise Stop('invalid server record/commit')
    if event.get('type')=='PushEvent':
        payload,repo=event.get('payload'),event.get('repo')
        if type(payload) is not dict or type(repo) is not dict or repo.get('name')!=REPOSITORY or payload.get('head',payload.get('after'))!=commit:
            raise Stop('server PushEvent repository/commit mismatch')
        ref,timestamp=payload.get('ref'),event.get('created_at')
        api='/events'
    elif event.get('activity_type')=='push':
        if event.get('after')!=commit:
            raise Stop('server activity commit mismatch')
        ref,timestamp=event.get('ref'),event.get('timestamp')
        api='/activity'
    else:
        raise Stop('expected server PushEvent or push activity')
    if type(ref) is not str or not ref.startswith('refs/heads/') or not ref[len('refs/heads/'):] or not event.get('id'):
        raise Stop('invalid server ref/id')
    try:
        pushed=parsed_time(timestamp)
    except (AttributeError,TypeError,ValueError):
        raise Stop('invalid server timestamp') from None
    if pushed>=dt.datetime.now(dt.timezone.utc):
        raise Stop('future server timestamp')
    return dict(remote_ref=ref,github_time=timestamp,server_event_id=event['id'],source_api='/repos/'+REPOSITORY+api)


def check_d1_push(root,freeze,push,starts_deviation=None):
    if push.get('freeze_sha256')!=sha((root/'freeze-d1.json').read_bytes()) or push.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or push.get('freeze_file')!='freeze-d1.json':
        raise Stop('push does not bind D1 and original freeze')
    if push.get('repo')!=REPOSITORY or push.get('evidence_file')!='collection/push-event.json':
        raise Stop('push repository/evidence mismatch')
    evidence=root/'collection/push-event.json'
    if evidence.is_symlink() or sha(evidence.read_bytes())!=push.get('evidence_sha256'):
        raise Stop('saved server evidence missing/changed')
    supplied=push_record(strict_load(evidence.read_bytes()),push.get('commit'))
    if any(push.get(k)!=v for k,v in supplied.items()):
        raise Stop('receipt differs from raw server evidence')
    pushed=parsed_time(supplied['github_time'])
    if not parsed_time(freeze['frozen_utc'])<=pushed:
        raise Stop('push must follow D1 freeze')
    for directory in ('starts','episode-starts'):
        for start in (root/'collection'/directory).glob('*.json'):
            value=read(start)
            if starts_deviation is not None and value.get('deviation')!=starts_deviation:
                continue
            if parsed_time(value['started'])<pushed or value.get('amendment_freeze_sha256')!=push['freeze_sha256']:
                raise Stop('D1 push must precede and bind every call/episode')
    return push


def attest(root,event_file,commit,clone_root,repo_path):
    """Read-only Git checks in the separate clone; write only to root."""
    from bob_collect import lock,save_bytes
    root,clone_root=Path(root).resolve(),Path(clone_root).resolve()
    freeze=verify(root)
    if freeze.get('deviation') not in ('D1','D2'):
        raise Stop('attest requires D1/D2')
    d2=freeze.get('deviation')=='D2'
    freeze_name=active_freeze(root)
    event_name='collection/push-d2-event.json' if d2 else 'collection/push-event.json'
    receipt_name='collection/push-d2.json' if d2 else 'collection/push.json'
    source=Path(event_file).read_bytes()
    supplied=push_record(strict_load(source),commit)
    rel=PurePosixPath(repo_path)
    if not repo_path or rel.is_absolute() or '..' in rel.parts or ':' in repo_path or '\\' in repo_path or str(rel)=='.':
        raise Stop('invalid repository project path')
    def git(*args):
        return subprocess.run(['git','-C',str(clone_root),*args],capture_output=True,check=True).stdout
    top=Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()
    if clone_root!=top or top.name=='RobinOS2' or root==top or top in root.parents or root in top.parents:
        raise Stop('attestation requires a separate research clone')
    if git('rev-parse','HEAD').decode().strip()!=commit:
        raise Stop('checkout HEAD differs from pushed commit')
    origin=git('remote','get-url','origin').decode().strip()
    if origin not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git',
                      'git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git'):
        raise Stop('origin does not identify research repository')
    manifests={'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':sha((root/'freeze-d1.json').read_bytes())}
    if d2:
        manifests['freeze-d2.json']=sha((root/'freeze-d2.json').read_bytes())
    for name,expected in dict(freeze['files'],**manifests).items():
        if sha(git('show',commit+':'+str(rel)+'/'+name))!=expected:
            raise Stop('pushed commit contains different frozen bytes: '+name)
    refs=git('ls-remote','origin',supplied['remote_ref']).decode().splitlines()
    if not any(line.split()==[commit,supplied['remote_ref']] for line in refs):
        raise Stop('remote ref differs from server record')
    push=dict(supplied,commit=commit,repo=REPOSITORY,repo_path=str(rel),clone_root=str(clone_root),
              freeze_file=freeze_name,freeze_sha256=sha((root/freeze_name).read_bytes()),
              original_freeze_sha256=ORIGINAL_FREEZE_SHA256,evidence_file=event_name,
              evidence_sha256=sha(source),recorded_utc=now())
    if d2:
        push['parent_freeze_sha256']=sha((root/'freeze-d1.json').read_bytes())
    if parsed_time(push['github_time'])<parsed_time(freeze['frozen_utc']):
        raise Stop('push predates '+freeze.get('deviation','')+' freeze')
    with lock(root/'collection/collector.lock'):
        if (root/receipt_name).exists() or (root/event_name).exists():
            raise Stop('push evidence exists; never overwrite')
        if d2:
            from bob_d2 import validate_disposition
            validate_disposition(root,pre_resume=False)
            if any(read(p).get('deviation')!='D1' for directory in ('starts','episode-starts') for p in (root/'collection'/directory).glob('*.json')):
                raise Stop('D2 attestation must precede D2 starts')
        elif any((root/'collection/starts').glob('*.json')) or any((root/'collection/episode-starts').glob('*.json')):
            raise Stop('attest before inference only')
        save_bytes(root/event_name,source)
        check_push(root,freeze,push)
        save(root/receipt_name,push)
    return push


def github_evidence(root,remote,evidence):
    """Parse a saved `gh api --include` response; this function makes no request."""
    from email.utils import parsedate_to_datetime
    root=Path(root)
    p=root/evidence
    raw=p.read_bytes().replace(b'\r\n',b'\n')
    header,sep,body=raw.partition(b'\n\n')
    if not sep or not header.splitlines()[0].startswith((b'HTTP/2.0 200',b'HTTP/2 200',b'HTTP/1.1 200')):
        raise Stop('saved GitHub API response must be HTTP 200 with headers')
    dates=[x.split(b':',1)[1].strip().decode('ascii') for x in header.splitlines()[1:] if x.lower().startswith(b'date:')]
    if len(dates)!=1:
        raise Stop('one genuine GitHub Date header required')
    committed=strict_load(body)
    commit=committed.get('sha')
    match=re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?',remote)
    if match is None:
        raise Stop('explicit GitHub research repository remote required')
    expected='https://api.github.com/repos/'+match[1]+'/commits/'+str(commit)
    if committed.get('url')!=expected:
        raise Stop('server evidence repository/commit does not match remote')
    timestamp=parsedate_to_datetime(dates[0]).isoformat()
    return dict(github_time=timestamp,commit=commit,remote=remote,source=expected,evidence=evidence)
