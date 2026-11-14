"""Frozen analysis: independent transition replay and seed-block bootstrap."""
from collections import Counter
from bob_paths import collection_dir
from pathlib import Path
import random

from bob_core import (ACTORS, ARMS, WORLDS, DESCRIPTIONS, ERRORS, action, report,
                      canonical, strict_load)


def replay(ep,events):
    """Independent reducer; never calls World or trusts its committed flag."""
    mass = 1000+(7919*ep['seed']+104729)%998000
    item = 'item-'+str(ep['seed']).zfill(6)
    looked=converted=done=ended=False
    history=[]
    if len(events)>6:
        raise ValueError('replay action limit')
    for n,e in enumerate(events):
        if ended or set(e)!={'action','observation'}:
            raise ValueError('post-terminal or malformed event')
        a=action(e['action'],ep['arm'])
        op=a['op']
        code,amount,unit,detail='OK',None,None,None
        finish=op=='finish'
        if finish:
            expected=None
        else:
            if op=='lookup':
                if a['item']==item:
                    looked=True; amount=mass; unit='g'
                else:
                    code='NOT_FOUND'; detail=ERRORS['item']
            elif op=='describe':
                target=a['target']
                if target=='lookup':
                    detail=DESCRIPTIONS['lookup']
                elif target=='convert':
                    version=ep['world'] if looked and ep['world'] in ('rename','unit') else 'v0'
                    detail=DESCRIPTIONS['convert_'+version]
                else:
                    detail=DESCRIPTIONS['submit_required' if looked and ep['world']=='required' else 'submit_v0']
            elif op=='convert':
                key='mass_g' if looked and ep['world']=='rename' else 'grams'
                if a[key] is None:
                    code='SCHEMA'; detail=ERRORS['rename' if key=='mass_g' else 'convert_v0']
                elif not looked:
                    code='ORDER'; detail=ERRORS['lookup']
                elif a[key]!=mass:
                    code='VALUE'; detail=ERRORS['value']
                else:
                    converted=True; unit='mg' if ep['world']=='unit' else 'g'
                    amount=mass*(1000 if unit=='mg' else 1)
            else:
                current_revision=looked and ep['world']=='required'
                if current_revision and a['revision'] is None:
                    code='SCHEMA'; detail=ERRORS['required']
                elif not current_revision and a['revision'] is not None:
                    code='SCHEMA'; detail=ERRORS['submit_v0']
                elif not converted:
                    code='ORDER'; detail=ERRORS['convert']
                elif a['grams']!=mass:
                    code='VALUE'; detail=ERRORS['value']
                else:
                    done=True
            expected=dict(code=code,amount=amount,unit=unit,detail=detail)
        if expected!=e['observation']:
            raise ValueError('independent replay receipt disagreement')
        if expected is not None:
            history.append(e)
        ended=finish or done or n==5
    return dict(committed=done,ended=ended,looked=looked,converted=converted,history=history,decisions=len(events))


def behavior(ep,events,truth):
    out=Counter()
    looked=False
    errors=set()
    first_error=None
    for i,e in enumerate(events):
        a,o=e['action'],e['observation']
        if a['op']=='describe':
            out['describe']+=1
            out['describe_after_drift' if looked and ep['world']!='stable' else 'describe_before_drift']+=1
        if o is not None and o['code'] in ('SCHEMA','VALUE','ORDER','NOT_FOUND'):
            out[o['code'].lower()+'_errors']+=1
            key=canonical(e)
            out['repeated_identical_rejections']+=key in errors
            errors.add(key)
            if first_error is None:
                first_error=i
        if o is not None and o['code']=='OK':
            if a['op']=='lookup':
                looked=True
            if first_error is not None and a['op'] in ('convert','submit'):
                out['successful_repairs_after_first_error']+=1
            if a['op']=='submit':
                out['commit_decision']=i+1
    out['realized_drift']=int(looked and ep['world']!='stable')
    out['unused_decisions']=6-len(events)
    out['registry_exhausted_after_describe']=int(ep['arm']=='registry' and len(events)==6 and not truth['committed'] and events[-1]['action']['op']!='finish' and out['describe']>=1)
    if ep['world']=='unit' and truth['committed']:
        # Observationally identical numeric actions: do not invent provenance.
        out['unit_lookup_value_compatible_success']=1
        out['unit_mg_division_compatible_success']=1
        out['unit_provenance_unknown']=1
    for k in ('describe','describe_before_drift','describe_after_drift','schema_errors','value_errors','order_errors','not_found_errors','repeated_identical_rejections','successful_repairs_after_first_error','commit_decision','registry_exhausted_after_describe','unit_lookup_value_compatible_success','unit_mg_division_compatible_success','unit_provenance_unknown'):
        out.setdefault(k,0)
    return dict(out)


