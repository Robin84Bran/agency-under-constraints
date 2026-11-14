"""D2 saved-byte disposition, narrow STOP clearance and local freeze lineage.

No provider calls, subprocesses, network, or Git. Original evidence is immutable;
only the frozen overlay changes its operational interpretation.
"""
import argparse
from pathlib import Path
from uc_core import ROOT, canonical, sha
from uc_store import Stop, read, save, now, lock

PARENTS={
 'freeze.json':'fc497643b1e72f1e928ab8a36dc74d72bc2b82d6a70239c1e18868924a854d51',
 'freeze-a1.json':'746b525bab8dc67fdb695958a3df071c005f72bef14950274b637925817eba82',
 'freeze-d1.json':'25e43f2fedd5448738844d8201b3e3f13384ef247ddffdcf08f78fbfcd7fa70b'}
CHANGED={'uc_usage_limit.py','uc_transport.py','uc_store.py','uc_collect.py','uc_analysis.py','uc_manifest.py',
         'uc_freeze.py','tests/test_a1.py','tests/test_d1.py','tests/test_runtime.py',
         'RUN.md','PROJECT_STATE.md','README.md'}
PLAN='deviations/d2/disposition-plan.json'
BASELINE='deviations/d2/collection-baseline.json'


def validate_d2(root,f):
    from uc_lineage import validate_d1
    root=Path(root)
    for name,digest in PARENTS.items():
        if (root/name).is_symlink() or sha((root/name).read_bytes())!=digest:raise Stop('D2 parent changed: '+name)
    validate_d1(root,read(root/'freeze-d1.json'))
    if f.get('parents')!=PARENTS or f.get('changed_inputs')!=sorted(CHANGED):raise Stop('D2 parent/scope binding')
    parent=read(root/'freeze-d1.json')
    for name,digest in parent['files'].items():
        target='deviations/d2/original/'+name if name in CHANGED else name
        if f['files'].get(target)!=digest:raise Stop('D2 protected input/archive changed: '+name)
    if f.get('baseline_sha256')!=f['files'].get(BASELINE) or f.get('plan_sha256')!=f['files'].get(PLAN):raise Stop('D2 plan/baseline binding')


def frozen_plan(root):
    root=Path(root);f=read(root/'freeze-d2.json');plan=read(root/PLAN)
    if sha((root/PLAN).read_bytes())!=f['files'][PLAN]:raise Stop('D2 plan changed')
    return f,plan


def baseline(root,base):
    from uc_store import Journal,Ledger,ActiveTime
    root=Path(root);base=Path(base);b=read(root/BASELINE)
    for name,pin in b['files'].items():
        p=base/name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.resolve().is_relative_to(base.resolve()):raise Stop('unsafe D2 baseline path')
        raw=p.read_bytes()
        if len(raw)<pin['bytes'] or sha(raw[:pin['bytes']])!=pin['sha256'] or (not name.endswith('.jsonl') and len(raw)!=pin['bytes']):raise Stop('D2 retained evidence changed: '+name)
    # Inventory above verifies each retained byte prefix. Replay each full current
    # journal once, including its checkpoints and semantic accounting/time rules.
    Ledger(base/'ledger.jsonl')
    for p in base.glob('*.jsonl'):
        if p.name not in ('ledger.jsonl','local-time.jsonl','claude-time.jsonl'):Journal(p)
    for name,cap in [('local',43200),('claude',7200)]:
        ActiveTime(base/(name+'-time.jsonl'),cap)
    return b


def clearance_record(root,base):
    root=Path(root);base=Path(base);f,plan=frozen_plan(root);r=read(base/'d2-clearance.json')
    expected=dict(kind='D2 evidence-specific STOP clearance',freeze_sha256=sha((root/'freeze-d2.json').read_bytes()),
                  plan_sha256=f['plan_sha256'],baseline_sha256=f['baseline_sha256'],
                  stop_sha256=plan['stop_sha256'],episode=plan['episode'],journal_prefixes=plan['journal_prefixes'])
    if any(r.get(k)!=v for k,v in expected.items()):raise Stop('D2 clearance binding mismatch')
    from uc_lineage import timestamp
    if timestamp(r['cleared_at'])<timestamp(f['created_at']):raise Stop('D2 clearance predates freeze')
    if sha((base/'STOP.json').read_bytes())!=plan['stop_sha256']:raise Stop('different STOP cannot be cleared')
    return r,plan


