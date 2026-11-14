"""Verify saved artifacts and provenance offline, without rerunning analysis."""
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sos_freeze import verify_freeze


def load(name):
    return json.loads((ROOT / name).read_text())


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def moment(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


freeze = verify_freeze(ROOT)
assert '_d1' in freeze
comparisons = []
for original, rebuilt in (
    ('analysis/results.json', 'analysis-rebuild-1/analysis/results.json'),
    ('delivery/frozen-analysis/RESULTS.md', 'analysis-rebuild-1/RESULTS.md'),
    ('delivery/frozen-analysis/README.md', 'analysis-rebuild-1/README.md'),
):
    same = (ROOT / original).read_bytes() == (ROOT / rebuilt).read_bytes()
    comparisons.append({'original': original, 'rebuilt': rebuilt, 'byte_identical': same,
                        'original_sha256': digest(original), 'rebuilt_sha256': digest(rebuilt)})
    assert same, original

results = load('analysis/results.json')
assert results['status'] == 'COMPLETE'
assert results['uncertainty']['bootstrap_replicates'] == 10000
assert results['uncertainty']['seed'] == 20261112
assert results['saved_calls'] == results['scheduled_jobs'] == 5604
assert not results['cross_family_plain_pass'] and not results['cross_family_explicit_pass']
assert all(not cell['pass'] for cells in results['primary'].values() for cell in cells.values())

jobs = {r['id']: r for r in load('config/requests.json')['jobs']}
starts = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'collection/starts').glob('*.json')}
calls = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'collection/calls').glob('*.json')}
assert set(jobs) == set(starts) == set(calls)
assert dict(Counter(r['model'] for r in calls.values())) == {'qwen7b': 1868, 'llama8b': 1868, 'claude': 1868}
assert all(r['status'] == 'response' for r in calls.values())

provenance = []
for manifest, attestation, expected_n in (
    ('freeze.json', 'collection/push.json', 3738),
    ('freeze-d1.json', 'collection/push-d1.json', 1866),
):
    pushed = load(attestation)
    hashed = digest(manifest)
    assert pushed['freeze_sha256'] == hashed
    bound = [r for r in starts.values() if r['freeze_sha256'] == hashed]
    assert len(bound) == expected_n
    assert moment(load(manifest)['frozen_utc']) < moment(pushed['github_time'])
    assert all(moment(pushed['github_time']) < moment(r['started']) for r in bound)
    provenance.append({'manifest': manifest, 'sha256': hashed, 'attestation': attestation,
                       'commit': pushed['commit'], 'github_time': pushed['github_time'],
                       'starts': len(bound), 'earliest_start': min(r['started'] for r in bound),
                       'push_before_every_start': True,
                       'scope': 'Saved operator attestations and hashes; no independent GitHub query.'})

ledger = [json.loads(line) for line in (ROOT / 'collection/cost.jsonl').read_text().splitlines()]
reserves = [e for e in ledger if e['event'] == 'reserve']
settles = [e for e in ledger if e['event'] == 'settle']
assert len(reserves) == len(settles) == 1868
assert {e['id'] for e in reserves} == {e['id'] for e in settles}
settled = sum((Decimal(e['usd']) for e in settles), Decimal(0))
assert settled == Decimal('11.053392') == Decimal(results['accounting']['ledger_accounted_usd'])
assert results['accounting']['outstanding_reservations_usd'] == '0'

for doc in ('RESULTS.md', 'README.md'):
    text = (ROOT / doc).read_text()
    assert 'For a general reader' in text and 'consistent with' in text
    assert 'P6' in text and 'D1' in text and '11.053392' in text
    assert 'byte-identical' in text

record = {
    'status': 'PASS', 'verified_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'original_analysis_command': 'python3 -B sos.py analyze',
    'rebuild_command': 'python3 -B sos.py analyze --output analysis-rebuild-1',
    'original_production_executions': 1, 'requested_rebuild_executions': 1,
    'bootstrap_replicates': 10000, 'bootstrap_seed': 20261112,
    'comparison_scope': 'All three generated artifacts; narrative root Markdown is expanded delivery prose.',
    'all_generated_artifacts_byte_identical': True, 'comparisons': comparisons,
    'both_freezes_verified': True, 'freeze_content_sha256': freeze['content_sha256'],
    'provenance': provenance, 'collection': {
        'saved_calls': len(calls), 'starts': len(starts),
        'calls_by_judge': dict(Counter(r['model'] for r in calls.values())),
        'ledger_sha256': digest('collection/cost.jsonl'), 'settled_usd': str(settled),
        'outstanding_reserved_usd': '0', 'transport_failures': 0,
        'integrity_flags_retained': sum(bool(r.get('integrity_failure')) for r in calls.values()),
    },
    'delivery_sha256': {name: digest(name) for name in (
        'RESULTS.md', 'README.md', 'QUESTIONS-post-analysis.md', 'PROJECT_STATE-post-analysis.md',
        'delivery/render_reports.py', 'delivery/verify_delivery.py')},
    'frozen_project_state_preserved': {
        'path': 'PROJECT_STATE.md', 'sha256': digest('PROJECT_STATE.md'),
        'reason': 'Bound by freeze-d1.json; current task also prohibits editing frozen files.',
        'current_state': 'PROJECT_STATE-post-analysis.md',
    },
    'scientific_acceptance': 'UNKNOWN',
    'unresolved': ['Claude primary F/R validity acceptance criterion is unmet.',
                   'Fresh-clone independent Claude review and findings dispositions pending.'],
    'review_scope': 'Same-workspace independent offline execution, not a fresh-clone or independent-reviewer rebuild.',
}
with (ROOT / 'delivery/verification.json').open('x') as handle:
    json.dump(record, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write('\n')
print(json.dumps({'status': record['status'], 'all_generated_artifacts_byte_identical': True,
                  'both_freezes_verified': True, 'settled_usd': str(settled)}, indent=2))
