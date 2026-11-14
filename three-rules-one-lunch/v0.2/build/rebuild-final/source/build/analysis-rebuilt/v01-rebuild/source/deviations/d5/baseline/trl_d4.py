"""D4: exact zero-usage subscription refusals are durable, resumable non-starts."""
import datetime as dt
from pathlib import Path
import re
import time
import uuid
from zoneinfo import ZoneInfo
from trl_core import canonical, generation_seed, render, roles, sha, strict_load, Simulator
from trl_io import Stop, now, read, save, timestamp
from trl_validation import stdout, usage, cost, validate
from trl_budget import Ledger, maximum, reservation, episode_hold
from trl_d3 import LEDGERS, verify_prefix

CLEARANCE = 'deviations/d4/clearance.json'


class UsageLimitPause(Stop):
    """Clean exit with saved evidence; never converted into an integrity STOP."""


def nonzero_counter(value):
    if type(value) is dict:
        return any(nonzero_counter(v) for v in value.values())
    if type(value) is list:
        return any(nonzero_counter(v) for v in value)
    return type(value) in (int,float) and value != 0


def refusal(raw):
    """Fail closed: only an entire recognized limit message, with no generation."""
    try:
        if type(raw) is not dict or type(raw.get('returncode')) is not int or raw['returncode'] != 1 or raw.get('transport_error'):
            return None
        e = strict_load(stdout(raw))
        u = usage(e, 'claude')
        if (type(e) is not dict or type(e.get('api_error_status')) is not int or e['api_error_status'] != 429 or
            e.get('is_error') is not True or e.get('type') != 'result' or
            e.get('api_error') != 'usage_limit_reached' or e.get('modelUsage') != {} or
            type(e.get('total_cost_usd')) not in (int, float) or e['total_cost_usd'] != 0 or
            u is None or any(u[k] != 0 for k in ('input','output','cache_read','cache_creation')) or
            e.get('structured_output') is not None or e.get('permission_denials') != [] or
            nonzero_counter(e.get('usage')) or nonzero_counter(e.get('subagent_stats')) or
            any(e.get(k) for k in ('tool_calls','tool_uses','deferred_tool_use','errors','safety_stops'))):
            return None
        # Other numeric usage leaves (thinking/cache/tool counters) must also be zero.
        m = re.fullmatch(r"You've hit your 5-hour limit · resets (\d{1,2})(?::(\d{2}))?(am|pm) \(([^()]+)\)", e.get('result',''))
        if not m or not 1 <= int(m[1]) <= 12 or int(m[2] or 0) > 59:
            return None
        ZoneInfo(m[4])
        return e
    except (ValueError, KeyError, TypeError, UnicodeError):
        return None


def reset_at(raw, observed):
    e = refusal(raw)
    if e is None:
        raise Stop('not a definite usage-limit non-start')
    m = re.search(r'resets (\d{1,2})(?::(\d{2}))?(am|pm) \(([^()]+)\)', e['result'])
    local = timestamp(observed).astimezone(ZoneInfo(m[4]))
    reset = local.replace(hour=int(m[1]) % 12 + (12 if m[3]=='pm' else 0), minute=int(m[2] or 0), second=0, microsecond=0)
    if reset <= local:
        reset += dt.timedelta(days=1)
    return reset.astimezone(dt.timezone.utc).isoformat()


def inventory(root):
    root = Path(root)
    result = {}
    for p in sorted((root/'collection').rglob('*')):
        if p.is_symlink():
            raise Stop('symlink collection evidence')
        if p.is_file() and not p.name.endswith('.lock'):
            result[p.relative_to(root).as_posix()] = sha(p.read_bytes())
    return result


