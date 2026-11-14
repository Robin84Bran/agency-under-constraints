"""Offline replay and predeclared paired-block analysis. No network imports."""
from collections import defaultdict
from pathlib import Path
import random
import statistics
from ps_core import World, fixture, render, sha, reservation, canonical, literal_map
from ps_io import Stop, read, Journal, Ledger
from ps_transport import decode, usage, cost_micro, provider_envelope
from ps_usage_limit import call_location, audit_pauses


def percentile(values,q):
    if not values: return None
    a=sorted(values);x=(len(a)-1)*q;i=int(x)
    return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)


def bootstrap(differences,replicates=10000):
    if not differences: return {'mean':None,'interval':None,'n':0}
    mean=sum(differences)/len(differences)
    if min(differences)==max(differences): interval=[mean,mean]
    else:
        rng=random.Random(20261112);n=len(differences)
        samples=[sum(rng.choices(differences,k=n))/n for _ in range(replicates)]
        interval=[percentile(samples,.025),percentile(samples,.975)]
    return {'mean':mean,'interval':interval,'n':len(differences),'replicates':replicates}


def score(ep,base,fake=False,timing=None):
    """Rebuild visible state and executed controls from requests + raw + events."""
    timing=load_timing(base) if timing is None else timing
    directory=Path(base)/'episodes'/ep['id'];world=World(ep);f=fixture(ep['seed'],ep['world'])
    started=0;valid=0;calls=[];notes=[];facts=[{'correct':None,'reason':'missing/unstarted','control':None} for _ in range(16)]
    stopped=False;usage_pending=False
    for i in range(8):
        prefix,pauses=call_location(directory,i)
        start=directory/f'{prefix}.start.json';event=directory/f'{prefix}.event.json'
        if pauses:
            refused=read(directory/f'{i}.request.json');visible=world.payload();prompt=render(visible)
            from ps_transport import claude_command
            tr=refused['transport_request']
            if ep['actor']!='claude' or refused['payload']!=visible or refused['prompt']!=prompt or refused['prompt_sha256']!=sha(prompt.encode()) or refused['reservation']!=reservation(ep['arm'],visible['mode']): raise Stop('non-start request/history mismatch')
            if tr['stdin']!=prompt or tr['argv']!=claude_command(tr['argv'][0],visible['mode'],refused['reservation']['micro_usd']): raise Stop('non-start request settings changed')
        if not start.exists():
            if pauses and not (directory/f'{prefix}.request.json').exists(): usage_pending=True
            if event.exists() or (directory/f'{prefix}.raw.json').exists(): raise Stop('response/event without durable start')
            stopped=True;continue
        started+=1
        if stopped: raise Stop('call dispatched after terminal gap/failure')
        request=read(directory/f'{prefix}.request.json');payload=world.payload();prompt=render(payload)
        s=read(start)
        if s['id']!=ep['id']+'-'+prefix: raise Stop('saved call identity mismatch')
        if s['request_sha256']!=sha((directory/f'{prefix}.request.json').read_bytes()) or request['payload']!=payload or request['prompt']!=prompt or request['prompt_sha256']!=sha(prompt.encode()) or request['reservation']!=reservation(ep['arm'],payload['mode']): raise Stop('replay request/history mismatch')
        from ps_transport import local_request, claude_command
        tr=request['transport_request']
        if ep['actor']!='claude' and tr!=local_request(ep,prompt,i): raise Stop('local request settings changed')
        if ep['actor']=='claude' and (tr['stdin']!=prompt or tr['argv']!=claude_command(tr['argv'][0],payload['mode'],request['reservation']['micro_usd'])): raise Stop('frontier request settings changed')
        rawpath=directory/f'{prefix}.raw.json';value=None;error=None;tin=tout=None;actual=None if ep['actor']=='claude' else 0
        if rawpath.exists():
            raw=read(rawpath)
            try:
                env,_=provider_envelope(raw['stdout'],ep['actor']);tin,tout=usage(env,ep['actor'])
                if ep['actor']=='claude' and tin is not None and tout is not None: actual=cost_micro(tin,tout,env)
            except (ValueError,KeyError,TypeError,AttributeError): pass
            try: value,_=decode(raw,ep,payload,reservation(ep['arm'],payload['mode']),fake)
            except (ValueError,Stop) as exc: error=str(exc)
            if actual is not None and actual>request['reservation']['micro_usd']: error='accounting overrun';value=None
        else: error='unknown response after durable start'
        applied=event.exists()
        if applied:
            if error or value is None: raise Stop('event with invalid/unavailable reply')
            if read(event)!={'index':i,'payload':payload,'value':value}: raise Stop('event differs from strict reply replay')
            valid+=1
            if i<4:
                note=value['note'];mapping=literal_map(note);j=f['cal_order'][i]
                fidelity=None if mapping is None else all(mapping[k+1]==__import__('ps_core').DIRECTIONS[d] for k,d in enumerate(f['calibration'][j]))
                notes.append({'visit':i+1,'slot':value['slot'],'note':note,'length':len(note),'empty':not note,'literal_fidelity':fidelity})
            else:
                j=f['return_order'][i-4]
                for k,(control,target) in enumerate(zip(value['controls'],f['targets'][j])):
                    hit=None if control is None else f['returns'][j][control-1]==target
                    facts[(i-4)*4+k]={'control':control,'target':target,'correct':hit,'reason':'abstention' if control is None else 'observed'}
            world.step(value)
        else:
            stopped=True
            if i>=4:
                for k in range(4): facts[(i-4)*4+k]['reason']=error or 'not executed before interruption/accounting stop'
        calls.append({'index':i,'id':s['id'],'prefix':prefix,'input_tokens':tin,'output_tokens':tout,'actual_micro_usd':actual,'error':error,'applied':applied,
                      'wall_seconds':timing.get(s['id']),'raw_sha256':sha(rawpath.read_bytes()) if rawpath.exists() else None})
    if (directory/'episode.json').exists():
        terminal=read(directory/'episode.json')
        if terminal['episode']!=ep or terminal['attempted_calls']!=started or terminal['completed_calls']!=valid: raise Stop('terminal summary differs from independent replay')
    last_write={n['slot']:i for i,n in enumerate(notes)}
    for i,n in enumerate(notes): n['retained_at_returns']=ep['arm']!='discard' and last_write[n['slot']]==i
    correct=sum(x['correct'] is True for x in facts);answered=sum(x['correct'] is not None for x in facts)
    positions=[sum(x['correct'] is True for x in facts[k:k+4])/4 for k in range(0,16,4)]
    return {**ep,'attempted':started>0,'calls_started':started,'valid_calls':valid,'technical_complete':valid==8,'operational_pause':usage_pending,
            'Y':correct/16,'F':sum(all(x['correct'] is True for x in facts[k:k+4]) for k in range(0,16,4))/4,
            'answered_only_accuracy':correct/answered if answered else None,'answered':answered,
            'nulls':sum(x['reason']=='abstention' for x in facts),'known_wrong':sum(x['correct'] is False for x in facts),
            'technical_missing':sum(x['reason'] not in ('observed','abstention') for x in facts),
            'returns':positions,'return_complete':[all(x['correct'] is True for x in facts[k:k+4]) for k in range(0,16,4)],'facts':facts,'notes':notes,'final_notes':world.notes,'calls':calls,
            'routing_metadata_bytes':len(canonical(dict(zip(f['labels'],f['slots']))).encode()) if ep['arm']=='keyed' else 0,
            'slot_identifier_bytes_per_call':[len(canonical([m['slot'] for m in read(directory/f'{c.get("prefix",c["index"])}.request.json')['payload']['memory']]).encode()) for c in calls]}


