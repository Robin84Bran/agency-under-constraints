"""v0.2 harness deviation: immutable non-start evidence and serial continuation.

The original CLI transport and all chargeable/error handling remain frozen.
Only a proven zero-usage subscription refusal permits another dispatch.
"""
import datetime as dt
import json
from pathlib import Path
import re
import time
from zoneinfo import ZoneInfo

import sos_collect as b


def require(ok, reason):
    if not ok:
        raise b.CollectionStop(reason)


def refusal(raw):
    """Fail closed on incomplete, duplicate, mixed or nonzero envelope evidence."""
    try:
        def unique(pairs):
            result = {}
            for k, v in pairs:
                if k in result:
                    raise ValueError('duplicate envelope key')
                result[k] = v
            return result
        e = json.loads(raw, object_pairs_hook=unique)
        u = e['usage']
        keys = ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')
        if (e.get('is_error') is not True or type(e.get('api_error_status')) is not int
                or e['api_error_status'] != 429 or type(e.get('total_cost_usd')) not in (int, float)
                or e['total_cost_usd'] != 0 or not isinstance(u, dict)
                or not all(type(u.get(k)) is int and u[k] == 0 for k in keys)):
            return None
        # A bare HTTP 429 can be a different error. Require the usage-limit result.
        if not re.fullmatch(r"You've hit your (?:\d+(?:-hour)?|weekly) limit · resets .+", e.get('result', '')):
            return None
        def zero_details(value, key=''):
            if isinstance(value, dict):
                return all(zero_details(v, k) for k, v in value.items())
            if isinstance(value, list):
                return not value  # iterations/output may contain generation evidence
            if isinstance(value, (int, float)):
                return value == 0
            return not ('token' in key.lower())
        if not zero_details(u) or not zero_details(e.get('modelUsage', {})):
            return None
        if e.get('structured_output') is not None or e.get('output') or e.get('content'):
            return None
        return e
    except (TypeError, ValueError, KeyError):
        return None


def reset_time(envelope, finished):
    """Resolve the CLI's local wall-clock reset on the receipt's local date.

    Unknown formats remain a durable pause; never guess a dispatch time.
    """
    message = envelope['result']
    match = re.search(r'resets (\d{1,2})(?::(\d{2}))?(am|pm) \(([^)]+)\)$', message)
    if not match:
        return None
    try:
        hour, minute, meridian, zone = match.groups()
        hour, minute = int(hour), int(minute or 0)
        if not (1 <= hour <= 12 and 0 <= minute < 60):
            return None
        local = b._recovery_time(finished).astimezone(ZoneInfo(zone))
        reset = local.replace(hour=hour % 12 + (12 if meridian == 'pm' else 0),
                              minute=minute, second=0, microsecond=0)
        if reset <= local:
            reset += dt.timedelta(days=1)
        return reset.astimezone(dt.timezone.utc).isoformat()
    except (ValueError, KeyError):
        return None


def locations(collection, jobid, number):
    if number == 0:
        return (collection / 'starts' / (jobid + '.json'), collection / 'calls' / (jobid + '.json'), jobid)
    key = jobid + '--nonstart-' + str(number)
    folder = collection / 'continuations' / jobid
    return folder / (str(number) + '.start.json'), folder / (str(number) + '.call.json'), key


def history(collection, jobs, frozen_hash, ledger):
    """Validate every original/continuation attempt before setup or dispatch."""
    known_paths, known_keys, attempts = set(), set(), {}
    for job in jobs:
        records = []
        number = 0
        while True:
            sp, cp, key = locations(collection, job['id'], number)
            exists = sp.exists() or cp.exists() or key in ledger.reserved
            if not exists:
                break
            known_keys.add(key)
            known_paths.update((sp, cp))
            require(sp.exists() or not cp.exists(), 'receipt without durable start/reservation')
            if sp.exists():
                start = b.read_json(sp)
                require(key in ledger.reserved, 'start without reservation')
                require(start.get('freeze_sha256') == frozen_hash, 'saved start freeze mismatch')
                require(all(start.get(k) == job[k] for k in job), 'saved start request drift')
            call = b.read_json(cp) if cp.exists() else None
            if call is not None:
                require(sp.exists() and key in ledger.reserved, 'receipt without durable start/reservation')
                require(all(call.get(k) == job[k] for k in job), 'saved receipt request drift')
                require(call.get('freeze_sha256') == frozen_hash, 'receipt freeze mismatch')
                for k in ('started', 'tag', 'reservation'):
                    require(call.get(k) == start.get(k), 'start/receipt disagreement')
                nonstart = refusal(call.get('raw_reply'))
                if key in ledger.settled:
                    expected = b.D(0) if nonstart else call.get('actual_usd')
                    require(expected is not None and b.D(expected) == ledger.amounts[key], 'settlement/receipt disagreement')
            else:
                require(key not in ledger.settled, 'settlement without receipt')
                nonstart = None
            if number:
                require(records[-1][3] is not None, 'continuation after uncertain/started generation')
                event = event_for(collection, records[-1][2])
                require(event.exists(), 'continuation without usage-limit pause evidence')
                cert = b.read_json(event)
                if sp.exists():
                    require(cert.get('reset_utc') is not None and
                            b._recovery_time(start['started']) >= b._recovery_time(cert['reset_utc']),
                            'continuation before stated reset')
            records.append((sp, cp, key, nonstart, call))
            number += 1
        attempts[job['id']] = records
    actual_paths = set((collection / 'starts').glob('*.json')) | set((collection / 'calls').glob('*.json'))
    actual_paths |= set((collection / 'continuations').rglob('*.json'))
    require(actual_paths <= known_paths, 'orphan receipt/start/continuation')
    require(set(ledger.reserved) <= known_keys, 'unknown attempt/reservation')
    for path in (collection / 'usage-limits').glob('*.json'):
        cert = b.read_json(path)
        key = cert.get('attempt_key')
        found = [r for rs in attempts.values() for r in rs if r[2] == key]
        require(len(found) == 1 and found[0][3] is not None, 'orphan/non-refusal pause evidence')
        require(cert == certificate(collection, *found[0][1:]), 'usage-limit evidence drift')
    return attempts


