"""Agreement-round sizing only: saved files in, deterministic JSON out; no providers imported."""
import ast
import hashlib
import json
import statistics
from pathlib import Path

BASE = Path('<WORKSPACE>/ANTresidency')
HA = BASE / 'Honest_Agent/v0.3.1'


def main():
    files = {}

    def read(p):
        raw = p.read_bytes()
        files[str(p.relative_to(BASE))] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    cfg = read(HA / 'config.json')
    provider = (HA / 'providers_api.py').read_bytes()
    files['Honest_Agent/v0.3.1/providers_api.py'] = hashlib.sha256(provider).hexdigest()
    cls = next(n for n in ast.parse(provider).body if isinstance(n, ast.ClassDef) and n.name == 'Ollama')
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    timeout = ast.literal_eval(init.args.defaults[-1])
    generate = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'generate')
    body = next(n.value for n in generate.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'body' for t in n.targets))
    fields = {ast.literal_eval(k): v for k, v in zip(body.keys, body.values)}
    options = {ast.literal_eval(k): ast.literal_eval(v)
               for k, v in zip(fields['options'].keys, fields['options'].values)
               if isinstance(v, ast.Constant)}
    assert options == {'temperature': 0.6, 'top_k': 16, 'num_predict': 192}
    assert timeout == 180
    ha = [read(p) for s in ('deployment', 'sharing')
          for p in sorted((HA / 'results' / s).glob('*/*/trial-*.json'))]
    rebel = [read(p) for p in sorted((BASE / 'Obedient_Rebel/v0.2.1/results/main').glob('*.json'))]
    assert (len(ha), len(rebel)) == (360, 1080)
    n = len(ha) + len(rebel)
    calls_per_model = n * 2 + 24
    out = {'method': 'Historical report-call extrapolation, not measured monitor latency; serial execution.',
           'ha_trajectories': len(ha), 'rebel_trajectories': len(rebel),
           'primary_local_calls': n * 2 * 2, 'replay_local_calls': 48,
           'total_planned_local_calls': calls_per_model * 2,
           'expected_monitor_wall_seconds': None,
           'unknown_reason': 'No local monitor timings exist; new prompts, caching, loads and outputs may differ.',
           'saved_request_settings': dict(options, stream=ast.literal_eval(fields['stream']),
                                          format=ast.literal_eval(fields['format'])),
           'models': {}}
    for model in ('qwen7b', 'llama8b'):
        calls = [c for t in ha for c in t['calls'] if c['model'] == model and c['role'] == 'report']
        assert len(calls) == 120 and all(c['attempts'] == 1 for c in calls)
        elapsed = sum(c['seconds'] for c in calls)
        outputs = sum(c['output_tokens'] for c in calls)
        out['models'][model] = {
            'config': cfg['models'][model], 'historical_report_calls': len(calls),
            'seconds_sum': elapsed, 'seconds_mean': statistics.mean(c['seconds'] for c in calls),
            'seconds_median': statistics.median(c['seconds'] for c in calls),
            'input_tokens_mean': statistics.mean(c['input_tokens'] for c in calls),
            'output_tokens_mean': outputs / len(calls), 'planned_calls': calls_per_model,
            'baseline_proxy_seconds': calls_per_model * elapsed / len(calls),
            'output_cap_scaled_proxy_seconds': calls_per_model * elapsed / outputs * options['num_predict']}
    out['baseline_proxy_seconds'] = sum(m['baseline_proxy_seconds'] for m in out['models'].values())
    out['output_cap_scaled_proxy_seconds'] = sum(m['output_cap_scaled_proxy_seconds'] for m in out['models'].values())
    out['request_timeout_seconds'] = timeout
    out['all_requests_hit_timeout_hours'] = calls_per_model * 2 * timeout / 3600
    out['source_sha256'] = files
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
