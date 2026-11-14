"""Pre-Claude schema revision; preserve r2 local evidence and its accounting."""
from pathlib import Path

from bob_core import canonical,sha,schedule
from bob_collect import Stop,read,save,now


def check_preserved(root):
    root=Path(root)
    record=read(root/'evidence/r3/preservation.json')
    for name,digest in dict(record['files'],**record['unchanged_inputs'],**record['parent_freezes']).items():
        path=root/name
        if path.is_symlink() or sha(path.read_bytes())!=digest:
            raise Stop('preserved r2 bytes changed: '+name)
    for name,prefix in record['append_only'].items():
        path=root/name
        with path.open('rb') as stream:raw=stream.read(prefix['bytes'])
        if path.is_symlink() or sha(raw)!=prefix['sha256']:
            raise Stop('preserved r2 ledger prefix changed')
    return record


def create_r3(root):
    from bob_freeze import FREEZES,inventory,verify
    from bob_audit import audit_episode,reconcile_ledger
    root=Path(root)
    if (root/'freeze-r3.json').exists():raise Stop('revision freeze exists; never overwrite')
    if (root/'collection-r3').exists() and any((root/'collection-r3').iterdir()):
        raise Stop('r3 attestation must be empty')
    preserved=check_preserved(root)
    parent=read(root/'freeze-r2.json')
    parents={n:sha((root/n).read_bytes()) for n in FREEZES[:3]}
    if (parent.get('revision')!='r2' or parent.get('parent_freezes')!={n:parents[n] for n in FREEZES[:2]} or
        preserved['parent_freezes']!=parents):raise Stop('revision parent freeze mismatch')
    if any(parent['files'].get(n)!=h for n,h in preserved['unchanged_inputs'].items()):
        raise Stop('local r2 inputs differ from parent freeze')
    plan=schedule();local={e['id']:e for e in plan if e['model']!='claude'}
    directory=root/'collection-r2'
    if any(p.is_file() for d in ('starts','episode-starts','calls','raw','requests') for p in (directory/d).glob('claude-*')):
        raise Stop('r3 requires zero Claude starts/calls')
    records={p.stem:read(p) for p in (directory/'episodes').glob('*.json')}
    starts={p.stem for p in (directory/'episode-starts').glob('*.json')}
    if set(records)!=set(local) or starts!=set(local):raise Stop('r3 requires all 1200 completed r2 locals')
    calls=set()
    for ident,saved in records.items():
        if saved['episode']!=local[ident]:raise Stop('r2 episode identity changed')
        audit_episode(root,local[ident],saved,parents['freeze-r2.json'])
        calls.update(saved['calls'])
    if any({p.stem for p in (directory/d).glob('*.json')}!=calls for d in ('starts','calls','requests')):
        raise Stop('r2 orphan/uncertain call evidence')
    ledger=reconcile_ledger(root,records)
    if ledger['status']!='PASS':raise Stop('r2 unresolved ledger')
    files=inventory(root);digest=sha(canonical(files).encode())
    report=read(root/'build/test-report.json')
    if report['status']!='PASS' or report['source_sha256']!=digest:raise Stop('tests must bind exact source')
    record=dict(parent,revision='r3',parent_freezes=parents,frozen_utc=now(),files=files,
                content_sha256=digest,tests=report['tests'],test_report_sha256=sha((root/'build/test-report.json').read_bytes()),
                collection_directory='collection-r2',attestation_directory='collection-r3',
                r2_preservation_sha256=sha((root/'evidence/r3/preservation.json').read_bytes()),
                preserved_local_episodes=1200,new_local_episodes=0,frontier_episodes=80,
                claude_schema_policy='OBJECT_ROOT_PROPERTY_DOMAINS_STRICT_VALIDATOR_CROSS_FIELD',
                provider_schema_acceptance_status='UNKNOWN',model_calls=0,new_usd=0)
    save(root/'freeze-r3.json',record);verify(root,'freeze-r3.json')
    return dict(status=record['status'],freeze_sha256=sha((root/'freeze-r3.json').read_bytes()),tests=record['tests'],preserved_local_episodes=1200)
