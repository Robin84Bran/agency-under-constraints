"""Offline admission/reconciliation; no provider imports."""
from pathlib import Path
from trl_core import sha
from trl_io import Stop, read
from trl_journal import Journal, verify_prefix
from trl_replay import inspect
from trl_budget import ActiveTime

def evidence_gate(root):
    root=Path(root);base=root/'collection';journal=Journal(base/'dispatch.jsonl')
    if journal.open: raise Stop('unsettled/uncertain dispatch; no resend')
    # Prefix checks protect history; the original time reader validates the entire tail.
    clock=ActiveTime(base/'time-local.jsonl',43200)
    if clock.used>43200: raise Stop('active-time ledger exceeds resource cap')
    order=read(root/'config/episodes.json');known={e['id'] for e in order}
    if any(d.name not in known for d in (base/'episodes').glob('*')): raise Stop('unplanned episode evidence')
    starts=[e for e in journal.events if e['event']=='start']; finishes={e['id']:e for e in journal.events if e['event']=='finish'}
    actual={p.parent.relative_to(base).as_posix() for p in (base/'episodes').rglob('start.json')}
    if {e['path'] for e in starts}!=actual: raise Stop('journal/start inventory mismatch')
    for e in starts:
        if e['episode'] not in known or not e['path'].startswith('episodes/'+e['episode']+'/calls/') or '..' in Path(e['path']).parts or Path(e['path']).is_absolute(): raise Stop('unplanned/unsafe journal path')
        p=base/e['path'];f=finishes[e['id']]
        for n,h in (('request.json',e['request_sha256']),('start.json',e['start_sha256']),('raw.json',f['raw_sha256']),('parsed.json',f['parsed_sha256'])):
            if sha((p/n).read_bytes())!=h: raise Stop('dispatch evidence changed')
        if (read(p/'start.json')['id']!=e['id'] or read(p/'start.json')['kind']!=e['kind'] or
            read(p/'parsed.json')['classification']!=f['classification']): raise Stop('dispatch start id changed')
    for checkpoint in (e for e in journal.events if e['event']=='checkpoint'):
        if checkpoint['ledger']!='collection/time-local.jsonl': raise Stop('unknown checkpoint ledger')
        verify_prefix(root/checkpoint['ledger'],checkpoint['prefix'])
    for p in base.glob('STOP*.json'): raise Stop('durable STOP exists: '+p.name)
    for ep in read(root/'config/episodes.json'):
        d=base/'episodes'/ep['id']
        if not d.exists(): continue
        sim,calls,next_,used=inspect(ep,d)
        all_paths={p.parent for p in (d/'calls').rglob('request.json')}
        if used!=all_paths: raise Stop('extra/post-terminal calls')
        if (d/'episode.json').exists():
            from trl_analysis import replay
            replay(ep,d)
        elif next_ is None or not next_[-1]: raise Stop('partial episode cannot resume')
    return journal