def prompt_stats(rows):
    vals=[c['input_tokens'] for r in rows for c in r['calls'] if c['input_tokens'] is not None]
    return {'count':len(vals),'sum':sum(vals),'mean':statistics.mean(vals) if vals else None,'median':statistics.median(vals) if vals else None,
            'max':max(vals) if vals else None,'missing_usage':sum(c['input_tokens'] is None for r in rows for c in r['calls']),
            'unstarted_calls':sum(8-r['calls_started'] for r in rows)}


def contrast(left,right,complete_only=False):
    a={r['seed']:r for r in left};b={r['seed']:r for r in right};seeds=sorted(set(a)&set(b))
    if complete_only: seeds=[s for s in seeds if a[s]['technical_complete'] and b[s]['technical_complete']]
    return {k:bootstrap([a[s][k]-b[s][k] for s in seeds]) for k in ('Y','F')} | {
            'complete_pairs':sum(a[s]['technical_complete'] and b[s]['technical_complete'] for s in seeds),
            'all_attempted':bool(seeds) and all(a[s]['attempted'] and b[s]['attempted'] and not a[s].get('operational_pause',False) and not b[s].get('operational_pause',False) for s in seeds),
            'prompt_tokens':{'left':prompt_stats([a[s] for s in seeds]),'right':prompt_stats([b[s] for s in seeds])}}


