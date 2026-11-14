"""D3c's narrowly bound harness STOP clearance and forward-only provenance."""
from pathlib import Path
from trl_core import sha, canonical
from trl_io import Stop, now, read, save, timestamp
from trl_d3 import LEDGERS, _preserved, verify_prefix, recover_prefix

CLEARANCE = 'deviations/d3c/clearance.json'
DISPOSITION = 'deviations/d3c/disposition.json'
EPISODE = 'claude-s000-central'
STOP_NAME = 'STOP-d3b.json'


def clearance(root):
    from trl_d3 import clearance as prior_clearance
    root = Path(root)
    c = read(root/CLEARANCE)
    prior = prior_clearance(root)
    if (c.get('deviation')!='D3c' or c.get('episode_id')!=EPISODE or
        c.get('disposition')!='SCORED_NO_RERUN' or c.get('stop_name')!=STOP_NAME or
        c.get('cleared_episodes')!=prior['cleared_episodes']+[EPISODE] or
        c.get('d3_clearance_sha256')!=sha((root/'deviations/d3/clearance.json').read_bytes()) or
        c.get('disposition_sha256')!=sha((root/DISPOSITION).read_bytes()) or
        not isinstance(c.get('reviewer'),str) or not c['reviewer'].strip() or
        not isinstance(c.get('reason'),str) or not c['reason'].strip() or
        timestamp(c['recorded_at'])<timestamp(read(root/'collection'/STOP_NAME)['time'])):
        raise Stop('invalid D3c clearance')
    _preserved(root,c)
    d = read(root/DISPOSITION)
    for name,digest in d['preserved_files'].items():
        if c['preserved_files'].get(name)!=digest:
            raise Stop('D3c disposition evidence mismatch: '+name)
    return c


def record_clearance(root,reviewer,reason):
    """Under collector lock, record this reviewed defect only; never alter evidence."""
    from trl_d3 import clearance as prior_clearance
    from trl_freeze import D3C_FREEZE_SHA256, d3c_scope
    from trl_validation import validate
    from trl_analysis import replay
    from trl_budget import Ledger
    root = Path(root)
    if (root/CLEARANCE).exists():
        raise FileExistsError(CLEARANCE+' is create-once')
    if not reviewer.strip() or not reason.strip():
        raise Stop('named reviewer and reason required')
    if sha((root/'freeze-d3c.json').read_bytes())!=D3C_FREEZE_SHA256:
        raise Stop('D3c freeze identity mismatch')
    d3c_scope(root,read(root/'freeze-d3c.json'))
    prior = prior_clearance(root)
    d = read(root/DISPOSITION)
    if sha((root/DISPOSITION).read_bytes())!=read(root/'freeze-d3c.json')['files'][DISPOSITION]:
        raise Stop('D3c frozen disposition changed')
    for name,digest in d['preserved_files'].items():
        if name in LEDGERS:
            recover_prefix(root,name,digest)
        elif (root/name).is_symlink() or sha((root/name).read_bytes())!=digest:
            raise Stop('D3c disposition evidence changed: '+name)
    directory = root/'collection/episodes'/EPISODE
    terminal = read(directory/'episode.json')
    contract = read(root/'collection/claude-contract.json')
    raw = read(directory/'r1-j0.raw.json')
    value,env,u = validate(raw,'claude',3,read(directory/'r1-j0.request.json')['reservation'])
    row = replay(terminal['episode'],directory)
    if (read(root/'collection'/STOP_NAME)['reason']!='unexpected real tool/subagent activity' or
        terminal.get('fatal') is not True or terminal.get('complete') is not False or
        contract.get('status')!='FAIL' or contract.get('call_id')!=EPISODE+'-r1-j0' or
        contract.get('raw_sha256')!=sha(canonical(raw).encode()) or
        value!=d['saved_action'] or d.get('disposition')!='SCORED_NO_RERUN' or
        row['Y']!=0 or row['H']!=0 or row['coverage']!=0 or row['calls']!=1 or row['complete']):
        raise Stop('D3c known harness failure does not replay')
    ledger = Ledger(root/'collection/cost.jsonl')
    if (ledger.stopped or any(ledger.holds.values()) or
        ledger.settled.get(EPISODE+'-r1-j0',{}).get('actual')!=d['settled_micro_usd']):
        raise Stop('D3c cannot clear budget uncertainty or an open hold')
    dirs = sorted(p.name for p in (root/'collection/episodes').iterdir() if p.is_dir())
    cleared = prior['cleared_episodes']+[EPISODE]
    if (dirs!=sorted(p.parent.name for p in (root/'collection/episodes').glob('*/episode.json')) or
        any(read(root/'collection/episodes'/n/'episode.json').get('fatal') for n in dirs if n not in cleared)):
        raise Stop('D3c cannot clear partial or other fatal episodes')
    if {p.name for p in (root/'collection').glob('STOP*.json')}!={'STOP.json','STOP-d2.json',STOP_NAME}:
        raise Stop('D3c unexpected durable STOP')
    files = {}
    for p in sorted((root/'collection').rglob('*')):
        if p.is_symlink():
            raise Stop('symlink collection evidence')
        if p.is_file() and not p.name.endswith('.lock'):
            files[p.relative_to(root).as_posix()] = sha(p.read_bytes())
    value = {'deviation':'D3c','recorded_at':now(),'reviewer':reviewer,'reason':reason,
        'episode_id':EPISODE,'stop_name':STOP_NAME,'cleared_episodes':cleared,
        'disposition':'SCORED_NO_RERUN','d3_clearance_sha256':sha((root/'deviations/d3/clearance.json').read_bytes()),
        'disposition_sha256':sha((root/DISPOSITION).read_bytes()),'terminal_episodes':dirs,
        'preserved_files':files,'ledger_prefixes':{
            n:{'bytes':(root/n).stat().st_size,'sha256':h} for n,h in files.items() if n in LEDGERS}}
    # A disposition may bind an earlier ledger prefix, rather than the whole current ledger.
    for n,h in d['preserved_files'].items():
        if n in LEDGERS:
            value['preserved_files'][n]=h
            value['ledger_prefixes'][n]=recover_prefix(root,n,h)
    _preserved(root,value)
    save(root/CLEARANCE,value)
    return clearance(root)


