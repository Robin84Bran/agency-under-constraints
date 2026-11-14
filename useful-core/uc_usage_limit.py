"""D1 operational non-starts. No provider imports or implicit model execution."""
import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from uc_core import World, P, SCHEMAS, canonical, sha, transport_load, strict_load, render, reserve, episode_reservation
from uc_store import Stop, Journal, read, save, save_bytes, now

TOKEN_KEYS=('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens')


def is_usage_limit(env,raw):
    """A deliberately narrow exception; contradictory/missing evidence fails closed."""
    if type(env) is not dict or type(raw.get('returncode')) is not int or raw['returncode']!=1 or raw.get('transport_error') or raw.get('harness_error'):
        return False
    if type(env.get('api_error_status')) is not int or env['api_error_status']!=429 or env.get('is_error') is not True:
        return False
    u=env.get('usage')
    if type(u) is not dict or any(type(u.get(k)) is not int or u[k]!=0 for k in TOKEN_KEYS):
        return False
    if type(env.get('total_cost_usd')) not in (int,float) or env['total_cost_usd']!=0:
        return False
    # Also reject contradictory detailed/model usage and activity, if supplied.
    def zero_tokens(value):
        if type(value) is dict:
            return all((not (('token' in k.lower() and k!='maxOutputTokens') or k in ('costUSD','webSearchRequests')) or
                        (type(v) in (int,float) and v==0) or type(v) in (dict,list)) and zero_tokens(v) for k,v in value.items())
        if type(value) is list:return all(zero_tokens(v) for v in value)
        return True
    if type(env.get('modelUsage',{})) is not dict or any(type(v) is not dict for v in env.get('modelUsage',{}).values()) or not zero_tokens(u) or not zero_tokens(env.get('modelUsage',{})):
        return False
    if env.get('structured_output') is not None:return False
    if any(env.get(k) for k in ('tool_calls','permission_denials','deferred_tool_use','input_truncated','context_truncated')):
        return False
    tools=u.get('server_tool_use',{})
    if type(tools) is not dict or any(v!=0 for v in tools.values()):
        return False
    result=env.get('result')
    return type(result) is str and re.fullmatch(r"You've hit your (?:5-hour|weekly|daily) limit · resets [^\n]+",result) is not None


def reset_time(env,started):
    """Resolve the supplied clock in its supplied timezone; unknown means stay paused."""
    m=re.fullmatch(r"You've hit your (?:5-hour|weekly|daily) limit · resets (\d{1,2})(?::(\d{2}))?(am|pm) \(([^)]+)\)",env['result'])
    if not m:return None
    try:
        hour,minute=int(m[1]),int(m[2] or 0)
        if not 1<=hour<=12 or minute>59:return None
        start=dt.datetime.fromisoformat(started.replace('Z','+00:00'))
        if start.tzinfo is None:return None
        local=start.astimezone(ZoneInfo(m[4]));hour=hour%12+(12 if m[3]=='pm' else 0)
        reset=local.replace(hour=hour,minute=minute,second=0,microsecond=0)
        if reset<=local:reset+=dt.timedelta(days=1)
        return reset.astimezone(dt.timezone.utc).isoformat()
    except (ValueError,KeyError):
        return None


def prefixes(base):
    return {p.name:dict(bytes=len(p.read_bytes()),sha256=sha(p.read_bytes())) for p in Path(base).glob('*.jsonl')}


def check_prefixes(base,pins):
    for name,pin in pins.items():
        if Path(name).name!=name:raise Stop('unsafe prefix path')
        path=Path(base)/name;raw=path.read_bytes()
        if len(raw)<pin['bytes'] or sha(raw[:pin['bytes']])!=pin['sha256']:
            raise Stop('usage-limit retained journal prefix changed')
        Journal(path)
    # Verify complete tails as well as retained prefixes, including new journals.
    for path in Path(base).glob('*.jsonl'):Journal(path)


def dispatches(directory):
    return sorted((Path(directory)/'dispatches').glob('*'),key=lambda p:(int(p.name.split('-')[0]),int(p.name.split('-')[1])))


def refusal_evidence(attempt):
    attempt=Path(attempt)
    req=read(attempt/'request.json');start=read(attempt/'start.json');raw=read(attempt/'raw.json')
    stdout=(attempt/'stdout').read_bytes();stderr=(attempt/'stderr').read_bytes()
    if raw.get('stdout_sha256')!=sha(stdout) or raw.get('stderr_sha256')!=sha(stderr):raise Stop('dispatch raw bytes changed')
    env=strict_load(stdout.decode())
    if not is_usage_limit(env,raw):raise Stop('dispatch is not a definite usage-limit non-start')
    return req,start,env


