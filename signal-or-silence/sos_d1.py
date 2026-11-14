"""Offline D1 cost-only overlay; original scientific inputs remain immutable."""
import datetime as dt
import hashlib
import json
from pathlib import Path

from sos_collect import CollectionStop, D, SYSTEM, canonical, read_json, save_new, sha

CHANGED = ('sos.py', 'sos_collect.py', 'sos_freeze.py', 'RUN.md')
ADDED = ('sos_d1.py', 'tests/test_d1.py', 'config/d1.json', 'DEVIATIONS.md',
         'PROJECT_STATE.md', 'deviations/d1/collection-baseline.json')
ORIGINALS = tuple('deviations/d1/originals/' + p for p in (*CHANGED, 'PROJECT_STATE.md'))
D1_FILES = (*CHANGED, *ADDED, *ORIGINALS)
OVERRUN = 'measured-max reservation overrun; no more dispatch'


def digest(root, name):
    p = Path(root) / name
    if p.is_symlink() or not p.is_file():
        raise ValueError('missing or symlink D1 input: ' + name)
    return sha(p.read_bytes())


def measure(root):
    """Count exact frozen bytes, not tokens from an unavailable CLI tokenizer.

    One token per visible UTF-8 byte is a conservative byte-token allowance.
    Hidden input and output are empirical allowances, never enforced caps.
    Integer arithmetic rounds a 10% margin up to a 64-token block.
    """
    root = Path(root)
    jobs = [j for j in read_json(root / 'config/requests.json')['jobs'] if j['model'] == 'claude']
    system_bytes = len(SYSTEM.encode('utf-8'))
    def padded(n):
        return ((n * 110 + 6399) // 6400) * 64
    reservations = {}
    for job in jobs:
        tin = padded(len(job['prompt'].encode('utf-8')) + system_bytes + 826)
        tout = padded(393)
        reservations[job['id']] = {'input_tokens': tin, 'output_tokens': tout,
            'usd': str((tin * D(4) + tout * D(20)) / D(1000000)),
            'basis': 'D1: visible UTF-8 bytes + 826 hidden tokens; 10% margin rounded up to 64; empirical, not hard cap'}
    by_instruction = {}
    for instruction in ('plain', 'explicit'):
        group = [j for j in jobs if j['instruction'] == instruction]
        worst = max(group, key=lambda j: len(j['prompt'].encode('utf-8')))
        by_instruction[instruction] = {'jobs': len(group),
            'max_prompt_utf8_bytes': len(worst['prompt'].encode('utf-8')),
            'max_canonical_request_utf8_bytes': max(len(canonical(j['request']).encode('utf-8')) for j in group),
            'worst_prompt_id': worst['id'], 'episode_id': worst['episode_id'],
            'view': worst['view'], 'max_input_reservation': max(reservations[j['id']]['input_tokens'] for j in group)}
    total = sum((D(v['usd']) for v in reservations.values()), D(0))
    if total + 5 >= 39:
        raise ValueError('D1 planned reservation including USD5 reserve must stay below USD39')
    return {'format': 1, 'deviation': 'D1', 'system_utf8_bytes': system_bytes,
        'hidden_input_median_tokens': 544, 'hidden_input_max_tokens': 826,
        'hidden_source': 'config/cost_basis.json: measured.prices.overhead_source',
        'exact_token_count_status': 'UNKNOWN',
        'token_count_reason': 'No offline Claude tokenizer; visible byte counts are exact, byte-token allowance conservative; hidden maximum empirical.',
        'margin_percent': 10, 'rounding_tokens': 64, 'by_instruction': by_instruction,
        'max_input_reservation': max(v['input_tokens'] for v in reservations.values()),
        'output_reservation': 448, 'reservations_usd': str(total),
        'planning_reserve_usd': '5', 'planned_total_usd': str(total + 5),
        'operational_stop_usd': '39', 'absolute_cap_usd': '40', 'reservations': reservations}


def verify_baseline(root):
    root = Path(root)
    baseline = read_json(root / 'deviations/d1/collection-baseline.json')
    for name, expected in baseline['files'].items():
        if not name.startswith(('collection/starts/', 'collection/calls/')) and name != 'collection/push.json':
            raise ValueError('invalid D1 baseline path')
        if digest(root, name) != expected:
            raise ValueError('pre-D1 collection evidence changed: ' + name)
    ledger = baseline['ledger']
    raw = (root / 'collection/cost.jsonl').read_bytes()
    if len(raw) < ledger['bytes'] or sha(raw[:ledger['bytes']]) != ledger['sha256']:
        raise ValueError('pre-D1 ledger bytes changed')
    return baseline


def verify(root, original, inventory, record=None):
    root = Path(root)
    record = read_json(root / 'freeze-d1.json') if record is None else record
    if record.get('deviation') != 'D1' or record.get('original_freeze_sha256') != digest(root, 'freeze.json'):
        raise ValueError('D1 original freeze link invalid')
    files = record['files']
    if set(files) != set(D1_FILES) or sha(canonical(files).encode()) != record['content_sha256']:
        raise ValueError('D1 manifest invalid')
    for name, expected in files.items():
        if digest(root, name) != expected:
            raise ValueError('D1 file changed: ' + name)
    for name in CHANGED:
        if digest(root, 'deviations/d1/originals/' + name) != original['files'][name]:
            raise ValueError('D1 original code backup differs: ' + name)
    expected = dict(original['files'])
    expected.update({name: files[name] for name in (*CHANGED, 'sos_d1.py', 'tests/test_d1.py', 'config/d1.json')})
    if inventory != expected:
        raise ValueError('D1 inventory changed outside cost amendment')
    if read_json(root / 'config/d1.json') != measure(root):
        raise ValueError('D1 measurements or reservations differ from frozen bytes')
    baseline = verify_baseline(root)
    overrun_ids = []
    for name in baseline['files']:
        if not name.startswith('collection/calls/'):
            continue
        receipt = read_json(root / name)
        if receipt.get('integrity_failure'):
            if not permits_overrun(root, receipt, record, baseline):
                raise ValueError('D1 cannot acknowledge a different integrity failure')
            overrun_ids.append(receipt['id'])
    if sorted(overrun_ids) != record['acknowledged_overrun_ids']:
        raise ValueError('D1 acknowledged overrun set differs')
    return record


def permits_overrun(root, receipt, record, baseline=None):
    """Only the exact pre-D1, saved cost overrun can be acknowledged."""
    key = receipt.get('id')
    baseline = baseline or read_json(Path(root) / 'deviations/d1/collection-baseline.json')
    name = 'collection/calls/' + str(key) + '.json'
    bound = read_json(Path(root) / 'config/d1.json')['reservations'].get(key)
    return (key in record.get('acknowledged_overrun_ids', []) and bound is not None
        and receipt.get('model') == 'claude' and receipt.get('status') == 'response'
        and receipt.get('integrity_failure') == OVERRUN
        and receipt.get('returned_model') == 'claude-opus-5-5'
        and receipt.get('returned_effort') in (None, 'medium')
        and type(receipt.get('input_tokens')) is int and 0 <= receipt['input_tokens'] <= bound['input_tokens']
        and type(receipt.get('output_tokens')) is int and 0 <= receipt['output_tokens'] <= bound['output_tokens']
        and baseline['files'].get(name) == digest(root, name))


def create(root):
    """Create exclusively, after code, documents, measurements and tests exist."""
    from sos_freeze import inventory, verify_freeze
    root = Path(root)
    if (root / 'freeze-d1.json').exists():
        raise FileExistsError('freeze-d1.json already exists; never overwrite')
    if (root / 'collection/collector.lock').exists():
        raise ValueError('D1 requires idle collector')
    reports = [read_json(p) for p in (root / 'build').glob('postfreeze_test_report*.json')]
    latest = max(reports, key=lambda v: v['tested_utc']) if reports else {}
    if latest.get('status') != 'PASS':
        raise ValueError('D1 offline tests must pass')
    baseline = verify_baseline(root)
    ids = sorted(read_json(root / p)['id'] for p in baseline['files']
                 if p.startswith('collection/calls/') and read_json(root / p).get('integrity_failure'))
    files = {p: digest(root, p) for p in D1_FILES}
    record = {'format': 1, 'deviation': 'D1', 'scope': 'cost-control-only',
        'original_freeze_sha256': digest(root, 'freeze.json'),
        'frozen_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'acknowledged_overrun_ids': ids, 'files': files,
        'content_sha256': sha(canonical(files).encode()), 'push_status': 'UNKNOWN'}
    verify(root, read_json(root / 'freeze.json'), inventory(root), record=record)
    save_new(root / 'freeze-d1.json', record)
    verify_freeze(root)
    return {'freeze_d1_sha256': digest(root, 'freeze-d1.json'), 'planned_total_usd': measure(root)['planned_total_usd']}


def push_gate(root, record):
    root = Path(root)
    push = read_json(root / 'collection/push-d1.json')
    expected = digest(root, 'freeze-d1.json')
    if push.get('freeze_sha256') != expected or push.get('original_freeze_sha256') != record['original_freeze_sha256']:
        raise CollectionStop('D1 push receipt does not identify current amendment')
    if any(not push.get(k) for k in ('github_time', 'server_timestamp_source', 'remote', 'commit')):
        raise CollectionStop('missing D1 push receipt field')
    try:
        pushed = dt.datetime.fromisoformat(push['github_time'].replace('Z', '+00:00'))
        frozen = dt.datetime.fromisoformat(record['frozen_utc'])
        if pushed.tzinfo is None or not frozen <= pushed <= dt.datetime.now(dt.timezone.utc):
            raise ValueError('D1 push must follow freeze')
        for path in (root / 'collection/starts').glob('*.json'):
            start = read_json(path)
            if start.get('freeze_sha256') == expected:
                started = dt.datetime.fromisoformat(start['started'].replace('Z', '+00:00'))
                if started.tzinfo is None or pushed > started:
                    raise ValueError('D1 push must precede D1 starts')
    except (ValueError, TypeError, KeyError) as exc:
        raise CollectionStop('invalid D1 push timestamp') from exc
    return expected