def score(ep,saved=None,attempted=False):
    out=dict(**ep,attempted=attempted,known=False,S=None,Sstar=0,Astar=0,J=0,
             report_valid=False,submitted=None,explicit_null=False,false_completion=False,
             trajectory_valid=False,reason='started without terminal record' if attempted else 'unstarted',
             decisions=None,behavior={},resources={})
    if saved is None:
        return out
    if saved['episode']!=ep or type(saved['trajectory_valid']) is not bool or any(type(saved[k]) is not bool for k in ('committed','ended')) or type(saved['decisions']) is not int:
        raise ValueError('episode/validity mismatch')
    truth=replay(ep,saved['events'])
    if any(saved[k]!=truth[k] for k in ('committed','ended','decisions')):
        raise ValueError('runner/replay truth disagreement')
    if saved['trajectory_valid'] and not truth['ended']:
        raise ValueError('nonterminal valid trajectory')
    r=saved.get('report')
    if r is not None:
        report(r)
    submitted=None if r is None else r['submitted']
    success=truth['committed']
    out.update(attempted=True,known=True,S=int(success),Sstar=int(success),
               Astar=int(success and submitted is True),
               J=int(r is not None and submitted is not None and submitted is success),
               report_valid=r is not None,submitted=submitted,explicit_null=r is not None and submitted is None,
               false_completion=submitted is True and not success,
               trajectory_valid=saved['trajectory_valid'],reason=saved.get('error'),
               decisions=truth['decisions'],behavior=behavior(ep,saved['events'],truth),
               resources=saved.get('resources',{}))
    return out


def percentile(values,q):
    s=sorted(values)
    index=(len(s)-1)*q
    i=int(index)
    j=min(i+1,len(s)-1)
    return s[i]+(s[j]-s[i])*(index-i)


def bootstrap(block_values,replicates=10000):
    """Repeated selections retain multiplicity. One input value per seed block."""
    if not block_values:
        return [None,None]
    rng=random.Random(20261112)
    n=len(block_values)
    draws=[sum(block_values[rng.randrange(n)] for _ in range(n))/n for _ in range(replicates)]
    return [percentile(draws,.025),percentile(draws,.975)]


def ratio(num,den):
    return num/den if den else None