def ensure_pause(base,attempt,ledger,timer):
    """Reconstruct only definite non-starts after a crash; never retry other raw output."""
    attempt=Path(attempt);base=Path(base);req,start,env=refusal_evidence(attempt)
    ident=start['id'];ep=attempt.parent.parent.name
    matches=[e for e in ledger.journal.events if e['event']=='nonstart' and e['id']==ident]
    event=dict(event='nonstart',id=ident,episode=ep,reserved=req['reservation']['micro_usd'],actual=0,
               evidence=attempt.relative_to(base).as_posix(),request_sha256=sha((attempt/'request.json').read_bytes()))
    if not matches:ledger.event(**event)
    elif len(matches)!=1 or any(matches[0].get(k)!=v for k,v in event.items()):raise Stop('non-start settlement mismatch')
    if ident not in timer.settled:
        # A process death retains the full time reservation, never invents elapsed time.
        if ident not in timer.holds:raise Stop('non-start missing active-time reservation')
        timer.journal.append(dict(event='settle',id=ident,seconds=timer.holds[ident],time=now()))
        timer.settled[ident]=timer.holds[ident]
    path=attempt/'usage-limit-pause.json'
    if not path.exists():
        files={p.name:sha(p.read_bytes()) for p in attempt.iterdir() if p.is_file()}
        save(path,dict(kind='usage-limit pause',disposition='DEFINITE_NON_START',time=now(),call=start['call'],
            episode=ep,attempt=ident,actual_micro_usd=0,reset_at=reset_time(env,start['started_at']),
            refusal=env['result'],files=files,
            history_files={p.name:sha(p.read_bytes()) for p in attempt.parent.parent.glob('*.*') if p.is_file()},
            journal_prefixes=prefixes(base)))
    pause=read(path)
    if (pause.get('kind')!='usage-limit pause' or pause.get('disposition')!='DEFINITE_NON_START' or
        pause.get('call')!=start['call'] or pause.get('attempt')!=ident or pause.get('actual_micro_usd')!=0 or
        pause.get('reset_at')!=reset_time(env,start['started_at'])):raise Stop('usage-limit pause changed')
    for name,digest in pause['files'].items():
        if Path(name).name!=name or sha((attempt/name).read_bytes())!=digest:raise Stop('non-start evidence changed')
    for name,digest in pause['history_files'].items():
        if Path(name).name!=name or sha((attempt.parent.parent/name).read_bytes())!=digest:raise Stop('prior history changed during usage-limit pause')
    check_prefixes(base,pause['journal_prefixes'])
    return pause


def ready(pause):
    reset=pause['reset_at']
    return reset is not None and dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat(reset)


