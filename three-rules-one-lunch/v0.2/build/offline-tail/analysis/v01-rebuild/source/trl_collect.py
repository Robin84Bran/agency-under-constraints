"""Serial round-snapshot harness. Live entry requires freeze, push and readiness gates."""
import argparse
import datetime as dt
from pathlib import Path
import time
import uuid
from trl_core import ROOT, ACTORS, Simulator, canonical, generation_seed, render, roles, sha, strict_load
from trl_io import Stop, lock, now, read, save, stop, timestamp
from trl_budget import Ledger, ActiveTime, episode_hold, maximum, reservation
from trl_validation import LocalTransportFailure
from trl_transport import Claude, Local, Fake, cost, request, stdout, usage, validate


def push_gate(root, historical=False):
    from trl_freeze import verify, active_freeze
    root = Path(root)
    digest = verify(root)
    active = active_freeze(root)
    if active=='freeze-d5.json':
        from trl_d5 import provenance_layers
    elif active=='freeze-d4.json':
        from trl_d4 import provenance_layers
    elif active in ('freeze-d3c.json','freeze-d3d.json'):
        from trl_d3c import provenance_layers
    elif active=='freeze-d3b.json':
        from trl_d3b import provenance_layers
    else:
        from trl_d3 import provenance_layers
    layers = provenance_layers(root,active)
    if historical:
        layers = layers[:-1]
    for name,suffix,starts in layers:
        _push_layer(root,name,suffix,starts)
    return digest


def _push_layer(root,name,suffix,starts):
    from trl_freeze import push_record
    digest = sha((root/name).read_bytes())
    a = read(root/('collection/push'+suffix+'.json'))
    raw_event = (root/('collection/push-event'+suffix+'.raw.json')).read_bytes()
    event = strict_load(raw_event.decode())
    f = read(root/name)
    if a['freeze_sha256']!=digest or a['event_sha256']!=sha(raw_event) or a['repo']!='Robin84Bran/research':
        raise Stop('push attestation does not bind freeze/server event')
    ref,when = push_record(event,a['commit'])
    if (when!=a['pushed_at'] or ref!=a['remote_ref'] or event['id']!=a['server_event_id'] or
            a.get('freeze_file')!=name or
            a.get('original_freeze_sha256')!=sha((root/'freeze.json').read_bytes()) or
            a.get('source_api')!='/repos/Robin84Bran/research/'+('events' if event.get('type')=='PushEvent' else 'activity') or
            a.get('origin') not in ('git@github.com:Robin84Bran/research.git','https://github.com/Robin84Bran/research.git',
                                  'https://github.com/Robin84Bran/research','ssh://git@github.com/Robin84Bran/research.git')):
        raise Stop('push event mismatch')
    pushed = timestamp(a['pushed_at'])
    if not timestamp(f['created_at'])<=pushed<dt.datetime.now(dt.timezone.utc):
        raise Stop('push must follow freeze and precede starts')
    attested = timestamp(a['attested_at']) if 'attested_at' in a else pushed
    if (name in ('freeze-d3c.json','freeze-d3d.json','freeze-d4.json','freeze-d5.json') and 'attested_at' not in a or
        not pushed<=attested<dt.datetime.now(dt.timezone.utc)):
        raise Stop('invalid or missing attestation time')
    for rel in starts:
        p = root/rel
        s = read(p)
        if s['freeze_sha256']!=digest or timestamp(s['started_at'])<=attested:
            raise Stop('push/start integrity mismatch')
    return digest


def readiness(root):
    """D1 is a frozen empirical method, not an assertion of advance certainty."""
    from trl_freeze import verify, active_freeze
    root = Path(root)
    if active_freeze(root) not in ('freeze-d1.json','freeze-d2.json','freeze-d3.json','freeze-d3b.json','freeze-d3d.json','freeze-d4.json','freeze-d5.json'):
        raise Stop('reviewed D1 freeze required before inference')
    verify(root)


