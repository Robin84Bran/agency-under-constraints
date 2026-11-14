"""Create-once v0.2 freeze and source-bound push evidence. No I/O at import."""
import datetime as dt
from bob_paths import collection_dir,prior_path
from pathlib import Path, PurePosixPath
import re
import subprocess

from bob_core import canonical,sha,strict_load,schedule,sizing
from bob_collect import Stop,read,save,save_bytes,now,lock

REPOSITORY='Robin84Bran/research'
TRANSPORT_POLICY='D3_ACCOUNT_ACTUAL_NO_REPAIR'
FREEZES=('freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json')


def attestation_dir(root):
    root=Path(root)
    return root/'collection-r3' if (root/'freeze-r3.json').exists() else collection_dir(root)

def freeze_path(root, name=None):
    root=Path(root)
    if name is not None and name not in FREEZES:
        raise Stop('unknown freeze name')
    return root/(name or next((n for n in reversed(FREEZES) if (root/n).exists()),'freeze.json'))



def inventory(root):
    files={}
    for p in sorted(Path(root).rglob('*')):
        rel=p.relative_to(root)
        if any(x in ('.git','.agents','.codex','__pycache__','.pytest_cache') for x in rel.parts) or rel.parts[0] in ('build','collection','collection-r2','collection-r3') or rel.as_posix() in FREEZES:continue
        if p.is_symlink():raise Stop('symlink in frozen source')
        if p.is_file():files[rel.as_posix()]=sha(p.read_bytes())
    return files


def verify(root, name=None):
    root=Path(root);path=freeze_path(root,name);record=read(path);files=inventory(root)
    if path.name=='freeze-r3.json':
        parents={n:sha((root/n).read_bytes()) for n in FREEZES[:3]}
        r2=read(root/'freeze-r2.json')
        if (record.get('revision')!='r3' or record.get('parent_freezes')!=parents or
            r2.get('revision')!='r2' or r2.get('parent_freezes')!={n:parents[n] for n in FREEZES[:2]} or
            read(root/'freeze-r1.json').get('parent_freeze_sha256')!=parents['freeze.json']):
            raise Stop('revision parent freeze mismatch')
        if (record.get('collection_directory')!='collection-r2' or record.get('attestation_directory')!='collection-r3' or
            record.get('r2_preservation_sha256')!=sha((root/'evidence/r3/preservation.json').read_bytes())):
            raise Stop('r3 preservation/collection mismatch')
    if path.name=='freeze-r1.json' and (record.get('parent_freeze_sha256')!=sha((root/'freeze.json').read_bytes()) or record.get('revision')!='r1'):
        raise Stop('revision parent freeze mismatch')
    if path.name=='freeze-r2.json':
        parents={n:sha((root/n).read_bytes()) for n in FREEZES[:2]}
        if record.get('revision')!='r2' or record.get('parent_freezes')!=parents or read(root/'freeze-r1.json').get('parent_freeze_sha256')!=parents['freeze.json']:
            raise Stop('revision parent freeze mismatch')
        if record.get('collection_directory')!='collection-r2' or record.get('void_r1_sha256')!=sha((root/'evidence/r2/void-r1.json').read_bytes()):
            raise Stop('r2 disposition/collection mismatch')
        prior=read(prior_path(root))
        for field in ('ledger','local_time'):
            if sha((root/prior[field+'_file']).read_bytes())!=prior[field+'_sha256']:
                raise Stop('r1 accounting evidence changed')
    if record.get('version')!='0.2' or record.get('format')!=1 or record['files']!=files or record['content_sha256']!=sha(canonical(files).encode()):raise Stop('source/fixture/freeze drift')
    if read(root/'config/order.json')!=schedule() or read(root/'config/sizing.json')!=sizing():raise Stop('schedule/sizing mismatch')
    report=read(root/'build/test-report.json')
    if report['status']!='PASS' or report['source_sha256']!=record['content_sha256'] or sha((root/'build/test-report.json').read_bytes())!=record['test_report_sha256']:raise Stop('source-bound passing tests missing')
    return record


def create_revision(root):
    root=Path(root)
    if (root/'freeze-r1.json').exists():raise Stop('revision freeze exists; never overwrite')
    if any(p.is_file() for d in ('starts','episode-starts') for p in (collection_dir(root)/d).glob('*.json')) or (collection_dir(root)/'push.json').exists():
        raise Stop('pre-push revision requires unstarted, unattested collection')
    parent=read(root/'freeze.json');files=inventory(root);digest=sha(canonical(files).encode())
    report=read(root/'build/test-report.json')
    if report['status']!='PASS' or report['source_sha256']!=digest:raise Stop('tests must bind exact source')
    record=dict(parent,revision='r1',parent_freeze_sha256=sha((root/'freeze.json').read_bytes()),
                frozen_utc=now(),files=files,content_sha256=digest,tests=report['tests'],
                test_report_sha256=sha((root/'build/test-report.json').read_bytes()),
                usage_limit_policy='DEFINITE_NONSTART_ZERO_USAGE_429_PAUSE_RESUME')
    save(root/'freeze-r1.json',record);verify(root,'freeze-r1.json')
    return dict(status=record['status'],freeze_sha256=sha((root/'freeze-r1.json').read_bytes()),tests=record['tests'])


