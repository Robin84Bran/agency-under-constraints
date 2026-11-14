"""D3 append-only provenance and narrowly bound local transport STOP clearance."""
from pathlib import Path
from trl_core import sha
from trl_io import Stop, now, read, save

CLEARANCE = 'deviations/d3/clearance.json'
EPISODE = 'qwen1b-s024-central'
LEDGERS = {'collection/time-local.jsonl','collection/time-claude.jsonl','collection/cost.jsonl'}


def verify_prefix(root,name,record,expected_hash=None):
    root = Path(root)
    p = root/name
    if (name not in LEDGERS or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or
        type(record) is not dict or type(record.get('bytes')) is not int or record['bytes']<0 or
        (expected_hash is not None and record.get('sha256')!=expected_hash)):
        raise Stop('invalid preserved ledger prefix: '+name)
    raw = p.read_bytes()
    n = record['bytes']
    if (len(raw)<n or sha(raw[:n])!=record.get('sha256') or
        (n and raw[n-1:n]!=b'\n') or (raw and not raw.endswith(b'\n'))):
        raise Stop('preserved ledger prefix changed/torn: '+name)


def recover_prefix(root,name,digest):
    """Recover D2's absent length only from an exact hash match at a line boundary."""
    raw = (Path(root)/name).read_bytes()
    matches = [n for n in [0]+[i+1 for i,b in enumerate(raw) if b==10] if sha(raw[:n])==digest]
    if len(matches)!=1:
        raise Stop('cannot recover unique preserved ledger prefix: '+name)
    record = {'bytes':matches[0],'sha256':digest}
    verify_prefix(root,name,record,expected_hash=digest)
    return record


def _preserved(root,c):
    root = Path(root)
    if set(c['ledger_prefixes'])!=set(c['preserved_files']) & LEDGERS:
        raise Stop('D3 ledger prefix inventory mismatch')
    for n,h in c['preserved_files'].items():
        p = root/n
        if n in LEDGERS:
            verify_prefix(root,n,c['ledger_prefixes'][n],expected_hash=h)
        elif (not n.startswith('collection/') or '..' in Path(n).parts or p.is_symlink() or
              not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h):
            raise Stop('D3 preserved evidence changed: '+n)
    for d in c['terminal_episodes']:
        actual = {p.relative_to(root).as_posix() for p in (root/'collection/episodes'/d).rglob('*') if p.is_file()}
        expected = {n for n in c['preserved_files'] if n.startswith('collection/episodes/'+d+'/')}
        if actual!=expected:
            raise Stop('D3 historical episode received additional evidence')


def clearance(root):
    from trl_d2 import clearance as d2_clearance, CLEARANCE as D2_CLEARANCE, EPISODE as D2_EPISODE
    root = Path(root)
    c = read(root/CLEARANCE)
    if (c.get('deviation')!='D3' or c.get('episode_id')!=EPISODE or
        c.get('disposition')!='SCORED_NO_RERUN' or
        c.get('cleared_episodes')!=[D2_EPISODE,EPISODE] or
        c.get('d2_clearance_sha256')!=sha((root/D2_CLEARANCE).read_bytes())):
        raise Stop('invalid D3 clearance')
    _preserved(root,c)
    d2 = read(root/D2_CLEARANCE)
    if set(c['d2_ledger_prefixes'])!=set(d2['preserved_files']) & LEDGERS:
        raise Stop('D2 ledger prefix inventory mismatch')
    d2_clearance(root,c['d2_ledger_prefixes'])
    return c


def record_clearance(root):
    """Offline only, under collector lock. Never rewrites a terminal or STOP."""
    from trl_d2 import clearance as d2_clearance, CLEARANCE as D2_CLEARANCE, EPISODE as D2_EPISODE
    from trl_validation import validate, stdout, LocalTransportFailure
    from trl_analysis import replay
    from trl_budget import maximum
    from trl_core import strict_load
    root = Path(root)
    if (root/CLEARANCE).exists():
        raise FileExistsError(CLEARANCE+' is create-once')
    d2 = read(root/D2_CLEARANCE)
    prefixes = {n:recover_prefix(root,n,h) for n,h in d2['preserved_files'].items() if n in LEDGERS}
    d2_clearance(root,prefixes)
    directory = root/'collection/episodes'/EPISODE
    terminal = read(directory/'episode.json')
    raw = read(directory/'r1-j0.raw.json')
    env = strict_load(stdout(raw))
    if (read(root/'collection/STOP-d2.json')['reason']!='usage UNKNOWN' or
        terminal['error']!='usage UNKNOWN' or not terminal['fatal'] or
        env.get('done') is not False or env.get('eval_count') is not None or
        read(directory/'r1-j0.request.json')['request'].get('stream') is not False):
        raise Stop('D3 known stop evidence mismatch')
    try:
        validate(raw,'qwen1b',3,maximum('central'))
    except LocalTransportFailure:
        pass
    else:
        raise Stop('D3 stop is not a local transport failure')
    row = replay(terminal['episode'],directory)
    if (row['Y']!=0 or row['H']!=0 or row['calls']!=1 or row['complete'] or not row['attempted'] or
        row['unknown_usage_calls']!=1 or row['input_tokens'] is not None or row['output_tokens'] is not None):
        raise Stop('D3 disposition does not replay')
    dirs = sorted(p.name for p in (root/'collection/episodes').iterdir() if p.is_dir())
    if (dirs!=sorted(p.parent.name for p in (root/'collection/episodes').glob('*/episode.json')) or
        any(read(root/'collection/episodes'/d/'episode.json').get('fatal') for d in dirs if d not in (D2_EPISODE,EPISODE))):
        raise Stop('D3 cannot clear partial or other fatal episodes')
    if {p.name for p in (root/'collection').glob('STOP*.json')}!={'STOP.json','STOP-d2.json'}:
        raise Stop('D3 unexpected durable STOP')
    files = {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted((root/'collection').rglob('*'))
             if p.is_file() and p.name!='collector.lock'}
    scan = read(root/'deviations/d3/scan.json')
    if files!=scan['collection_files'] or any(v['accepted_done_not_true'] or v['accepted_usage_missing'] for v in scan['counts'].values()):
        raise Stop('D3 scan evidence changed or accepted incomplete reply')
    value = {'deviation':'D3','recorded_at':now(),'agreement':'Claude reviewer / Codex builder',
        'episode_id':EPISODE,'cleared_episodes':[D2_EPISODE,EPISODE],'disposition':'SCORED_NO_RERUN',
        'attempted_calls':1,'technical_opportunities':3,'missing_opportunities':9,'Y':0,'H':0,
        'input_tokens':None,'output_tokens':None,'usage_status':'UNKNOWN',
        'd2_clearance_sha256':sha((root/D2_CLEARANCE).read_bytes()),'d2_ledger_prefixes':prefixes,
        'terminal_episodes':dirs,'preserved_files':files,
        'ledger_prefixes':{n:{'bytes':(root/n).stat().st_size,'sha256':h} for n,h in files.items() if n in LEDGERS},
        'reason':'Clear only the bound local incomplete-envelope STOP; retain all bytes and fatal flags. Usage remains UNKNOWN.'}
    _preserved(root,value)
    save(root/CLEARANCE,value)
    return clearance(root)


