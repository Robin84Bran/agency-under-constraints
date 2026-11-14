"""D2 saved-byte envelope deviation; no provider, Git, or network operations."""
from functools import lru_cache
from pathlib import Path
from od_core import ROOT,sha
from od_io import Stop,read,save,now,lock,Ledger,ActiveTime
from od_usage import verify_prefixes,prefix_snapshot
from od_provenance import timestamp

PARENTS=('freeze.json','freeze-a1.json','freeze-d1.json','freeze-d1-final.json')
D2_CHANGED=frozenset(('od_validation.py','od_usage.py','od_collect.py','od_analysis.py','od_freeze.py','od_provenance.py','od_io.py','RUN.md','PROJECT_STATE.md','DEVIATIONS.md','tests/test_validation.py','tests/test_d1.py'))

@lru_cache(maxsize=4)
def baseline_bytes(path,digest):
    from od_core import strict_load
    data=Path(path).read_bytes()
    if sha(data)!=digest: raise Stop('D2 baseline manifest changed')
    return strict_load(data)

def baseline(root):
    root=Path(root);p=root/'evidence/d2-baseline.json'
    f=root/'freeze-d2.json'
    return baseline_bytes(str(p.resolve()),read(f)['files']['evidence/d2-baseline.json']) if f.exists() else read(p)

def verify_baseline(root):
    root=Path(root);base=root/'collection';b=baseline(root)
    verify_prefixes(base,b['prefixes'])
    for n,h in b['files'].items():
        p=base/n
        if p.is_symlink() or not p.resolve().is_relative_to(base.resolve()) or sha(p.read_bytes())!=h: raise Stop('D2 baseline evidence changed: '+n)
    Ledger(base/'ledger.jsonl')
    for name,cap in (('local',28800),('claude',7200)):
        if ActiveTime(base/(name+'-time.jsonl'),cap).breaches: raise Stop('D2 active time breach')

def lineage(root,f):
    root=Path(root)
    if set(f['parents'])!=set(PARENTS) or f['revision']!='D2' or set(f['changed_originals'])!=D2_CHANGED: raise Stop('D2 lineage/scope mismatch')
    for n,h in f['parents'].items():
        if (root/n).is_symlink() or sha((root/n).read_bytes())!=h: raise Stop('D2 parent freeze mismatch: '+n)
    parent=read(root/'freeze-d1-final.json')
    from od_d1 import lineage as d1_lineage,verify_draft
    d1_lineage(root,parent);verify_draft(root,parent)
    for n,h in parent['files'].items():
        if n in D2_CHANGED:
            if f['files'].get('deviations/d2/parent-d1-final/'+n)!=h: raise Stop('D2 parent archive mismatch: '+n)
        elif f['files'].get(n)!=h: raise Stop('D2 forbidden science/evidence change: '+n)
    inherited=set(parent)-{'revision','kind','created_at','files','parents','changed_originals'}
    if any(f.get(k)!=parent[k] for k in inherited): raise Stop('D2 metadata drift')
    if timestamp(f['created_at'])<=timestamp(parent['created_at']): raise Stop('D2 chronology mismatch')

def verify_d2(root):
    from od_freeze import inputs
    root=Path(root);p=root/'freeze-d2.json';f=read(p);lineage(root,f)
    if p.is_symlink() or set(f['files'])!=set(inputs(root)): raise Stop('D2 freeze input set drift')
    for n,h in f['files'].items():
        q=root/n
        if q.is_symlink() or not q.resolve().is_relative_to(root.resolve()) or sha(q.read_bytes())!=h: raise Stop('D2 frozen input changed: '+n)
    return sha(p.read_bytes())

def freeze_d2(root=ROOT):
    from od_freeze import inputs
    root=Path(root);parent=read(root/'freeze-d1-final.json')
    f=dict(parent,revision='D2',kind='post-stop saved-byte envelope classification deviation; no model calls',created_at=now(),changed_originals=sorted(D2_CHANGED),parents={n:sha((root/n).read_bytes()) for n in PARENTS},files={n:sha((root/n).read_bytes()) for n in inputs(root)})
    lineage(root,f);verify_baseline(root)
    b=baseline(root);terminals=[n for n in b['files'] if n.startswith('episodes/') and n.endswith('/episode.json')]
    if len(terminals)!=3601 or sum(n.startswith('episodes/claude-') for n in terminals)!=1 or b['local_terminal_count']!=3600 or b['claude_terminal_count']!=1: raise Stop('D2 requires exact saved 3600-local/one-Claude baseline')
    save(root/'freeze-d2.json',f);return verify_d2(root)

def clearance_valid(base):
    base=Path(base);p=base/'envelope-stop-clearance.json'
    if not p.exists() or any(q.name!='STOP.json' for q in base.glob('STOP*.json')): return False
    c=read(p);verify_prefixes(base,c['prefixes'])
    if c['stop_sha256']!=sha((base/'STOP.json').read_bytes()): raise Stop('D2 clearance STOP changed')
    d=base/c['path']
    if d.is_symlink() or not d.resolve().is_relative_to((base/'episodes').resolve()): raise Stop('D2 unsafe clearance path')
    from od_usage import nonstart
    marker=nonstart(d)
    if marker is None or c['nonstart_sha256']!=sha((d/'nonstart.json').read_bytes()) or c['terminal_sha256']!=sha((d/'episode.json').read_bytes()): raise Stop('D2 clearance evidence changed')
    root=base.parent;f=root/'freeze-d2.json'
    if not f.exists() or c['freeze_sha256']!=sha(f.read_bytes()): raise Stop('D2 clearance freeze mismatch')
    # A crash after saving a new fatal terminal but before its STOP cannot revive
    # the historical clearance. Only the exact original terminal is superseded.
    old=baseline(root)['files']
    for terminal in (base/'episodes').rglob('episode.json'):
        if terminal.relative_to(base).as_posix() not in old and read(terminal).get('fatal'): return False
    Ledger(base/'ledger.jsonl')
    for name,cap in (('local',28800),('claude',7200)):
        if ActiveTime(base/(name+'-time.jsonl'),cap).breaches: raise Stop('D2 clearance timer breach')
    return True