def create_r2(root):
    root=Path(root)
    if (root/'freeze-r2.json').exists():raise Stop('revision freeze exists; never overwrite')
    directory=root/'collection-r2'
    if directory.is_symlink() or (directory.exists() and any(directory.iterdir())):
        raise Stop('r2 collection must be empty and unattested')
    preserved=read(root/'evidence/r2/preservation.json')['files']
    actual={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'collection').rglob('*') if p.is_file()}
    actual.update({n:sha((root/n).read_bytes()) for n in FREEZES[:2]})
    if actual!=preserved:raise Stop('VOID-HARNESS evidence changed')
    disposition=read(root/'evidence/r2/void-r1.json')
    if disposition.get('disposition')!='VOID-HARNESS' or disposition.get('episodes')!=1200 or disposition.get('behaviour_analysis_allowed') is not False:
        raise Stop('r1 VOID-HARNESS disposition missing')
    parent=read(root/'freeze-r1.json')
    parents={n:sha((root/n).read_bytes()) for n in FREEZES[:2]}
    if parent.get('revision')!='r1' or parent.get('parent_freeze_sha256')!=parents['freeze.json']:
        raise Stop('revision parent freeze mismatch')
    prior=read(root/'config/prior-spend-r2.json')
    for field in ('ledger','local_time'):
        if sha((root/prior[field+'_file']).read_bytes())!=prior[field+'_sha256']:
            raise Stop('r1 accounting evidence changed')
    files=inventory(root);digest=sha(canonical(files).encode())
    report=read(root/'build/test-report.json')
    if report['status']!='PASS' or report['source_sha256']!=digest:raise Stop('tests must bind exact source')
    record=dict(parent,revision='r2',parent_freezes=parents,
                frozen_utc=now(),files=files,content_sha256=digest,tests=report['tests'],
                test_report_sha256=sha((root/'build/test-report.json').read_bytes()),
                collection_directory='collection-r2',void_r1_sha256=sha((root/'evidence/r2/void-r1.json').read_bytes()),
                prior_spend=prior,
                frontier_reservation_micro_usd=sizing()['frontier_micro_usd'],
                usage_limit_policy='DEFINITE_NONSTART_ZERO_USAGE_429_PAUSE_RESUME')
    save(root/'freeze-r2.json',record);verify(root,'freeze-r2.json')
    directory.mkdir(exist_ok=True)
    return dict(status=record['status'],freeze_sha256=sha((root/'freeze-r2.json').read_bytes()),tests=record['tests'],void_r1_episodes=1200)


def create(root):
    root=Path(root)
    if (root/'freeze.json').exists():raise Stop('freeze exists; never overwrite')
    files=inventory(root);digest=sha(canonical(files).encode());report=read(root/'build/test-report.json')
    if report['status']!='PASS' or report['source_sha256']!=digest:raise Stop('tests must bind exact source')
    if (collection_dir(root)).exists() and any((collection_dir(root)).rglob('*.json')):raise Stop('freeze must precede collection')
    record=dict(format=1,version='0.2',frozen_utc=now(),files=files,content_sha256=digest,status='FROZEN_OFFLINE_NO_INFERENCE',transport_policy=TRANSPORT_POLICY,model_calls=0,new_usd=0,local_episodes=1200,frontier_episodes=80,maximum_generations=8960,tests=report['tests'],test_report_sha256=sha((root/'build/test-report.json').read_bytes()),frontier_reservation_micro_usd=sizing()['frontier_micro_usd'],protected_reserve_micro_usd=2000000,prior_spend=read(prior_path(root)),push_status='UNKNOWN',live_runtime_status='UNKNOWN',unresolved=['real post-freeze push attestation','fresh runtime identity/context/capacity','empirical CLI output/usage and current prices; no inferred hard bound'],stop_after_version='0.2')
    save(root/'freeze.json',record);verify(root)
    return dict(status=record['status'],freeze_sha256=sha(freeze_path(root).read_bytes()),tests=record['tests'])


def parsed_time(value):
    try:t=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError,AttributeError,TypeError):raise Stop('invalid server timestamp') from None
    if t.tzinfo is None:raise Stop('timezone required')
    return t


