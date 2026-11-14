"""Post-push D1 lineage and local attestation. Offline; no Git or provider imports."""
import datetime as dt
from pathlib import Path
import re
from uc_core import sha,canonical
from uc_store import Stop,read,save,now,lock,Journal,Ledger,ActiveTime
from uc_usage_limit import check_prefixes

A1_SHA256='746b525bab8dc67fdb695958a3df071c005f72bef14950274b637925817eba82'
D1_CHANGED={'uc_collect.py','uc_freeze.py','uc_manifest.py','uc_analysis.py','uc_store.py',
            'tests/test_a1.py','RUN.md','PROJECT_STATE.md','README.md'}


def timestamp(value):
    t=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:raise Stop('missing timezone')
    return t


def validate_d1(root,value):
    from uc_manifest import PARENT_SHA256,validate_a1
    root=Path(root);a1=read(root/'freeze-a1.json');validate_a1(root,a1)
    if sha((root/'freeze-a1.json').read_bytes())!=A1_SHA256 or value.get('parents')!={'freeze.json':PARENT_SHA256,'freeze-a1.json':A1_SHA256}:
        raise Stop('D1 parent binding mismatch')
    if value.get('changed_inputs')!=sorted(D1_CHANGED):raise Stop('D1 scope mismatch')
    if a1['content_sha256']!=sha(canonical(a1['files']).encode()):raise Stop('A1 content identity')
    for name,digest in a1['files'].items():
        target='deviations/d1/original/'+name if name in D1_CHANGED else name
        if value['files'].get(target)!=digest:raise Stop('D1 changed protected input or missing archive: '+name)
    if value.get('baseline_sha256')!=value['files'].get('deviations/d1/collection-baseline.json'):
        raise Stop('D1 baseline identity mismatch')


def check_baseline(root,data):
    """All old files remain exact; journals may grow with valid retained prefixes."""
    root=Path(root);data=Path(data);baseline=read(root/'deviations/d1/collection-baseline.json')
    for name,pin in baseline['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise Stop('unsafe baseline path')
        path=data/name
        if path.is_symlink() or not path.resolve().is_relative_to(data.resolve()):raise Stop('unsafe baseline evidence')
        raw=path.read_bytes()
        if len(raw)<pin['bytes'] or sha(raw[:pin['bytes']])!=pin['sha256'] or (not name.endswith('.jsonl') and len(raw)!=pin['bytes']):
            raise Stop('D1 pre-existing evidence changed: '+name)
    check_prefixes(data,{name:pin for name,pin in baseline['files'].items() if name.endswith('.jsonl')})
    Ledger(data/'ledger.jsonl')
    for name,cap in [('local',43200),('claude',7200)]:
        if (data/(name+'-time.jsonl')).exists():ActiveTime(data/(name+'-time.jsonl'),cap)
    return baseline


def parent_push(root,data):
    """Validate saved genuine parent activity and its binding without network access."""
    root=Path(root);data=Path(data);a=read(data/'push.json');source=(data/'push-event.json').read_bytes();e=read(data/'push-event.json')
    a1=read(root/'freeze-a1.json')
    if (a.get('repo')!='Robin84Bran/research' or a.get('source_api')!='/repos/Robin84Bran/research/activity' or
        a.get('freeze_file')!='freeze-a1.json' or a.get('freeze_sha256')!=A1_SHA256 or
        a.get('manifest_sha256')!=a1['content_sha256'] or a.get('event_sha256')!=sha(source) or
        e.get('activity_type')!='push' or e.get('after')!=a.get('commit') or e.get('ref')!=a.get('remote_ref') or
        e.get('timestamp')!=a.get('pushed_at') or e.get('id') is None or e['id']!=a.get('server_event_id') or
        re.fullmatch('[a-f0-9]{40}',str(a.get('commit'))) is None or re.fullmatch(r'refs/heads/[^\s:]+',str(e.get('ref'))) is None):
        raise Stop('D1 parent push binding mismatch')
    if not timestamp(a1['created_at'])<timestamp(a['pushed_at'])<dt.datetime.now(dt.timezone.utc):raise Stop('parent push ordering')
    return a


def d1_provenance(root,data,require_attest=True):
    from uc_manifest import active
    root=Path(root);data=Path(data);name,f=active(root)
    if name!='freeze-d1.json':raise Stop('D1 freeze required')
    digest=sha((root/name).read_bytes())
    if f['content_sha256']!=sha(canonical(f['files']).encode()):raise Stop('D1 content identity')
    for filename,h in f['files'].items():
        p=root/filename
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h:raise Stop('D1 input changed: '+filename)
    baseline=check_baseline(root,data);parent=parent_push(root,data)
    if timestamp(f['created_at'])<=timestamp(parent['pushed_at']):raise Stop('D1 must follow parent push')
    receipt=None
    if require_attest:
        receipt=read(data/'d1-attestation.json')
        if (receipt.get('freeze_sha256')!=digest or receipt.get('parents')!=f['parents'] or
            receipt.get('parent_push_sha256')!=sha((data/'push.json').read_bytes()) or
            receipt.get('baseline_sha256')!=f['baseline_sha256'] or receipt.get('kind')!='D1 local harness attestation' or
            timestamp(receipt['attested_at'])<timestamp(f['created_at'])):raise Stop('D1 attestation mismatch')
    schedule=read(root/'config/episodes.json');local=[ep for ep in schedule if ep['actor']!='claude']
    for ep in local:
        terminal=data/'episodes'/ep['id']/'episode.json'
        if not terminal.exists() or terminal.relative_to(data).as_posix() not in baseline['files']:raise Stop('D1 requires retained complete local cohort')
    for p in list(data.glob('episodes/*/*.start.json'))+list(data.glob('episodes/*/dispatches/*/start.json')):
        start=read(p);rel=p.relative_to(data).as_posix()
        if rel in baseline['files']:
            if start.get('freeze_sha256')!=A1_SHA256 or timestamp(start['started_at'])<=timestamp(parent['pushed_at']):raise Stop('parent start ordering/binding')
        else:
            if receipt is None:raise Stop('D1 attestation must precede new starts')
            episode=p.parent.name if p.name.endswith('.start.json') else p.parent.parent.parent.name
            if not any(e['id']==episode and e['actor']=='claude' for e in schedule):raise Stop('D1 permits only new Claude starts')
            if start.get('freeze_sha256')!=digest or timestamp(start['started_at'])<=timestamp(receipt['attested_at']):raise Stop('D1 start ordering/binding')
    return digest


def attest_d1(root):
    root=Path(root)
    from uc_freeze import verify
    with lock(root/'collection'):
        digest=verify(root);d1_provenance(root,root/'collection',False)
        f=read(root/'freeze-d1.json')
        save(root/'collection/d1-attestation.json',dict(kind='D1 local harness attestation',attested_at=now(),
            freeze_sha256=digest,parents=f['parents'],baseline_sha256=f['baseline_sha256'],
            parent_push_sha256=sha((root/'collection/push.json').read_bytes()),
            authority='Claude delegating reviewer: post-push D1 before first Claude call; no new push required'))
    return digest
