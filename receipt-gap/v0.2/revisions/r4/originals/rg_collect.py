"""Serial collector. Importing this module never contacts a provider."""
import contextlib
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

from rg_usage_limit import (refusal, nonstart, network_failure, make_pause, verified_pause, attempts_for,
                            episode_directory, episode_directories)

from rg_core import (ROOT, P, PINS, SCHEMAS, ModelOutputError, World, action, canonical, episode_reservation,
                     render, report, reserve, sha, strict_load, strict_envelope, schema_for)


class Stop(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    return strict_load(Path(path).read_text())


def syncdir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(canonical(value)+'\n'); f.flush(); os.fsync(f.fileno())
    syncdir(path.parent)


def append(path, value):
    with Path(path).open('a') as f:
        f.write(canonical(value)+'\n'); f.flush(); os.fsync(f.fileno())
    syncdir(Path(path).parent)


@contextlib.contextmanager
def lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'collector.lock').open('a') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop('concurrent collector admission rejected')
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


class Ledger:
    """Append-only integer microdollar holds. Caller holds collection lock."""
    def __init__(self, path):
        self.path, self.holds, self.spent, self.calls, self.finished = Path(path), {}, 0, {}, set()
        self.carried = False
        self.nonstarts, self.restored = {}, set()
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                self.apply(strict_load(line))

    @property
    def exposure(self):
        return self.spent + sum(self.holds.values())

    def apply(self, e):
        op, ident = e['event'], e['id']
        if op == 'carry':
            expected = read(ROOT/'config/prior-spend.json')
            if (self.carried or self.holds or self.spent or self.calls or self.finished or
                {k:v for k,v in e.items() if k != 'time'} != expected):
                raise Stop('invalid project spend carry')
            self.spent = e['settled_micro_usd']
            self.holds = dict(e['holds'])
            self.carried = True
        elif op == 'reserve':
            amount = e['amount']
            if type(amount) is not int or amount < 0 or ident in self.holds or self.exposure+amount+1000000 > 25000000 or self.exposure+amount+1000000 >= 39000000:
                raise Stop('reservation cap or duplicate episode')
            self.holds[ident] = amount
        elif op == 'settle':
            amount, held, episode = e['actual'], e['reserved'], e['episode']
            if any(type(v) is not int or v < 0 for v in (amount, held)) or ident in self.calls or episode not in self.holds or held > self.holds[episode] or episode in self.finished:
                raise Stop('invalid settlement')
            self.spent += amount
            self.holds[episode] -= held
            self.calls[ident] = amount
            if e.get('nonstart') is True:
                if amount != 0:
                    raise Stop('non-start must settle at zero')
                self.nonstarts[ident] = (episode, held)
        elif op == 'recognize-nonstart':
            episode, held = e['episode'], e['reserved']
            if self.calls.get(ident) != 0 or ident in self.nonstarts or episode in self.finished or type(held) is not int or held < 0:
                raise Stop('invalid historical non-start recognition')
            self.nonstarts[ident] = (episode, held)
        elif op == 'restore':
            episode, amount = e['episode'], e['amount']
            if (ident in self.restored or self.nonstarts.get(ident) != (episode, amount)
                    or episode in self.finished or self.exposure+amount+1000000 > 25000000):
                raise Stop('invalid non-start reservation restore')
            self.holds[episode] += amount
            self.restored.add(ident)
        elif op == 'release':
            if ident not in self.holds or ident in self.finished or ident.startswith('v0.1/'):
                raise Stop('invalid release')
            self.holds[ident] = 0
            self.finished.add(ident)
        else:
            raise Stop('unknown ledger operation')

    def event(self, **e):
        e['time'] = now()
        self.apply(e)
        append(self.path, e)


