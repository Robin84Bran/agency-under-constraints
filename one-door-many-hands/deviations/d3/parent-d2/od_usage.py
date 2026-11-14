"""D1/D2 definite nonstarts; immutable evidence and exact saved-request resumes."""
import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo
from od_core import sha
from od_io import Stop,read,save,Log,Ledger,ActiveTime,now,lock
from od_validation import envelope,usage,cost


def zero_tree(value):
    if type(value) is dict: return all(zero_tree(v) for v in value.values())
    if type(value) is list: return not value
    return type(value) in (int,float) and value==0


def refusal(raw):
    """No inference from error text alone, rounded costs, or missing counters."""
    try:
        if type(raw) is not dict: return None
        if raw.get('harness_error'): return None
        rc=raw.get('returncode')
        if not ((type(rc) is int and rc in (0,1)) or (rc is None and raw.get('transport_error'))): return None
        e,problem=envelope(raw,'claude')
        u=usage(e,'claude')
        if problem or e.get('type')!='result' or e.get('is_error') is not True or type(e.get('api_error_status')) is not int or e['api_error_status']!=429: return None
        if u is None or any(u[k]!=0 for k in ('input','output','cache_read','cache_creation')): return None
        if type(e.get('total_cost_usd')) not in (int,float) or e['total_cost_usd']!=0: return None
        if e.get('structured_output') is not None or e.get('permission_denials') not in (None,[]): return None
        if any(e.get(k) for k in ('tool_uses','tool_calls','deferred_tool_use','safety_stops')): return None
        if e.get('subagent_stats') and not zero_tree(e['subagent_stats']): return None
        mu=e.get('modelUsage')
        if mu not in (None,{}):
            from od_core import MODEL
            if type(mu) is not dict or set(mu)!={MODEL} or type(mu[MODEL]) is not dict: return None
            m=mu[MODEL]
            if m.get('canonicalModel',MODEL)!=MODEL: return None
            for k in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens','webSearchRequests','thinkingTokens','cacheCreationEphemeral5mInputTokens','cacheCreationEphemeral1hInputTokens'):
                if k in m and (type(m[k]) is not int or m[k]!=0): return None
            if 'costUSD' in m and (type(m['costUSD']) not in (int,float) or m['costUSD']!=0): return None
        from od_core import MODEL
        if e.get('model',MODEL)!=MODEL or e.get('effort','medium')!='medium': return None
        def token_zero(v):
            if type(v) is not dict: return True
            return all((zero_tree(x) if 'token' in k or k=='server_tool_use' else token_zero(x)) for k,x in v.items())
        if not token_zero(e['usage']): return None
        message=e.get('result','')
        if type(message) is not str or not re.fullmatch(r"You've hit your(?: [^\n]+)? limit · resets [^\n]+",message): return None
        m=re.fullmatch(r"You've hit your(?: [^\n]+)? limit · resets (\d{1,2})(?::(\d{2}))?(am|pm) \(([^\n()]+)\)",message)
        if not m: return {'message':message,'reset_unknown':True}
        hour,minute=int(m[1]),int(m[2] or 0)
        if not 1<=hour<=12 or not 0<=minute<60: return None
        zone=ZoneInfo(m[4])
        return {'message':e['result'],'hour':hour%12+(12 if m[3]=='pm' else 0),'minute':minute,'timezone':zone.key}
    except (ValueError,KeyError,TypeError,UnicodeError): return None


def reset_at(info,finished):
    if info.get('reset_unknown'): return None
    if info.get('kind')=='verified transport nonstart': return finished
    t=dt.datetime.fromisoformat(finished).astimezone(ZoneInfo(info['timezone']))
    reset=t.replace(hour=info['hour'],minute=info['minute'],second=0,microsecond=0)
    if reset<=t: reset+=dt.timedelta(days=1)
    return reset.astimezone(dt.timezone.utc).isoformat()


