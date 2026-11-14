"""Read-only archive sizing for the survey; no provider imports or model execution.

Run: python3 -B survey_inventory.py > survey_inventory.json
Only the shell redirection writes, inside this project. Numbers are historical.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path('<WORKSPACE>/ANTresidency')
groups = defaultdict(list)
hashes = {}


def read(path):
    raw = path.read_bytes()
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def parse(raw):
    # Match the archived extract_json tolerance without importing its providers.
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        if not isinstance(raw, str):
            return None
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())
    try:
        return json.loads(cleaned)
    except ValueError:
        start, end = cleaned.find('{'), cleaned.rfind('}')
        try:
            return json.loads(cleaned[start:end + 1]) if start >= 0 and end > start else None
        except ValueError:
            return None


def add(study, series, view, call, referee=False):
    answer = parse(call.get('raw'))
    field = 'rules_followed' if referee else 'violation'
    valid = isinstance(answer, dict) and field in answer
    value = answer.get(field) if valid else None
    valid = valid and (value in ('yes', 'no', 'unknown') if referee
                      else value is None or type(value) is bool)
    abstain = valid and (value == 'unknown' if referee else value is None)
    groups[(study, series, view)].append(dict(
        input_tokens=call.get('input_tokens'), output_tokens=call.get('output_tokens'),
        usd=call.get('usd'), attempts=call.get('attempts'),
        status='UNKNOWN' if abstain else 'DECIDED' if valid else 'TECHNICAL_FAILURE',
        returned_model=call.get('returned_model')))


for series in ('deployment', 'sharing', 'calibration'):
    for path in sorted((ROOT / 'Honest_Agent/v0.3.1/results' / series).rglob('trial-*.json')):
        trial = read(path)
        for call in trial['calls']:
            if call['role'].startswith('monitor_'):
                add('HA v0.3.1', 'calibration' if series == 'calibration' else 'main',
                    call['role'].rsplit('_', 1)[1], call)

studies = [('Honest_Agent/v0.3.2', 'HA v0.3.2'),
           ('Honest_Agent/v0.3.3', 'HA v0.3.3'),
           ('Obedient_Rebel/v0.2.2', 'Rebel v0.2.2')]
for folder, study in studies:
    for path in sorted((ROOT / folder / 'results/judgments').rglob('*.json')):
        if path.name.endswith('.start.json'):
            continue
        judgment = read(path)
        add(study, 'main', judgment.get('view', path.stem.rsplit('-', 1)[1]),
            judgment['call'], referee=folder.endswith('v0.3.3'))

out = []
for (study, series, view), rows in sorted(groups.items()):
    n = len(rows)
    row = dict(study=study, series=series, view=view, calls=n,
               statuses=dict(Counter(r['status'] for r in rows)),
               models=dict(Counter(r['returned_model'] for r in rows)),
               attempts=dict(Counter(r['attempts'] for r in rows)))
    for field in ('input_tokens', 'output_tokens', 'usd'):
        values = [r[field] for r in rows if r[field] is not None]
        row[field + '_missing'] = n - len(values)
        if not values:
            row[field] = None
            continue
        numbers = [Decimal(str(v)) for v in values]
        row[field] = dict(total=float(sum(numbers)), mean=float(sum(numbers) / len(numbers)),
                          min=float(min(numbers)), max=float(max(numbers)))
    out.append(row)

ledgers = []
for folder in ('Honest_Agent/v0.3.1',) + tuple(s[0] for s in studies):
    path = ROOT / folder / 'results/spend-ledger.jsonl'
    raw = path.read_bytes()
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    ledgers.append(dict(study=folder, entries=len(rows),
                        usd=float(sum(Decimal(str(r['usd'])) for r in rows)),
                        roles=dict(Counter(r['role'] for r in rows))))

print(json.dumps(dict(scope='Historical survey only, 2026-11-11 HKT',
                      groups=out, ledgers=ledgers, source_sha256=hashes), indent=2))