class ActiveTime:
    def __init__(self, path, cap):
        self.path, self.cap = Path(path), cap
        events = [strict_load(x) for x in self.path.read_text().splitlines()] if self.path.exists() else []
        self.holds, self.settled = {}, {}
        for e in events:
            if e['event'] == 'start':
                if e['id'] in self.holds:
                    raise Stop('duplicate timer')
                self.holds[e['id']] = e['seconds']
            elif e['event'] == 'settle' and e['id'] in self.holds and e['id'] not in self.settled:
                self.settled[e['id']] = e['seconds']
            else:
                raise Stop('invalid timer ledger')
        self.charged = sum(self.settled.get(k, v) for k, v in self.holds.items())
        self.pending = time.monotonic()

    def begin(self, ident, seconds):
        if self.charged >= self.cap or self.charged+seconds > self.cap or ident in self.holds:
            raise Stop('cumulative active-time cap')
        append(self.path, {'event':'start','id':ident,'seconds':seconds,'time':now()})
        self.holds[ident] = seconds
        self.charged += seconds
        return self.pending

    def end(self, ident, began):
        ended = time.monotonic()
        elapsed = max(0, ended-began)
        append(self.path, {'event':'settle','id':ident,'seconds':elapsed,'time':now()})
        self.charged += elapsed - self.holds[ident]
        self.settled[ident] = elapsed
        self.pending = ended


def claude_command(binary, phase, budget, toolkit='plain'):
    return [str(binary), '--print', '--safe-mode', '--restricted', '--strict-mcp-config',
            '--mcp-config', '{"mcpServers":{}}', '--tools', '', '--disable-slash-commands',
            '--no-chrome', '--no-session-persistence', '--setting-sources', '',
            '--output-format', 'json', '--model', 'claude-opus-5-5', '--effort', 'medium',
            '--system-prompt', P['system'], '--json-schema', canonical(schema_for(phase, toolkit)),
            '--max-turns', '1', '--max-budget-usd', format(budget/1000000, '.6f')]