def event_for(collection, key):
    return collection / 'usage-limits' / (key + '.json')


def certificate(collection, cp, key, envelope, call):
    return {'status': 'usage-limit pause', 'disposition': 'DEFINITE_NON_START',
            'attempt_key': key, 'job_id': call['id'], 'request_sha256': call['request_sha256'],
            'prompt_sha256': call['prompt_sha256'], 'receipt': str(cp.relative_to(collection)),
            'receipt_sha256': b.sha(cp.read_bytes()), 'raw_envelope_sha256': b.sha(call['raw_reply'].encode()),
            'reset_utc': reset_time(envelope, call['finished']), 'reset_message': envelope['result'],
            'cost_usd': '0', 'recorded_from_saved_status': call['status']}


def disposition(collection, record, ledger):
    sp, cp, key, envelope, call = record
    require(envelope is not None, 'only proven refusal can release a hold')
    cert = certificate(collection, cp, key, envelope, call)
    path = event_for(collection, key)
    if path.exists():
        require(b.read_json(path) == cert, 'usage-limit pause evidence drift')
    else:
        b.save_new(path, cert)
    if key not in ledger.settled:
        ledger.settle(key, b.D(0))
    require(ledger.amounts[key] == 0, 'non-start settlement must be zero')
    return cert


def effective_failures(collection, receipts, paths):
    """Retain the frozen recovery rules, hashing the actual attempt receipt."""
    tail = b._failure_tail(receipts)
    covered = 0
    for path in (collection / 'recoveries').glob('*.json'):
        cert = b.read_json(path)
        ids, hashes = cert.get('last_failure_ids'), cert.get('receipt_sha256')
        require(isinstance(ids, list) and len(ids) >= 3 and isinstance(hashes, dict)
                and isinstance(cert.get('reason'), str) and cert['reason'].strip(),
                'invalid recovery certificate fields')
        if ids != [key for key, _ in tail[:len(ids)]]:
            continue
        require(all(hashes.get(key) == b.sha(paths[key].read_bytes()) for key in ids),
                'recovery certificate receipt hash mismatch')
        diagnosed = b._recovery_time(cert.get('diagnosed_at'))
        require(b._recovery_time(tail[len(ids) - 1][1].get('finished')) < diagnosed <=
                dt.datetime.now(dt.timezone.utc), 'recovery diagnosis must follow its failures')
        if len(tail) > len(ids):
            require(diagnosed < b._recovery_time(tail[len(ids)][1].get('started')),
                    'recovery diagnosis must precede later attempted calls')
        covered = max(covered, len(ids))
    return len(tail) - covered


