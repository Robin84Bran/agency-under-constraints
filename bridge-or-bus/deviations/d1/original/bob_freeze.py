"""Portable immutable manifest and real-push attestation gates."""
import datetime as dt
from pathlib import Path, PurePosixPath
import re
import subprocess

from bob_core import canonical,sha,strict_load,schedule,sizing
from bob_collect import Stop,now,read,save


def inventory(root):
    root=Path(root)
    files={}
    for p in sorted(root.rglob('*')):
        relative=p.relative_to(root)
        if any(s in ('.git','.agents','.codex','__pycache__','.pytest_cache') for s in relative.parts) or relative.parts[0] in ('build','collection','_releases') or str(relative)=='freeze.json':
            continue
        if p.is_symlink():
            raise Stop('symlink in frozen source: '+str(relative))
        if p.is_file():
            files[relative.as_posix()]=sha(p.read_bytes())
    return files


def verify(root):
    root=Path(root)
    record=read(root/'freeze.json')
    files=record['files']
    if not files or record.get('format')!=1 or sha(canonical(files).encode())!=record.get('content_sha256'):
        raise Stop('invalid freeze manifest')
    for name in files:
        rel=PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise Stop('unsafe freeze path')
    if files!=inventory(root):
        raise Stop('source/fixture/freeze drift; no collection')
    if read(root/'config/order.json')!=schedule() or read(root/'config/sizing.json')!=sizing():
        raise Stop('frozen design/sizing mismatch')
    return record


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
    push=check_push(root,freeze,read(root/'collection/push.json'))
    git_proof(root,push['commit'])
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