def is_cleared_stop(root,p):
    root = Path(root)
    if not (root/CLEARANCE).exists() or p.name!=STOP_NAME:
        return False
    c = clearance(root)
    return c['preserved_files'].get('collection/'+p.name)==sha(p.read_bytes())


def stop_gate(root):
    from trl_d3b import pause_if_needed, pause_gate, stop_paths
    root = Path(root)
    c = clearance(root)
    allowed = {'STOP.json','STOP-d2.json'}|{p.name for p in stop_paths(root)}
    if any(p.name not in allowed for p in (root/'collection').glob('STOP*.json')):
        raise Stop('uncleared durable integrity STOP exists')
    pause_if_needed(root)
    pause_gate(root)
    return c


def provenance_layers(root,active):
    from trl_d3b import provenance_layers as prior_layers
    root = Path(root)
    c = clearance(root)
    starts = {p.relative_to(root).as_posix() for p in (root/'collection/episodes').glob('*/*.start.json')}
    prior = starts & set(c['preserved_files'])
    layers = prior_layers(root,'freeze-d3b.json')
    # D3b owns only starts preserved at clearance, never starts' self-reported hashes.
    layers[-1] = (*layers[-1][:2],layers[-1][2] & prior)
    layers.append(('freeze-d3c.json','-d3c',set() if active=='freeze-d3d.json' else starts-prior))
    if active=='freeze-d3d.json':
        layers.append(('freeze-d3d.json','-d3d',starts-prior))
    return layers


def prepush_gate(root,name):
    c = clearance(root)
    if any(p.relative_to(root).as_posix() not in c['preserved_files']
           for p in (Path(root)/'collection/episodes').glob('*/*.start.json')):
        raise Stop(name+' attestation must precede all new starts')
    return c
