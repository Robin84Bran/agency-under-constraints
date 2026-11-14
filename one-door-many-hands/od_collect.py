"""Serial, locked, reservation-before-start collection; builder uses fake only."""
from pathlib import Path
from http.client import HTTPException
import tempfile
from od_core import ROOT,ACTORS,render,reserve,canonical,sha
from od_io import Stop,read,save,lock,now,Ledger,ActiveTime,durable_stop,save_bytes
from od_transport import Local,Claude,CLAUDE_BIN,request
from od_identity import verify_preflight
from od_validation import validate,accounting,cost,ReplyFailure,TransportFailure
from od_recovery import transport_state,record_transport
from od_usage import refusal,network_nonstart,record_nonstart,episode_state,directories,attempt_id,pending_pause,stop_cleared


def run_episode(root,base,ep,transport,ledger,timer,freeze_hash,first=False,d3=False):
    previous=directories(base,ep['id'])
    if previous:
        terminal,events=episode_state(base,ep['id'])
        if terminal is not None or not events: raise Stop('existing episode cannot be replayed')
        if pending_pause(base,[ep]): return {'usage_limit_pause':events[-1]}
        directory=previous[0]/'usage-resumes'/f'{len(previous):04d}'
    else: directory=base/'episodes'/ep['id']
    prompt=render(ep);bound=reserve(prompt);req=request(ep,prompt,bound)
    if d3 and ep['actor']=='claude':
        from od_d3 import dispatch_bound,forecast
        forecast(root,base)
        bound=read(previous[0]/'request.json')['reservation'] if previous else dispatch_bound(base,prompt)
        req=request(ep,prompt,bound)
    directory.mkdir(parents=True)
    paid=ep['actor']=='claude';ident=attempt_id(ep['id'],len(previous))
    began=timer.begin(ident,310 if paid else 190)
    if paid: ledger.event(event='reserve',id=ident,amount=bound['micro_usd'])
    record={'episode':ep,'request':req,'prompt_sha256':sha(prompt.encode()),'reservation':bound}
    if previous:
        if read(previous[0]/'request.json')!=record: raise Stop('usage resume frozen request drift')
        save_bytes(directory/'request.json',(previous[0]/'request.json').read_bytes())
    else: save(directory/'request.json',record)
    start={'id':ep['id'],'started_at':now(),'freeze_sha256':freeze_hash,'revision':'A1'}
    if d3:start['accounting_revision']='D3'
    save(directory/'start.json',start)
    # Cwd creation/cleanup failures are harness failures, outside transport catch.
    with tempfile.TemporaryDirectory(prefix='one-door-call-') as work:
        try: raw=transport.generate(ep,req,Path(work))
        except (OSError,HTTPException) as exc:
            raw={'stdout_b64':'','stderr_b64':'','returncode':None,'transport_error':type(exc).__name__+': '+str(exc)}
        except Exception as exc:
            raw={'stdout_b64':'','stderr_b64':'','returncode':None,'harness_error':type(exc).__name__+': '+str(exc)}
        save(directory/'raw.json',raw)
    if paid and (refusal(raw) or network_nonstart(raw)):
        ledger.event(event='settle',id=ident,actual=0)
        timer.end(ident,began)
        pause=record_nonstart(directory)
        if ident in timer.breaches:
            durable_stop(base,'cumulative active time exceeded');raise Stop('cumulative active time exceeded')
        return {'usage_limit_pause':pause}
    u=accounting(raw,ep['actor'],d3=d3);fatal=None
    if paid:
        if u is None: fatal='unknown frontier usage/cost; full hold retained'
        else:
            actual=cost(u);ledger.event(event='settle',id=ident,actual=actual)
            if d3:
                from od_d3 import accounting_event,cap_check
                event=accounting_event(u,bound)
                if event:save(directory/'accounting.json',event)
                try:cap_check(ledger.exposure)
                except Stop as exc:fatal=str(exc)
            elif actual>bound['micro_usd'] or sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>bound['output_tokens'] or ledger.exposure+1000000>25000000 or ledger.exposure+1000000>=39000000: fatal='frontier reservation/accounting overrun'
    try: result=validate(raw,ep['actor'],bound,d3=d3)
    except (Stop,ReplyFailure,TransportFailure) as exc:
        result={'fleet':None,'schema_valid':False,'status':'TRANSPORT_FAILURE' if isinstance(exc,TransportFailure) else 'REPLY_FAILURE' if isinstance(exc,ReplyFailure) else 'ENVELOPE_FAILURE','reason':str(exc),'usage':u}
        if isinstance(exc,Stop): fatal=fatal or str(exc)
    timer.end(ident,began)
    if ident in timer.breaches: fatal=fatal or 'cumulative active time exceeded'
    result.update(attempted=True,first_frozen_compatibility_check=bool(paid and first),fatal=fatal,finished_at=now())
    save(directory/'episode.json',result)
    if paid and d3 and not fatal:
        from od_d3 import forecast
        try:forecast(root,base)
        except Stop as exc:
            durable_stop(base,str(exc));raise
    if fatal: durable_stop(base,fatal)
    return result


