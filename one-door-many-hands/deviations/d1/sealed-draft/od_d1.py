"""Local post-push D1 binding. Parent push remains immutable; no new Git needed."""
from functools import lru_cache
from pathlib import Path
from od_core import sha,canonical
from od_io import Stop,read,save,lock,now
from od_provenance import timestamp
from od_usage import verify_prefixes,prefix_snapshot

D1_CHANGED=frozenset(('od_collect.py','od_validation.py','od_analysis.py','od_freeze.py','od_provenance.py','od_recovery.py','RUN.md','PROJECT_STATE.md','DEVIATIONS.md','tests/test_a1.py'))


def lineage(root,f):
    root=Path(root)
    for name,h in f['parents'].items():
        if (root/name).is_symlink() or sha((root/name).read_bytes())!=h: raise Stop('D1 parent freeze mismatch')
    parent=read(root/'freeze-a1.json');original=read(root/'freeze.json')
    if parent['parent_freeze_sha256']!=f['parents']['freeze.json']: raise Stop('D1 A1 lineage mismatch')
    from od_freeze import A1_CHANGED
    for n,h in original['files'].items():
        expected='deviations/a1/original/'+n if n in A1_CHANGED else n
        if parent['files'].get(expected)!=h: raise Stop('D1 original lineage mismatch')
    if set(f['changed_originals'])!=D1_CHANGED: raise Stop('D1 scope mismatch')
    for n,h in parent['files'].items():
        archived='deviations/d1/parent-a1/'+n
        if f['files'].get(archived)!=h: raise Stop('D1 parent archive mismatch: '+n)
        if n not in D1_CHANGED and f['files'].get(n)!=h: raise Stop('D1 forbidden science/evidence change: '+n)
    if any(f.get(k)!=v for k,v in parent.items() if k not in ('revision','kind','created_at','files','changed_originals','parent_freeze_sha256')): raise Stop('D1 frozen metadata drift')
    if timestamp(f['created_at'])<=timestamp(parent['created_at']): raise Stop('D1 chronology mismatch')


def verify_d1(root):
    from od_freeze import inputs
    root=Path(root);p=root/'freeze-d1.json';f=read(p)
    lineage(root,f)
    if set(f['files'])!=set(inputs(root)): raise Stop('D1 freeze input set drift')
    for n,h in f['files'].items():
        p=root/n
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h: raise Stop('D1 frozen input changed: '+n)
    return sha((root/'freeze-d1.json').read_bytes())


def freeze_d1(root):
    from od_freeze import inputs
    root=Path(root);parent=read(root/'freeze-a1.json')
    f=dict(parent,revision='D1',kind='post-push harness-only usage-limit nonstart deviation before Claude calls',created_at=now(),changed_originals=sorted(D1_CHANGED),parents={n:sha((root/n).read_bytes()) for n in ('freeze.json','freeze-a1.json')},files={n:sha((root/n).read_bytes()) for n in inputs(root)})
    lineage(root,f)
    baseline=read(root/'evidence/d1-baseline.json')
    if baseline['claude_terminal_count']!=0 or baseline['local_terminal_count']!=3600: raise Stop('D1 requires completed locals and no Claude calls at baseline')
    verify_baseline(root)
    save(root/'freeze-d1.json',f)
    return verify_d1(root)


@lru_cache(maxsize=4)
def baseline_file(path,digest):
    from od_core import strict_load
    data=Path(path).read_bytes()
    if sha(data)!=digest: raise Stop('D1 baseline manifest changed')
    return strict_load(data)


def baseline(root):
    root=Path(root);p=root/'evidence/d1-baseline.json'
    if (root/'freeze-d1.json').exists():
        return baseline_file(str(p.resolve()),read(root/'freeze-d1.json')['files']['evidence/d1-baseline.json'])
    return read(p)


def verify_baseline(root):
    root=Path(root);b=baseline(root);base=root/'collection'
    verify_prefixes(base,b['prefixes'])
    for n,h in b['files'].items():
        p=base/n
        if p.is_symlink() or sha(p.read_bytes())!=h: raise Stop('D1 baseline evidence changed: '+n)


def attest_d1(root):
    root=Path(root);h=verify_d1(root)
    with lock(root/'collection'):
        verify_baseline(root)
        # Validate the original already-pushed receipt under its original freeze.
        from od_provenance import parent_receipt_gate
        parent_receipt_gate(root)
        from od_analysis import replay
        replay(root,root/'collection')
        p=root/'collection/d1-attestation.json'
        record={'kind':'local post-push D1 attestation','freeze_sha256':h,'parents':read(root/'freeze-d1.json')['parents'],'parent_push_sha256':sha((root/'collection/push.json').read_bytes()),'parent_event_sha256':sha((root/'collection/push-event.json').read_bytes()),'prefixes':prefix_snapshot(root/'collection'),'attested_at':now()}
        if p.exists():
            d1_gate(root);return read(p)
        save(p,record);return record


def d1_gate(root):
    root=Path(root);a=read(root/'collection/d1-attestation.json');f=read(root/'freeze-d1.json')
    if a['freeze_sha256']!=sha((root/'freeze-d1.json').read_bytes()) or a['parents']!=f['parents'] or a['parent_push_sha256']!=sha((root/'collection/push.json').read_bytes()) or a['parent_event_sha256']!=sha((root/'collection/push-event.json').read_bytes()): raise Stop('D1 attestation binding mismatch')
    if timestamp(a['attested_at'])<=timestamp(f['created_at']): raise Stop('D1 attestation predates freeze')
    verify_prefixes(root/'collection',a['prefixes'])
    return timestamp(a['attested_at'])