def clearance(root):
    root = Path(root)
    c = read(root/CLEARANCE)
    if (c.get('deviation') != 'D4' or c.get('disposition') != 'DEFINITE_NON_START_RESUME_IDENTICAL' or
        not c.get('reviewer') or not c.get('reason')):
        raise Stop('invalid D4 clearance')
    for n,h in c['preserved_files'].items():
        p = root/n
        if n in LEDGERS:
            verify_prefix(root,n,c['ledger_prefixes'][n],h)
        elif p.is_symlink() or sha(p.read_bytes()) != h:
            raise Stop('D4 preserved evidence changed: '+n)
    if set(c['ledger_prefixes']) != set(c['preserved_files']) & LEDGERS:
        raise Stop('D4 ledger prefix inventory mismatch')
    for event in c['events']:
        prefix = root/event['prefix']
        raw = read(Path(str(prefix)+'.raw.json'))
        if (refusal(raw) is None or event['reset_at'] != reset_at(raw,event['observed_at']) or
            event['request_sha256'] != sha(Path(str(prefix)+'.request.json').read_bytes())):
            raise Stop('D4 refusal evidence changed')
    return c


def record_clearance(root, reviewer, reason):
    """Record re-disposition from saved bytes. Never change STOP, terminal or ledgers."""
    from trl_d3c import clearance as prior_clearance
    from trl_d3b import stop_paths
    from trl_analysis import replay
    root = Path(root)
    if (root/CLEARANCE).exists():
        raise FileExistsError(CLEARANCE+' is create-once')
    if not reviewer.strip() or not reason.strip():
        raise Stop('named reviewer and reason required')
    prior = prior_clearance(root)
    ledger = Ledger(root/'collection/cost.jsonl')
    if ledger.stopped or any(ledger.holds.values()):
        raise Stop('D4 cannot clear uncertain costs or open holds')
    events, paused = [], []
    for p in sorted((root/'collection/episodes').glob('*/*.raw.json')):
        if not p.parent.name.startswith('claude-') or refusal(read(p)) is None:
            continue
        prefix = Path(str(p)[:-9])
        parsed = read(Path(str(prefix)+'.parsed.json'))
        req = read(Path(str(prefix)+'.request.json'))
        terminal = read(p.parent/'episode.json')
        key = prefix.name
        row = replay(terminal['episode'],p.parent)
        if (terminal.get('complete') is not False or not terminal.get('fatal') or
            terminal.get('error') != parsed.get('error') or
            terminal.get('error') != 'transport failed/uncertain start; no resend' or
            parsed.get('value') is not None or parsed['raw_envelope'] != refusal(read(p)) or
            req['id'] != parsed['id'] or read(Path(str(prefix)+'.start.json'))['id'] != req['id'] or
            ledger.settled.get(req['id'],{}).get('actual') != 0 or row['complete'] or
            terminal['attempted_calls'] != len(list(p.parent.glob('*.start.json'))) or
            sorted(p.parent.glob('*.raw.json'))[-1] != p or
            (p.parent/f'round-{req["round"]}.json').exists()):
            raise Stop('D4 historical non-start does not match terminal evidence')
        events.append({'episode_id':terminal['episode']['id'],'key':key,
            'prefix':prefix.relative_to(root).as_posix(),'observed_at':parsed['finished_at'],
            'reset_at':reset_at(read(p),parsed['finished_at']),
            'request_sha256':sha(Path(str(prefix)+'.request.json').read_bytes()),
            'disposition':'DEFINITE_NON_START','previous_disposition':'terminal technical/transport failure',
            'settled_micro_usd':0})
        paused.append(terminal['episode']['id'])
    clear_stops = []
    for p in stop_paths(root):
        if 'collection/'+p.name in prior['preserved_files'] or (root/'collection/d3b-clearances'/p.name).exists():
            continue
        s = read(p)
        if (s.get('reason') != 'transport failed/uncertain start; no resend' or len(events) != 1 or
            timestamp(s['time']) < timestamp(events[0]['observed_at'])):
            raise Stop('D4 cannot clear unrelated integrity STOP')
        clear_stops.append(p.name)
    for d in (root/'collection/episodes').iterdir():
        if not (d/'episode.json').exists():
            raise Stop('D4 cannot clear unrelated partial episode')
        if read(d/'episode.json').get('fatal') and d.name not in prior['cleared_episodes']+paused:
            raise Stop('D4 cannot clear unrelated fatal episode')
    if any(p.name not in {'STOP.json','STOP-d2.json'}|{p.name for p in stop_paths(root)} for p in (root/'collection').glob('STOP*.json')):
        raise Stop('D4 cannot clear unknown STOP')
    files = inventory(root)
    value = {'deviation':'D4','kind':'usage-limit pause','recorded_at':now(),'reviewer':reviewer,'reason':reason,
        'disposition':'DEFINITE_NON_START_RESUME_IDENTICAL','events':events,'paused_episodes':paused,
        'cleared_stops':clear_stops,'cleared_episodes':prior['cleared_episodes']+paused,
        'preserved_files':files,'ledger_prefixes':{n:{'bytes':(root/n).stat().st_size,'sha256':h} for n,h in files.items() if n in LEDGERS}}
    save(root/CLEARANCE,value)
    return clearance(root)