def run_paid_episode(ep,transport,base,ledger,timer,freeze_hash,fake=False,gate=None):
    """D1 paid runner. Refusal dispatches remain outside canonical model-call files."""
    # Import only when explicitly invoked; analysis remains provider independent.
    from uc_transport import usage,cost_micro,decode
    from uc_core import ModelOutputError
    from uc_store import EpisodeFailure,TransportFailure
    from uc_collect import durable_stop
    base=Path(base);directory=base/'episodes'/ep['id'];directory.mkdir(parents=True,exist_ok=True)
    if (directory/'episode.json').exists():raise Stop('terminal episode cannot be resent')
    attempts=dispatches(directory)
    if list(directory.glob('*.start.json')) and not attempts:raise Stop('ambiguous parent episode; never resend')
    if ep['id'] not in ledger.holds:
        if attempts:raise Stop('dispatch lacks reservation')
        ledger.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
    world=World(ep['seed'],ep['world']);calls=[];final=None;error=None;failure_kind=None;fatal=False
    # Only a proven refusal allows an interrupted episode to resume.
    for attempt in attempts:
        if not (attempt/'accepted.json').exists():
            pause=ensure_pause(base,attempt,ledger,timer)
            if not ready(pause):return dict(usage_limit_pause=pause)
    if attempts:
        audit_nonstarts(base)
        canonical_starts=list(directory.glob('*.start.json'))
        from uc_analysis import audit_episode
        audit_episode(base,ep,None,fake)
        for p in sorted(canonical_starts,key=lambda p:int(p.name.split('.')[0])):
            stem=p.with_name(p.name.replace('.start.json',''));parsed=read(str(stem)+'.parsed.json')
            if parsed['error'] is not None:raise Stop('cannot resume after a model-call failure')
            calls.append(read(p)['id'])
            if read(str(stem)+'.request.json')['phase']=='report':final=parsed['value']
            else:
                world.step(parsed['value'])
                if world.events[-1]!=read(str(stem)+'.event.json'):raise Stop('saved history changed')
        # A crash after real generation has no new retry permission, even if older refusals exist.
        last=attempts[-1]
        if (last/'accepted.json').exists():raise Stop('interrupted after model generation; never resend')
    while final is None and error is None:
        phase='report' if world.ended else 'action';decision=7 if phase=='report' else len(world.history)+1
        prompt=render(ep,world.history,6-len(world.history),phase);bound=reserve(prompt,phase)
        prior=[a for a in attempts if int(a.name.split('-')[0])==decision]
        request=transport.request(ep,prompt,phase,decision,bound)
        record=dict(phase=phase,prompt=prompt,prompt_sha256=sha(prompt.encode()),system=P['system'],schema=SCHEMAS[phase],reservation=bound,outer=request)
        request_bytes=(canonical(record)+'\n').encode()
        for a in prior:
            if (a/'request.json').read_bytes()!=request_bytes:raise Stop('resumed request bytes differ')
        ident=ep['id']+f'-{decision}';attempt_id=ident+f'-dispatch-{len(prior):04d}'
        attempt=directory/'dispatches'/f'{decision}-{len(prior):04d}'
        save_bytes(attempt/'request.json',request_bytes)
        if gate is not None:gate()
        began=timer.begin(attempt_id,430)
        start=dict(id=ident,started_at=now(),freeze_sha256=freeze_hash,phase=phase,requested_model='claude-opus-5-5',requested_effort='medium')
        save(attempt/'start.json',dict(start,id=attempt_id,call=ident))
        try:raw=transport.generate(request,directory)
        except Exception as exc:raw=dict(stdout=b'',stderr=(type(exc).__name__+': '+str(exc)).encode(),returncode=None,harness_error='unexpected adapter exception; ambiguous start')
        stdout=raw.pop('stdout');stderr=raw.pop('stderr')
        save_bytes(attempt/'stdout',stdout);save_bytes(attempt/'stderr',stderr)
        raw=dict(raw,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr));save(attempt/'raw.json',raw)
        env=None
        try:env=transport_load(stdout.decode())
        except (ValueError,UnicodeError):pass
        refusal_env=None
        try:refusal_env=strict_load(stdout.decode())
        except (ValueError,UnicodeError):pass
        if is_usage_limit(refusal_env,raw):
            timer.end(attempt_id,began)
            pause=ensure_pause(base,attempt,ledger,timer)
            return dict(usage_limit_pause=pause)
        # Publish exact dispatch evidence at the unchanged canonical call position.
        stem=directory/str(decision)
        for suffix,data in [('request.json',request_bytes),('start.json',(canonical(start)+'\n').encode()),('stdout',stdout),('stderr',stderr),('raw.json',(canonical(raw)+'\n').encode())]:
            save_bytes(str(stem)+'.'+suffix,data)
        calls.append(ident);parsed=None;tin=tout=actual=None
        try:
            if raw.get('harness_error'):raise Stop(raw['harness_error'])
            if type(env) is not dict:raise Stop('invalid transport JSON envelope')
            tin,tout=usage(env,'claude');actual=cost_micro(tin,tout,env)
            ledger.event(event='settle',id=ident,episode=ep['id'],reserved=bound['micro_usd'],actual=actual)
            if ledger.blocked or tin>bound['input_tokens'] or tout>512:raise Stop('measured reservation overrun; settled in full')
            parsed=decode(env,raw,ep,phase,bound,fake)
        except Stop as exc:error=str(exc);fatal=True;failure_kind='fatal'
        except TransportFailure as exc:error=str(exc);failure_kind='transport'
        except (EpisodeFailure,ModelOutputError) as exc:error=str(exc);failure_kind='content'
        except Exception as exc:error=type(exc).__name__+': '+str(exc);fatal=True;failure_kind='fatal'
        if not (base/'claude-contract.json').exists():
            save(base/'claude-contract.json',dict(status='FAIL' if fatal else ('PASS' if error is None else 'MODEL_FAILURE'),call=ident,
                freeze_sha256=freeze_hash,strict_valid=error is None,error=error,fatal=fatal,failure_kind=failure_kind,
                num_turns=env.get('num_turns') if type(env) is dict else None,
                returned_effort=env.get('effort','UNKNOWN') if type(env) is dict else 'UNKNOWN',structured_output_only=True,scored_and_charged=True))
        save(str(stem)+'.parsed.json',dict(value=parsed,error=error,fatal=fatal,input_tokens=tin,output_tokens=tout,
            failure_kind=failure_kind,actual_micro_usd=actual,usage_status='UNKNOWN' if tin is None or tout is None else 'KNOWN',
            stop_reason=env.get('stop_reason') if type(env) is dict else None,returned_effort=env.get('effort','UNKNOWN') if type(env) is dict else 'UNKNOWN'))
        if error is None:
            if phase=='report':final=parsed
            else:world.step(parsed);save(str(stem)+'.event.json',world.events[-1])
        timer.end(attempt_id,began)
        save(attempt/'accepted.json',dict(call=ident,files={p.name:sha(p.read_bytes()) for p in directory.glob(str(decision)+'.*')}))
    terminal=dict(episode=ep,calls=calls,events=world.events,artifacts=world.artifacts,delivered=world.delivered,
        ended=world.ended,report=final,technically_complete=error is None and world.ended and final is not None,error=error,fatal=fatal,failure_kind=failure_kind)
    save(directory/'episode.json',terminal)
    if fatal:
        if not ledger.blocked:ledger.event(event='stop',id=ep['id'],reason=error)
        durable_stop(base,error)
    else:ledger.event(event='release',id=ep['id'])
    return terminal


