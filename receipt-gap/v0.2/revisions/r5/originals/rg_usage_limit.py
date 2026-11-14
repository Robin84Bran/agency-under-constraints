"""Strict pre-generation non-start evidence; contains no provider or dispatch code."""
import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from rg_core import sha, strict_load

LIMIT = re.compile(r"You've hit your 5-hour limit · resets (\d{1,2})(?::(\d{2}))?(am|pm) \((Asia/Hong_Kong)\)")
TOKENS = ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')


def all_zero(value):
    if type(value) is dict:
        return all(all_zero(v) for v in value.values())
    return type(value) is int and value == 0


def zero_usage(value):
    if type(value) is not dict:
        return False
    metadata = {'service_tier':str, 'inference_geo':str, 'speed':str}
    for key, item in value.items():
        if key in metadata:
            if type(item) is not metadata[key]:
                return False
        elif key == 'iterations':
            if item != []:
                return False
        elif key == 'fallback_credit':
            if item is not None and not (type(item) in (int,float) and item == 0):
                return False
        elif not all_zero(item):
            return False
    return True


def zero_model_usage(value):
    if type(value) is not dict:
        return False
    for model in value.values():
        if type(model) is not dict:
            return False
        for key,item in model.items():
            if key in ('contextWindow','maxOutputTokens'):
                if type(item) is not int or item < 0:
                    return False
            elif key in ('canonicalModel','provider','costBasis'):
                if type(item) is not str:
                    return False
            elif key == 'costUSD':
                if type(item) not in (int,float) or item != 0:
                    return False
            elif not all_zero(item):
                return False
    return True


def refusal(raw):
    """False for missing metadata, generated output, malformed or mixed replies."""
    try:
        e = strict_load(raw['stdout'])
        u = e.get('usage')
        return (type(raw.get('returncode')) is int and raw['returncode'] in (0, 1)
                and not raw.get('transport_error') and e.get('is_error') is True
                and type(e.get('api_error_status')) is int and e['api_error_status'] == 429
                and type(u) is dict and all(type(u.get(k)) is int and u[k] == 0 for k in TOKENS)
                and zero_usage(u) and type(e.get('total_cost_usd')) in (int, float)
                and e['total_cost_usd'] == 0 and type(e.get('result')) is str
                and LIMIT.fullmatch(e['result']) is not None
                and 1 <= int(LIMIT.fullmatch(e['result'])[1]) <= 12
                and 0 <= int(LIMIT.fullmatch(e['result'])[2] or 0) <= 59
                and not any(k in e for k in ('structured_output', 'response', 'output', 'content'))
                and all(all_zero(e[k]) for k in ('subagent_stats', 'safety_stops', 'queued_turn_count') if k in e)
                and ('permission_denials' not in e or e['permission_denials'] == [])
                and zero_model_usage(e.get('modelUsage', {})))
    except (ValueError, KeyError, TypeError, AttributeError):
        return False


def dns_nonstart(raw):
    """Claude's r3 ruling: only a completely ungenerated DNS refusal is retryable."""
    try:
        e = strict_load(raw['stdout']); u = e.get('usage')
        return (type(raw.get('returncode')) is int and raw['returncode'] in (0, 1)
                and not raw.get('transport_error') and e.get('is_error') is True
                and type(e.get('result')) is str and 'ENOTFOUND' in e['result']
                and ('duration_api_ms' not in e or type(e['duration_api_ms']) in (int, float) and e['duration_api_ms'] == 0)
                and type(u) is dict and all(type(u.get(k)) is int and u[k] == 0 for k in TOKENS)
                and zero_usage(u) and type(e.get('total_cost_usd')) in (int, float)
                and e['total_cost_usd'] == 0 and type(e.get('modelUsage')) is dict and e['modelUsage'] == {}
                and not any(k in e for k in ('structured_output', 'response', 'output', 'content'))
                and all(all_zero(e[k]) for k in ('subagent_stats', 'safety_stops', 'queued_turn_count') if k in e)
                and ('permission_denials' not in e or e['permission_denials'] == []))
    except (ValueError, KeyError, TypeError, AttributeError):
        return False


def nonstart(raw):
    return refusal(raw) or dns_nonstart(raw)


def network_failure(raw):
    """Explicit uncertain transport; unknown metadata alone stays fail-closed."""
    if nonstart(raw):
        return False
    if raw.get('transport_error'):
        return True
    try:
        e = strict_load(raw['stdout'])
        message = e.get('result', '')
        return (e.get('is_error') is True and type(message) is str
                and re.search(r'ECONNRESET|ETIMEDOUT|ENOTFOUND|ECONNREFUSED|EHOSTUNREACH|ENETUNREACH|EAI_AGAIN|EPIPE|timeout|timed out|connection reset|network error|fetch failed|socket hang up|reach the API server', message, re.I) is not None)
    except (ValueError, KeyError, TypeError, AttributeError):
        return False


