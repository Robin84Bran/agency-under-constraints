"""Frozen, network-free raw-evidence replay and assigned-denominator analysis."""
import argparse
from collections import Counter,defaultdict
import datetime as dt
from pathlib import Path
from od_core import ROOT,ACTORS,render,reserve,payload,score,sha,canonical,schedule
from od_contract import request
from od_io import Stop,read,save,Ledger,Log,ActiveTime
from od_validation import validate,accounting,cost,ReplyFailure,TransportFailure
from od_stats import percentile,evaluate_sample
from od_usage import directories,attempt_id,episode_state,nonstart,verify_prefixes
import random


def replay(root,base,allow_fake=False,jobs=None):
    root=Path(root);base=Path(base)
    if not allow_fake:
        from od_freeze import verify
        active_hash=verify(root)
        if (root/'freeze-d1.json').exists():
            from od_d1 import verify_baseline
            verify_baseline(root)
    jobs=jobs if jobs is not None else read(root/'config/episodes.json')
    planned={e['id']:e for e in jobs}
    ledger=Ledger(base/'ledger.jsonl');by_id={};raw_usage={};fatal_by_id={};operational=[]
    attempts={attempt_id(e['id'],i):(e,p,i) for e in jobs for i,p in enumerate(directories(base,e['id']))}
    # Independently replay the ledger against raw costs and frozen reservations.
    for event in ledger.log.events:
        ident=event['id']
        if ident not in attempts or attempts[ident][0]['actor']!='claude': raise Stop('unexpected paid ledger identity')
        if event['event']=='reserve' and event['amount']!=reserve(render(attempts[ident][0]))['micro_usd']: raise Stop('reservation differs from frozen request')
        if event['event']=='settle':
            p=attempts[ident][1];raw=read(p/'raw.json');legacy=read(p/'start.json').get('revision')!='A1';u=accounting(raw,'claude',legacy=legacy)
            if u is None or event['actual']!=cost(u): raise Stop('ledger/raw settlement disagreement')
    timers={name:ActiveTime(base/(name+'-time.jsonl'),7200 if name=='claude' else 28800) for name in ('local','claude')}
    observed={p.name for p in (base/'episodes').iterdir()} if (base/'episodes').exists() else set()
    if not observed<=set(planned): raise Stop('unplanned episode evidence')
    # Validate every nonstart against its exact request, accounting and timer bytes.
    for aid,(ep,p,index) in attempts.items():
        marker=nonstart(p)
        if marker is None: continue
        if ep['actor']!='claude': raise Stop('nonstart attached to local episode')
        if aid not in timers['claude'].settled or ledger.settlements.get(aid)!=0: raise Stop('nonstart missing zero settlement/timer')
        if aid in timers['claude'].breaches: raise Stop('nonstart exceeded active time cap')
        record=read(p/'request.json');prompt=render(ep);bound=reserve(prompt);start=read(p/'start.json')
        if record!={'episode':ep,'request':request(ep,prompt,bound),'prompt_sha256':sha(prompt.encode()),'reservation':bound}: raise Stop('nonstart request drift')
        if start['id']!=ep['id']: raise Stop('nonstart identity mismatch')
        if not allow_fake:
            from od_provenance import start_gate
            start_gate(root,start)
        elif start['freeze_sha256']!='FAKE-OFFLINE': raise Stop('invalid fake nonstart')
        reservation=next(e for e in ledger.log.events if e['event']=='reserve' and e['id']==aid)
        if dt.datetime.fromisoformat(reservation['time'])>dt.datetime.fromisoformat(start['started_at']) or dt.datetime.fromisoformat(marker['finished_at'])<dt.datetime.fromisoformat(start['started_at']): raise Stop('nonstart chronology mismatch')
        if index:
            prior=nonstart(directories(base,ep['id'])[index-1])
            if prior is None or dt.datetime.fromisoformat(start['started_at'])<dt.datetime.fromisoformat(prior['reset_at']): raise Stop('usage resume before reset')
        operational.append(dict(marker,id=ep['id'],attempt_id=aid))
    paid_seen=False
    for ep in jobs:
        ident=ep['id'];p=base/'episodes'/ident
        if ident not in observed: continue
        if p.is_symlink() or any(x.is_symlink() for x in p.iterdir()): raise Stop('symlink evidence')
        p,events=episode_state(base,ident)
        if p is None: continue
        aid=attempt_id(ident,len(directories(base,ident))-1)
        if events and dt.datetime.fromisoformat(read(p/'start.json')['started_at'])<dt.datetime.fromisoformat(events[-1]['reset_at']): raise Stop('usage resume before reset')
        terminal=read(p/'episode.json');start=read(p/'start.json');record=read(p/'request.json');raw=read(p/'raw.json')
        legacy=start.get('revision')!='A1'
        if start.get('id')!=ident: raise Stop('start identity mismatch')
        timer=timers['claude' if ep['actor']=='claude' else 'local']
        if aid not in timer.holds or aid not in timer.settled: raise Stop('attempt lacks complete timer evidence')
        if start.get('freeze_sha256')=='FAKE-OFFLINE' and not allow_fake: raise Stop('fake evidence forbidden')
        if not allow_fake:
            if legacy: raise Stop('start freeze mismatch')
            from od_provenance import start_gate
            start_gate(root,start)
        prompt=render(ep);bound=reserve(prompt)
        if record!={'episode':ep,'request':request(ep,prompt,bound),'prompt_sha256':sha(prompt.encode()),'reservation':bound}: raise Stop('realized request drift')
        u=accounting(raw,ep['actor'],legacy=legacy);raw_usage[ident]=u
        fatal=None
        paid=ep['actor']=='claude'
        first=paid and not paid_seen
        if paid:
            paid_seen=True
            if aid not in ledger.reservations: raise Stop('paid start has no reservation')
            if u is None:
                fatal='unknown frontier usage/cost; full hold retained'
                if aid in ledger.settlements: raise Stop('unknown cost was released')
            else:
                if ledger.settlements.get(aid)!=cost(u): raise Stop('known usage unsettled')
                if cost(u)>bound['micro_usd'] or sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>bound['output_tokens']: fatal='frontier reservation/accounting overrun'
        try: decoded=validate(raw,ep['actor'],bound,legacy=legacy)
        except (Stop,ReplyFailure,TransportFailure) as exc:
            decoded={'fleet':None,'schema_valid':False,'status':'TRANSPORT_FAILURE' if isinstance(exc,TransportFailure) else 'REPLY_FAILURE' if isinstance(exc,ReplyFailure) else 'ENVELOPE_FAILURE','reason':str(exc),'usage':u}
            if isinstance(exc,Stop) or (legacy and paid and first): fatal=fatal or str(exc)
        if aid in timer.breaches: fatal=fatal or 'cumulative active time exceeded'
        expected=dict(decoded,attempted=True,first_frozen_compatibility_check=first,fatal=fatal)
        observed_terminal={k:v for k,v in terminal.items() if k!='finished_at'}
        if observed_terminal!=expected: raise Stop('terminal/raw replay disagreement: '+ident)
        if fatal and not (base/'STOP.json').exists(): raise Stop('fatal evidence lacks STOP')
        if dt.datetime.fromisoformat(terminal['finished_at'])<dt.datetime.fromisoformat(start['started_at']): raise Stop('finish predates start')
        by_id[ident]=decoded;fatal_by_id[ident]=fatal
        if paid:
            reservation=next(e for e in ledger.log.events if e['event']=='reserve' and e['id']==aid)
            if dt.datetime.fromisoformat(reservation['time'])>dt.datetime.fromisoformat(start['started_at']): raise Stop('start precedes reservation')
    if set(ledger.reservations)!={aid for aid,(ep,p,i) in attempts.items() if ep['actor']=='claude'}: raise Stop('orphan reservation/interrupted start')
    for cohort in (ACTORS[:3],('claude',)):
        gap=False;paused=False
        for e in jobs:
            if e['actor'] not in cohort: continue
            if e['id'] not in observed: gap=True
            else:
                if gap: raise Stop('attempted schedule is not a prefix')
                if paused: raise Stop('dispatch continued after usage-limit pause')
                paused=episode_state(base,e['id'])[0] is None
    if any(fatal_by_id.values()):
        # A fatal attempt must be the final attempted schedule item in its cohort.
        for cohort in (ACTORS[:3],('claude',)):
            stopped=False
            for e in jobs:
                if e['actor'] not in cohort or e['id'] not in by_id: continue
                if stopped: raise Stop('dispatch continued after fatal episode')
                stopped=bool(fatal_by_id[e['id']])
    if not allow_fake:
        from od_identity import verify_preflight
        for actor in {e['actor'] for e in jobs if e['id'] in observed}:
            records=sorted((base/'preflight'/actor).glob('*.json'))
            if not records: raise Stop('missing preflight evidence')
            for p in records:
                value=read(p);verify_preflight(root,actor,value)
                if value!=read(records[0]): raise Stop('retained runtime drift')
    stop_reason=read(base/'STOP.json')['reason'] if (base/'STOP.json').exists() else None
    from od_recovery import transport_pause
    for cohort in ('local','claude'):
        pause=transport_pause(base,jobs,cohort)
        if pause and not (base/'STOP.json').exists(): raise Stop('transport threshold lacks durable STOP')
    if not allow_fake and (paid_seen or operational) and any(e['actor']!='claude' and e['id'] not in by_id for e in jobs): raise Stop('frontier evidence precedes complete locals')
    rows=[]
    for ep in jobs:
        d=by_id.get(ep['id']);valid=bool(d and d['schema_valid']);n=d['fleet'] if valid else None
        rows.append(dict(ep,fleet=n,choice_status=d['status'] if d else 'UNKNOWN',reason=d.get('reason') if d else 'unstarted assigned episode'+('; collector STOP: '+stop_reason if stop_reason else ''),attempted=d is not None,schema_valid=valid,usage=raw_usage.get(ep['id']),**score(ep,n,valid)))
    accounting_result={'spent_micro_usd':ledger.spent,'open_holds_micro_usd':sum(ledger.holds.values()),'cash_billing_usd':None,'ledger_events':len(ledger.log.events),'active_seconds':{name:t.charged for name,t in timers.items()}}
    if operational or (not allow_fake and (root/'freeze-d1.json').exists()): accounting_result['operational_events']={'usage_limit_refusals':len(operational),'events':operational}
    return rows,accounting_result