def collect(module, root, collection, jobs, config, chosen, transport, frozen_hash, entered=None):
    """Claude-only equivalent of the inherited serial loop, with non-starts."""
    require(chosen == {'claude'} and all(j['model'] == 'claude' for j in jobs), 'Claude-only deviation')
    ledger = module.CostLedger(collection / 'cost.jsonl', config['cost'].get('cap_usd', '39'))
    attempts = history(collection, jobs, frozen_hash, ledger)
    require(not any(r[4] and r[4].get('integrity_failure') for rs in attempts.values() for r in rs),
            'saved integrity failure requires offline diagnosis')
    effective = {k: rs[-1][4] for k, rs in attempts.items() if rs and rs[-1][4] and not rs[-1][3]}
    paths = {k: rs[-1][1] for k, rs in attempts.items() if k in effective}
    failures = effective_failures(collection, effective, paths)
    require(failures < 3, 'three consecutive transport failures require offline diagnosis')
    summary = {'completed': 0, 'already_saved': 0, 'uncertain': 0, 'reused': 0,
               'usage_limit_refusals': 0, 'status': 'COMPLETE'}
    # Reconstruct durable pauses/settlements after a crash, before transport setup.
    pauses = []
    for records in attempts.values():
        for record in records:
            if record[3]:
                cert = disposition(collection, record, ledger)
                if record is records[-1]:
                    pauses.append(cert)
    if any(c['reset_utc'] is None or b._recovery_time(c['reset_utc']) > dt.datetime.now(dt.timezone.utc) for c in pauses):
        return dict(summary, status='usage-limit pause', accounted_usd=str(ledger.total), local_active_seconds=0)
    ready = False
    cfg = module.model_config(config, 'claude')
    for job in jobs:
        records = attempts[job['id']]
        if records and not records[-1][3]:
            summary['already_saved' if records[-1][4] else 'uncertain'] += 1
            continue
        number = len(records)
        sp, cp, key = locations(collection, job['id'], number)
        if not ready:
            transport = transport if transport is not None else module.DefaultTransport(root)
            module._check_runtime(root, collection, 'claude', transport.preflight('claude', cfg), config)
            ready = True
        estimate = module.dispatch_reservation(job, config)
        ledger.reserve(key, estimate)
        record = dict(job, started=b.utcnow(), freeze_sha256=frozen_hash, tag=cfg['tag'],
                      digest=cfg.get('digest'), reservation=estimate)
        b.save_new(sp, record)
        begin, fatal = time.monotonic(), None
        try:
            result = transport.generate(job, cfg)
            if not isinstance(result, dict):
                raise b.TransportError('invalid transport return', repr(result))
            record.update(result, status='response')
            if result.get('returned_model') != cfg['tag']:
                fatal = 'returned model identity mismatch'
            if result.get('returned_effort') not in (None, cfg['effort']):
                fatal = 'returned effort mismatch'
            failures = 0
        except Exception as exc:
            record.update(status='transport_failure', error=type(exc).__name__ + ': ' + str(exc),
                          raw_reply=getattr(exc, 'raw_reply', None), stderr=getattr(exc, 'stderr', None),
                          input_tokens=None, output_tokens=None)
            failures += 1
        record.update(finished=b.utcnow(), seconds=time.monotonic() - begin, actual_usd=None,
                      accounted_usd=estimate['usd'])
        envelope = refusal(record.get('raw_reply'))
        if envelope:
            record.update(status='usage_limit_pause', actual_usd='0', accounted_usd='0',
                          input_tokens=0, output_tokens=0, usage=envelope['usage'])
            fatal = None
        elif record['status'] == 'response':
            tin, tout = record.get('input_tokens'), record.get('output_tokens')
            if type(tin) is int and type(tout) is int and tin >= 0 and tout >= 0:
                actual = (tin * b.D(str(config['cost'].get('input_usd_per_million', 4))) +
                          tout * b.D(str(config['cost'].get('output_usd_per_million', 20)))) / b.D(1000000)
                record.update(actual_usd=str(actual), accounted_usd=str(actual))
                if tin > estimate['input_tokens'] or tout > estimate['output_tokens']:
                    fatal = 'measured-max reservation overrun; no more dispatch'
            else:
                record['accounting_status'] = 'UNKNOWN; full reservation retained'
        if fatal:
            record['integrity_failure'] = fatal
        b.save_new(cp, record)
        if envelope:
            cert = disposition(collection, (sp, cp, key, envelope, record), ledger)
            return dict(summary, status='usage-limit pause', usage_limit_refusals=1,
                        reset_utc=cert['reset_utc'], accounted_usd=str(ledger.total), local_active_seconds=0)
        if record['actual_usd'] is not None:
            ledger.settle(key, b.D(record['actual_usd']))
        summary['completed'] += 1
        if fatal:
            raise b.CollectionStop(fatal)
        require(ledger.total <= ledger.cap, 'actual cost exceeds operational cap')
        require(failures < 3, 'three consecutive transport failures; no retries')
    return dict(summary, accounted_usd=str(ledger.total), local_active_seconds=0)


def effective_calls(root, jobs, ledger, frozen_hash):
    attempts = history(root / 'collection', jobs, frozen_hash, ledger)
    calls = {k: rs[-1][4] for k, rs in attempts.items() if rs and rs[-1][4] and not rs[-1][3]}
    events = [certificate(root / 'collection', *r[1:]) for rs in attempts.values() for r in rs if r[3]]
    return calls, events