def directories(base,ident):
    p=Path(base)/'episodes'/ident
    if not p.exists(): return []
    if p.is_symlink() or not p.is_dir(): raise Stop('unsafe episode directory')
    parent=p/'usage-resumes'
    if parent.is_symlink(): raise Stop('unsafe usage resume directory')
    children=sorted(parent.iterdir()) if parent.exists() else []
    if [x.name for x in children]!=[f'{i:04d}' for i in range(1,len(children)+1)] or any(x.is_symlink() or not x.is_dir() for x in children): raise Stop('usage attempt sequence changed')
    return [p]+children


def attempt_id(ident,index): return ident if index==0 else ident+'@usage-resume-'+f'{index:04d}'


def nonstart(p):
    """Verify disposition from saved bytes, never merely trust a status flag."""
    p=Path(p)
    if not (p/'nonstart.json').exists(): return None
    record=read(p/'nonstart.json');raw=read(p/'raw.json');info=refusal(raw) or network_nonstart(raw)
    if info is None or record!={'kind':info.get('kind','usage-limit pause'),'definite_nonstart':True,'raw_sha256':sha((p/'raw.json').read_bytes()),'request_sha256':sha((p/'request.json').read_bytes()),'finished_at':record['finished_at'],'reset_at':reset_at(info,record['finished_at']),'message':info['message']}:
        raise Stop('invalid usage-limit nonstart evidence')
    return record


def record_nonstart(p,finished=None):
    info=refusal(read(p/'raw.json')) or network_nonstart(read(p/'raw.json'))
    if info is None: raise Stop('not a definite usage-limit nonstart')
    finished=finished or now()
    save(p/'nonstart.json',{'kind':info.get('kind','usage-limit pause'),'definite_nonstart':True,'raw_sha256':sha((p/'raw.json').read_bytes()),'request_sha256':sha((p/'request.json').read_bytes()),'finished_at':finished,'reset_at':reset_at(info,finished),'message':info['message']})
    return nonstart(p)


def episode_state(base,ident):
    ds=directories(base,ident)
    if not ds: return None,[]
    original=(ds[0]/'request.json').read_bytes();events=[]
    for index,p in enumerate(ds):
        if any(x.is_symlink() for x in p.iterdir()) or (p/'request.json').read_bytes()!=original: raise Stop('usage resume request bytes changed')
        if not (p/'start.json').exists() or not (p/'raw.json').exists(): raise Stop('interrupted/reserved episode; never resend')
        pause=nonstart(p)
        if pause:
            events.append(dict(pause,id=ident,attempt_id=attempt_id(ident,index),path=p.relative_to(base).as_posix()))
        elif index!=len(ds)-1 or not (p/'episode.json').exists(): raise Stop('uncertain or completed start cannot be resent')
    return (None if nonstart(ds[-1]) else ds[-1]),events


def pending_pause(base,jobs):
    for ep in jobs:
        terminal,events=episode_state(base,ep['id'])
        if events and terminal is None:
            last=events[-1]
            if last['reset_at'] is None or dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(last['reset_at']): return last
    return None


def prefix_snapshot(base):
    return {n:{'bytes':len(Log(Path(base)/n).data),'sha256':sha(Log(Path(base)/n).data)} for n in ('ledger.jsonl','local-time.jsonl','claude-time.jsonl')}


def verify_prefixes(base,prefixes):
    for n,cp in prefixes.items():
        data=Log(Path(base)/n).data
        if len(data)<cp['bytes'] or sha(data[:cp['bytes']])!=cp['sha256']: raise Stop('D1 ledger prefix mismatch')


def stop_cleared(base):
    if (Path(base)/'envelope-stop-clearance.json').exists():
        from od_d2 import clearance_valid
        return clearance_valid(base)
    if (Path(base)/'STOP-after-usage-clearance.json').exists(): return False
    p=Path(base)/'usage-limit-clearance.json'
    if not p.exists(): return False
    c=read(p);verify_prefixes(base,c['prefixes'])
    if c['stop_sha256']!=sha((Path(base)/'STOP.json').read_bytes()): raise Stop('clearance STOP mismatch')
    d=Path(base)/c['path'];record=nonstart(d)
    if record is None or c['nonstart_sha256']!=sha((d/'nonstart.json').read_bytes()): raise Stop('clearance nonstart mismatch')
    return True


