"""Offline freeze, prefix-preserving clearance and operator attestation."""
from pathlib import Path

import sos_collect as b
import usage_limit as u

FREEZE = 'freeze-usage-limit.json'
AREA = 'deviations/usage-limit'


def digest(path):
    path = Path(path)
    u.require(path.is_file() and not path.is_symlink(), 'missing/symlink input: ' + str(path))
    return b.sha(path.read_bytes())


def prefix(root, spec):
    path = b.project_path(root, spec['path'])
    digest(path)
    with path.open('rb') as stream:
        data = stream.read(spec['size'])
    u.require(len(data) == spec['size'] and b.sha(data) == spec['sha256'], 'ledger prefix drift')


def baseline(root):
    value = b.read_json(root / AREA / 'collection-baseline.json')
    u.require(value['parent_freeze_sha256'] == digest(root / 'freeze.json'), 'parent freeze drift')
    for name, expected in value['files'].items():
        if name != value['ledger_prefix']['path']:
            u.require(digest(b.project_path(root, name)) == expected, 'collection baseline drift: ' + name)
    prefix(root, value['ledger_prefix'])
    return value


def parent(root):
    record = b.read_json(root / 'freeze.json')
    u.require(b.sha(b.canonical(record['files']).encode()) == record['content_sha256'], 'parent manifest drift')
    for name, expected in record['files'].items():
        archived = root / AREA / 'parent-inputs' / name
        path = archived if archived.exists() else b.project_path(root, name)
        u.require(digest(path) == expected, 'parent input drift: ' + name)
    return record


def verify(root):
    record = b.read_json(root / FREEZE)
    u.require(record['status'] == 'FROZEN_HARNESS_USAGE_LIMIT_DEVIATION', 'deviation identity drift')
    u.require(record['parent_freeze_sha256'] == digest(root / 'freeze.json'), 'parent freeze drift')
    u.require(record['parent_push_sha256'] == digest(root / 'collection/push.json'), 'parent push drift')
    parent(root)
    for name, expected in record['files'].items():
        u.require(digest(b.project_path(root, name)) == expected, 'usage-limit freeze drift: ' + name)
    u.require(b.sha(b.canonical(record['files']).encode()) == record['content_sha256'], 'deviation manifest drift')
    baseline(root)
    clearance = root / 'collection/usage-limit-clearance.json'
    if clearance.exists():
        c = b.read_json(clearance)
        u.require(c['deviation_freeze_sha256'] == digest(root / FREEZE), 'clearance freeze drift')
        prefix(root, c['ledger_before'])
        prefix(root, c['ledger_after'])
        for name, expected in c['evidence'].items():
            u.require(digest(b.project_path(root, name)) == expected, 'clearance evidence drift')
    # Scientific identity remains the parent freeze; the deviation is a second gate.
    return b.read_json(root / 'freeze.json')


def freeze(root, adapter):
    u.require(not (root / FREEZE).exists(), 'deviation freeze already exists; never replace')
    parent(root)
    baseline(root)
    inherited = b.read_json(root / 'evidence/inherited-inputs.json')['files']
    for name, expected in inherited.items():
        u.require(digest(b.project_path(root.parent, name)) == expected, 'inherited input drift: ' + name)
    reports = []
    for kind in ('test', 'dry-run', 'integrity'):
        matches = []
        for p in (root / 'build').glob('postfreeze-' + kind + '-*.json'):
            r = b.read_json(p)
            if (r.get('status') == 'PASS' and r.get('adapter_sha256') == digest(root / 'sos_v02.py')
                    and r.get('deviation_sources') == source_hashes(root)):
                if kind != 'test' or (r.get('test_sources') == {
                        p.name: digest(p) for p in (root / 'tests').glob('*.py')}
                        and r.get('deviation_sources') == source_hashes(root)):
                    matches.append(p)
        u.require(matches, 'current offline ' + kind + ' evidence required')
        reports.append(sorted(matches)[-1])
    paths = {root / n for n in b.read_json(root / 'freeze.json')['files']}
    paths |= set((root / AREA).rglob('*')) | set((root / 'tests').rglob('*'))
    paths |= {root / 'usage_limit.py', root / 'usage_deviation.py'} | set(reports)
    files = {str(p.relative_to(root)): digest(p) for p in sorted(paths)
             if p.is_file() and '__pycache__' not in p.parts}
    record = {'format': 1, 'version': 'v0.2', 'status': 'FROZEN_HARNESS_USAGE_LIMIT_DEVIATION',
              'frozen_utc': b.utcnow(), 'parent_freeze_sha256': digest(root / 'freeze.json'),
              'parent_push_sha256': digest(root / 'collection/push.json'),
              'files': files, 'content_sha256': b.sha(b.canonical(files).encode()),
              'authority': 'Claude delegating reviewer decision; harness only; no model calls or Git operations.',
              'scientific_changes': 0, 'new_model_calls': 0}
    b.save_new(root / FREEZE, record)
    verify(root)
    return {'freeze_file': FREEZE, 'sha256': digest(root / FREEZE)}