def stop_gate(root):
    root = Path(root)
    c = clearance(root)
    if any(p.name not in ('STOP.json','STOP-d2.json') for p in (root/'collection').glob('STOP*.json')):
        raise Stop('uncleared durable STOP exists')
    return c


def provenance_layers(root,active):
    """Partition starts by preserved evidence, never by trusting a start's claimed hash."""
    root = Path(root)
    starts = {p.relative_to(root).as_posix() for p in (root/'collection/episodes').glob('*/*.start.json')}
    if active=='freeze-d3.json':
        c = clearance(root)
        d2 = read(root/'deviations/d2/clearance.json')
        old = starts & set(d2['preserved_files'])
        prior = starts & set(c['preserved_files'])
        return [('freeze-d1.json','',old),('freeze-d2.json','-d2',prior-old),('freeze-d3.json','-d3',starts-prior)]
    if active=='freeze-d2.json':
        from trl_d2 import clearance as d2_clearance
        c = d2_clearance(root)
        old = starts & set(c['preserved_files'])
        return [('freeze-d1.json','',old),('freeze-d2.json','-d2',starts-old)]
    return [(active,'',starts)]


def scan(root):
    """Inventory all saved local raw replies; never invokes a transport or analysis."""
    from collections import Counter
    from trl_core import strict_load
    from trl_validation import stdout, usage
    root = Path(root)
    keys = ('raw_envelopes','done_not_true','usage_missing','accepted','accepted_done_not_true',
            'accepted_usage_missing','request_stream_not_false','decode_errors','parsed_missing')
    counts = {a:Counter(dict.fromkeys(keys,0)) for a in ('qwen7b','llama8b','qwen1b')}
    anomalies = []
    for p in sorted((root/'collection/episodes').glob('*/*.raw.json')):
        actor = p.parent.name.split('-')[0]
        if actor not in counts:
            continue
        c = counts[actor]
        c['raw_envelopes'] += 1
        try:
            e = strict_load(stdout(read(p)))
            done = type(e) is dict and e.get('done') is True
            known = usage(e,actor) is not None
        except (ValueError,KeyError,TypeError,UnicodeError):
            e,done,known = {},False,False
            c['decode_errors'] += 1
        parsedpath = p.with_name(p.name.replace('.raw.json','.parsed.json'))
        parsed = read(parsedpath) if parsedpath.exists() else None
        c['parsed_missing'] += parsed is None
        accepted = parsed is not None and parsed.get('error') is None
        c['done_not_true'] += not done
        c['usage_missing'] += not known
        c['accepted'] += accepted
        c['accepted_done_not_true'] += accepted and not done
        c['accepted_usage_missing'] += accepted and not known
        req = read(p.with_name(p.name.replace('.raw.json','.request.json')))['request']
        c['request_stream_not_false'] += req.get('stream') is not False
        if not done or not known:
            anomalies.append({'path':p.relative_to(root).as_posix(),'raw_sha256':sha(p.read_bytes()),
                'done':e.get('done') if type(e) is dict else None,'usage':usage(e,actor),'accepted':accepted,
                'parsed_error':parsed.get('error') if parsed else None,'request_stream':req.get('stream')})
    return {'scanned_at':now(),'scope':'every saved collection/episodes local *.raw.json; no fake/build data',
        'counts':{a:dict(c) for a,c in counts.items()},'anomalies':anomalies,
        'collection_files':{p.relative_to(root).as_posix():sha(p.read_bytes())
            for p in sorted((root/'collection').rglob('*')) if p.is_file() and p.name!='collector.lock'},
        'model_calls':0,'network_calls':0}


if __name__=='__main__':
    import argparse
    from trl_core import ROOT
    p = argparse.ArgumentParser()
    p.add_argument('command',choices=['scan'])
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    value = scan(a.root)
    save(a.out,value)
    print(value['counts'])