def interval(block_values):
    if not block_values: return None
    rng=random.Random(20261112);n=len(block_values)
    draws=[sum(rng.choices(block_values,k=n))/n for _ in range(10000)]
    return [percentile(draws,.025),percentile(draws,.975)]


def contrast(rows,actor,mode,complete_only=False):
    subset=[r for r in rows if r['actor']==actor and r['mode']==mode]
    cells={(r['block'],r['door'],r['evidence']):r for r in subset}
    blocks=sorted({r['block'] for r in subset});dr=[];do=[];discord=Counter();pairs=[]
    for b in blocks:
        rr=[];oo=[]
        for B in (1,6,24):
            a=cells.get((b,B,'rules'));z=cells.get((b,B,'rehearsal'))
            if a is None or z is None: continue
            if complete_only and not (a['schema_valid'] and z['schema_valid']): continue
            rr.append(a['regret']-z['regret']);oo.append(z['optimal']-a['optimal'])
            discord[f"{a['optimal']}->{z['optimal']}"]+=1
            pairs.append({'block':b,'door':B,'rules_fleet':a['fleet'],'rehearsal_fleet':z['fleet'],'rules_optimal':a['optimal'],'rehearsal_optimal':z['optimal']})
        if rr: dr.append(sum(rr)/len(rr));do.append(sum(oo)/len(oo))
    rehearsal=[r for r in subset if r['evidence']=='rehearsal']
    return {'blocks':len(dr),'pairs':len(pairs),'D_R':sum(dr)/len(dr) if dr else None,'D_O':sum(do)/len(do) if do else None,
      'D_R_interval':interval(dr),'D_O_interval':interval(do),'rehearsal_optimal_rate':sum(r['optimal'] for r in rehearsal)/len(rehearsal) if rehearsal else None,
      'choice_discordance':dict(discord),'paired_choices':pairs,'complete_valid_pair_sensitivity':complete_only}


