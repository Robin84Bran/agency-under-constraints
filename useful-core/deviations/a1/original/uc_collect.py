"""Serial frozen runner. Importing this module never starts transport or collection."""
from pathlib import Path
from uc_core import ROOT,ACTORS,World,canonical,sha,strict_load,render,reserve,episode_reservation,P,SCHEMAS
from uc_store import Stop,EpisodeFailure,Journal,Ledger,ActiveTime,lock,save,save_bytes,read,now
from uc_transport import Local,Claude,usage,cost_micro,decode


def durable_stop(base,reason,cohort=None):
    path=Path(base)/('STOP-'+cohort+'.json' if cohort else 'STOP.json')
    if not path.exists():
        save(path,dict(reason=reason,time=now()))


def run_episode(ep,transport,base,ledger,timer,freeze_hash,fake=False,gate=None):
    base=Path(base);directory=base/'episodes'/ep['id'];directory.mkdir(parents=True,exist_ok=True)
    if (directory/'episode.json').exists() or list(directory.glob('*.start.json')):
        raise Stop('terminal or ambiguous episode cannot be resent')
    paid=ep['actor']=='claude'
    if paid:
        ledger.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
    world=World(ep['seed'],ep['world']);calls=[];final=None;error=None;fatal=False
    for index in range(1,8):
        phase='report' if world.ended else 'action'
        decision=7 if phase=='report' else index
        prompt=render(ep,world.history,6-len(world.history),phase);bound=reserve(prompt,phase)
        ident=ep['id']+f'-{decision}';stem=directory/str(decision)
        request=transport.request(ep,prompt,phase,decision,bound)
        save(str(stem)+'.request.json',dict(phase=phase,prompt=prompt,prompt_sha256=sha(prompt.encode()),system=P['system'],schema=SCHEMAS[phase],reservation=bound,outer=request))
        # Whole-episode hold is durable before this start; no silent subhold clipping.
        if gate is not None:
            gate()
        began=timer.begin(ident,430 if paid else 190)
        save(str(stem)+'.start.json',dict(id=ident,started_at=now(),freeze_sha256=freeze_hash,phase=phase,
                                        requested_model='claude-opus-5-5' if paid else request['model'],requested_effort='medium' if paid else None))
        calls.append(ident)
        try:
            raw=transport.generate(request,directory)
        except Exception as exc:
            raw=dict(stdout=b'',stderr=(type(exc).__name__+': '+str(exc)).encode(),returncode=None,transport_error='ambiguous start')
        # Raw bytes survive Unicode errors and JSON validation failures.
        stdout=raw.pop('stdout');stderr=raw.pop('stderr')
        save_bytes(str(stem)+'.stdout',stdout);save_bytes(str(stem)+'.stderr',stderr)
        save(str(stem)+'.raw.json',dict(raw,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)))
        parsed=None;tin=tout=actual=None;envelope=None
        first=paid and not (base/'claude-contract.json').exists()
        try:
            if stdout:
                try:
                    envelope=strict_load(stdout.decode('utf-8'))
                except (ValueError,UnicodeError) as exc:
                    if not paid and raw.get('transport_error'):
                        raise EpisodeFailure('ordinary local transport failure; partial envelope retained') from exc
                    raise Stop('invalid transport JSON envelope') from exc
                if type(envelope) is not dict:
                    envelope=None
                    raise Stop('envelope is not object')
                tin,tout=usage(envelope,ep['actor'])
            if paid:
                if envelope is None:
                    raise Stop('unknown paid usage/cost; hold retained')
                actual=cost_micro(tin,tout,envelope)
                ledger.event(event='settle',id=ident,episode=ep['id'],reserved=bound['micro_usd'],actual=actual)
                if ledger.blocked or tin>bound['input_tokens'] or tout>512:
                    raise Stop('measured reservation overrun; settled in full')
            if raw.get('returncode')!=0 or raw.get('transport_error'):
                raise EpisodeFailure('ordinary transport failure; no retry')
            if envelope is None:
                raise EpisodeFailure('empty transport response')
            parsed=decode(envelope,raw,ep,phase,bound,fake)
        except Stop as exc:
            error=str(exc);fatal=True
        except (EpisodeFailure,ValueError,TypeError,KeyError,UnicodeError) as exc:
            error=str(exc)
        if first:
            save(base/'claude-contract.json',dict(status='PASS' if error is None else 'FAIL',call=ident,
                freeze_sha256=freeze_hash,strict_valid=error is None,error=error,
                num_turns=None if envelope is None else envelope.get('num_turns'),
                returned_effort='UNKNOWN' if envelope is None else envelope.get('effort','UNKNOWN'),
                structured_output_only=True,scored_and_charged=True))
            if error:
                fatal=True
        save(str(stem)+'.parsed.json',dict(value=parsed,error=error,fatal=fatal,input_tokens=tin,output_tokens=tout,
              actual_micro_usd=actual if paid else 0,usage_status='UNKNOWN' if tin is None or tout is None else 'KNOWN',
              stop_reason=None if envelope is None else envelope.get('stop_reason',envelope.get('done_reason')),
              returned_effort=(envelope or {}).get('effort','UNKNOWN') if paid else None))
        if not error:
            if phase=='report':
                final=parsed
            else:
                world.step(parsed);save(str(stem)+'.event.json',world.events[-1])
        timer.end(ident,began)
        if error or phase=='report':
            break
    terminal=dict(episode=ep,calls=calls,events=world.events,artifacts=world.artifacts,delivered=world.delivered,
                  ended=world.ended,report=final,technically_complete=error is None and world.ended and final is not None,
                  error=error,fatal=fatal)
    save(directory/'episode.json',terminal)
    if fatal:
        if paid and not ledger.blocked:
            ledger.event(event='stop',id=ep['id'],reason=error)
        durable_stop(base,error)
    elif paid:
        ledger.event(event='release',id=ep['id'])
    return terminal