def make_pause(raw, start, request, attempt, timestamp):
    dns = dns_nonstart(raw)
    return {'status':'dns non-start pause' if dns else 'usage-limit pause',
            'id':start['id'], 'time':timestamp,
            'reset_at':None if dns else reset_at(raw, start['started_at']),
            'request_sha256':sha(request.read_bytes()),
            'raw_sha256':sha((attempt/'raw.json').read_bytes()),
            'start_sha256':sha((attempt/'start.json').read_bytes())}


def episode_directory(base, ident):
    """Fixed r3 overlay keeps the stopped terminal and all old evidence immutable."""
    base = Path(base); record = base/'clearance-r3.json'
    if record.exists():
        r = read(record)
        if r.get('episode') == ident:
            if (r.get('status') != 'PASS' or r.get('cleared') is not True
                    or r.get('stop_sha256') != sha((base/'STOP.json').read_bytes())):
                raise ValueError('r3 resume clearance mismatch')
            d = base/'resumes/r3/episodes'/ident
            for name, digest in r['resume_files'].items():
                path = d/name
                if path.is_symlink() or sha(path.read_bytes()) != digest:
                    raise ValueError('r3 resume evidence changed')
            return d
    return base/'episodes'/ident


def episode_directories(base):
    base = Path(base)
    ids = {p.name for p in (base/'episodes').glob('*') if p.is_dir()}
    ids.update(p.name for p in (base/'resumes/r3/episodes').glob('*') if p.is_dir())
    return [episode_directory(base, ident) for ident in sorted(ids)]


def reset_at(raw, started_at):
    if not refusal(raw):
        raise ValueError('not an exact usage-limit refusal')
    match = LIMIT.fullmatch(strict_load(raw['stdout'])['result'])
    hour, minute, period, zone = match.groups()
    hour, minute = int(hour), int(minute or 0)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise ValueError('invalid reset clock')
    started = dt.datetime.fromisoformat(started_at).astimezone(ZoneInfo(zone))
    reset = started.replace(hour=hour % 12 + (12 if period == 'pm' else 0), minute=minute, second=0, microsecond=0)
    if reset <= started:
        reset += dt.timedelta(days=1)
    return reset.astimezone(dt.timezone.utc).isoformat()


def read(path):
    return strict_load(Path(path).read_text())


def verified_pause(attempt, request):
    """Bind a pause to immutable raw, start and identical request bytes."""
    pause = read(attempt/'pause.json')
    raw = read(attempt/'raw.json')
    start = read(attempt/'start.json')
    if (pause.get('status') != ('dns non-start pause' if dns_nonstart(raw) else 'usage-limit pause') or not nonstart(raw)
            or pause.get('raw_sha256') != sha((attempt/'raw.json').read_bytes())
            or pause.get('start_sha256') != sha((attempt/'start.json').read_bytes())
            or pause.get('request_sha256') != sha(request.read_bytes())
            or pause.get('id') != start['id']
            or pause.get('reset_at') != (None if dns_nonstart(raw) else reset_at(raw, start['started_at']))):
        raise ValueError('usage-limit pause evidence mismatch')
    return pause


def attempts_for(directory, index):
    path = directory/'dispatches'/str(index)
    if not path.exists():
        return []
    attempts = sorted(path.iterdir(), key=lambda p: int(p.name))
    if [p.name for p in attempts] != [str(i) for i in range(len(attempts))]:
        raise ValueError('dispatch sequence gap')
    return attempts


def operational_events(base):
    events = []
    for attempt in sorted(p for d in episode_directories(base) for p in d.glob('dispatches/*/*')):
        if (attempt/'pause.json').exists():
            index = attempt.parent.name
            pause = verified_pause(attempt, attempt.parents[2]/(index+'.request.json'))
            events.append({'kind':'dns non-start' if dns_nonstart(read(attempt/'raw.json')) else 'usage-limit refusal', 'id':pause['id'], 'reset_at':pause['reset_at'],
                           'cost_micro_usd':0, 'model_output':False})

    for directory in episode_directories(base):
        if (directory/'episode.json').exists():
            terminal = read(directory/'episode.json')
            if terminal.get('transport_failure'):
                events.append({'kind':'transport failure', 'id':terminal['episode']['id'],
                               'cost_micro_usd':None, 'model_output':False})
    return events