def is_cleared_stop(root,p):
    root = Path(root)
    if not (root/CLEARANCE).exists():
        return False
    c = clearance(root)
    return p.name in c['cleared_stops'] and c['preserved_files'].get('collection/'+p.name) == sha(p.read_bytes())


def provenance_layers(root, active='freeze-d4.json'):
    from trl_d3c import provenance_layers as prior_layers
    root = Path(root)
    c = clearance(root)
    old = set(c['preserved_files'])
    layers = prior_layers(root,'freeze-d3d.json')
    layers[-1] = (*layers[-1][:2],layers[-1][2] & old)
    starts = {p.relative_to(root).as_posix() for folder in ('episodes','d4-episodes') for p in (root/'collection'/folder).rglob('*.start.json')}
    layers.append(('freeze-d4.json','-d4',starts-old))
    return layers


def prepush_gate(root):
    c = clearance(root)
    if provenance_layers(root)[-1][2]:
        raise Stop('D4 attestation must precede all D4 starts')
    return c


def stop_gate(root):
    from trl_d3c import stop_gate as prior_gate
    c = clearance(root)
    prior_gate(root)
    return c


def call_prefixes(directory,key):
    """Original call first; append-only attempts live outside original episode evidence."""
    directory = Path(directory)
    overlay = directory.parent.parent/'d4-episodes'/directory.name
    firsts = [p for p in (directory/key,overlay/key) if Path(str(p)+'.start.json').exists()]
    if len(firsts)>1:
        raise Stop('duplicate original D4 call')
    attempts_dir = overlay/'attempts'/key
    attempts = sorted(attempts_dir.glob('[0-9][0-9][0-9][0-9]')) if attempts_dir.exists() else []
    if [p.name for p in attempts] != [f'{n:04}' for n in range(1,len(attempts)+1)]:
        raise Stop('non-contiguous D4 attempt evidence')
    if attempts and not firsts:
        raise Stop('D4 retry without original non-start')
    return firsts + [p/'call' for p in attempts]


def terminal_path(directory):
    directory = Path(directory)
    overlay = directory.parent.parent/'d4-episodes'/directory.name/'episode.json'
    return overlay if overlay.exists() else directory/'episode.json'


def effective_calls(directory):
    result, events, used = {}, [], set()
    directory = Path(directory)
    for r in range(1,5):
        for j in range(4):
            key = f'r{r}-j{j}'
            prefixes = call_prefixes(directory,key)
            used.update(Path(str(p)+'.start.json') for p in prefixes)
            if prefixes:
                request_bytes = Path(str(prefixes[0])+'.request.json').read_bytes()
                if any(Path(str(p)+'.request.json').exists() and Path(str(p)+'.request.json').read_bytes() != request_bytes for p in prefixes[1:]):
                    raise Stop('D4 retry request bytes differ')
            for i,p in enumerate(prefixes):
                rawpath = Path(str(p)+'.raw.json')
                if not rawpath.exists():
                    raise Stop('uncertain D4 start; no resend')
                raw = read(rawpath)
                if refusal(raw) is not None:
                    events.append(p)
                    if i == len(prefixes)-1:
                        result[key] = None
                else:
                    if i != len(prefixes)-1:
                        raise Stop('D4 attempt after a model response/uncertain start')
                    result[key] = p
    overlay = directory.parent.parent/'d4-episodes'/directory.name
    actual = set(directory.glob('*.start.json')) | set(overlay.rglob('*.start.json'))
    if actual != used:
        raise Stop('unexpected extra D4 call evidence')
    return result, events


