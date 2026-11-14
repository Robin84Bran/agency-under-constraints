"""Agreement-round sizing only: saved-file reads, no provider imports or services.

Create once: python3 -B agreement-r2/measure_resources.py snapshot
Rebuild saved metadata arithmetic: python3 -B agreement-r2/measure_resources.py verify
Sibling response text/verdicts are never extracted, printed, or used for selection.
"""
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path('<WORKSPACE>')
HA = ROOT / 'ANTresidency/Honest_Agent/v0.3.1'
REBEL = ROOT / 'ANTresidency/Obedient_Rebel/v0.2.2'
WOP = ROOT / '06_intelligence/AI_research/research/work-or-proof'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stats(values):
    if not values:
        return None
    return dict(n=len(values), total=sum(values), mean=statistics.mean(values),
                median=statistics.median(values), min=min(values), max=max(values))


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['cohort'], row['model'], row['source'], row['view'])].append(row)
    out = []
    for (cohort, model, source, view), group in sorted(groups.items()):
        item = dict(cohort=cohort, model=model, source=source, view=view, calls=len(group))
        for field in ('seconds', 'usd', 'input_tokens', 'output_tokens', 'cached_input_tokens'):
            vals = [r[field] for r in group if type(r.get(field)) in (int, float)]
            item[field] = stats(vals)
            item[field + '_missing'] = len(group) - len(vals)
        out.append(item)
    balanced = {}
    for model in ('qwen7b', 'llama8b'):
        means = [g['seconds']['mean'] for g in out
                 if g['cohort'] == 'WoP metadata' and g['model'] == model and g['view'] == 'trace']
        balanced[model] = statistics.mean(means) if len(means) == 2 else None
    local_seconds = (1921 * sum(balanced.values())
                     if all(v is not None for v in balanced.values()) else None)
    claude = [r for r in rows if r['cohort'] == 'HA main']
    mean_usd = sum(Decimal(str(r['usd'])) for r in claude) / len(claude)
    frontier_seconds = 1921 * statistics.mean(r['seconds'] for r in claude)
    return dict(groups=out, source_balanced_local_trace_seconds=balanced,
                planned=dict(primary_per_model=1440, receipt_max_per_model=480,
                             preflight_per_model=1, local_max=3842, claude_max=1921,
                             local_timeout_seconds=180, local_active_cap_seconds=43200),
                estimates=dict(local_seconds=local_seconds,
                               local_1_5x_seconds=local_seconds * 1.5 if local_seconds is not None else None,
                               claude_seconds=frontier_seconds,
                               all_serial_seconds=local_seconds + frontier_seconds if local_seconds is not None else None,
                               claude_historical_mean_usd=float(mean_usd),
                               claude_1921_historical_usd=float(mean_usd * 1921),
                               claude_1921_1_5x_usd=float(mean_usd * 1921 * Decimal('1.5')),
                               reserve_scenario_per_call_usd=float(Decimal('2500') * 4 / 1000000 + Decimal('256') * 20 / 1000000),
                               reserve_scenario_total_with_5_usd=float(1921 * (Decimal('2500') * 4 / 1000000 + Decimal('256') * 20 / 1000000) + 5)))


def snapshot():
    rows = []
    settings = {}
    for name, path in [('ha_config', HA / 'config.json'), ('ha_providers', HA / 'providers_api.py'),
                       ('ha_runner', HA / 'run_v031.py'), ('wop_collector', WOP / 'wop_collect.py')]:
        raw = path.read_bytes()
        settings[name] = dict(path=str(path), sha256=sha(raw))
    config = json.loads((HA / 'config.json').read_bytes())
    tree = ast.parse((HA / 'run_v031.py').read_text())
    monitor = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'MONITOR' for t in n.targets))

    def add(path, raw, call, cohort, source, model, view):
        rows.append(dict(path=str(path), sha256=sha(raw), cohort=cohort, source=source,
                         model=model, view=view, seconds=call.get('seconds'), usd=call.get('usd'),
                         input_tokens=call.get('input_tokens'), output_tokens=call.get('output_tokens')))

    for series in ('deployment', 'sharing'):
        for path in sorted((HA / 'results' / series).rglob('trial-*.json')):
            raw = path.read_bytes()
            trial = json.loads(raw)
            for call in trial['calls']:
                if call['role'].startswith('monitor_'):
                    add(path, raw, call, 'HA main', 'HA', 'claude', call['role'].rsplit('_', 1)[1])
    for path in sorted((REBEL / 'results/judgments').glob('*.json')):
        if path.name.endswith('.start.json'):
            continue
        raw = path.read_bytes()
        judgment = json.loads(raw)
        add(path, raw, judgment['call'], 'Rebel main', 'Rebel', 'claude', judgment['view'])

    # Fix the file list once, without waiting for the sibling collection to finish.
    paths = sorted((WOP / 'collection/calls').rglob('*.json'))
    counters = Counter()
    for path in paths:
        if path.name.endswith('.start.json'):
            counters['start_files'] += 1
            continue
        raw = path.read_bytes()
        record = json.loads(raw)
        counters['receipts'] += 1
        if record.get('replay'):
            counters['replays_excluded'] += 1
            continue
        counters['original_receipts'] += 1
        usage = record.get('usage') or {}
        add(path, raw, dict(seconds=record.get('seconds'), usd=record.get('usd'),
                            input_tokens=usage.get('input_tokens'), output_tokens=usage.get('output_tokens')),
            'WoP metadata', record['source'], record['model'], record['view'])
        rows[-1]['cached_input_tokens'] = (record.get('response') or {}).get('prompt_eval_cached_count')
    data = dict(captured_at=datetime.now(timezone.utc).isoformat(),
                scope='Historical Claude costs/timings and sibling resource metadata only; no sibling verdicts inspected.',
                settings=settings, monitor_verbatim=monitor,
                local_models={k: config['models'][k] for k in ('qwen7b', 'llama8b')},
                saved_prices=config['prices_usd_per_million_tokens']['claude'],
                ollama_settings=dict(stream=False, format='json', temperature=0.6, top_k=16,
                                     num_predict=192, seed='source seed', timeout_seconds=180),
                sibling_file_snapshot=dict(counters), rows=rows, summary=summarize(rows))
    with (HERE / 'resource_measurements.json').open('x') as handle:
        json.dump(data, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(data['summary'], indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['snapshot']:
        snapshot()
    elif sys.argv[1:] == ['verify']:
        saved = json.loads((HERE / 'resource_measurements.json').read_bytes())
        assert summarize(saved['rows']) == saved['summary']
        assert sum(g['calls'] for g in saved['summary']['groups'] if g['cohort'] == 'HA main') == 720
        assert sum(g['calls'] for g in saved['summary']['groups'] if g['cohort'] == 'Rebel main') == 2160
        print('Saved resource arithmetic verified; no live files, model calls, or network used.')
    else:
        raise SystemExit('Use snapshot (exclusive creation) or verify (saved metadata only).')