def check_existing(base,jobs,freeze_hash):
    expected={e['id']:e for e in jobs}
    directory=base/'episodes'
    for p in directory.iterdir() if directory.exists() else []:
        if p.name not in expected or not p.is_dir() or p.is_symlink(): raise Stop('unexpected episode path')
        terminal,events=episode_state(base,p.name)
        for d in directories(base,p.name):
            if read(d/'start.json')['freeze_sha256'] not in freeze_hash: raise Stop('existing start freeze mismatch')
    return {p.name for p in directory.iterdir() if episode_state(base,p.name)[0] is not None} if directory.exists() else set()



def collect(root=ROOT,cohort='local',binary=CLAUDE_BIN,fake_transport=None,output=None,jobs_override=None):
    root=Path(root);fake=fake_transport is not None;base=Path(output) if output else root/'collection'
    if fake and (output is None or base.resolve()==(root/'collection').resolve()): raise Stop('fake must use separate output')
    if not fake and (jobs_override is not None or output is not None): raise Stop('live fixed schedule/output only')
    with lock(base):
        if (base/'STOP.json').exists() and not stop_cleared(base): raise Stop('durable STOP: '+read(base/'STOP.json')['reason'])
        from od_freeze import verify,push_gate
        freeze_hash='FAKE-OFFLINE' if fake else push_gate(root)
        jobs=jobs_override if fake and jobs_override is not None else read(root/'config/episodes.json')
        from od_provenance import allowed_hashes
        existing=check_existing(base,jobs,{freeze_hash} if fake else allowed_hashes(root))
        ledger=Ledger(base/'ledger.jsonl')
        d3=bool(getattr(fake_transport,'d3',False)) if fake else (root/'freeze-d3.json').exists()
        known_attempts={attempt_id(e['id'],i) for e in jobs for i,_ in enumerate(directories(base,e['id']))}
        if set(ledger.reservations)-known_attempts: raise Stop('unresolved reserved episode; no resend')
        timer=ActiveTime(base/(cohort+'-time.jsonl'),7200 if cohort=='claude' else 28800)
        if timer.breaches: raise Stop('cumulative active time exceeded')
        # Prefix checks precede recovery. A crash cannot lose the third-failure pause.
        state=transport_state(base,jobs,cohort);pause=state['reason']
        if pause:
            durable_stop(base,pause);raise Stop(pause)
        if not fake:
            # Verify all prior raw/request/terminal/ledger evidence before resuming.
            from od_analysis import replay
            replay(root,base,allow_fake=False)
        if cohort=='claude' and not fake:
            local=[e for e in jobs if e['actor']!='claude']
            if any(e['id'] not in existing for e in local): raise Stop('finish all 3600 local episodes before Claude')
        pause=pending_pause(base,jobs)
        if pause: return {'kind':'usage-limit pause','cohort':cohort,'pause':pause}
        actors=('claude',) if cohort=='claude' else ACTORS[:3]
        for actor in actors:
            actor_jobs=[e for e in jobs if e['actor']==actor]
            pending=[e for e in actor_jobs if e['id'] not in existing]
            if not pending: continue
            if not fake: verify(root)
            t=fake_transport or (Claude(root,binary) if actor=='claude' else Local(root))
            try:
                preid=f'preflight-{actor}-{len(timer.holds)}'
                began=timer.begin(preid,40)
                preflight=t.preflight(actor)
                timer.end(preid,began)
                if preid in timer.breaches: raise Stop('cumulative preflight time exceeded')
                prepath=base/'preflight'/actor
                old=sorted(prepath.glob('*.json')) if prepath.exists() else []
                save(prepath/f'{len(old):04d}.json',preflight)
                if not fake: verify_preflight(root,actor,preflight)
                if old and read(old[0])!=preflight: raise Stop('runtime/identity drift across resumes')
                for ep in pending:
                    if not fake: verify(root)
                    result=run_episode(root,base,ep,t,ledger,timer,freeze_hash,first=actor=='claude' and not any(e['actor']=='claude' and episode_state(base,e['id'])[0] is not None for e in jobs),d3=d3)
                    if 'usage_limit_pause' in result: return {'kind':result['usage_limit_pause']['kind'],'cohort':cohort,'pause':result['usage_limit_pause']}
                    if result['fatal']: raise Stop(result['fatal'])
                    record_transport(state,ep['id'],result)
                    if state['reason']: raise Stop(state['reason'])
            except Exception as exc:
                durable_stop(base,exc);raise
        return {'kind':'FAKE' if fake else 'COLLECTION','cohort':cohort,'spent_micro_usd':ledger.spent,'open_holds_micro_usd':sum(ledger.holds.values())}