def network_nonstart(raw):
    """D2 narrow DNS pre-generation proof; never infer this from text alone."""
    try:
        if type(raw) is not dict or raw.get('transport_error') or raw.get('harness_error') or type(raw.get('returncode')) is not int or raw['returncode']!=1: return None
        e,problem=envelope(raw,'claude');u=usage(e,'claude')
        if problem or e.get('type')!='result' or e.get('is_error') is not True or e.get('terminal_reason')!='api_error' or e.get('api_error_status') is not None: return None
        if type(e.get('duration_api_ms')) is not int or e['duration_api_ms']!=0 or u is None or any(u[k]!=0 for k in ('input','output','cache_read','cache_creation')): return None
        if type(e.get('total_cost_usd')) not in (int,float) or e['total_cost_usd']!=0 or e.get('modelUsage') not in (None,{}): return None
        from od_core import MODEL
        if e.get('model',MODEL)!=MODEL or e.get('effort','medium')!='medium': return None
        if e.get('result')!="API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)": return None
        if e.get('structured_output') is not None or e.get('permission_denials')!=[] or any(e.get(k) for k in ('tool_uses','tool_calls','deferred_tool_use','safety_stops')): return None
        if e.get('subagent_stats') and not zero_tree(e['subagent_stats']): return None
        st=e['usage'].get('server_tool_use')
        if type(st) is not dict or not {'web_search_requests','web_fetch_requests'}<=set(st) or not zero_tree(st): return None
        for key in ('output_tokens_details','cache_creation'):
            if key in e['usage'] and not zero_tree(e['usage'][key]): return None
        return {'kind':'verified transport nonstart','message':e['result']}
    except (ValueError,KeyError,TypeError,UnicodeError): return None


def clear_usage_stop(root):
    """Append a re-disposition/clearance; retain original STOP and terminal bytes."""
    root=Path(root);base=root/'collection'
    from od_freeze import verify
    verify(root)
    with lock(base):
        if not (base/'STOP.json').exists(): return {'clearance':'not needed; no STOP'}
        if stop_cleared(base): return read(base/'usage-limit-clearance.json')
        ledger=Ledger(base/'ledger.jsonl');timer=ActiveTime(base/'claude-time.jsonl',7200);ActiveTime(base/'local-time.jsonl',28800)
        if timer.breaches: raise Stop('resource breach cannot be cleared as usage limit')
        jobs=read(root/'config/episodes.json');candidates=[]
        for ep in jobs:
            if ep['actor']!='claude': continue
            for i,p in enumerate(directories(base,ep['id'])):
                if (p/'raw.json').exists() and refusal(read(p/'raw.json')): candidates.append((ep,p,i))
        if len(candidates)!=1: raise Stop('clearance requires exactly one final saved refusal')
        ep,p,index=candidates[0];ident=attempt_id(ep['id'],index)
        terminal=read(p/'episode.json')
        if read(base/'STOP.json')['reason']!=terminal.get('fatal') or terminal.get('fatal')!='transport failure/uncertain start; never resend': raise Stop('STOP is not the refusal failure')
        if any((base/'episodes'/e['id']).exists() for e in jobs[jobs.index(ep)+1:] if e['actor']=='claude'): raise Stop('dispatch after saved refusal')
        if ident not in ledger.reservations or ledger.settlements.get(ident,0)!=0: raise Stop('refusal reservation/settlement mismatch')
        if ident not in ledger.settlements: ledger.event(event='settle',id=ident,actual=0)
        if not (p/'nonstart.json').exists(): record_nonstart(p,terminal['finished_at'])
        c={'kind':'D1 usage-limit STOP clearance; prior failure re-dispositioned as operational nonstart','time':now(),'stop_sha256':sha((base/'STOP.json').read_bytes()),'path':p.relative_to(base).as_posix(),'nonstart_sha256':sha((p/'nonstart.json').read_bytes()),'prefixes':prefix_snapshot(base)}
        save(base/'usage-limit-clearance.json',c);return c