def validate_clear_event(base,e,prior):
    base=Path(base);root=base.parent
    r,plan=clearance_record(root,base)
    expected=dict(event='clear-stop-d2',id=plan['episode'],clearance_sha256=sha((base/'d2-clearance.json').read_bytes()),
                  stop_sha256=plan['stop_sha256'])
    if any(e.get(k)!=v for k,v in expected.items()):raise Stop('D2 ledger clearance mismatch')
    if len(prior)!=plan['ledger_events'] or not prior or prior[-1]!=plan['ledger_stop'] or sum(v['event']=='stop' for v in prior)!=1:
        raise Stop('D2 clearance does not match the single frozen stop')
    if any(v['event']=='settle' and v['actual']>v['reserved'] for v in prior):raise Stop('cannot clear an accounting overrun')
    pin=plan['journal_prefixes']['ledger.jsonl'];raw=(base/'ledger.jsonl').read_bytes()
    if len(raw)<pin['bytes'] or sha(raw[:pin['bytes']])!=pin['sha256']:raise Stop('D2 ledger prefix changed')


def effective_read(base,path):
    """Use a frozen disposition overlay only after its exact clearance exists."""
    base=Path(base);path=Path(path);value=read(path)
    if not (base/'d2-clearance.json').exists():return value
    receipt=read(base/'d2-clearance.json')
    if path.parent.name!=receipt.get('episode') or path.name not in ('2.parsed.json','episode.json'):return value
    _,plan=clearance_record(base.parent,base)
    name=path.relative_to(base).as_posix();overlay=plan['overlays'].get(name)
    if overlay is None:return value
    if sha(path.read_bytes())!=overlay['original_sha256']:raise Stop('D2 overlay source changed')
    return overlay['value']


def contract_freeze(base,current):
    base=Path(base)
    if not (base/'d2-clearance.json').exists():return current
    _,plan=clearance_record(base.parent,base)
    if sha((base/'claude-contract.json').read_bytes())!=plan['contract_sha256']:raise Stop('D2 historical contract changed')
    return read(base/'claude-contract.json')['freeze_sha256']


def stop_cleared(root,base,path):
    root=Path(root);base=Path(base);path=Path(path)
    if path.name!='STOP.json' or not (root/'freeze-d2.json').exists() or not (base/'d2-clearance.json').exists():return False
    from uc_store import Ledger
    _,plan=clearance_record(root,base);ledger=Ledger(base/'ledger.jsonl')
    return not ledger.blocked and plan['episode'] in ledger.finished


def provenance(root,base,require_attest=True):
    from uc_freeze import verify
    from uc_lineage import parent_push,timestamp
    from uc_store import Ledger
    root=Path(root);base=Path(base);digest=verify(root);f,plan=frozen_plan(root)
    if require_attest and not (base/'d2-attestation.json').exists():raise FileNotFoundError(base/'d2-attestation.json')
    baseline(root,base);parent_push(root,base)
    d1=read(base/'d1-attestation.json')
    if d1.get('freeze_sha256')!=PARENTS['freeze-d1.json']:raise Stop('D2 historical D1 attestation changed')
    r=None
    if require_attest:
        r=read(base/'d2-attestation.json')
        if (r.get('kind')!='D2 local harness attestation' or r.get('freeze_sha256')!=digest or r.get('parents')!=PARENTS or
            r.get('clearance_sha256')!=sha((base/'d2-clearance.json').read_bytes()) or
            timestamp(r['attested_at'])<timestamp(f['created_at'])):raise Stop('D2 attestation binding mismatch')
    b=read(root/BASELINE);d1_files=read(root/'deviations/d1/collection-baseline.json')['files']
    for p in list(base.glob('episodes/*/*.start.json'))+list(base.glob('episodes/*/dispatches/*/start.json')):
        start=read(p);name=p.relative_to(base).as_posix()
        if name in b['files']:
            expected=PARENTS['freeze-a1.json'] if name in d1_files else PARENTS['freeze-d1.json']
            boundary=read(base/'push.json')['pushed_at'] if expected==PARENTS['freeze-a1.json'] else d1['attested_at']
            if start['freeze_sha256']!=expected or timestamp(start['started_at'])<=timestamp(boundary):raise Stop('D2 historical start binding/order')
        else:
            if r is None or start['freeze_sha256']!=digest or timestamp(start['started_at'])<=timestamp(r['attested_at']):raise Stop('D2 start before attestation/binding')
            episode=p.parent.name if p.name.endswith('.start.json') else p.parent.parent.parent.name
            if not any(e['id']==episode and e['actor']=='claude' for e in read(root/'config/episodes.json')):raise Stop('D2 only permits new Claude starts')
    if require_attest and not stop_cleared(root,base,base/'STOP.json'):raise Stop('D2 STOP not cleared')
    Ledger(base/'ledger.jsonl')
    return digest