def audit_nonstarts(base):
    """Verify operational records independently of model-call scoring and resource totals."""
    base=Path(base);events=[]
    for attempt in sorted(base.glob('episodes/*/dispatches/*')):
        if (attempt/'accepted.json').exists():
            accepted=read(attempt/'accepted.json');directory=attempt.parent.parent;d=attempt.name.split('-')[0]
            for name,digest in accepted['files'].items():
                if Path(name).name!=name or sha((directory/name).read_bytes())!=digest:raise Stop('accepted model evidence changed')
            for src,dest in [('request.json',d+'.request.json'),('stdout',d+'.stdout'),('stderr',d+'.stderr'),('raw.json',d+'.raw.json')]:
                if (attempt/src).read_bytes()!=(directory/dest).read_bytes():raise Stop('dispatch/canonical evidence differs')
            a=read(attempt/'start.json');s=read(directory/(d+'.start.json'))
            if dict(a,id=a['call'])!={**s,'call':s['id']}:raise Stop('dispatch/canonical start differs')
            continue
        req,start,env=refusal_evidence(attempt);path=attempt/'usage-limit-pause.json'
        if not path.exists():raise Stop('non-start needs durable pause reconstruction')
        pause=read(path)
        if (pause.get('kind')!='usage-limit pause' or pause.get('disposition')!='DEFINITE_NON_START' or
            pause.get('actual_micro_usd')!=0 or pause.get('attempt')!=start['id'] or pause.get('call')!=start['call'] or
            pause.get('reset_at')!=reset_time(env,start['started_at'])):raise Stop('non-start disposition changed')
        for name,digest in pause['files'].items():
            if Path(name).name!=name or sha((attempt/name).read_bytes())!=digest:raise Stop('non-start evidence changed')
        for name,digest in pause['history_files'].items():
            if Path(name).name!=name or sha((attempt.parent.parent/name).read_bytes())!=digest:raise Stop('prior history changed during usage-limit pause')
        check_prefixes(base,pause['journal_prefixes'])
        directory=attempt.parent.parent;d=attempt.name.split('-')[0]
        # All redispatches for this position and the canonical model call must use identical bytes.
        for other in dispatches(directory):
            if other.name.split('-')[0]==d and (other/'request.json').read_bytes()!=(attempt/'request.json').read_bytes():raise Stop('redispatch changed request bytes')
        canonical_request=directory/(d+'.request.json')
        if canonical_request.exists() and canonical_request.read_bytes()!=(attempt/'request.json').read_bytes():raise Stop('canonical request differs from non-start')
        events.append(dict(id=start['id'],call=start['call'],episode=directory.name,actor='claude',actual_micro_usd=0,
            reservation=req['reservation'],evidence=attempt.relative_to(base).as_posix(),request_sha256=sha((attempt/'request.json').read_bytes()),
            disposition='DEFINITE_NON_START',kind='usage-limit pause',reset_at=pause['reset_at']))
    return events