def source_hashes(root):
    return {name: digest(root / name) for name in ('usage_limit.py', 'usage_deviation.py')}


def attest(root, frozen_hash):
    verify(root)
    u.require(frozen_hash == digest(root / FREEZE), 'wrong deviation attestation hash')
    u.require(not (root / 'collection/collector.lock').exists(), 'collector must be idle')
    value = {'deviation_freeze_sha256': frozen_hash, 'parent_freeze_sha256': digest(root / 'freeze.json'),
             'attested_utc': b.utcnow(), 'operator': 'Claude',
             'scope': 'Reviewed harness-only deviation; resume identical requests after stated reset.'}
    path = root / 'collection/usage-limit-attestation.json'
    if path.exists():
        u.require(b.read_json(path)['deviation_freeze_sha256'] == frozen_hash, 'attestation drift')
        return b.read_json(path)
    b.save_new(path, value)
    return value


def gate(root):
    a = b.read_json(root / 'collection/usage-limit-attestation.json')
    u.require(a['deviation_freeze_sha256'] == digest(root / FREEZE), 'missing/wrong deviation attestation')
    t = b._recovery_time(a['attested_utc'])
    u.require(b._recovery_time(b.read_json(root / FREEZE)['frozen_utc']) <= t <=
              b.dt.datetime.now(b.dt.timezone.utc), 'invalid deviation attestation time')
    for p in (root / 'collection/continuations').rglob('*.start.json'):
        u.require(t <= b._recovery_time(b.read_json(p)['started']), 'attestation after continuation')


def ledger_spec(root):
    p = root / 'collection/cost.jsonl'
    return {'path': 'collection/cost.jsonl', 'size': p.stat().st_size, 'sha256': digest(p)}


def clear(root, adapter):
    adapter.verify(root)
    adapter.output_boundary(root)
    u.require(not (root / 'collection/collector.lock').exists(), 'collector must be idle')
    path = root / 'collection/usage-limit-clearance.json'
    if path.exists():
        return b.read_json(path)
    jobs = b.read_json(root / 'config/requests.json')['jobs']
    prior = adapter.reconcile(root.parent / 'collection/cost.jsonl')['accounted_usd']
    ledger = adapter.RollingLedger(root / 'collection/cost.jsonl', prior=prior)
    attempts = u.history(root / 'collection', jobs, digest(root / 'freeze.json'), ledger)
    before = ledger_spec(root)
    evidence, keys = {}, []
    for records in attempts.values():
        for r in records:
            if r[3]:
                cert = u.disposition(root / 'collection', r, ledger)
                for p in (r[1], u.event_for(root / 'collection', r[2])):
                    evidence[str(p.relative_to(root))] = digest(p)
                keys.append(r[2])
    u.require(keys, 'no saved usage-limit refusals to clear')
    value = {'status': 'CLEARED_TO_USAGE_LIMIT_PAUSE', 'recorded_utc': b.utcnow(),
             'deviation_freeze_sha256': digest(root / FREEZE), 'attempt_keys': keys,
             'ledger_before': before, 'ledger_after': ledger_spec(root), 'evidence': evidence,
             'reason': 'Claude reviewer re-disposition: exact 429 zero-usage refusals are definite non-starts; no receipt rewritten.',
             're_dispositioned_transport_failures': len(keys), 'cumulative_accounted_usd': str(ledger.total)}
    b.save_new(path, value)
    verify(root)
    return value