def check_frontier_contract(base,freeze_hash,schedule):
    """Resumes cannot silently replace a missing or changed first-call attestation."""
    base=Path(base)
    starts=[(read(p),p) for p in base.glob('episodes/*/*.start.json') if read(p).get('requested_model')=='claude-opus-5-5']
    path=base/'claude-contract.json'
    if not starts:
        if path.exists():raise Stop('orphan frontier contract')
        return
    if not path.exists():raise Stop('missing retained first frontier contract')
    contract=read(path);start,source=min(starts,key=lambda item:item[0]['started_at'])
    if contract.get('status')!='PASS' or contract.get('strict_valid') is not True or contract.get('call')!=start['id'] or contract.get('freeze_sha256')!=freeze_hash:
        raise Stop('first frontier contract failed or changed')
    stem=source.with_name(source.name.replace('.start.json',''))
    req=read(str(stem)+'.request.json');raw=read(str(stem)+'.raw.json');stdout=Path(str(stem)+'.stdout').read_bytes()
    if raw['stdout_sha256']!=sha(stdout):raise Stop('first frontier raw bytes changed')
    ep=next(e for e in schedule if e['id']==source.parent.name)
    value=decode(strict_load(stdout.decode()),raw,ep,req['phase'],req['reservation'])
    parsed=read(str(stem)+'.parsed.json')
    if parsed.get('value')!=value or parsed.get('error') is not None or contract.get('num_turns')!=strict_load(stdout.decode()).get('num_turns'):
        raise Stop('first frontier strict payload changed')


def collect(root=ROOT,cohort='local',binary=None):
    """This entry point requires a later collection delegation and push attestation."""
    root=Path(root);base=root/'collection'
    from uc_freeze import push_gate
    with lock(base):
        for p in (base/'STOP.json',base/f'STOP-{cohort}.json'):
            if p.exists():
                raise Stop('durable stop: '+read(p)['reason'])
        freeze_hash=push_gate(root)
        schedule=read(root/'config/episodes.json')
        if cohort=='claude':
            if not binary:
                raise Stop('explicit Claude binary required')
            for ep in schedule:
                if ep['actor']!='claude' and not (base/'episodes'/ep['id']/'episode.json').exists():
                    raise Stop('complete/account every local episode before frontier')
            check_frontier_contract(base,freeze_hash,schedule)
            transport=Claude(binary,root)
        else:
            transport=Local(root)
        ledger=Ledger(base/'ledger.jsonl');timer=ActiveTime(base/f'{cohort}-time.jsonl',7200 if cohort=='claude' else 43200)
        if ledger.blocked:
            raise Stop('ledger admission stopped')
        actors=['claude'] if cohort=='claude' else list(ACTORS[:-1])
        try:
            for actor in actors:
                ident=actor+'-preflight-'+str(len(timer.holds));began=timer.begin(ident,40)
                metadata=transport.preflight(actor)
                save(base/'preflight'/f'{ident}.json',metadata)
                runtime=base/'runtime'/f'{actor}.json'
                if runtime.exists() and read(runtime)!=metadata:
                    raise Stop('runtime identity/default/settings changed across resumes')
                if not runtime.exists():
                    save(runtime,metadata)
                timer.end(ident,began)
                consecutive=0
                for ep in [e for e in schedule if e['actor']==actor]:
                    directory=base/'episodes'/ep['id']
                    if (directory/'episode.json').exists():
                        terminal=read(directory/'episode.json')
                    else:
                        if list(directory.glob('*.start.json')):
                            raise Stop('ambiguous episode start; never resend')
                        terminal=run_episode(ep,transport,base,ledger,timer,freeze_hash,gate=lambda:push_gate(root))
                    if terminal['fatal']:
                        raise Stop(terminal['error'])
                    consecutive=consecutive+1 if terminal['error'] else 0
                    if consecutive>=3:
                        durable_stop(base,'three consecutive technical episode failures',cohort)
                        raise EpisodeFailure('cohort paused: three consecutive technical failures')
            return dict(settled_micro_usd=ledger.spent,outstanding_holds_micro_usd=sum(ledger.holds.values()),active_seconds=timer.charged)
        except Stop as exc:
            durable_stop(base,str(exc));raise