def episode(ep,transport,base,ledger,timer,freeze_hash,cohort_run_id=None):
    """Callable by offline fixtures; CLI never offers a fake bypass for live collection."""
    directory = Path(base)/'episodes'/ep['id']
    directory.mkdir(parents=True,exist_ok=True)
    if list(directory.iterdir()):
        raise Stop('episode already contains evidence; never resend an uncertain start')
    paid = ep['actor']=='claude'
    if paid:
        ledger.event(event='reserve',id=ep['id'],amount=episode_hold(ep['regime']))
    sim, calls, error, fatal = Simulator(ep['seed']),[],None,False
    started_at = now()
    transport_failure = False
    for r in range(1,5):
        values, attempted_slots = {},[]
        snapshot = [x[:] for x in sim.receipts]
        for role in roles(ep['regime']):
            quota = 3 if role==0 else 1
            key = f'r{r}-j{role}'
            call_id = ep['id']+'-'+key
            prompt = render(ep['regime'],r,role,snapshot)
            sizing = reservation(prompt,quota)
            bound = maximum(ep['regime'])
            req = request(ep['actor'],prompt,quota,generation_seed(ep['seed'],r,role),bound)
            timer.admit(420 if paid else 180)
            save(directory/(key+'.request.json'),{'id':call_id,'round':r,'role':role,'quota':quota,
                'prompt':prompt,'prompt_sha256':sha(prompt.encode()),'request':req,
                'request_sha256':sha(canonical(req).encode()),'sizing':sizing,'reservation':bound,
                'generation_seed':generation_seed(ep['seed'],r,role),'requested_effort':'medium' if paid else None})
            # Allocation is flushed before the unique start, both precede dispatch.
            if paid:
                ledger.event(event='start',id=call_id,episode=ep['id'],amount=bound['micro_usd'])
            save(directory/(key+'.start.json'),{'id':call_id,'started_at':now(),'freeze_sha256':freeze_hash})
            attempted_slots.extend((1,2,3) if role==0 else (role,))
            began = time.monotonic()
            try:
                raw = transport.generate(ep['actor'],req,directory)
            except Exception as exc:
                from trl_transport import raw_record
                raw = raw_record(b'',str(exc).encode(),None,transport_error=type(exc).__name__)
            save(directory/(key+'.raw.json'),raw)
            u, envelope, parsed = None,None,None
            try:
                envelope = strict_load(stdout(raw))
                u = usage(envelope,ep['actor'])
            except (ValueError,KeyError,TypeError,UnicodeError):
                pass
            # Complete failed-call usage is charged too, before validating action content.
            if paid:
                if u is None:
                    ledger.event(event='unknown',id=call_id)
                    fatal,error = True,'usage UNKNOWN; outstanding episode hold retained'
                else:
                    overrun = sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>1024
                    ledger.event(event='settle',id=call_id,actual=cost(u),overrun=overrun)
                    if ledger.stopped:
                        fatal,error = True,'reservation/output overrun; actual charged, durable stop'
            try:
                parsed,envelope,u = validate(raw,ep['actor'],quota,bound)
            except (ValueError,KeyError,TypeError,Stop) as exc:
                error = error or str(exc)
                transport_failure |= isinstance(exc,LocalTransportFailure)
                fatal |= not isinstance(exc,LocalTransportFailure) and (isinstance(exc,Stop) or envelope is None)
            # The first scheduled Claude call is the contract check, never a probe.
            # Its raw bytes and reported charge survive failure; no second dispatch.
            if paid and len(ledger.starts)==1:
                contract_ok = error is None and type(envelope) is dict and type(envelope.get('structured_output')) is dict
                save(Path(base)/'claude-contract.json',{'call_id':call_id,'checked_at':now(),
                    'freeze_sha256':freeze_hash,'status':'PASS' if contract_ok else 'FAIL',
                    'raw_sha256':sha(canonical(raw).encode()),'error':error})
                if not contract_ok:
                    fatal,error = True,error or 'first Claude structured_output contract failed'
            elapsed = time.monotonic()-began
            result = {'id':call_id,'round':r,'role':role,'value':parsed if error is None else None,
                'error':error,'usage':u,'elapsed_seconds':elapsed,'finished_at':now(),
                'returned_model':list(envelope.get('modelUsage',{})) if paid and type(envelope) is dict else (envelope.get('model') if type(envelope) is dict else None),
                'returned_effort':envelope.get('effort','UNKNOWN') if paid and type(envelope) is dict else None,
                'raw_envelope':envelope,'payload':envelope.get('structured_output') if paid and type(envelope) is dict else parsed}
            save(directory/(key+'.parsed.json'),result)
            calls.append(result)
            if error:
                break
            values[role] = parsed
        if error:
            sim.terminate(error,attempted_slots)
            break
        sim.execute(ep['regime'],values)
        save(directory/(f'round-{r}.json'),sim.events[-3:])
    if paid and all(k in ledger.settled for k,v in ledger.starts.items() if v['episode']==ep['id']):
        ledger.event(event='release',id=ep['id'])
    result = {'episode':ep,'kind':'FAKE' if isinstance(transport,Fake) else 'MODEL',
        'started_at':started_at,'finished_at':now(),'attempted_calls':len(calls),
        'complete':error is None and len(calls)==4*len(roles(ep['regime'])),
        'error':error,'fatal':bool(fatal),'events':sim.events,'receipts':sim.receipts}
    if cohort_run_id is not None:
        result.update(cohort_run_id=cohort_run_id,transport_failure=transport_failure)
    save(directory/'episode.json',result)
    if fatal:
        stop(base,error)
        raise Stop(error)
    return result