def clear_envelope_stop(root=ROOT):
    root=Path(root);h=verify_d2(root);base=root/'collection'
    with lock(base):
        verify_baseline(root)
        if clearance_valid(base): return read(base/'envelope-stop-clearance.json')
        if (base/'envelope-stop-clearance.json').exists(): raise Stop('D2 clearance cannot unlock a later STOP')
        if any(q.name!='STOP.json' for q in base.glob('STOP*.json')): raise Stop('D2 cannot clear a later or unrelated STOP')
        decision=read(root/'evidence/d2-decision.json')
        if decision['disposition']!='VERIFIED_TRANSPORT_NONSTART': raise Stop('D2 recorded disposition does not permit DNS clearance')
        jobs=read(root/'config/episodes.json');observed=[ep for ep in jobs if ep['actor']=='claude' and (base/'episodes'/ep['id']).exists()]
        if len(observed)!=1: raise Stop('D2 clearance requires the one frozen Claude attempt')
        ep=observed[0];p=base/'episodes'/ep['id'];terminal=read(p/'episode.json')
        if read(base/'STOP.json')['reason']!=terminal.get('fatal') or terminal.get('fatal')!='transport failure/uncertain start; never resend': raise Stop('D2 STOP/terminal mismatch')
        from od_usage import network_nonstart,record_nonstart
        if not network_nonstart(read(p/'raw.json')): raise Stop('D2 not the verified saved pre-generation failure')
        from od_core import render,reserve
        from od_contract import request
        from od_validation import accounting
        prompt=render(ep);bound=reserve(prompt)
        if read(p/'request.json')!={'episode':ep,'request':request(ep,prompt,bound),'prompt_sha256':sha(prompt.encode()),'reservation':bound}: raise Stop('D2 saved request drift')
        expected={'fleet':None,'schema_valid':False,'status':'ENVELOPE_FAILURE','reason':terminal['fatal'],'usage':accounting(read(p/'raw.json'),'claude'),'attempted':True,'first_frozen_compatibility_check':True,'fatal':terminal['fatal'],'finished_at':terminal['finished_at']}
        if terminal!=expected: raise Stop('D2 original terminal disagrees with saved failure')
        ledger=Ledger(base/'ledger.jsonl');timer=ActiveTime(base/'claude-time.jsonl',7200)
        if set(ledger.reservations)!={ep['id']} or ledger.settlements.get(ep['id'])!=0 or set(timer.holds)!=set(timer.settled) or ep['id'] not in timer.settled or timer.breaches: raise Stop('D2 settlement/time mismatch')
        if not (p/'nonstart.json').exists(): record_nonstart(p,terminal['finished_at'])
        c={'kind':'D2 verified transport nonstart STOP clearance','time':now(),'freeze_sha256':h,'stop_sha256':sha((base/'STOP.json').read_bytes()),'path':p.relative_to(base).as_posix(),'nonstart_sha256':sha((p/'nonstart.json').read_bytes()),'terminal_sha256':sha((p/'episode.json').read_bytes()),'prefixes':prefix_snapshot(base)}
        save(base/'envelope-stop-clearance.json',c);return c

def attest_d2(root=ROOT):
    root=Path(root);h=verify_d2(root);base=root/'collection'
    with lock(base):
        verify_baseline(root)
        if (base/'STOP.json').exists() and not clearance_valid(base): raise Stop('D2 requires recorded STOP clearance')
        from od_provenance import parent_receipt_gate
        parent_receipt_gate(root)
        from od_analysis import replay
        replay(root,base)
        p=base/'d2-attestation.json'
        if p.exists(): d2_gate(root);return read(p)
        record={'kind':'local D2 attestation; original push retained','freeze_sha256':h,'parents':read(root/'freeze-d2.json')['parents'],'parent_push_sha256':sha((base/'push.json').read_bytes()),'parent_attestation_sha256':sha((base/'d1-attestation.json').read_bytes()),'clearance_sha256':sha((base/'envelope-stop-clearance.json').read_bytes()),'prefixes':prefix_snapshot(base),'attested_at':now()}
        save(p,record);return record

def d2_gate(root):
    root=Path(root);base=root/'collection';a=read(base/'d2-attestation.json');f=read(root/'freeze-d2.json')
    if a['freeze_sha256']!=sha((root/'freeze-d2.json').read_bytes()) or a['parents']!=f['parents'] or a['parent_push_sha256']!=sha((base/'push.json').read_bytes()) or a['parent_attestation_sha256']!=sha((base/'d1-attestation.json').read_bytes()) or a['clearance_sha256']!=sha((base/'envelope-stop-clearance.json').read_bytes()): raise Stop('D2 attestation binding mismatch')
    if timestamp(a['attested_at'])<=timestamp(f['created_at']): raise Stop('D2 attestation predates freeze')
    verify_prefixes(base,a['prefixes']);verify_baseline(root)
    if not clearance_valid(base): raise Stop('D2 STOP clearance invalid')
    return timestamp(a['attested_at'])
