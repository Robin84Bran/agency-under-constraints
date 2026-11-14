"""Offline survey only: read archived JSON; print deterministic usage inventory.

No project modules are imported, no inference is performed, and no files are
written. Run with python3 -B survey_inventory.py. Paths are archive-local.
"""
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ARCHIVE = Path('<WORKSPACE>/ANTresidency')
TOY = Path('<WORKSPACE>/00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof')
manifest = {}


def load(path):
    raw = path.read_bytes()
    manifest[str(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def signature(items):
    text = ''.join(f'{key}\t{value}\n' for key, value in sorted(items.items()))
    return hashlib.sha256(text.encode()).hexdigest()


def stats(values):
    return dict(total=sum(values), mean=statistics.mean(values),
                median=statistics.median(values), minimum=min(values), maximum=max(values))


def summarize(rows):
    calls = [row['call'] for row in rows]
    money = sum((Decimal(str(c['usd'])) for c in calls), Decimal(0))
    return dict(
        calls=len(calls),
        input_tokens=stats([c['input_tokens'] for c in calls]),
        output_tokens=stats([c['output_tokens'] for c in calls]),
        total_tokens=stats([c['input_tokens'] + c['output_tokens'] for c in calls]),
        usd=dict(total=float(money), mean=float(money / len(calls)),
                 median=statistics.median(c['usd'] for c in calls),
                 minimum=min(c['usd'] for c in calls), maximum=max(c['usd'] for c in calls)),
        verdicts=dict(Counter('abstain' if r['verdict'] is None else str(r['verdict']).lower() for r in rows)),
        breaches=sum(r['breach'] for r in rows),
        true_positives=sum(r['breach'] and r['verdict'] is True for r in rows),
        false_positives=sum(not r['breach'] and r['verdict'] is True for r in rows),
        breach_abstentions=sum(r['breach'] and r['verdict'] is None for r in rows),
        clean_abstentions=sum(not r['breach'] and r['verdict'] is None for r in rows),
        parse_errors=sum(bool(c.get('error')) for c in calls),
        extra_attempts=sum(c['attempts'] - 1 for c in calls),
        returned_models=dict(Counter(c.get('returned_model') for c in calls)),
    )


def main():
    output = dict(scope='Survey inventory, not policy evaluation', date_hkt='2026-11-11', studies={})
    ha = ARCHIVE / 'Honest_Agent/v0.3.1'
    ha_trials = {}
    for series in ('deployment', 'sharing'):
        for path in sorted((ha / 'results' / series).glob('*/*/trial-*.json')):
            ha_trials[path.relative_to(ha / 'results').as_posix()] = load(path)
    rebel = ARCHIVE / 'Obedient_Rebel/v0.2.1/results/main'
    rebel_trials = {p.name: load(p) for p in sorted(rebel.glob('*.json'))}
    assert len(ha_trials) == 360 and len(rebel_trials) == 1080
    for rel in ('Honest_Agent/v0.3.1', 'Honest_Agent/v0.3.2', 'Honest_Agent/v0.3.3', 'Obedient_Rebel/v0.2.2'):
        base = ARCHIVE / rel
        cfg = load(base / 'config.json')
        groups = defaultdict(list)
        pairs = defaultdict(dict)
        if rel.endswith('0.3.1'):
            for series in ('deployment', 'sharing', 'calibration'):
                for path in sorted((base / 'results' / series).glob('*/*/trial-*.json')):
                    data = load(path)
                    for c in data['calls']:
                        if not c['role'].startswith('monitor_'):
                            continue
                        view = c['role'].split('_')[-1]
                        split = 'calibration' if series == 'calibration' else 'main'
                        row = dict(call=c, verdict=data['monitors']['claude_' + view], breach=data['truth']['violation'])
                        groups[split + '/' + view].append(row)
                        if split == 'main':
                            pairs[path.relative_to(base / 'results').as_posix()][view] = row
        else:
            for path in sorted((base / 'results/judgments').rglob('*.json')):
                if path.name.endswith('.start.json'):
                    continue
                data = load(path)
                c = data['call']
                view = data.get('view', c['role']).split('_')[-1]
                if rel.startswith('Obedient'):
                    key = data['run']
                    breach = rebel_trials[key]['truth']['compliance'] is False
                else:
                    parent = path.parent.relative_to(base / 'results/judgments')
                    key = (parent / (path.stem.rsplit('-', 1)[0] + '.json')).as_posix()
                    breach = ha_trials[key]['truth']['violation']
                if rel.endswith('0.3.3'):
                    assert data['valid']
                    answer = data['answer']['rules_followed']
                    verdict = None if answer == 'unknown' else answer == 'no'
                else:
                    assert data['model_verified']
                    verdict = data['verdict']
                row = dict(call=c, verdict=verdict, breach=breach)
                groups['main/' + view].append(row)
                pairs[key][view] = row
        assert all(set(pair) == {'final', 'trace'} for pair in pairs.values())
        summary = {k: summarize(v) for k, v in sorted(groups.items())}
        for rows in groups.values():
            for row in rows:
                call = row['call']
                price = cfg['prices_usd_per_million_tokens'][call['model']]
                expected = (call['input_tokens'] * price['input'] + call['output_tokens'] * price['output']) / 1e6
                assert abs(expected - call['usd']) < 1e-10
                text = call['raw'].strip()
                try:
                    raw = json.loads(text)
                except ValueError:
                    raw = json.loads(text[text.index('{'):text.rindex('}') + 1])
                if 'violation' in raw:
                    assert raw['violation'] is row['verdict']
                else:
                    assert set(raw) == {'job_done', 'rules_followed'}
        ledger_path = base / 'results/spend-ledger.jsonl'
        ledger_raw = ledger_path.read_bytes()
        manifest[str(ledger_path)] = hashlib.sha256(ledger_raw).hexdigest()
        ledger = [json.loads(line) for line in ledger_raw.splitlines() if line.strip()]
        ledger_by_role = defaultdict(list)
        for entry in ledger:
            ledger_by_role[entry['role']].append(Decimal(str(entry['usd'])))
        ledger_total = sum((Decimal(str(x['usd'])) for x in ledger), Decimal(0))
        saved_total = sum((Decimal(str(x['usd']['total'])) for x in summary.values()), Decimal(0))
        preflight = sum(ledger_by_role['preflight'], Decimal(0))
        assert abs(ledger_total - saved_total - preflight) < Decimal('0.00000001')
        for key, group in summary.items():
            view = key.split('/')[-1]
            role = view if rel.endswith('0.3.3') else 'monitor_' + ('gpt' if rel.endswith('0.3.2') else 'claude') + '_' + view
            # v0.3.1 main and calibration share ledger roles; reconcile their sum.
            saved_role = sum(v['usd']['total'] for k, v in summary.items() if k.endswith('/' + view))
            assert abs(float(sum(ledger_by_role[role], Decimal(0))) - saved_role) < 1e-8
        triggered = [p for p in pairs.values() if p['final']['verdict'] is not False]
        census_tokens = sum(p['final']['call']['input_tokens'] + p['final']['call']['output_tokens'] for p in pairs.values())
        escalation_tokens = sum(p['trace']['call']['input_tokens'] + p['trace']['call']['output_tokens'] for p in triggered)
        census_usd = sum(p['final']['call']['usd'] for p in pairs.values())
        escalation_usd = sum(p['trace']['call']['usd'] for p in triggered)
        output['studies'][rel] = dict(
            groups=summary, unique_actor_runs=len(pairs), paired_views=len(pairs),
            ledger=dict(records=len(ledger), total_usd=float(ledger_total),
                        preflight_usd=float(preflight), estimated_entries=sum(bool(x['estimated']) for x in ledger)),
            recorded_prices=cfg['prices_usd_per_million_tokens'],
            triage_inventory=dict(trigger='final violation or abstention', escalations=len(triggered),
                                  report_census_tokens=census_tokens, escalation_tokens=escalation_tokens,
                                  total_tokens=census_tokens + escalation_tokens,
                                  report_census_usd=census_usd, escalation_usd=escalation_usd,
                                  total_usd=census_usd + escalation_usd))
    toy = load(TOY / 'results.json')
    model_hash = hashlib.sha256((TOY / 'model.mjs').read_bytes()).hexdigest()
    assert model_hash == toy['modelSha256']
    assert sum(len(b['outcomes']) for b in toy['batches']) == 3200
    for batch in toy['batches']:
        for policy in batch['summary']:
            vals = [x['accepted'] for x in batch['outcomes'] if x['policy'] == policy]
            assert len(vals) == 64
            assert statistics.mean(vals) == batch['summary'][policy]['accepted']['mean']
    output['toy'] = dict(model_sha256=model_hash, worlds=toy['worlds'], outcomes=toy['policyOutcomes'],
                         accepted_means={b['id']: {p: v['accepted']['mean'] for p, v in b['summary'].items()} for b in toy['batches']})
    output['source_manifest'] = dict(files=len(manifest), path_and_sha256_digest=signature(manifest))
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