def event_fields(event,commit):
    if type(event) is not dict or re.fullmatch('[0-9a-f]{40}',commit or '') is None or event.get('activity_type')!='push' or event.get('after')!=commit or not event.get('id') or not str(event.get('ref','')).startswith('refs/heads/'):raise Stop('repository activity push record/commit required')
    if parsed_time(event.get('timestamp'))>=dt.datetime.now(dt.timezone.utc):raise Stop('future push evidence')
    return dict(commit=commit,github_time=event['timestamp'],remote_ref=event['ref'],server_event_id=event['id'],repo=REPOSITORY)


def check_push(root,record,push):
    root=Path(root)
    if push.get('freeze_sha256')!=sha(freeze_path(root).read_bytes()) or push.get('repo')!=REPOSITORY or push.get('evidence_file')!=(attestation_dir(root)/'push-event.json').relative_to(root).as_posix():raise Stop('push does not bind v0.2 freeze/repository')
    p=attestation_dir(root)/'push-event.json'
    if p.is_symlink() or sha(p.read_bytes())!=push.get('evidence_sha256'):raise Stop('push evidence missing/changed')
    supplied=event_fields(read(p),push.get('commit'))
    if any(push.get(k)!=v for k,v in supplied.items()) or parsed_time(push['github_time'])<parsed_time(record['frozen_utc']):raise Stop('push fields/time mismatch')
    local_push=read(collection_dir(root)/'push.json') if record.get('revision')=='r3' else None
    for folder in ('starts','episode-starts'):
        for p in (collection_dir(root)/folder).glob('*.json'):
            value=read(p)
            historical=record.get('revision')=='r3' and not value.get('episode_id',value.get('episode',{}).get('id','')).startswith('claude-')
            expected=local_push if historical else push
            if historical and expected.get('freeze_sha256')!=record['parent_freezes']['freeze-r2.json']:
                raise Stop('local r2 push binding changed')
            if value.get('freeze_sha256')!=expected['freeze_sha256'] or parsed_time(value['started'])<parsed_time(expected['github_time']):raise Stop('push must bind and precede every v0.2 start')
    return push


def push_gate(root,record):
    p=attestation_dir(Path(root))/'push.json'
    if not p.is_file() or p.is_symlink():raise Stop('real v0.2 push attestation missing; no dispatch')
    return check_push(root,record,read(p))


def attest(root,event_file,commit,clone_root,repo_path,freeze_name=None):
    """Future reviewer handoff only: read-only Git, create-once local receipt."""
    root=Path(root).resolve();clone=Path(clone_root).resolve();record=verify(root,freeze_name)
    if freeze_path(root,freeze_name)!=freeze_path(root):raise Stop('attest must use current revision freeze')
    rel=PurePosixPath(repo_path)
    if rel.is_absolute() or '..' in rel.parts or str(rel)=='.' or ':' in repo_path or '\\' in repo_path:raise Stop('invalid repository project path')
    raw=Path(event_file).read_bytes();fields=event_fields(strict_load(raw),commit)
    def git(*args):return subprocess.run(['git','-C',str(clone),*args],capture_output=True,check=True).stdout
    top=Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()
    if top!=clone or top.name=='RobinOS2' or root==top or root in top.parents or top in root.parents:raise Stop('separate research clone required')
    if git('rev-parse','HEAD').decode().strip()!=commit:raise Stop('HEAD mismatch')
    if git('remote','get-url','origin').decode().strip() not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git','git@github.com:'+REPOSITORY+'.git'):raise Stop('origin mismatch')
    manifests={n:sha((root/n).read_bytes()) for n in FREEZES if (root/n).exists()}
    for name,digest in dict(record['files'],**manifests).items():
        if sha(git('show',commit+':'+str(rel)+'/'+name))!=digest:raise Stop('pushed bytes differ: '+name)
    if not any(line.split()==[commit,fields['remote_ref']] for line in git('ls-remote','origin',fields['remote_ref']).decode().splitlines()):raise Stop('remote ref mismatch')
    if parsed_time(fields['github_time'])<parsed_time(record['frozen_utc']):raise Stop('push predates freeze')
    with lock(collection_dir(root)/'collector.lock'):
        verify(root)
        if record.get('revision')=='r3':
            from bob_revision_r3 import check_preserved
            check_preserved(root)
            started=any(p.is_file() for d in ('starts','episode-starts') for p in (collection_dir(root)/d).glob('claude-*.json'))
        else:
            started=any(p.is_file() for d in ('starts','episode-starts') for p in (collection_dir(root)/d).glob('*.json'))
        if started:raise Stop('attest before all new starts')
        receipt=dict(fields,freeze_sha256=sha(freeze_path(root).read_bytes()),evidence_file=(attestation_dir(root)/'push-event.json').relative_to(root).as_posix(),evidence_sha256=sha(raw),recorded_utc=now(),repo_path=repo_path)
        save_bytes(attestation_dir(root)/'push-event.json',raw);check_push(root,record,receipt);save(attestation_dir(root)/'push.json',receipt)
    return receipt