def pause_record(base,ep,key,prefix,observed):
    base, prefix = Path(base),Path(prefix)
    start = read(Path(str(prefix)+'.start.json'))
    files = {str(prefix.relative_to(base))+'.'+suffix:sha(Path(str(prefix)+'.'+suffix).read_bytes()) for suffix in ('request.json','start.json','raw.json','parsed.json')}
    value = {'deviation':'D4','kind':'usage-limit pause','disposition':'DEFINITE_NON_START',
        'episode_id':ep['id'],'key':key,'call_id':start['id'],'observed_at':observed,
        'reset_at':reset_at(read(Path(str(prefix)+'.raw.json')),observed),'files':files,
        'request_sha256':files[str(prefix.relative_to(base))+'.request.json'],'settled_micro_usd':0}
    save(base/'usage-limit-pauses'/(start['id']+'.json'),value)
    return value


def verify_pause(base,prefix):
    base,prefix = Path(base),Path(prefix)
    start = read(Path(str(prefix)+'.start.json'))
    p = base/'usage-limit-pauses'/(start['id']+'.json')
    if not p.exists():
        # Historical refusal is bound by the D4 clearance, not a fabricated new record.
        c = clearance(base.parent)
        matches = [e for e in c['events'] if e['prefix'] == prefix.relative_to(base.parent).as_posix()]
        if len(matches) != 1:
            raise Stop('missing durable usage-limit pause')
        return matches[0]
    record = read(p)
    if record.get('kind') != 'usage-limit pause' or record.get('disposition') != 'DEFINITE_NON_START':
        raise Stop('invalid usage-limit pause record')
    for name,digest in record['files'].items():
        if sha((base/name).read_bytes()) != digest:
            raise Stop('usage-limit pause evidence changed')
    if record['reset_at'] != reset_at(read(Path(str(prefix)+'.raw.json')),record['observed_at']):
        raise Stop('usage-limit pause reset changed')
    return record


def pending(base):
    base = Path(base)
    waiting = []
    for d in (base/'episodes').iterdir():
        calls, events = effective_calls(d)
        if any(p is None for p in calls.values()):
            last = events[-1]
            record = verify_pause(base,last)
            waiting.append((d.name,last,record))
    if len(waiting)>1:
        raise Stop('multiple pending usage-limit positions')
    return waiting


def admission(root):
    root = Path(root)
    c = stop_gate(root)
    overlay = root/'collection/d4-episodes'
    if overlay.exists() and any(not (root/'collection/episodes'/p.name).is_dir() for p in overlay.iterdir()):
        raise Stop('orphan D4 continuation evidence')
    waits = pending(root/'collection')
    for ident,p,record in waits:
        if timestamp(now()) <= timestamp(record['reset_at']):
            raise UsageLimitPause('usage-limit pause until '+record['reset_at'])
    return c,{ident for ident,_,_ in waits}