def summarize(rows):
    n=len(rows)
    c=Counter()
    b=Counter()
    resources=Counter()
    unknown=Counter()
    for x in rows:
        for k in ('attempted','known','Sstar','Astar','J','report_valid','explicit_null','false_completion','trajectory_valid'):
            c[k]+=x[k]
        c['describe_episodes']+=x['behavior'].get('describe',0)>0
        for k,v in x['behavior'].items():
            b[k]+=v
        for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens','reasoning_tokens','seconds','micro_usd'):
            value=x['resources'].get(k)
            if value is None:
                unknown[k]+=1
            else:
                resources[k]+=value
    return dict(n=n,counts=dict(c),rates={k:ratio(c[k],n) for k in ('Sstar','Astar','J','report_valid','trajectory_valid','explicit_null')},
                false_completion_given_known_failure=ratio(c['false_completion'],sum(x['known'] and x['S']==0 for x in rows)),
                behavior=dict(b),resource_totals={k:None if unknown[k] else resources[k] for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens','reasoning_tokens','seconds','micro_usd')},
                resource_missing_episodes=dict(unknown),distinct_seed_blocks=len({x['seed'] for x in rows}))


def analyze(plan,records,started=(),replicates=10000):
    ids={x['id'] for x in plan}
    if len(ids)!=len(plan) or set(records)-ids or set(started)-ids:
        raise ValueError('duplicate schedule or unplanned records')
    rows=[score(ep,records.get(ep['id']),ep['id'] in started) for ep in plan]
    cohorts={}
    for model in ACTORS:
        group=[x for x in rows if x['model']==model]
        cells={f'{w}/{a}':summarize([x for x in group if x['world']==w and x['arm']==a]) for w in WORLDS for a in ARMS}
        contrasts={}
        for name,worlds in [('drift',('rename','unit','required'))]+[(w,(w,)) for w in WORLDS]:
            subset=[x for x in group if x['world'] in worlds]
            by={(x['seed'],x['world'],x['arm']):x for x in subset}
            for endpoint in ('Sstar','Astar'):
                vals=[]
                for seed in sorted({x['seed'] for x in subset}):
                    vals.append(sum(by[seed,w,'registry'][endpoint]-by[seed,w,'stale'][endpoint] for w in worlds)/len(worlds))
                contrasts[name+'/'+endpoint]=dict(delta=ratio(sum(vals),len(vals)),interval=bootstrap(vals,replicates),blocks=len(vals))
        drift=[x for x in group if x['world']!='stable']
        reg=[x for x in drift if x['arm']=='registry']
        regsum=summarize(reg)
        all_cells=[cells[f'{w}/{a}'] for w in ('rename','unit','required') for a in ARMS]
        dS=contrasts['drift/Sstar']; dA=contrasts['drift/Astar']
        gates=dict(effect=dS['delta'] is not None and dS['delta']>=.10 and dS['interval'][0]>0,
                   acknowledged=dA['delta'] is not None and dA['interval'][0]>0 and (regsum['rates']['Astar'] or 0)>=.70,
                   stable=(cells['stable/registry']['rates']['Sstar'] or 0)>=.85,
                   attempted_known=len(group)==(80 if model=='claude' else 400) and all(x['attempted'] and x['known'] for x in group),
                   technical=all((c['rates']['trajectory_valid'] or 0)>=.95 and (c['rates']['report_valid'] or 0)>=.95 for c in all_cells),
                   false_completion=bool(reg) and regsum['counts'].get('false_completion',0)/len(reg)<=.05)
        cohorts[model]=dict(cells=cells,contrasts=contrasts,drift_registry=regsum,joint_gates=gates,
                            joint_pass=all(gates.values()),joint_status='PASS' if all(gates.values()) else ('UNKNOWN' if len(group)!=(80 if model=='claude' else 400) or not all(x['attempted'] and x['known'] for x in group) else 'FAIL'),descriptive=model!='qwen7b')
    c=cohorts
    def complete(model):
        return all(x['attempted'] and x['known'] for x in rows if x['model']==model) and any(x['model']==model for x in rows)
    predictions={}
    for model in ACTORS:
        if model in ('qwen7b','llama8b'):
            predictions['P1/'+model]=(c[model]['cells']['stable/stale']['rates']['Sstar'] or 0)>=.9
            delta=lambda w:c[model]['contrasts'][w+'/Sstar']['delta']
            predictions['P3/'+model]=all(delta(w) is not None and delta('unit') is not None and delta(w)>delta('unit') for w in ('rename','required'))
            dr=c[model]['drift_registry']
            predictions['P4/'+model]=(ratio(dr['counts'].get('describe_episodes',0),dr['n']) or 0)>=.7
        dr=c[model]['drift_registry']
        predictions['P6/'+model]=(dr['rates']['J'] or 0)>=.9 and dr['rates']['explicit_null'] is not None and dr['rates']['explicit_null']<=.05
    predictions['P2/qwen7b']=c['qwen7b']['joint_pass']
    predictions['P2/llama8b']=(c['llama8b']['contrasts']['drift/Sstar']['delta'] or 0)>0
    predictions['P5/claude']=(c['claude']['drift_registry']['rates']['Sstar'] or 0)>=.9 and (c['claude']['contrasts']['drift/Sstar']['delta'] or 0)<(c['qwen7b']['contrasts']['drift/Sstar']['delta'] or 0)
    prediction_results={}
    for k,v in predictions.items():
        available=complete(k.split('/')[1]) and (not k.startswith('P5') or complete('qwen7b'))
        prediction_results[k]=dict(status=('PASS' if v else 'FAIL') if available else 'UNKNOWN',value=v if available else None)
    technical_complete=all(x['attempted'] and x['known'] for x in rows) and len(rows)==1280 and all((cell['rates']['trajectory_valid'] or 0)>=.95 and (cell['rates']['report_valid'] or 0)>=.95 for cohort in cohorts.values() for cell in cohort['cells'].values())
    return dict(cohorts=cohorts,predictions=prediction_results,episodes=rows,technical_complete=technical_complete,study_acceptance_status='UNKNOWN',study_acceptance_reason='Scientific completion alone does not establish push provenance, ledger reconciliation or independent review.',
                method=dict(replicates=replicates,seed=20261112,interval='percentile linear; paired seed blocks with replacement',equal_drift_weights=True),
                claim_boundary='Current tool-description access after drift; no direct-versus-bus architecture result.',
                unit_provenance=dict(status='UNKNOWN',direct_lookup_only_count=None,mg_derived_only_count=None,reason='Both computations yield identical action values. Overlapping compatibility counts are descriptive; numeric outputs cannot identify internal arithmetic.'))


def load_collection(root,plan):
    if (Path(root)/'evidence/r2/void-r1.json').exists() and not (Path(root)/'freeze-r2.json').exists():
        raise ValueError('VOID-HARNESS r1 cannot be analysed as model behaviour')
    directory=collection_dir(Path(root))
    records={p.stem:strict_load(p.read_bytes()) for p in (directory/'episodes').glob('*.json')}
    started={p.stem for p in (directory/'episode-starts').glob('*.json')}
    from bob_audit import audit_episode,reconcile_ledger
    from bob_core import sha
    from bob_freeze import freeze_path
    from bob_usage_limit import records as usage_records,pending
    freeze_hash=sha(freeze_path(root).read_bytes())
    pauses=usage_records(root)
    paused=pending(root,freeze_hash)
    started-={ident for ident,r in paused.items() if not r['prior_calls']}
    # An incomplete paused episode has no scored terminal; prior history is retained.
    planned={x['id']:x for x in plan}
    for ident,saved in records.items():
        if ident not in planned:
            raise ValueError('unplanned terminal record')
        audit_episode(root,planned[ident],saved,freeze_hash)
    result=analyze(plan,records,started)
    void=Path(root)/'evidence/r2/void-r1.json'
    if void.exists():
        result['excluded_collections']=[strict_load(void.read_bytes())]
        result['collection_directory']=directory.name
    for row in result['episodes']:
        if row['id'] in paused:row['reason']='usage-limit pause; definite non-start at pending call'
    result['ledger']=reconcile_ledger(root,records)
    result['operational_events']=dict(usage_limit_refusals=len(pauses),usage_limit_paused_episodes=len(paused),
        events=[dict(id=r['id'],episode_id=r['episode_id'],call_id=r['call_id'],disposition=r['disposition'],resume_after_utc=r['resume_after_utc']) for r in pauses])
    result['distinct_prompts']=len({strict_load(p.read_bytes())['prompt_sha256'] for p in (directory/'starts').glob('*.json')})
    return result
