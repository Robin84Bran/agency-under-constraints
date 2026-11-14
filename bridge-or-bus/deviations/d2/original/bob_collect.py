"""Serial append-only collection. Imports never execute a model or contact a server."""
import contextlib
import datetime as dt
from decimal import Decimal, ROUND_CEILING
import fcntl
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import urllib.request

from bob_core import (ROOT,P,PINS,SCHEMAS,World,action,report,canonical,strict_load,
                      render,reserve,subholds,sha)


class Stop(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    return strict_load(Path(path).read_bytes())


def syncdir(path):
    fd=os.open(str(path),os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save_bytes(path,data):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    syncdir(p.parent)


def save(path,value):
    save_bytes(path,(canonical(value)+'\n').encode())


def append(path,value):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('ab') as f:
        f.write((canonical(value)+'\n').encode()); f.flush(); os.fsync(f.fileno())
    syncdir(p.parent)


@contextlib.contextmanager
def lock(path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Stop('concurrent admission rejected') from exc
        try:
            yield
        finally:
            fcntl.flock(f,fcntl.LOCK_UN)


class Ledger:
    """Integer microdollars. Each transaction replays under an OS file lock."""
    def __init__(self,path):
        self.path=Path(path)
        self.load()

    def load(self):
        self.holds={}; self.calls={}; self.finished=set(); self.spent=0; self.blocked=False
        if self.path.exists():
            raw=self.path.read_bytes()
            if raw and not raw.endswith(b'\n'):
                raise Stop('torn ledger')
            for line in raw.splitlines():
                self.apply(strict_load(line))

    @property
    def exposure(self):
        return self.spent+sum(sum(v.values()) for v in self.holds.values())

    def apply(self,e):
        op,ident=e['event'],e['id']
        if op=='reserve':
            hs=e['subholds']
            if (self.blocked or ident in self.holds or len(hs)!=7 or
                any(type(v) is not int or v<0 for v in hs) or
                self.exposure+sum(hs)+2000000>25000000 or
                self.exposure+sum(hs)+2000000>=39000000 or
                self.exposure+sum(hs)>=40000000):
                raise Stop('reservation cap, durable stop or duplicate episode')
            self.holds[ident]={str(i):v for i,v in enumerate(hs)}
        elif op=='settle':
            episode,slot,actual=e['episode'],str(e['slot']),e['actual']
            if (type(actual) is not int or actual<0 or ident in self.calls or episode in self.finished or
                episode not in self.holds or slot not in self.holds[episode]):
                raise Stop('invalid settlement')
            held=self.holds[episode].pop(slot)
            self.spent+=actual
            self.calls[ident]=actual
            self.blocked |= actual>held or self.exposure+2000000>25000000 or self.exposure+2000000>=39000000 or self.spent>=40000000
        elif op=='release':
            if ident not in self.holds or ident in self.finished:
                raise Stop('invalid release')
            self.holds[ident]={}; self.finished.add(ident)
        elif op=='stop':
            self.blocked=True
        else:
            raise Stop('unknown ledger event')

    def event(self,**e):
        with lock(self.path.with_suffix('.lock')):
            self.load()
            e['time']=now()
            self.apply(e)
            append(self.path,e)
        if self.blocked:
            raise Stop('durable accounting stop; saved full cost/hold, no more dispatch')

    def reserve(self,ep):
        hs=subholds(ep) if ep['model']=='claude' else [dict(micro_usd=0)]*7
        self.event(event='reserve',id=ep['id'],subholds=[x['micro_usd'] for x in hs])


class ActiveTime:
    """Persisted timeout reservations; an unsettled crash is charged in full."""
    def __init__(self,path,cap):
        self.path,self.cap=Path(path),cap
        self.holds={}; self.settled={}
        if self.path.exists():
            raw=self.path.read_bytes()
            if raw and not raw.endswith(b'\n'):
                raise Stop('torn active time ledger')
            for rawline in raw.splitlines():
                e=strict_load(rawline)
                amount=e['seconds']
                if type(amount) not in (int,float) or not math.isfinite(amount) or amount<0:
                    raise Stop('invalid time amount')
                if e['event']=='start' and e['id'] not in self.holds:
                    self.holds[e['id']]=amount
                elif e['event']=='settle' and e['id'] in self.holds and e['id'] not in self.settled:
                    self.settled[e['id']]=amount
                else:
                    raise Stop('invalid time event')
        self.pending=time.monotonic()

    @property
    def charged(self):
        return sum(self.settled.get(k,v) for k,v in self.holds.items())

    def begin(self,ident,seconds):
        if ident in self.holds or self.charged+seconds>self.cap:
            raise Stop('persistent active-time cap or duplicate timer')
        append(self.path,dict(event='start',id=ident,seconds=seconds,time=now()))
        self.holds[ident]=seconds
        return self.pending

    def end(self,ident,began):
        elapsed=max(0,time.monotonic()-began)
        append(self.path,dict(event='settle',id=ident,seconds=elapsed,time=now()))
        self.settled[ident]=elapsed
        self.pending=time.monotonic()


def claude_command(binary,phase,budget):
    return [str(binary),'--print','--safe-mode','--restricted','--strict-mcp-config',
            '--mcp-config','{"mcpServers":{}}','--tools','','--disable-slash-commands',
            '--no-chrome','--no-session-persistence','--setting-sources','',
            '--output-format','json','--json-schema',canonical(SCHEMAS[phase]),
            '--model','claude-opus-5-5','--effort','medium','--system-prompt',P['system'],
            '--max-turns','1','--max-budget-usd',format(budget/1000000,'.6f')]


def clean_env():
    env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
    env.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS='512',CLAUDE_CODE_MAX_RETRIES='0',
               MAX_STRUCTURED_OUTPUT_RETRIES='0',CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1')
    return env


def frontier_gate(root):
    from bob_freeze import verify,TRANSPORT_POLICY
    if not (Path(root)/'freeze-d1.json').is_file():
        raise Stop('Claude requires reviewed D1 freeze before dispatch')
    freeze=verify(root)
    if freeze.get('deviation')!='D1' or freeze.get('transport_policy')!=TRANSPORT_POLICY:
        raise Stop('Claude empirical transport policy not frozen')


class ClaudeAdapter:
    def __init__(self,root,binary):
        frontier_gate(root)
        self.binary=Path(binary)
        expected=read(Path(root)/'evidence/claude-transport.json')['binary_sha256']
        if sha(self.binary.read_bytes())!=expected:
            raise Stop('Claude binary changed')
        self.root=Path(root)

    def generate(self,request,phase,budget):
        with tempfile.TemporaryDirectory(prefix='bob-claude-',dir=self.root/'collection') as workdir:
            p=subprocess.run(claude_command(self.binary,phase,budget),input=request['prompt'].encode(),
                             capture_output=True,timeout=420,env=clean_env(),cwd=workdir)
            return dict(stdout=p.stdout,stderr=p.stderr,returncode=p.returncode)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise Stop('local endpoint redirect refused')


def http(path,body=None,timeout=10):
    data=None if body is None else canonical(body).encode()
    req=urllib.request.Request('http://127.0.0.1:11435'+path,data=data,headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def expired(signum,frame):
        raise TimeoutError('local HTTP wall timeout')
    previous=signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,timeout)
    try:
        with opener.open(req,timeout=timeout) as response:
            return response.read()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)


class LocalAdapter:
    def __init__(self,root,model):
        self.root,self.model=Path(root),model
        self.ready=False

    def check(self):
        tag,digest=PINS[self.model]
        tags_raw=http('/api/tags')
        show_raw=http('/api/show',{'model':tag})
        version_raw=http('/api/version')
        tags,show,version=map(strict_load,(tags_raw,show_raw,version_raw))
        found=[m for m in tags.get('models',[]) if m.get('name')==tag]
        if len(found)!=1 or found[0].get('digest') not in (digest,'sha256:'+digest):
            raise Stop('local model digest mismatch')
        info=show.get('model_info',{})
        contexts=[v for k,v in info.items() if k.endswith('.context_length') and type(v) is int]
        if not contexts or min(contexts)<8192 or not show.get('template') or not version.get('version'):
            raise Stop('missing local template/runtime/context evidence')
        from bob_core import bound_prompt
        max_visible=max(len(bound_prompt(dict(seed=49,arm=arm),d,phase).encode()) for arm in ('stale','registry') for d in range(7) for phase in ('action','report'))
        context_byte_allowance=max_visible+len(show['template'].encode())+len(P['system'].encode())+192+512
        if context_byte_allowance>8192:
            raise Stop('full prompt/template/output byte allowance does not fit local context')
        # No hidden model system text or model-default sampling overrides.
        if show.get('system') not in (None,''):
            raise Stop('unexpected model system prompt')
        snapshot=dict(model=self.model,tag=tag,digest=digest,tags=tags,show=show,version=version,
                      raw_sha256=[sha(x) for x in (tags_raw,show_raw,version_raw)],context_byte_allowance=context_byte_allowance,time=now())
        runtime=self.root/'collection/runtime'/f'{self.model}.json'
        if runtime.exists():
            old=read(runtime)
            if any(old[k]!=snapshot[k] for k in ('model','tag','digest','show','version')):
                raise Stop('local runtime changed across resumes')
        else:
            save(runtime,snapshot)
        self.ready=True

    def generate(self,request,phase,budget):
        if not self.ready:
            self.check()
        raw=http('/api/generate',request,timeout=180)
        ps=http('/api/ps')
        save_bytes(self.root/'collection/runtime'/f"{self.model}-{time.time_ns()}-ps.json",ps)
        active=[m for m in strict_load(ps).get('models',[]) if m.get('name')==PINS[self.model][0]]
        if len(active)!=1 or active[0].get('context_length')!=8192:
            # Preserve generation bytes even on post-generation runtime failure.
            return dict(stdout=raw,stderr=b'actual runtime context mismatch',returncode=1)
        return dict(stdout=raw,stderr=b'',returncode=0)


def request_for(ep,prompt):
    if ep['model']=='claude':
        return dict(prompt=prompt,system=P['system'])
    return dict(model=PINS[ep['model']][0],prompt=prompt,system=P['system'],stream=False,format='json',
                options=dict(temperature=.6,top_k=16,num_predict=192,num_ctx=8192,seed=ep['seed']))


def nonnegative_int(value,label):
    if type(value) is not int or value<0:
        raise Stop('missing/invalid '+label)
    return value


def usage(envelope,model):
    if model!='claude':
        return dict(input_tokens=nonnegative_int(envelope.get('prompt_eval_count'),'input usage'),
                    output_tokens=nonnegative_int(envelope.get('eval_count'),'output usage'),
                    cache_read_input_tokens=None,cache_creation_input_tokens=None,reasoning_tokens=None,micro_usd=0)
    u=envelope.get('usage')
    if type(u) is not dict:
        raise Stop('missing Claude usage; retain hold')
    counts={k:nonnegative_int(u.get(k),k) for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')}
    cost=envelope.get('total_cost_usd')
    if type(cost) not in (int,float) or not math.isfinite(cost) or cost<0:
        raise Stop('missing Claude total cost; retain hold')
    counts.update(reasoning_tokens=None,micro_usd=int((Decimal(str(cost))*1000000).to_integral_value(rounding=ROUND_CEILING)))
    return counts


def payload(envelope,ep,phase):
    if type(envelope) is not dict:
        raise ValueError('provider envelope must be object')
    if ep['model']=='claude':
        if envelope.get('type')!='result' or envelope.get('subtype')!='success' or envelope.get('is_error') is not False:
            raise ValueError('Claude failed/unfinished envelope')
        models=envelope.get('modelUsage')
        if type(models) is not dict or set(models)!={'claude-opus-5-5'}:
            raise Stop('Claude returned identity mismatch/UNKNOWN')
        if envelope.get('effort') not in (None,'medium'):
            raise Stop('Claude returned effort mismatch')
        if envelope.get('num_turns')!=1 or type(envelope.get('num_turns')) is not int:
            raise Stop('Claude internal turn count mismatch/UNKNOWN')
        v=envelope.get('structured_output')
        if type(v) is not dict:
            raise ValueError('missing object structured_output; no fallback')
    else:
        if envelope.get('model')!=PINS[ep['model']][0] or envelope.get('done') is not True:
            raise Stop('local identity/incomplete envelope')
        if envelope.get('done_reason')!='stop':
            raise Stop('local output truncation or unknown stop reason')
        if nonnegative_int(envelope.get('prompt_eval_count'),'input tokens')+192>8192:
            raise Stop('local context would truncate')
        v=strict_load(envelope.get('response'))
    return action(v,ep['arm']) if phase=='action' else report(v)


def run_episode(root,ep,transport,ledger,timer,freeze_hash,guard=None):
    """Shared live/fake harness. Every request/start precedes the sole dispatch."""
    root=Path(root)
    ident=ep['id']
    amendment={}
    if (root/'freeze-d1.json').exists():
        amendment=dict(deviation='D1',amendment_freeze_sha256=sha((root/'freeze-d1.json').read_bytes()))
    if ident not in ledger.holds:
        ledger.reserve(ep)
    save(root/'collection/episode-starts'/f'{ident}.json',dict(episode=ep,started=now(),freeze_sha256=freeze_hash,**amendment))
    w=World(ep['seed'],ep['world'],ep['arm'])
    final_report=None
    valid=True
    error=None
    fatal=False
    raw_resources=[]
    transport_failure=False
    calls=[]
    holds=subholds(ep)
    for slot in range(7):
        if guard is not None:
            guard()
        phase='report' if w.ended else 'action'
        if phase=='action' and slot>=6:
            raise Stop('harness action boundary violation')
        charge_slot=6 if phase=='report' else slot
        cid=f'{ident}-{phase}-{slot}'
        prompt=render(ep,w.history,6-w.decisions,phase)
        bound=holds[charge_slot]
        measured=reserve(prompt,phase)
        if measured['micro_usd']>bound['micro_usd']:
            raise Stop('realized prompt exceeds frozen bound')
        req=request_for(ep,prompt)
        rawreq=canonical(req).encode()
        save_bytes(root/'collection/requests'/f'{cid}.json',rawreq)
        began=timer.begin(cid,460 if ep['model']=='claude' else 230)
        save(root/'collection/starts'/f'{cid}.json',dict(id=cid,episode_id=ident,slot=charge_slot,phase=phase,
             started=now(),freeze_sha256=freeze_hash,request_sha256=sha(rawreq),prompt_sha256=sha(prompt.encode()),
             **amendment,
             requested_model='claude-opus-5-5' if ep['model']=='claude' else PINS[ep['model']][0],
             requested_effort='medium' if ep['model']=='claude' else None,reservation=bound,
             schema_sha256=sha(canonical(SCHEMAS[phase]).encode()),system_sha256=sha(P['system'].encode()),
             candidate_claude_argv=claude_command(read(root/'config/runtime.json')['claude_binary'] if (root/'config/runtime.json').exists() else 'FAKE_CLAUDE_NOT_EXECUTED',phase,bound['micro_usd']) if ep['model']=='claude' else None,
             candidate_claude_controls={k:v for k,v in clean_env().items() if k.startswith(('CLAUDE_CODE_','MAX_STRUCTURED_','DISABLE_'))} if ep['model']=='claude' else None))
        call_began=time.monotonic()
        result=None; envelope=None; stats=None; parsed=None; call_error=None
        try:
            result=transport.generate(req,phase,bound['micro_usd'])
            save_bytes(root/'collection/raw'/f'{cid}.stdout',result['stdout'])
            save_bytes(root/'collection/raw'/f'{cid}.stderr',result['stderr'])
            envelope=strict_load(result['stdout'])
            stats=usage(envelope,ep['model'])
            if ep['model']=='claude':
                ledger.event(event='settle',id=cid,episode=ident,slot=charge_slot,actual=stats['micro_usd'])
                # Include cached input. These are empirical reservation checks;
                # settlement always uses the complete reported aggregate dollar cost.
                tokens=sum(stats[k] for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens'))
                if tokens>bound['input_tokens'] or stats['output_tokens']>bound['output_tokens']:
                    raise Stop('measured usage reservation overrun')
            else:
                ledger.event(event='settle',id=cid,episode=ident,slot=charge_slot,actual=0)
            if result['returncode']!=0:
                raise Stop('transport exit/runtime failure')
            # Every paid call, including the first frozen call, must demonstrate
            # the single object field in a strictly parsed outer JSON envelope.
            # Do this after known usage settlement so a failed gate still counts.
            if ep['model']=='claude':
                if envelope.get('type')!='result' or envelope.get('subtype')!='success' or envelope.get('is_error') is not False:
                    raise Stop('Claude failed/unfinished envelope')
                if type(envelope.get('structured_output')) is not dict:
                    raise Stop('missing object structured_output; no fallback')
            parsed=payload(envelope,ep,phase)
            if phase=='action':
                w.step(parsed)
            else:
                final_report=parsed
        except Exception as exc:
            # No resend, repair or report query after any generation failure.
            call_error=type(exc).__name__+': '+str(exc)
            if isinstance(exc,subprocess.TimeoutExpired):
                if exc.stdout is not None:
                    save_bytes(root/'collection/raw'/f'{cid}.stdout',exc.stdout)
                if exc.stderr is not None:
                    save_bytes(root/'collection/raw'/f'{cid}.stderr',exc.stderr)
            valid=False if phase=='action' else valid
            fatal=isinstance(exc,Stop) or ep['model']=='claude' and stats is None
            error=call_error
            transport_failure=result is None or result.get('returncode')!=0
        finally:
            elapsed=time.monotonic()-call_began
            if stats is not None:
                stats['seconds']=elapsed; raw_resources.append(stats)
            timer.end(cid,began)
            receipt=dict(id=cid,episode_id=ident,phase=phase,slot=charge_slot,finished=now(),
                         response_sha256=sha(result['stdout']) if result is not None else None,
                         stderr_sha256=sha(result['stderr']) if result is not None else None,
                         returncode=result['returncode'] if result is not None else None,
                         envelope=envelope,parsed=parsed,error=call_error,usage=stats,elapsed_seconds=elapsed,
                         returned_effort=envelope.get('effort') if type(envelope) is dict else None)
            save(root/'collection/calls'/f'{cid}.json',receipt)
            calls.append(cid)
        if call_error is not None or phase=='report':
            break
    resources={}
    for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens','reasoning_tokens','seconds','micro_usd'):
        resources[k]=sum(x[k] for x in raw_resources) if len(raw_resources)==len(calls) and all(x[k] is not None for x in raw_resources) else None
    saved=dict(episode=ep,events=w.events,committed=w.committed,ended=w.ended,decisions=w.decisions,
               trajectory_valid=valid and w.ended,report=final_report,error=error,transport_failure=transport_failure,resources=resources,calls=calls,
               terminal_reason='accepted_submit' if w.committed else 'finish' if w.ended and w.decisions<6 else 'decision_exhaustion' if w.ended else 'generation_failure')
    save(root/'collection/episodes'/f'{ident}.json',saved)
    # Missing paid usage or a crash preserves the complete unresolved reservation.
    if fatal:
        ledger.event(event='stop',id=ident,reason=error)
    if ep['model']=='claude' and any(cid not in ledger.calls for cid in calls):
        ledger.event(event='stop',id=ident,reason='unresolved paid usage')
    ledger.event(event='release',id=ident)
    return saved


def collect(root,models):
    from bob_freeze import verify,push_gate
    root=Path(root)
    with lock(root/'collection/collector.lock'):
        freeze=verify(root)
        push_gate(root,freeze)
        plan=read(root/'config/order.json')
        ledger=Ledger(root/'collection/cost.jsonl')
        if ledger.blocked:
            raise Stop('durable accounting stop')
        # Any half-written episode/call is ambiguous; no automatic recovery.
        starts={p.stem for p in (root/'collection/episode-starts').glob('*.json')}
        finished={p.stem for p in (root/'collection/episodes').glob('*.json')}
        if starts-finished or set(ledger.holds)-ledger.finished:
            raise Stop('uncertain start/hold; inspect saved evidence, never resend')
        from bob_audit import audit_episode,reconcile_ledger
        planned={e['id']:e for e in plan}
        records={ident:read(root/'collection/episodes'/f'{ident}.json') for ident in finished}
        freeze_hash=sha((root/'freeze.json').read_bytes())
        for ident,saved in records.items():
            if ident not in planned:
                raise Stop('unplanned saved episode')
            audit_episode(root,planned[ident],saved,freeze_hash)
        reconcile_ledger(root,records)
        for model in models:
            if model not in ('qwen7b','llama8b','qwen1b','claude'):
                raise Stop('unknown model')
        selected=[e for e in plan if e['model'] in models]
        if (root/'collection/transport-pause.json').exists():
            raise Stop('saved transport pause requires offline diagnosis; no automatic resume')
        failures=0
        transports={}
        timers={}
        for ep in selected:
            if ep['id'] in finished:
                continue
            index=plan.index(ep)
            if any(x['id'] not in finished for x in plan[:index]):
                raise Stop('frozen serial model/episode order violated')
            model=ep['model']
            if model not in transports:
                if model=='claude':
                    # Gate occurs before paid reservation, start or process creation.
                    frontier_gate(root)
                transports[model]=ClaudeAdapter(root,read(root/'config/runtime.json')['claude_binary']) if model=='claude' else LocalAdapter(root,model)
                timers.setdefault('frontier' if model=='claude' else 'local',ActiveTime(root/'collection'/('frontier-time.jsonl' if model=='claude' else 'local-time.jsonl'),7200 if model=='claude' else 43200))
            timer=timers['frontier' if model=='claude' else 'local']
            saved=run_episode(root,ep,transports[model],ledger,timer,sha((root/'freeze.json').read_bytes()),guard=lambda:verify(root))
            finished.add(ep['id'])
            failures=failures+1 if saved['transport_failure'] else 0
            if failures>=3:
                save(root/'collection/transport-pause.json',dict(time=now(),reason='three consecutive generation/transport failures; offline diagnosis required'))
                raise Stop('three consecutive transport failures; no automatic resume')