def primary(keyed,shared):
    c=contrast(keyed,shared);sensitivity=contrast(keyed,shared,True)
    conditions=[c['Y']['mean'] is not None and c['Y']['mean']>=.10 and c['Y']['interval'][0]>0,
                c['F']['mean'] is not None and c['F']['mean']>0 and c['F']['interval'][0]>0,
                len(keyed)==len(shared)==100 and all(r['attempted'] for r in keyed+shared) and all(sum(r['technical_complete'] for r in rows)>=95 for rows in (keyed,shared)),
                sensitivity['Y']['n']>=95 and sensitivity['Y']['interval'][0]>0]
    return {'status':'met' if all(conditions) else 'failed' if c['all_attempted'] else 'UNKNOWN',
            'reason':None if c['all_attempted'] else 'unattempted or operationally paused primary episodes; operational denominators retained',
            'conditions':conditions,'contrast':c,'complete_pair_sensitivity':sensitivity}


def analyze(root,base,fake=False):
    root=Path(root);base=Path(base);schedule=read(root/'config/episodes.json')
    timing=load_timing(base)
    rows=[score(ep,base,fake,timing) for ep in schedule];groups=defaultdict(list)
    for row in rows: groups[(row['actor'],row['world'],row['arm'])].append(row)
    contrasts={};cells={}
    for (actor,world,arm),rs in sorted(groups.items()):
        cells['/'.join((actor,world,arm))]={'episodes':len(rs),'attempted':sum(r['attempted'] for r in rs),
             'technical_complete':sum(r['technical_complete'] for r in rs),'operationally_paused':sum(r.get('operational_pause',False) for r in rs),'Y':statistics.mean(r['Y'] for r in rs),'F':statistics.mean(r['F'] for r in rs),
             'prompt_tokens':prompt_stats(rs),
             'output_tokens':sum(c['output_tokens'] for r in rs for c in r['calls'] if c['output_tokens'] is not None),
             'wall_seconds':sum(c['wall_seconds'] for r in rs for c in r['calls'] if c['wall_seconds'] is not None),
             'model_call_micro_usd':sum(c['actual_micro_usd'] for r in rs for c in r['calls'] if c['actual_micro_usd'] is not None),
             'nulls':sum(r['nulls'] for r in rs),'known_wrong':sum(r['known_wrong'] for r in rs),'technical_missing':sum(r['technical_missing'] for r in rs)}
    for actor,world in sorted({(a,w) for a,w,_ in groups}):
        for left,right in [('keyed','shared'),('keyed','discard'),('shared','discard')]:
            contrasts['/'.join((actor,world,left+'-'+right))]=contrast(groups[(actor,world,left)],groups[(actor,world,right)])
    for actor in ('qwen7b','llama8b','qwen1b','claude'):
        for arm in ('keyed','shared','discard'):
            contrasts['/'.join((actor,'stale-minus-stable',arm))]=contrast(groups[(actor,'stale-remap',arm)],groups[(actor,'different-stable',arm)])
    p1=primary(groups[('qwen7b','different-stable','keyed')],groups[('qwen7b','different-stable','shared')])
    predictions={'P1':{'status':p1['status'],'reason':p1['reason']}}
    def decision(name,keys,fn):
        relevant=[r for key in keys for r in groups[key]]
        known=bool(relevant) and all(r['attempted'] and not r.get('operational_pause',False) for r in relevant)
        predictions[name]={'status':('met' if fn() else 'failed') if known else 'UNKNOWN','reason':None if known else 'mandatory episodes unattempted or operationally paused'}
    stable='different-stable';actors=('qwen7b','llama8b')
    decision('P2',[('llama8b',stable,a) for a in ('keyed','shared')],lambda:all(contrasts['llama8b/different-stable/keyed-shared'][k]['mean']>0 for k in ('Y','F')))
    decision('P3',[(m,stable,a) for m in actors for a in ('keyed','discard')],lambda:all(contrasts[m+'/different-stable/keyed-discard']['Y']['mean']>0 for m in actors))
    decision('P4',[(m,w,a) for m in actors for w in (stable,'same-stable') for a in ('keyed','shared')],lambda:all(
        contrasts[m+'/same-stable/keyed-shared']['Y']['mean']<contrast([r for r in groups[(m,stable,'keyed')] if r['seed']<20],[r for r in groups[(m,stable,'shared')] if r['seed']<20])['Y']['mean'] for m in actors))
    decision('P5',[(m,w,'keyed') for m in actors for w in (stable,'stale-remap')],lambda:all(contrasts[m+'/stale-minus-stable/keyed']['Y']['mean']<0 for m in actors))
    decision('P6',[('claude',stable,a) for a in ('keyed','shared')],lambda:contrasts['claude/different-stable/keyed-shared']['Y']['mean']>0)
    decision('P7',list(groups),lambda:all(sum(r['technical_complete'] for r in rs)/len(rs)>=.95 for rs in groups.values()))
    accounting=audit_accounting(base,rows)
    return {'kind':'OFFLINE-FAKE' if fake else 'saved-evidence replay','model_results':not fake,'episodes':rows,'cells':cells,'contrasts':contrasts,
            'primary':p1,'predictions':predictions,'accounting':accounting,'operational_events':accounting['operational_events'],'attempted_episodes':sum(r['attempted'] for r in rows),
            'limitations':['Automatic routing also changes visible context; prompt tokens accompany every contrast.',
                           'Operational missing/abstention zeros do not assert observed environmental failure.',
                           'Intervals describe generator blocks and saved first replies, not real-world tasks.']}