def collect(root,cohort):
    root = Path(root)
    digest = push_gate(root)   # Before model-service access or transport construction.
    readiness(root)
    base = root/'collection'
    with lock(base/'collector.lock'):
        from trl_freeze import active_freeze
        if push_gate(root)!=digest:
            raise Stop('active push changed before admission')
        cleared = None
        d5 = active_freeze(root)=='freeze-d5.json'
        d4 = active_freeze(root) in ('freeze-d4.json','freeze-d5.json')
        resumable = set()
        d3b = active_freeze(root) in ('freeze-d3b.json','freeze-d3d.json','freeze-d4.json','freeze-d5.json')
        if d5:
            from trl_d5 import admission
            cleared,resumable = admission(root)
        elif d4:
            from trl_d4 import admission
            cleared,resumable = admission(root)
        elif active_freeze(root)=='freeze-d3d.json':
            from trl_d3c import stop_gate
            cleared = stop_gate(root)
        elif d3b:
            from trl_d3b import stop_gate
            cleared = stop_gate(root)
        elif active_freeze(root)=='freeze-d3.json':
            from trl_d3 import stop_gate
            cleared = stop_gate(root)
        elif active_freeze(root)=='freeze-d2.json':
            from trl_d2 import stop_gate
            cleared = stop_gate(root)
        elif (base/'STOP.json').exists():
            raise Stop('durable STOP exists')
        order = read(root/'config/episodes.json')
        selected = [e for e in order if (e['actor']=='claude')==(cohort=='claude')]
        if cohort=='claude' and any(not (base/'episodes'/e['id']/'episode.json').exists() for e in order if e['actor']!='claude'):
            raise Stop('all mandatory local episodes must terminate before frontier')
        ledger = Ledger(base/'cost.jsonl')
        if ledger.stopped or any(v for v in ledger.holds.values()):
            raise Stop('uncertain/open prior reservation or durable cost stop')
        # Refuse partial episodes even when a crash occurred before its first call.
        for directory in (base/'episodes').glob('*'):
            if d4 and directory.name in resumable:
                continue
            if d4:
                if d5:
                    from trl_d5 import terminal_path
                else:
                    from trl_d4 import terminal_path
                terminal = terminal_path(directory)
            else:
                terminal = directory/'episode.json'
            if not terminal.exists():
                raise Stop('nonterminal episode; no resend; analyze retained evidence')
            historically_cleared = (cleared and directory.name in cleared.get('cleared_episodes',[cleared.get('episode_id')])
                                    and terminal == directory/'episode.json')
            if read(terminal).get('fatal') and not historically_cleared:
                raise Stop('terminal integrity failure; durable stop required')
        timer = ActiveTime(base/('time-'+cohort+'.jsonl'),10800 if cohort=='claude' else 43200)
        timer.begin(str(uuid.uuid4()))
        try:
            runtime = {}
            for ep in selected:
                directory = base/'episodes'/ep['id']
                if d4:
                    if d5:
                        from trl_d5 import terminal_path
                    else:
                        from trl_d4 import terminal_path
                    terminal = terminal_path(directory)
                    if terminal.exists() and directory.name not in resumable:
                        continue
                if (directory/'episode.json').exists() and directory.name not in resumable:
                    if not read(directory/'episode.json')['complete']:
                        # Malformed first replies remain terminal and are not rerun.
                        continue
                    continue
                actor = ep['actor']
                transport = Claude(root) if actor=='claude' else Local()
                if actor not in runtime:
                    timer.admit(420 if actor=='claude' else 180)
                    runtime[actor] = transport.preflight(actor)
                    save(base/'runtime'/(actor+'-'+timer.ident+'.json'),runtime[actor])
                    previous = sorted((base/'runtime').glob(actor+'-*.json'))
                    if any(read(p)!=runtime[actor] for p in previous):
                        raise Stop('runtime/template/default settings drift across resumes')
                if d4 and actor=='claude':
                    if d5:
                        from trl_d5 import episode as d4_episode
                    else:
                        from trl_d4 import episode as d4_episode
                    d4_episode(ep,transport,base,ledger,timer,digest,cohort_run_id=timer.ident)
                else:
                    episode(ep,transport,base,ledger,timer,digest,cohort_run_id=timer.ident if d3b else None)
                if d3b:
                    from trl_d3b import pause_if_needed
                    pause_if_needed(root)
        except Exception as exc:
            from trl_d3b import PauseStop
            from trl_d4 import UsageLimitPause
            if isinstance(exc,UsageLimitPause):
                return
            if not isinstance(exc,PauseStop):
                stop(base,str(exc))
            raise
        finally:
            timer.end()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--cohort',choices=['local','claude'],required=True)
    a = p.parse_args()
    from trl_d4 import UsageLimitPause
    try:
        collect(a.root,a.cohort)
    except UsageLimitPause as exc:
        print(str(exc))

if __name__=='__main__':
    main()