def episode(ep,transport,base,ledger,timer,freeze_hash,cohort_run_id=None):
    """Replay saved history, dispatch only a new call or the proven non-start position."""
    from trl_transport import Fake, raw_record, request
    base = Path(base)
    directory = base/'episodes'/ep['id']
    directory.mkdir(parents=True,exist_ok=True)
    overlay = base/'d4-episodes'/ep['id']
    resumed = bool(list(directory.iterdir()))
    effective, refusals = effective_calls(directory)
    old_terminal = terminal_path(directory)
    if resumed and not any(v is None for v in effective.values()):
        raise Stop('terminal episode or partial evidence without a known non-start; never rerun')
    sim,calls,error,fatal = Simulator(ep['seed']),[],None,False
    starts = sorted(directory.glob('*.start.json'))
    started_at = read(old_terminal)['started_at'] if old_terminal.exists() else (min(read(p)['started_at'] for p in starts) if starts else now())
    allocation = ep['id']+'.d4-'+str(uuid.uuid4())
    reserved = False
    for r in range(1,5):
        values,attempted = {},[]
        snapshot = [x[:] for x in sim.receipts]
        for role in roles(ep['regime']):
            key = f'r{r}-j{role}'
            quota = 3 if role==0 else 1
            logical = ep['id']+'-'+key
            bound = maximum(ep['regime'])
            prompt = render(ep['regime'],r,role,snapshot)
            expected = {'id':logical,'round':r,'role':role,'quota':quota,'prompt':prompt,
                'prompt_sha256':sha(prompt.encode()),'request':request(ep['actor'],prompt,quota,generation_seed(ep['seed'],r,role),bound),
                'sizing':reservation(prompt,quota),'reservation':bound,'generation_seed':generation_seed(ep['seed'],r,role),'requested_effort':'medium'}
            expected['request_sha256'] = sha(canonical(expected['request']).encode())
            prefixes = call_prefixes(directory,key)
            if prefixes:
                first_bytes = Path(str(prefixes[0])+'.request.json').read_bytes()
                if read(Path(str(prefixes[0])+'.request.json')) != expected:
                    raise Stop('saved request/history differs from frozen request')
                for p in prefixes:
                    if refusal(read(Path(str(p)+'.raw.json'))) is not None:
                        verify_pause(base,p)
                    if Path(str(p)+'.request.json').read_bytes() != first_bytes:
                        raise Stop('D4 retry request bytes differ')
                last = prefixes[-1]
                if effective[key] is not None:
                    raw = read(Path(str(last)+'.raw.json'))
                    parsed = read(Path(str(last)+'.parsed.json'))
                    value,env,u = validate(raw,'claude',quota,bound)
                    sid = read(Path(str(last)+'.start.json'))['id']
                    if ledger.settled.get(sid,{}).get('actual') != cost(u):
                        raise Stop('saved model response has no matching cost settlement')
                    if parsed.get('error') is not None or parsed.get('value') != value or parsed.get('usage') != u:
                        raise Stop('saved successful call differs from raw validation')
                    values[role] = value
                    calls.append(parsed)
                    attempted.extend((1,2,3) if role==0 else (role,))
                    continue
                record = verify_pause(base,last)
                if timestamp(now()) <= timestamp(record['reset_at']):
                    raise UsageLimitPause('usage-limit pause until '+record['reset_at'])
                prefix = overlay/'attempts'/key/f'{len(prefixes):04}'/'call'
                ident = logical+f'.attempt-{len(prefixes):04}'
                request_bytes = first_bytes
            else:
                prefix,ident = (overlay if resumed else directory)/key,logical
                request_bytes = (canonical(expected)+'\n').encode()
            timer.admit(420)
            if not reserved:
                ledger.event(event='reserve',id=allocation,amount=episode_hold(ep['regime']))
                reserved = True
            # Keep the exact serialized request record, including original identity, on resend.
            request_path = Path(str(prefix)+'.request.json')
            request_path.parent.mkdir(parents=True,exist_ok=True)
            with request_path.open('xb') as f:
                f.write(request_bytes);f.flush();__import__('os').fsync(f.fileno())
            __import__('trl_io').syncdir(request_path.parent)
            ledger.event(event='start',id=ident,episode=allocation,amount=bound['micro_usd'])
            save(Path(str(prefix)+'.start.json'),{'id':ident,'logical_call_id':logical,'started_at':now(),'freeze_sha256':freeze_hash,'allocation':allocation})
            began = time.monotonic()
            try:
                raw = transport.generate('claude',read(request_path)['request'],request_path.parent)
            except Exception as exc:
                raw = raw_record(b'',str(exc).encode(),None,transport_error=type(exc).__name__)
            save(Path(str(prefix)+'.raw.json'),raw)
            env,u,value = None,None,None
            try:
                env = strict_load(stdout(raw));u = usage(env,'claude')
            except (ValueError,KeyError,TypeError,UnicodeError):
                pass
            is_limit = refusal(raw) is not None
            if u is None:
                ledger.event(event='unknown',id=ident)
                error,fatal = 'usage UNKNOWN; outstanding episode hold retained',True
            else:
                overrun = sum(u[k] for k in ('input','cache_read','cache_creation')) > bound['input_tokens'] or u['output']>1024
                ledger.event(event='settle',id=ident,actual=cost(u),overrun=overrun)
                if ledger.stopped:
                    error,fatal = 'reservation/output overrun; actual charged, durable stop',True
            if not is_limit:
                try:
                    value,env,u = validate(raw,'claude',quota,bound)
                except (ValueError,KeyError,TypeError,Stop) as exc:
                    error = error or str(exc)
                    fatal |= isinstance(exc,Stop) or env is None
                # A refusal never consumes the first actual Claude contract check.
                generated_before = [p for p in (base/'episodes').glob('claude-*/*.raw.json') if p != Path(str(prefix)+'.raw.json') and refusal(read(p)) is None]
                if not (base/'claude-contract.json').exists() and not generated_before:
                    ok = error is None and type(env) is dict and type(env.get('structured_output')) is dict
                    save(base/'claude-contract.json',{'call_id':ident,'checked_at':now(),'freeze_sha256':freeze_hash,
                        'status':'PASS' if ok else 'FAIL','raw_sha256':sha(canonical(raw).encode()),'error':error})
                    if not ok:
                        error,fatal = error or 'first Claude structured_output contract failed',True
            parsed = {'id':ident,'logical_call_id':logical,'round':r,'role':role,'value':value if error is None and not is_limit else None,
                'error':'usage-limit pause' if is_limit else error,'usage':u,'elapsed_seconds':time.monotonic()-began,'finished_at':now(),
                'returned_model':list(env.get('modelUsage',{})) if type(env) is dict else None,
                'returned_effort':env.get('effort','UNKNOWN') if type(env) is dict else None,'raw_envelope':env,
                'payload':env.get('structured_output') if type(env) is dict else None}
            if is_limit:
                parsed['operational_event'] = 'DEFINITE_NON_START'
            save(Path(str(prefix)+'.parsed.json'),parsed)
            if is_limit:
                ledger.event(event='release',id=allocation)
                record = pause_record(base,ep,key,prefix,parsed['finished_at'])
                raise UsageLimitPause('usage-limit pause until '+record['reset_at'])
            calls.append(parsed)
            attempted.extend((1,2,3) if role==0 else (role,))
            if error:
                break
            values[role] = value
        if error:
            sim.terminate(error,attempted)
            break
        sim.execute(ep['regime'],values)
        roundpath = directory/f'round-{r}.json'
        if not roundpath.exists() and (overlay/f'round-{r}.json').exists():
            roundpath = overlay/f'round-{r}.json'
        if roundpath.exists():
            if read(roundpath) != sim.events[-3:]:
                raise Stop('saved round/history changed')
        else:
            save((overlay if resumed else directory)/f'round-{r}.json',sim.events[-3:])
    if reserved and all(k in ledger.settled for k,v in ledger.starts.items() if v['episode']==allocation):
        ledger.event(event='release',id=allocation)
    result = {'episode':ep,'kind':'FAKE' if isinstance(transport,Fake) else 'MODEL','started_at':started_at,'finished_at':now(),
        'attempted_calls':len(calls),'complete':error is None and len(calls)==4*len(roles(ep['regime'])),
        'error':error,'fatal':bool(fatal),'events':sim.events,'receipts':sim.receipts,
        'cohort_run_id':cohort_run_id,'transport_failure':False,'deviation':'D4'}
    save((overlay if resumed else directory)/'episode.json',result)
    if fatal:
        __import__('trl_io').stop(base,error)
        raise Stop(error)
    return result