def seal(root):
    from uc_freeze import inputs,verify
    from uc_lineage import parent_push
    root=Path(root);base=root/'collection'
    if (root/'freeze-d2.json').exists():raise FileExistsError(root/'freeze-d2.json')
    baseline(root,base);parent_push(root,base)
    files={name:sha((root/name).read_bytes()) for name in inputs(root)}
    parent=read(root/'freeze-d1.json')
    f=dict(parent,revision='v0.1-r1-a1-d1-d2',created_at=now(),parents=PARENTS,changed_inputs=sorted(CHANGED),
           files=files,content_sha256=sha(canonical(files).encode()),baseline_sha256=files[BASELINE],plan_sha256=files[PLAN],
           authority='Claude delegating reviewer: saved-byte D2 diagnosis, fix, clearance and local attestation; no model calls, pushes or Git')
    validate_d2(root,f);save(root/'freeze-d2.json',f)
    return verify(root)


def clear(root):
    """Create-once record + resumable journal appends; never edits/deletes STOP."""
    from uc_freeze import verify
    from uc_store import Ledger
    from uc_transport import decode
    from uc_store import TransportFailure
    from uc_core import transport_load
    root=Path(root);base=root/'collection'
    with lock(base):
        digest=verify(root);baseline(root,base);f,plan=frozen_plan(root)
        stem=base/'episodes'/plan['episode']/'2'
        if sha((base/'STOP.json').read_bytes())!=plan['stop_sha256']:raise Stop('different STOP')
        req=read(str(stem)+'.request.json');raw=read(str(stem)+'.raw.json');env=transport_load(Path(str(stem)+'.stdout').read_text())
        try:decode(env,raw,read(stem.parent/'episode.json')['episode'],req['phase'],req['reservation'])
        except TransportFailure:pass
        else:raise Stop('saved bytes no longer support D2 transport disposition')
        record=base/'d2-clearance.json'
        if not record.exists():
            save(record,dict(kind='D2 evidence-specific STOP clearance',cleared_at=now(),freeze_sha256=digest,
                plan_sha256=f['plan_sha256'],baseline_sha256=f['baseline_sha256'],stop_sha256=plan['stop_sha256'],
                episode=plan['episode'],journal_prefixes=plan['journal_prefixes'],
                authority='Claude delegating reviewer: recorded D2 clearance; preserve original STOP and evidence; no episode rerun'))
        clearance_record(root,base)
        ledger=Ledger(base/'ledger.jsonl')
        if not any(e['event']=='clear-stop-d2' for e in ledger.journal.events):
            ledger.event(event='clear-stop-d2',id=plan['episode'],clearance_sha256=sha(record.read_bytes()),stop_sha256=plan['stop_sha256'])
        if plan['episode'] not in ledger.finished:ledger.event(event='release',id=plan['episode'])
        if not stop_cleared(root,base,base/'STOP.json'):raise Stop('incomplete D2 clearance')
    return digest


def attest(root):
    root=Path(root);base=root/'collection'
    with lock(base):
        if (base/'d2-attestation.json').exists():raise FileExistsError(base/'d2-attestation.json')
        digest=provenance(root,base,False)
        if not stop_cleared(root,base,base/'STOP.json'):raise Stop('clear D2 STOP before attesting')
        save(base/'d2-attestation.json',dict(kind='D2 local harness attestation',attested_at=now(),freeze_sha256=digest,
            parents=PARENTS,clearance_sha256=sha((base/'d2-clearance.json').read_bytes()),
            authority='Claude delegating reviewer: local saved-byte D2; no new push required'))
    return digest


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','clear-stop','attest','verify']);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    if a.command=='verify':
        from uc_freeze import verify
        result=verify(a.root)
    else:result={'seal':seal,'clear-stop':clear,'attest':attest}[a.command](a.root)
    print(result)

if __name__=='__main__':main()