def load_timing(base):
    result={}
    for cohort in ('local','claude'):
        for e in Journal(Path(base)/f'{cohort}-time.jsonl').rows:
            if e['event']=='settle': result[e['id']]=e['seconds']
    return result


def audit_accounting(base,rows):
    base=Path(base);ledger=Ledger(base/'ledger.jsonl');starts={}
    operational_events=audit_pauses(base,ledger)
    for p in (base/'episodes').glob('*/*.start.json'):
        s=read(p);raw=ledger.journal.raw
        if sha(raw[:s['ledger_prefix_bytes']])!=s['ledger_prefix_sha256']: raise Stop('start binds altered ledger prefix')
        starts[s['id']]=s
    unsealed=[]
    for r in rows:
        path=base/'episodes'/r['id']/'episode.json'
        if path.exists():
            terminal=read(path)
            if r['id'] not in ledger.sealed: unsealed.append(r['id'])
            elif ledger.sealed[r['id']]!=sha(path.read_bytes()): raise Stop('terminal seal changed')
            files=terminal.get('evidence_files',{})
            actual={p.name for p in path.parent.iterdir() if p.is_file() and p.name!='episode.json'}
            if set(files)!=actual: raise Stop('episode evidence inventory changed')
            for name,digest in files.items():
                if Path(name).name!=name or sha((path.parent/name).read_bytes())!=digest: raise Stop('sealed episode evidence changed')
        elif r['id'] in ledger.sealed: raise Stop('sealed terminal missing')
    if set(ledger.sealed)-{r['id'] for r in rows}: raise Stop('unknown sealed episode')
    paid={c.get('id',r['id']+f'-{c["index"]}'):c for r in rows if r['actor']=='claude' for c in r['calls']}
    if set(ledger.started)!=set(paid)|set(ledger.usage_pauses): raise Stop('paid starts differ from ledger allocations')
    for ident,actual in ledger.settled.items():
        if (0 if ident in ledger.usage_pauses else paid[ident]['actual_micro_usd'])!=actual: raise Stop('settlement differs from retained usage')
    contract_path=base/'frontier-contract.json'
    if paid:
        accepted=[ident for ident in paid if paid[ident]['applied']]
        earliest=min(accepted,key=lambda ident:starts[ident]['started_at']) if accepted else None
        if contract_path.exists():
            contract=read(contract_path)
            if earliest is None: raise Stop('contract without accepted frontier payload')
            epid=ledger.started[earliest]['episode'];rawpath=base/'episodes'/epid/(paid[earliest].get('prefix',str(paid[earliest]['index']))+'.raw.json')
            if contract.get('call_id')!=earliest or contract.get('raw_sha256')!=sha(rawpath.read_bytes()) or not paid[earliest]['applied'] or contract.get('strict_valid_structured_output') is not True: raise Stop('frontier first-call contract evidence mismatch')
        elif earliest is not None: raise Stop('missing first-call contract evidence')
    elif contract_path.exists(): raise Stop('frontier contract exists without paid call')
    active={}
    for cohort in ('local','claude'):
        j=Journal(base/f'{cohort}-time.jsonl');holds={};settled={}
        for e in j.rows:
            if e['event']=='start':
                if e['id'] in holds: raise Stop('duplicate active-time start')
                holds[e['id']]=e['seconds']
            elif e['event']=='settle':
                if e['id'] not in holds or e['id'] in settled: raise Stop('invalid active-time settlement')
                settled[e['id']]=e['seconds']
        active[cohort]={'seconds':sum(settled.get(k,v) for k,v in holds.items()),'unsettled':len(set(holds)-set(settled))}
    return {'settled_micro_usd':ledger.spent,'held_micro_usd':sum(ledger.holds.values()),'exposure_micro_usd':ledger.exposure,
            'unsealed_terminals':unsealed,'unsettled_calls':sorted(set(ledger.started)-set(ledger.settled)),'blocked':ledger.blocked,'active_time':active,
            'usage_limit_refusals':len(operational_events),'operational_events':operational_events,'actual_cash_payment_usd':None,'actual_cash_payment_status':'UNKNOWN'}