def clean_env():
    # Subscription credentials remain in the pre-existing CLI store, never copied.
    env = {k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
    env.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS='512', CLAUDE_CODE_MAX_RETRIES='0',
               MAX_STRUCTURED_OUTPUT_RETRIES='0', CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', CLAUDE_CODE_NO_MODEL_FALLBACK='1', DISABLE_AUTOUPDATER='1')
    return env


def http(path, body=None, timeout=10):
    data = None if body is None else canonical(body).encode()
    req = urllib.request.Request('http://127.0.0.1:11435'+path, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode('utf8')
    return raw


class Local:
    def preflight(self, actor):
        tag, digest = PINS[actor]
        version, tags, shown = http('/api/version'), http('/api/tags'), http('/api/show', {'model':tag})
        found = {m['name']:m['digest'] for m in strict_load(tags)['models']}
        if (strict_load(version).get('version') != '0.33.3' or
            found.get(tag) != digest or not strict_load(shown).get('template')):
            raise Stop('local identity/template preflight failed')
        return {'version':strict_load(version),'tags':strict_load(tags),'show':strict_load(shown),
                'expected_tag':tag,'expected_digest':digest,'requested_context':8192}

    def generate(self, ep, prompt, phase, budget, work):
        body = {'model':PINS[ep['actor']][0], 'prompt':prompt,'system':P['system'],
                'format':schema_for(phase, ep['toolkit']) if phase == 'action' else 'json','stream':False,
                'options':{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192,'seed':ep['seed']}}
        raw = http('/api/generate', body, 180)
        # Running metadata is read only, after generation; capture errors rather than discard raw.
        try:
            ps = strict_load(http('/api/ps'))
        except Exception as exc:
            ps = {'error':str(exc)}
        return {'stdout':raw,'stderr':'','returncode':0,'running':ps,'request':body}


class Claude:
    def __init__(self, binary):
        self.binary = Path(binary).resolve()

    def preflight(self, actor):
        ev = read(ROOT/'evidence/cli-contract.json')
        if sha(self.binary.read_bytes()) != ev['binary_sha256']:
            raise Stop('CLI binary changed since offline verification')
        helptext = subprocess.check_output([str(self.binary),'--help'], text=True, timeout=30)
        if '--json-schema' not in helptext:
            raise Stop('schema flag disappeared')
        return {'binary_sha256':ev['binary_sha256'],'version':ev['version'],'help_sha256':sha(helptext.encode()),
                'requested_effort':'medium','returned_effort':'UNKNOWN','output_token_limit':512}

    def generate(self, ep, prompt, phase, budget, work):
        cmd = claude_command(self.binary, phase, budget, ep['toolkit'])
        try:
            p = subprocess.run(cmd,input=prompt,text=True,capture_output=True,cwd=work,
                               env=clean_env(),timeout=420)
            return {'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode}
        except subprocess.TimeoutExpired as exc:
            # Partial bytes survive; no resend. Ledger keeps the call subhold.
            return {'stdout':(exc.stdout or b'').decode() if isinstance(exc.stdout,bytes) else (exc.stdout or ''),
                    'stderr':(exc.stderr or b'').decode() if isinstance(exc.stderr,bytes) else (exc.stderr or ''),
                    'returncode':None,'transport_error':'timeout; uncertain start'}


def usage(envelope, actor):
    """Missing values are UNKNOWN, never implicit zero. Input cache classes disjoint."""
    if actor != 'claude':
        a, b = envelope.get('prompt_eval_count'), envelope.get('eval_count')
    else:
        u = envelope.get('usage', {})
        vals = [u.get(k) for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens')]
        a = sum(vals) if all(type(v) is int and v >= 0 for v in vals) else None
        b = u.get('output_tokens')
    return (a if type(a) is int and a >= 0 else None, b if type(b) is int and b >= 0 else None)


def cost_micro(tin,tout,envelope):
    cost=4*tin+20*tout
    reported=envelope.get('total_cost_usd')
    if reported is not None:
        try:
            value=Decimal(str(reported))
        except InvalidOperation as exc:
            raise Stop('invalid reported API-equivalent cost') from exc
        if not value.is_finite() or value<0:
            raise Stop('invalid reported API-equivalent cost')
        cost=max(cost,int((value*1000000).to_integral_value(rounding=ROUND_CEILING)))
    return cost


def provider_envelope(raw, actor):
    try:
        return strict_envelope(raw['stdout'], actor)
    except (ValueError, KeyError, TypeError) as exc:
        raise Stop(str(exc)) from exc


def no_positive_counts(value, label):
    """Nonempty zero-count statistics are valid; actual activity is fatal."""
    if type(value) is dict:
        for key, item in value.items():
            no_positive_counts(item, label+'.'+key)
    elif type(value) is not int or value < 0:
        raise Stop('malformed activity count: '+label)
    elif value > 0:
        raise Stop('unexpected positive activity count: '+label)


def no_external_activity(e):
    for name in ('subagent_stats', 'safety_stops', 'queued_turn_count'):
        if name in e:
            no_positive_counts(e[name], name)
    if 'permission_denials' in e and (type(e['permission_denials']) is not list or e['permission_denials']):
        raise Stop('unexpected permission denials')
    u = e.get('usage', {})
    if 'server_tool_use' in u:
        no_positive_counts(u['server_tool_use'], 'server_tool_use')
    for m in e.get('modelUsage', {}).values():
        for k in ('webSearchRequests', 'webFetchRequests'):
            if k in m:
                no_positive_counts(m[k], k)


def decode(raw, ep, phase, bound, fake=False):
    e, payload_error = provider_envelope(raw, ep['actor'])
    schema_failure = (ep['actor'] == 'claude' and e.get('type') == 'result' and
                      e.get('subtype') == 'error_max_structured_output_retries' and e.get('is_error') is True)
    generated = (ep['actor'] == 'claude' and any(v is not None and v > 0 for v in usage(e, 'claude')))
    exit_failure = type(raw.get('returncode')) is not int or raw['returncode'] != 0 or bool(raw.get('transport_error'))
    generated_error = generated and (e.get('is_error') is True or exit_failure)
    if exit_failure and not (generated_error or schema_failure and raw.get('returncode')==1 and not raw.get('transport_error')):
        raise Stop('transport failure or uncertain start')
    tin, tout = usage(e, ep['actor'])
    if ep['actor'] == 'claude':
        no_external_activity(e)
        models = e.get('modelUsage', {})
        if (models and set(models) != {'claude-opus-5-5'}) or (not models and not generated_error):
            raise Stop('unverified frontier identity')
        if e.get('effort', 'medium') != 'medium':
            raise Stop('conflicting frontier effort')
        turns = e.get('num_turns')
        valid_turns = (type(turns) is int and turns in (1, 2)) or (generated_error and 'num_turns' not in e)
        success = e.get('subtype') == 'success' and e.get('is_error') is False
        if e.get('type') != 'result' or not (success or schema_failure or generated_error) or not valid_turns or (not generated_error and e.get('stop_reason') not in ('end_turn','tool_use','max_tokens','length')):
            raise Stop('frontier envelope, turn limit or truncation mismatch')
        if tin is None or tout is None:
            raise Stop('unknown frontier usage; hold retained')
        if tin > bound['input_tokens'] or tout > 512:
            raise Stop('frontier reservation overrun')
        if schema_failure or generated_error:
            raise ModelOutputError('provider rejected generated model output')
        if e.get('stop_reason') in ('max_tokens','length') or tout == 512:
            raise ModelOutputError('truncated model output')
        if payload_error:
            raise ModelOutputError(payload_error)
        v = e.get('structured_output')
        if type(v) is not dict:
            raise ModelOutputError('structured_output must be an object; no fallback')
    else:
        if e.get('model') != PINS[ep['actor']][0] or e.get('done') is not True or e.get('error') or e.get('done_reason') not in ('stop','length'):
            raise Stop('local identity, truncation or stop mismatch')
        if tin is None or tout is None or tin+192 >= 8192:
            raise Stop('local context usage unknown or exhausted')
        running = raw.get('running', {}).get('models', [])
        if not fake and not any(m.get('name') == PINS[ep['actor']][0] and m.get('digest') == PINS[ep['actor']][1] and m.get('context_length') == 8192 for m in running):
            raise Stop('returned running identity/context mismatch')
        if e.get('done_reason') == 'length':
            raise ModelOutputError('truncated model output')
        try:
            v = strict_load(e.get('response'))
        except (ValueError, TypeError, RecursionError) as exc:
            raise ModelOutputError(str(exc)) from exc
    return action(v, ep['toolkit']) if phase == 'action' else report(v)


def checked_receipt(root, receipt, event_file, freeze_hash, freeze_file="freeze.json"):
    from rg_freeze import push_record
    a = read(Path(root)/'collection'/receipt)
    if a.get('freeze_file', 'freeze.json') != freeze_file or a['freeze_sha256'] != freeze_hash or a['repo'] != 'Robin84Bran/research':
        raise Stop('push attestation mismatch')
    pushed = dt.datetime.fromisoformat(a['pushed_at'].replace('Z','+00:00'))
    frozen = dt.datetime.fromisoformat(read(Path(root)/freeze_file)['created_at'])
    if pushed.tzinfo is None or pushed < frozen or pushed >= dt.datetime.now(dt.timezone.utc):
        raise Stop('invalid server push time')
    event=read(Path(root)/'collection'/event_file)
    ref, timestamp = push_record(event, a['commit'])
    if (timestamp!=a['pushed_at'] or ref!=a['remote_ref'] or
        event.get('id')!=a['server_event_id'] or sha((Path(root)/'collection'/event_file).read_bytes())!=a['event_sha256']):
        raise Stop('retained server event differs from attestation')
    return pushed


def push_gate(root, freeze_file="freeze.json"):
    from rg_freeze import verify
    freeze_hash = verify(root, freeze_file)
    suffix = '-r3' if freeze_file=='freeze-r3.json' else '-r2' if freeze_file=='freeze-r2.json' else ''
    receipt_name = 'push'+suffix+'.json'
    event_name = 'push-event'+suffix+'.json'
    pushed = checked_receipt(root, receipt_name, event_name, freeze_hash, freeze_file)
    provenance={freeze_hash:pushed}
    if freeze_file in ('freeze-r2.json','freeze-r3.json'):
        old_hash=sha((Path(root)/'freeze-r1.json').read_bytes())
        provenance[old_hash]=checked_receipt(root,'push.json','push-event.json',old_hash,'freeze-r1.json')
    if freeze_file=='freeze-r3.json' and (Path(root)/'collection/push-r2.json').exists():
        old_hash=sha((Path(root)/'freeze-r2.json').read_bytes())
        provenance[old_hash]=checked_receipt(root,'push-r2.json','push-event-r2.json',old_hash,'freeze-r2.json')
    starts = list((Path(root)/'collection/episodes').glob('*/*.start.json')) + list((Path(root)/'collection/episodes').glob('*/dispatches/*/*/start.json'))
    starts += list((Path(root)/'collection/resumes/r3/episodes').glob('*/dispatches/*/*/start.json'))
    for start in starts:
        record = read(start)
        started = dt.datetime.fromisoformat(record['started_at'].replace('Z', '+00:00'))
        prior_push=provenance.get(record.get('freeze_sha256'))
        if prior_push is None or started.tzinfo is None or prior_push >= started:
            raise Stop('call must follow its attested v0.2 freeze push')
    return freeze_hash


def prior_spend_gate(root):
    root = Path(root)
    prior = read(root/'config/prior-spend.json')
    source = root/'evidence/v01-ledger.jsonl'
    if source.is_symlink() or sha(source.read_bytes()) != prior['source_sha256']:
        raise Stop('historical ledger snapshot changed')
    # The canonical runtime must also bind the current v0.1 ledger. An independent
    # code-only package can verify the immutable snapshot without requiring calls.
    live = root.parent/'collection/ledger.jsonl'
    if not live.is_file() or live.is_symlink() or sha(live.read_bytes()) != prior['source_sha256']:
        raise Stop('v0.1 ledger missing or advanced after v0.2 registration')
    return prior


def durable_stop(base, reason, stop_name='STOP.json'):
    if not (base/stop_name).exists():
        save(base/stop_name, {'reason':reason,'time':now()})


def run_episode(ep, transport, base, ledger, timer, freeze_hash, fake=False, stop_name='STOP.json'):
    directory = episode_directory(base, ep['id'])
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'episode.json').exists():
        raise Stop('episode already terminal')
    resuming = any(directory.glob('dispatches/*/*/pause.json'))
    if list(directory.glob('*.start.json')) and not resuming:
        raise Stop('started episode cannot be retried')
    paid = ep['actor'] == 'claude'
    if paid and ep['id'] not in ledger.holds:
        ledger.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
    world = World(ep['seed'],ep['toolkit'],ep['receipt_loss'])
    attempted, trajectory_valid, final, error = 0, True, None, None
    for index in range(11):
        phase = 'report' if world.ended else 'action'
        prompt = render(ep,world.history,10-world.decisions,phase)
        bound = reserve(prompt,phase,ep['toolkit'])
        request_path = directory/(str(index)+'.request.json')
        request = {'phase':phase,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),
                   'system':P['system'],'schema':schema_for(phase, ep['toolkit']),'reservation':bound}
        if request_path.exists():
            if read(request_path) != request:
                raise Stop('saved request differs on resume')
        else:
            save(request_path, request)
        if (directory/(str(index)+'.parsed.json')).exists():
            if not resuming:
                raise Stop('prior response without reviewed pause')
            prior = read(directory/(str(index)+'.parsed.json'))
            value = decode(read(directory/(str(index)+'.raw.json')),ep,phase,bound,fake)
            if prior['error'] is not None or prior['value'] != value or phase != 'action':
                raise Stop('invalid prior history on resume')
            world.step(value)
            if world.events[-1] != read(directory/(str(index)+'.event.json')):
                raise Stop('saved prior event differs on resume')
            attempted += 1
            continue
        attempts = attempts_for(directory,index) if paid else []
        for attempt in attempts:
            pause = verified_pause(attempt,request_path)
            if pause['reset_at'] is not None and dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(pause['reset_at']):
                return pause
            if pause['id'] not in ledger.nonstarts:
                raise Stop('pause lacks zero settlement')
        if attempts:
            previous = pause['id']
            if previous not in ledger.restored:
                ledger.event(event='restore',id=previous,episode=ep['id'],amount=bound['micro_usd'])
        call_id = ep['id']+'-'+str(index) + ('-attempt'+str(len(attempts)) if attempts else '')
        began = timer.begin(call_id, 430 if paid else 190)
        start = {'id':call_id,'started_at':now(),'freeze_sha256':freeze_hash}
        dispatch = directory/'dispatches'/str(index)/str(len(attempts)) if paid else None
        if paid:
            save(dispatch/'start.json',start)
        else:
            save(directory/(str(index)+'.start.json'),start)
        attempted += 1
        fatal, parsed = False, None
        try:
            raw = transport.generate(ep,prompt,phase,bound['micro_usd'],directory)
        except Exception as exc:
            raw = {'stdout':'','stderr':'','returncode':None,'transport_error':type(exc).__name__+': '+str(exc)}
        if paid:
            save(dispatch/'raw.json',raw)
            if nonstart(raw):
                ledger.event(event='settle',id=call_id,episode=ep['id'],reserved=bound['micro_usd'],actual=0,nonstart=True)
                timer.end(call_id,began)
                pause = make_pause(raw,start,request_path,dispatch,now())
                save(dispatch/'pause.json',pause)
                return pause
            save(directory/(str(index)+'.start.json'),start)
        save(directory/(str(index)+'.raw.json'),raw)
        envelope = None
        try:
            envelope, _ = provider_envelope(raw,ep['actor'])
            tin, tout = usage(envelope,ep['actor'])
        except (ValueError, KeyError, TypeError, AttributeError, Stop):
            tin = tout = None
        transport_failed = network_failure(raw)
        if transport_failed:
            error = 'episode transport failure; no resend'
        if paid and tin is not None and tout is not None:
            actual = cost_micro(tin,tout,envelope)
            ledger.event(event='settle',id=call_id,episode=ep['id'],reserved=bound['micro_usd'],actual=actual)
            if tin > bound['input_tokens'] or tout > 512 or actual > bound['micro_usd'] or ledger.exposure+1000000 > 25000000 or ledger.exposure+1000000 >= 39000000:
                fatal, error = True, 'measured reservation overrun'
        elif paid:
            fatal, error = not transport_failed, 'unknown usage or uncertain start; hold retained'
        try:
            if transport_failed:
                if paid and envelope is not None:
                    no_external_activity(envelope)
                    models = envelope.get('modelUsage', {})
                    if models and set(models) != {'claude-opus-5-5'}:
                        raise Stop('conflicting frontier identity in transport failure')
                    if envelope.get('effort','medium') != 'medium' or ('num_turns' in envelope and (type(envelope['num_turns']) is not int or envelope['num_turns'] not in (0,1,2))):
                        raise Stop('conflicting frontier effort or turns in transport failure')
                raise ModelOutputError(error)
            parsed = decode(raw,ep,phase,bound,fake)
        except ModelOutputError as exc:
            error = error or str(exc)
        except (ValueError, KeyError, TypeError, AttributeError, Stop) as exc:
            error = str(exc)
            # Only explicitly typed model-content failures are episode-local.
            fatal = True
        if error:
            if phase == 'action':
                trajectory_valid = False
            save(directory/(str(index)+'.parsed.json'),{'value':None,'error':error,'input_tokens':tin,'output_tokens':tout})
            timer.end(call_id,began)
            if fatal:
                durable_stop(base,error,stop_name)
            break
        save(directory/(str(index)+'.parsed.json'),{'value':parsed,'error':None,'input_tokens':tin,'output_tokens':tout})
        if phase == 'report':
            final = parsed
        else:
            world.step(parsed)
            save(directory/(str(index)+'.event.json'),world.events[-1])
        timer.end(call_id,began)
        if phase == 'report':
            break
    terminal = {'episode':ep,'attempted_calls':attempted,'trajectory_valid':trajectory_valid and world.ended,
                'action_failure':not trajectory_valid,'report':final,'error':error,'events':world.events,
                'counts':world.counts,'decisions':world.decisions,'ended':world.ended}
    if transport_failed:
        terminal['transport_failure'] = True
    save(directory/'episode.json',terminal)
    # Unknown call usage keeps the episode hold. A known terminal releases future calls.
    if paid and not (base/stop_name).exists() and (tin is not None and tout is not None):
        ledger.event(event='release',id=ep['id'])
    return terminal


def collect(root, cohort, binary=None, fake_transport=None, output=None, freeze_file="freeze.json"):
    root = Path(root)
    fake = fake_transport is not None
    base = Path(output) if output else root/'collection'
    with lock(base):
        stop_name = 'STOP.json'
        if not fake and (base/'OFFLINE-FAKE.json').exists():
            raise Stop('fake data cannot admit production collection')
        if (base/stop_name).exists():
            from rg_revision import stop_cleared
            if fake or not stop_cleared(root,base,freeze_file):
                raise Stop('durable STOP: '+read(base/stop_name)['reason'])
            stop_name='STOP-r3.json' if freeze_file=='freeze-r3.json' else 'STOP-r2.json'
            if (base/stop_name).exists():
                raise Stop('durable revision STOP: '+read(base/stop_name)['reason'])
        for name in ('STOP-r2.json','STOP-r3.json'):
            if (base/name).exists():
                raise Stop('durable STOP: '+read(base/name)['reason'])
        freeze_hash = 'OFFLINE-FAKE' if fake else push_gate(root, freeze_file)
        schedule = read(root/'config/episodes.json')
        actors = ['claude'] if cohort == 'claude' else ['qwen7b','llama8b','qwen1b']
        if cohort == 'claude' and not fake:
            for ep in schedule:
                if ep['actor'] != 'claude' and not (episode_directory(base,ep['id'])/'episode.json').exists():
                    raise Stop('local cohort must finish or be explicitly accounted before frontier')
        ledger = Ledger(base/'ledger.jsonl')
        if not fake:
            prior = prior_spend_gate(root)
            if not ledger.carried:
                ledger.event(**prior)
        timer = ActiveTime(base/(cohort+'-time.jsonl'),7200 if cohort == 'claude' else 43200)
        transport = fake_transport or (Claude(binary) if cohort == 'claude' and binary else Local())
        if cohort == 'claude' and not binary and not fake:
            raise Stop('explicit verified Claude binary required')
        if fake and not (base/'OFFLINE-FAKE.json').exists():
            save(base/'OFFLINE-FAKE.json',{'real_model_calls':0})
        for attempt in (p for d in episode_directories(base) for p in d.glob('dispatches/*/*')):
            if (attempt/'pause.json').exists():
                pause = verified_pause(attempt,attempt.parents[2]/(attempt.parent.name+'.request.json'))
                if pause['reset_at'] is not None and dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(pause['reset_at']):
                    return pause
        consecutive_transport = 0
        for actor in actors:
            todo = [e for e in schedule if e['actor'] == actor]
            if not fake:
                token = actor+'-preflight-'+str(len(timer.holds))
                began = timer.begin(token,40)
                metadata = transport.preflight(actor)
                save(base/'preflight'/(token+'.json'),metadata)
                timer.end(token,began)
            for ep in todo:
                directory = episode_directory(base, ep['id'])
                if (directory/'episode.json').exists():
                    consecutive_transport = consecutive_transport+1 if read(directory/'episode.json').get('transport_failure') else 0
                    if consecutive_transport >= 3:
                        durable_stop(base,'three consecutive episode transport failures',stop_name)
                        raise Stop('three consecutive episode transport failures')
                    continue
                if directory.exists() and list(directory.glob('*.start.json')) and not any(directory.glob('dispatches/*/*/pause.json')):
                    durable_stop(base,'uncertain started episode; never rerun',stop_name)
                    raise Stop('uncertain started episode')
                try:
                    result = run_episode(ep,transport,base,ledger,timer,freeze_hash,fake,stop_name)
                    if result.get('status') in ('usage-limit pause','dns non-start pause'):
                        return result
                except (Stop, ValueError, KeyError, OSError) as exc:
                    durable_stop(base,str(exc),stop_name); raise
                consecutive_transport = consecutive_transport+1 if result.get('transport_failure') else 0
                if consecutive_transport >= 3:
                    durable_stop(base,'three consecutive episode transport failures',stop_name)
                if (base/stop_name).exists():
                    raise Stop(read(base/stop_name)['reason'])
        return {'exposure_micro_usd':ledger.exposure,'settled_micro_usd':ledger.spent,'active_seconds':timer.charged}
