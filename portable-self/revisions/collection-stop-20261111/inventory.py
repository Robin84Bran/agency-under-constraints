"""Read-only v0.1 inventory/replay; outputs only to this amendment directory."""
from pathlib import Path
import sys, collections, datetime, json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from ps_core import sha
from ps_io import read, save
from ps_analysis import score, load_timing, audit_accounting
OUT=Path(__file__).resolve().parent

def snapshot():
    paths=list((ROOT/'collection').rglob('*'))
    paths.extend(ROOT/n for n in read(ROOT/'freeze-a1.json')['files'] if n not in ('DEVIATIONS.md','PROJECT_STATE.md'))
    paths.extend(ROOT/n for n in ('freeze.json','freeze-a1.json'))
    return {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(set(paths)) if p.is_file()}

if __name__=='__main__':
    before=snapshot();schedule=read(ROOT/'config/episodes.json');timing=load_timing(ROOT/'collection')
    rows=[score(ep,ROOT/'collection',False,timing) for ep in schedule]
    inventory=[]
    for row in rows:
        d=ROOT/'collection/episodes'/row['id']
        if not d.exists(): continue
        terminal=read(d/'episode.json') if (d/'episode.json').exists() else None
        inventory.append({**{k:row[k] for k in ('id','actor','seed','world','arm','calls_started','valid_calls','technical_complete','Y','F','known_wrong','nulls','technical_missing','facts')},
          'state':'terminal' if terminal else 'partial', 'terminal_error':terminal.get('error') if terminal else None,
          'file_count':len(list(d.iterdir())), 'unanswered_started_calls':[c['index'] for c in row['calls'] if c['raw_sha256'] is None]})
    audit=audit_accounting(ROOT/'collection',rows)
    after=snapshot()
    if before!=after: raise RuntimeError('v0.1 evidence changed during inventory')
    value={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'Claude',
      'note_reported_terminal_episodes':287,'note_reported_errors':{'invalid control':280,'invalid action keys/length':6},
      'observed_episode_directories':len(inventory),'observed_terminal_records':sum(x['state']=='terminal' for x in inventory),
      'observed_partial_records':sum(x['state']=='partial' for x in inventory),
      'whole_episode_technical_complete':sum(x['technical_complete'] for x in inventory),
      'terminal_errors':dict(collections.Counter(x['terminal_error'] for x in inventory if x['state']=='terminal')),
      'planned_episodes':len(schedule),'definitely_unstarted_episodes':sum(not x['attempted'] for x in rows),
      'discrepancy':'Reviewer note is a 287-episode observation; disk retains 288 terminal records and one partial. Exact timing of the extra terminal relative to process kill is UNKNOWN; no record is discarded.',
      'scoring':'Original ps_analysis.score, strict decoder and fixed denominators; missing/invalid actions are operational misses with factual correctness null. No rerun.',
      'accounting':audit,'episodes':inventory,'real_model_calls_by_inventory':0}
    save(OUT/'evidence-hashes.json',before)
    save(OUT/'inventory.json',value)
    save(OUT/'preservation-check.json',{'unchanged':True,'files':len(before),'hash_inventory_sha256':sha((OUT/'evidence-hashes.json').read_bytes())})
    print(json.dumps({k:v for k,v in value.items() if k!='episodes'},indent=2))
