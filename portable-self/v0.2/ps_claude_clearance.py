"""Offline, exact-evidence clearance of the reviewed Claude identity-check bug."""
from pathlib import Path
import os
from ps_core import sha
from ps_io import Stop, Ledger, Journal, read, save, lock, now, syncdir
from ps_transport import definite_api_nonstart

REV='revisions/claude-envelope'
EP='claude-00-different-stable-discard'
RECEIPT='clearance-claude-envelope.json'
ARCHIVED_STOP='STOP-cleared-claude-envelope.json'


def inspect(root,base,ledger):
    """No mutation; all original evidence, seals and anchored prefixes must match."""
    root=Path(root);base=Path(base);before=read(root/REV/'before.json')
    for item in before['journals']:
        journal=Journal(base/item['path']);n=item['prefix_bytes']
        if len(journal.raw)<n or sha(journal.raw[:n])!=item['prefix_sha256']:
            raise Stop('clearance historical journal prefix changed')
    directory=base/'episodes'/EP
    for name,digest in before['episode_files'].items():
        if sha((directory/name).read_bytes())!=digest: raise Stop('clearance episode evidence changed')
    if ledger.sealed.get(EP)!=sha((directory/'episode.json').read_bytes()): raise Stop('clearance terminal seal mismatch')
    raw=read(directory/'0.raw.json');start=read(directory/'0.start.json')
    if not definite_api_nonstart(raw): raise Stop('clearance requires saved definite DNS non-start')
    if (ledger.settled.get(start['id'])!=0 or set(ledger.started)-set(ledger.settled) or
        start['request_sha256']!=sha((directory/'0.request.json').read_bytes()) or
        sha(ledger.journal.raw[:start['ledger_prefix_bytes']])!=start['ledger_prefix_sha256']):
        raise Stop('clearance paid allocation/prefix mismatch')
    if read(directory/'0.parsed.json')['error']!='frontier identity mismatch': raise Stop('different stopping disposition')
    return before


def audit_clearances(root,base,ledger):
    root=Path(root);base=Path(base)
    if not ledger.clearances:
        if (base/RECEIPT).exists(): raise Stop('unregistered clearance; run clear-claude-stop to recover')
        return []
    if len(ledger.clearances)!=1: raise Stop('unexpected additional stop clearance')
    event=ledger.clearances[0];path=base/RECEIPT;record=read(path)
    if event.get('clearance_file')!=RECEIPT or sha(path.read_bytes())!=event['clearance_sha256']:
        raise Stop('clearance receipt binding changed')
    before=inspect(root,base,ledger)
    if (record['freeze_sha256']!=sha((root/'freeze-claude-envelope.json').read_bytes()) or
        record['before_sha256']!=sha((root/REV/'before.json').read_bytes()) or
        record['stop_sha256']!=before['stop_sha256'] or record['stop_seq']!=event['stop_seq'] or
        record['stop_seq']!=before['journals'][0]['events']-1 or
        record['classification']!='HARNESS BUG' or record['replay_permitted'] is not False):
        raise Stop('clearance provenance changed')
    stop=ledger.journal.rows[event['stop_seq']]
    if stop['event']!='stop' or stop['reason']!='frontier identity mismatch': raise Stop('different STOP cannot be cleared')
    if sha((base/ARCHIVED_STOP).read_bytes())!=record['stop_sha256']: raise Stop('archived STOP changed')
    return [record]


def clear_stop(root):
    """Idempotent offline command. No dispatch, git, push, network or attestation."""
    root=Path(root);base=root/'collection'
    from ps_freeze import verify,active_manifest
    freeze_hash=verify(root)
    if active_manifest(root).name!='freeze-claude-envelope.json': raise Stop('reviewed successor freeze required')
    with lock(base):
        ledger=Ledger(base/'ledger.jsonl');before=inspect(root,base,ledger)
        path=base/RECEIPT;stop=base/'STOP.json';archive=base/ARCHIVED_STOP
        if not path.exists():
            if (not ledger.blocked or ledger.last_stop['seq']!=before['journals'][0]['events']-1 or
                ledger.last_stop['reason']!='frontier identity mismatch' or
                sha(stop.read_bytes())!=before['stop_sha256'] or archive.exists()):
                raise Stop('STOP differs from reviewed evidence')
            # Independent replay verifies every terminal, request, raw envelope,
            # allocation and time ledger before any clearance mutation.
            from ps_analysis import score,load_timing,audit_accounting
            timing=load_timing(base)
            audit_accounting(base,[score(ep,base,False,timing) for ep in read(root/'config/episodes.json')])
            save(path,{'classification':'HARNESS BUG','disposition':'definite pre-generation DNS error; terminal retained',
                'recorded_at':now(),'delegating_reviewer':'Claude','replay_permitted':False,'episode':EP,
                'freeze_sha256':freeze_hash,'before_sha256':sha((root/REV/'before.json').read_bytes()),
                'stop_sha256':before['stop_sha256'],'stop_seq':ledger.last_stop['seq']})
        record=read(path)
        if (record['freeze_sha256']!=freeze_hash or record['before_sha256']!=sha((root/REV/'before.json').read_bytes()) or
            record['stop_sha256']!=before['stop_sha256'] or record['classification']!='HARNESS BUG' or
            record['replay_permitted'] is not False or record['stop_seq']!=before['journals'][0]['events']-1):
            raise Stop('existing clearance does not match reviewed evidence')
        if not ledger.clearances:
            if not ledger.blocked or ledger.last_stop['seq']!=record['stop_seq']: raise Stop('different ledger stop')
            ledger.event(event='clear-stop',id='collection',stop_seq=record['stop_seq'],
                clearance_file=RECEIPT,clearance_sha256=sha(path.read_bytes()))
        if stop.exists():
            if sha(stop.read_bytes())!=record['stop_sha256'] or archive.exists(): raise Stop('STOP archive collision')
            # Same-directory rename preserves the original file bytes. The old
            # STOP remains evidence and a later independent STOP can use its name.
            os.rename(stop,archive);syncdir(base)
        audit_clearances(root,base,ledger)
        if EP not in ledger.finished: ledger.event(event='release',id=EP)
        return {'clearance':str(path),'blocked':ledger.blocked,'episode_replayed':False,'freeze_sha256':freeze_hash}