def technical_gates(rows,summaries):
    gates={}
    for actor in ACTORS:
        rs=[r for r in rows if r['actor']==actor]
        assigned=120 if actor=='claude' else 1200
        complete=len(rs)==assigned and all(r['attempted'] for r in rs)
        relevant=[v for k,v in summaries.items() if k.startswith(actor+'/')]
        cells_ok=all(v['schema_valid']/v['assigned']>=(.90 if actor=='claude' else .95) for v in relevant) if relevant else None
        overall=sum(r['schema_valid'] for r in rs)/len(rs) if rs else None
        gates[actor]={'assigned':len(rs),'registered':assigned,'complete':complete,'cell_validity':cells_ok,'overall_validity':overall,
          'status':'UNKNOWN' if not complete else 'PASS' if cells_ok and overall>=.95 else 'FAIL'}
    return gates


def analyze_rows(rows):
    contrasts={f'{a}/{m}':contrast(rows,a,m) for a in ACTORS for m in ('independent','common') if any(r['actor']==a and r['mode']==m for r in rows)}
    cells=defaultdict(list)
    for r in rows: cells[f"{r['actor']}/door{r['door']}/{r['mode']}/{r['evidence']}"].append(r)
    summaries={}
    for key,rs in cells.items():
        us=[r['usage'] for r in rs if r['usage'] is not None]
        known=[r for r in rs if r['fleet'] is not None and r['schema_valid']]
        summaries[key]={'assigned':len(rs),'attempted':sum(r['attempted'] for r in rs),'schema_valid':sum(r['schema_valid'] for r in rs),
          'null':sum(r['schema_valid'] and r['fleet'] is None for r in rs),'technical':sum(r['attempted'] and not r['schema_valid'] for r in rs),
          'unstarted':sum(not r['attempted'] for r in rs),'choices':dict(Counter(str(r['fleet']) for r in known)),
          **{k:sum(r[k] for r in rs)/len(rs) for k in ('regret','optimal','operational_value')},
          **{k:sum(r[k] for r in known)/len(known) if known else None for k in ('chosen_value','chosen_work','chosen_outage')},
          'known_usage_calls':len(us),'input_tokens':sum(sum(u[k] for k in ('input','cache_read','cache_creation')) for u in us) if us else None,
          'output_tokens':sum(u['output'] for u in us) if us else None,'usage_complete':len(us)==len(rs),
          'failure_reasons':dict(Counter(r['reason'] for r in rs if r['attempted'] and not r['schema_valid'])),
          'cache_read_input_tokens':sum(u['cache_read'] for u in us) if us else None,'cache_creation_input_tokens':sum(u['cache_creation'] for u in us) if us else None,
          'api_equivalent_micro_usd':sum(cost(u) for u in us) if us and rs[0]['actor']=='claude' else 0 if rs[0]['actor']!='claude' else None,
          'reported_micro_usd':sum(u['reported_cost_micro_usd'] for u in us) if us and rs[0]['actor']=='claude' else None}
    primary=[r for r in rows if r['actor']=='qwen7b' and r['mode']=='independent'];p=contrasts.get('qwen7b/independent')
    complete=len(primary)==600 and all(r['attempted'] for r in primary)
    valid_cells=all(sum(r['schema_valid'] for r in primary if r['door']==B and r['evidence']==e)>=95 for B in (1,6,24) for e in ('rules','rehearsal')) if len(primary)==600 else False
    nulls=sum(r['schema_valid'] and r['fleet'] is None for r in primary if r['evidence']=='rehearsal')
    components={'all_600_attempted':complete,'validity_per_cell':valid_cells,'D_R_at_least_005':bool(p and p['D_R'] is not None and p['D_R']>=.05),
       'D_R_lower_positive':bool(p and p['D_R_interval'] and p['D_R_interval'][0]>0),'D_O_lower_positive':bool(p and p['D_O_interval'] and p['D_O_interval'][0]>0),
       'rehearsal_optimal_at_least_075':bool(p and p['rehearsal_optimal_rate']>=.75),'rehearsal_null_at_most_005':nulls/600<=.05 if len(primary)==600 else False}
    joint='UNKNOWN' if not complete else 'PASS' if all(components.values()) else 'FAIL'
    def prediction(rs,metric,predicate,required):
        if len(rs)!=required or not all(r['attempted'] for r in rs): return {'status':'UNKNOWN','assigned':len(rs),'reason':'incomplete assigned responses','value':None}
        v=metric(rs);return {'status':'MET' if predicate(v) else 'UNMET','assigned':len(rs),'value':v}
    predictions={'P1':{'status':'UNKNOWN' if joint=='UNKNOWN' else 'MET' if joint=='PASS' else 'UNMET','assigned':600,'reason':'joint primary rule'},
      'P2':prediction([r for r in primary if r['door']==1 and r['evidence']=='rehearsal'],lambda rs:sum(r['optimal'] for r in rs)/len(rs),lambda v:v>=.9,100),
      'P3':prediction([r for r in primary if r['door']==6 and r['evidence']=='rules'],lambda rs:sum(r['schema_valid'] and r['fleet']==24 for r in rs)/len(rs),lambda v:v>=.1,100),
      'P4':prediction([r for r in rows if r['actor']=='qwen7b' and r['mode']=='common' and r['evidence']=='rehearsal'],lambda rs:sum(r['optimal'] for r in rs)/len(rs),lambda v:v>=.9,300)}
    p5=[r for r in rows if r['actor'] in ('llama8b','claude') and r['mode']=='independent']
    p5complete=len(p5)==660 and all(r['attempted'] for r in p5)
    predictions['P5']={'status':'UNKNOWN' if not p5complete else 'MET' if all(contrasts[a+'/independent'][k]>0 for a in ('llama8b','claude') for k in ('D_R','D_O')) else 'UNMET','assigned':660,'reason':'two descriptive family contrasts'}
    return {'joint_primary':joint,'primary_components':components,'rehearsal_null_guardrail':{'numerator':nulls,'denominator':600,'basis':'all assigned independent decisions, as registered'},'technical_acceptance':technical_gates(rows,summaries),'contrasts':contrasts,'cells':summaries,'predictions':predictions,
      'complete_pair_sensitivity':contrast(rows,'qwen7b','independent',True) if primary else None,
      'claim_boundary':'A pass means models use worked examples better than complete written rules on this fixed planning task.',
      'interval_scope':'Fixed numeric grid, one saved reply per prompt; not all tasks or full generation variance.'}


def analysis(root,data,output,allow_fake=False,jobs=None):
    if not allow_fake:
        from od_freeze import verify
        verify(root)
    rows,ledger=replay(root,data,allow_fake,jobs)
    result={'kind':'FAKE_OFFLINE_NOT_STUDY_RESULTS' if allow_fake else 'FROZEN_ANALYSIS','rows':rows,'ledger':ledger,**analyze_rows(rows)}
    # Raw wall time is reconstructed from terminal/start timestamps, with timer charges separate.
    durations=defaultdict(float);cell_durations=defaultdict(float)
    for r in rows:
        if r['attempted']:
            d=episode_state(Path(data),r['id'])[0]
            seconds=(dt.datetime.fromisoformat(read(d/'episode.json')['finished_at'])-dt.datetime.fromisoformat(read(d/'start.json')['started_at'])).total_seconds()
            durations[r['actor']]+=seconds
            cell_durations[f"{r['actor']}/door{r['door']}/{r['mode']}/{r['evidence']}"]+=seconds
    result['elapsed_seconds_by_model']=dict(durations)
    result['elapsed_seconds_by_cell']=dict(cell_durations)
    save(output,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--data',type=Path,default=ROOT/'collection');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();analysis(a.root,a.data,a.output)
