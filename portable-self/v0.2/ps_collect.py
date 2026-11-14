"""Serial eight-call episodes; durable starts, holds and fail-closed resume."""
from pathlib import Path
import time
from ps_core import ROOT, World, render, reservation, episode_reservation, sha, strict_load
from ps_io import Stop, EpisodeFailure, TransportFailure, Ledger, ActiveTime, Journal, now, read, save, save_bytes, lock
from ps_transport import Local, Claude, decode, usage, cost_micro, provider_envelope, usage_limit_refusal
from ps_usage_limit import call_location, record_pause, pause_ready, audit_pauses, recover_pauses


def durable_stop(base,ledger,reason):
    if not ledger.blocked: ledger.event(event='stop',id='collection',reason=reason)
    if not (base/'STOP.json').exists(): save(base/'STOP.json',{'time':now(),'reason':reason})


def run_episode(ep,transport,base,ledger,timer,freeze_hash,fake=False):
    directory=base/'episodes'/ep['id']
    resuming=directory.exists()
    if resuming:
        if ep['actor']!='claude' or (directory/'episode.json').exists(): raise Stop('episode directory already exists; never replay started/prepared work')
        if not any(directory.glob('*.pause.json')): raise Stop('uncertain/prepared episode retained; never replay')
    else: directory.mkdir(parents=True)
    paid=ep['actor']=='claude'
    if paid and not resuming: ledger.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
    if not resuming: save(directory/'planned.json',ep)
    elif read(directory/'planned.json')!=ep: raise Stop('resumed episode plan changed')
    world=World(ep);error=None;attempted=0;fatal=False;transport_failure=False
    for index in range(8):
        payload=world.payload();prompt=render(payload);bound=reservation(ep['arm'],payload['mode'])
        prefix,pauses=call_location(directory,index);ident=ep['id']+'-'+prefix
        if (directory/f'{prefix}.event.json').exists():
            parsed,_=decode(read(directory/f'{prefix}.raw.json'),ep,payload,bound,fake)
            if read(directory/f'{prefix}.event.json')!={'index':index,'payload':payload,'value':parsed}: raise Stop('resumed history differs')
            world.step(parsed);attempted+=1;continue
        if (directory/f'{prefix}.request.json').exists(): raise Stop('uncertain/prepared call retained; never replay')
        if pauses and not pause_ready(pauses[-1]): return {'usage_limit_pause':pauses[-1]}
        if len(prompt.encode())>bound['prompt_bytes']: raise Stop('renderer exceeds frozen prompt byte bound')
        request=transport.request(ep,prompt,payload['mode'],bound,index)
        saved_request={'payload':payload,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),
             'transport_request':request,'reservation':bound,'generation_seed':None if paid else 1000*ep['seed']+index+1}
        if pauses:
            original=directory/f'{index}.request.json'
            if read(original)!=saved_request: raise Stop('usage-limit resume changed request/history')
            save_bytes(directory/f'{prefix}.request.json',original.read_bytes());request=read(original)['transport_request']
        else: save(directory/f'{prefix}.request.json',saved_request)
        began=timer.begin(ident,420 if paid else 180)
        if paid: ledger.event(event='start',id=ident,episode=ep['id'],reserved=bound['micro_usd'])
        save(directory/f'{prefix}.start.json',{'id':ident,'started_at':now(),'freeze_sha256':freeze_hash,
             'request_sha256':sha((directory/f'{prefix}.request.json').read_bytes()),
             'ledger_prefix_bytes':len(ledger.journal.raw),'ledger_prefix_sha256':sha(ledger.journal.raw)})
        attempted+=1
        try: raw=transport.generate(request,directory)
        except Exception as exc: raw={'stdout':'','stderr':'','returncode':None,'transport_error':type(exc).__name__+': '+str(exc)}
        save(directory/f'{prefix}.raw.json',raw)
        if paid and usage_limit_refusal(raw):
            return {'usage_limit_pause':record_pause(directory,prefix,ledger,timer,began)}
        fatal=False;parsed=None;metrics={'input_tokens':None,'output_tokens':None};actual=None if paid else 0
        try:
            e,_=provider_envelope(raw['stdout'],ep['actor']);tin,tout=usage(e,ep['actor'])
        except (ValueError,KeyError,TypeError,AttributeError): e={};tin=tout=None
        metrics.update(input_tokens=tin,output_tokens=tout)
        if paid:
            if tin is None or tout is None:
                fatal=True;error='unknown paid usage; hold retained'
            else:
                try:
                    actual=cost_micro(tin,tout,e)
                    ledger.event(event='settle',id=ident,actual=actual)
                    if actual>bound['micro_usd'] or tin>bound['input_tokens'] or tout>bound['output_tokens'] or ledger.exposure+1000000>25000000 or ledger.exposure+1000000>=39000000:
                        fatal=True;error='measured reservation overrun'
                except Exception as exc: fatal=True;error='paid accounting: '+str(exc)
        first_paid=paid and not (base/'frontier-contract.json').exists()
        try:
            parsed,decoded=decode(raw,ep,payload,bound,fake);metrics.update(decoded)
        except (Stop,EpisodeFailure) as exc:
            fatal=fatal or isinstance(exc,Stop);transport_failure=isinstance(exc,TransportFailure);error=error or str(exc)
        if error:
            save(directory/f'{prefix}.parsed.json',{'value':None,'error':error,'fatal':fatal,'metrics':metrics,'actual_micro_usd':actual})
            timer.end(ident,began)
            break
        save(directory/f'{prefix}.parsed.json',{'value':parsed,'error':None,'fatal':False,'metrics':metrics,'actual_micro_usd':actual})
        if first_paid:
            save(base/'frontier-contract.json',{'call_id':ident,'raw_sha256':sha((directory/f'{prefix}.raw.json').read_bytes()),
                 'strict_valid_structured_output':True,'metrics':metrics,'verified_at':now()})
        # Events contain validated decisions, never truth feedback in future inputs.
        save(directory/f'{prefix}.event.json',{'index':index,'payload':payload,'value':parsed})
        world.step(parsed);timer.end(ident,began)
    terminal={'episode':ep,'attempted_calls':attempted,'completed_calls':world.index,'error':error,'transport_failure':transport_failure,'ended_at':now(),
              'evidence_files':{p.name:sha(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}}
    save(directory/'episode.json',terminal)
    ledger.event(event='seal',id=ep['id'],terminal_sha256=sha((directory/'episode.json').read_bytes()))
    if fatal: durable_stop(base,ledger,error)
    if paid and not ledger.blocked: ledger.event(event='release',id=ep['id'])
    return terminal


def transport_pause(base,ledger,cohort):
    """Reconstruct sealed episodes, including a crash before the pause was saved."""
    streak=[]
    for ident,digest in ledger.sealed.items():
        path=base/'episodes'/ident/'episode.json'
        if sha(path.read_bytes())!=digest: raise Stop('transport streak terminal seal changed')
        terminal=read(path)
        if ('claude' if terminal['episode']['actor']=='claude' else 'local')!=cohort: continue
        streak=streak+[ident] if terminal.get('transport_failure',False) else []
        if len(streak)>=3:
            durable_stop(base,ledger,'three consecutive transport-failure episodes: '+','.join(streak[-3:]))
            raise Stop('durable transport-failure pause; reviewed amendment required')


def collect(root,cohort,binary=None,fake_transport=None,output=None,episodes=None):
    root=Path(root);fake=fake_transport is not None;base=Path(output) if output else root/'collection'
    if fake and base.resolve()==(root/'collection').resolve(): raise Stop('fake output must be isolated')
    with lock(base):
        ledger=Ledger(base/'ledger.jsonl')
        from ps_claude_clearance import audit_clearances
        audit_clearances(root,base,ledger)
        if ledger.blocked or (base/'STOP.json').exists(): raise Stop('durable stop; reviewed amendment required')
        if fake: freeze_hash='OFFLINE-FAKE'
        else:
            from ps_freeze import push_gate
            freeze_hash=push_gate(root)
        timer=ActiveTime(base/f'{cohort}-time.jsonl',10800 if cohort=='claude' else 86400)
        if cohort=='claude': recover_pauses(base,ledger,timer)
        audit_pauses(base,ledger)
        if not fake:
            from ps_analysis import score, audit_accounting, load_timing
            saved_schedule=read(root/'config/episodes.json')
            known={ep['id'] for ep in saved_schedule}
            if any(p.name not in known for p in (base/'episodes').glob('*')): raise Stop('unknown episode directory')
            timing=load_timing(base)
            previous=[score(ep,base,False,timing) for ep in saved_schedule]
            audit=audit_accounting(base,previous)
            if audit['unsealed_terminals']:
                durable_stop(base,ledger,'unsealed terminal after interruption');raise Stop('unsealed terminal')
            if set(ledger.started)-set(ledger.settled):
                durable_stop(base,ledger,'unreconciled paid call; hold retained');raise Stop('unreconciled paid call')
        transport_pause(base,ledger,cohort)
        schedule=episodes if episodes is not None else read(root/'config/episodes.json')
        actors=['claude'] if cohort=='claude' else ['qwen7b','llama8b','qwen1b']
        if not fake and cohort=='claude':
            for ep in schedule:
                if ep['actor']!='claude' and not (base/'episodes'/ep['id']/'episode.json').exists(): raise Stop('local cohort not fully accounted')
        transport=fake_transport or (Claude(root,binary) if cohort=='claude' and binary else Local(root))
        if cohort=='claude' and not binary and not fake: raise Stop('explicit Claude binary required')
        for actor in actors:
            todo=[ep for ep in schedule if ep['actor']==actor and not (base/'episodes'/ep['id']/'episode.json').exists()]
            if not todo: continue
            for ep in todo:
                if (base/'episodes'/ep['id']).exists() and not any((base/'episodes'/ep['id']).glob('*.pause.json')):
                    durable_stop(base,ledger,'uncertain/prepared episode retained; never replay');raise Stop('unreconciled episode')
            if not fake:
                token=actor+'-preflight-'+str(len(timer.holds));began=timer.begin(token,80)
                try:
                    metadata=transport.preflight(actor);save(base/'preflight'/f'{token}.json',metadata);timer.end(token,began)
                except Exception as exc:
                    durable_stop(base,ledger,'preflight failed: '+str(exc));raise
            for ep in todo:
                try:
                    terminal=run_episode(ep,transport,base,ledger,timer,freeze_hash,fake)
                    if 'usage_limit_pause' in terminal:
                        return {'status':'usage-limit pause','pause':terminal['usage_limit_pause'],'exposure_micro_usd':ledger.exposure,'settled_micro_usd':ledger.spent}
                except Exception as exc:
                    durable_stop(base,ledger,type(exc).__name__+': '+str(exc));raise
                if ledger.blocked: raise Stop(read(base/'STOP.json')['reason'])
                transport_pause(base,ledger,cohort)
        # Charge all collector overhead since the last saved settlement.
        tail='overhead-'+str(len(timer.holds));began=timer.begin(tail,0);timer.end(tail,began)
        return {'exposure_micro_usd':ledger.exposure,'settled_micro_usd':ledger.spent,'active_seconds':timer.charged,'real_model_calls':0 if fake else 'see retained starts'}
