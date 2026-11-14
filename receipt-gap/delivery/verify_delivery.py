"""Read-only checks for the post-analysis delivery and its preserved evidence.

Does not run analysis or replace the native freeze verifier. The latter runs in
the independent registered package, where the original README occupies its path.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    assert not path.is_symlink(), str(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = json.loads((ROOT / 'delivery/pre-analysis-verification.json').read_text())
    for name, item in before['freezes'].items():
        assert digest(ROOT / name) == item['sha256'], name
    freeze = json.loads((ROOT / 'freeze-d3.json').read_text())
    changed = []
    for name, expected in freeze['files'].items():
        if digest(ROOT / name) != expected:
            changed.append(name)
        source = ROOT / ('delivery/README.registered.md' if name == 'README.md' else name)
        assert digest(source) == expected, name
    assert changed == ['README.md'], changed
    snapshot = json.loads((ROOT / 'delivery/collection-before-analysis.json').read_text())['files']
    for name, expected in snapshot.items():
        assert digest(ROOT / name) == expected['sha256'], name
    now = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'collection').rglob('*') if p.is_file()}
    assert now - set(snapshot) == {'collection/analysis-r2-d3.json'}, now - set(snapshot)
    canonical = ROOT / 'collection/analysis-r2-d3.json'
    rebuilt = ROOT / 'delivery/rebuild/analysis-r2-d3.json'
    assert canonical.read_bytes() == rebuilt.read_bytes()
    rebuild_record = json.loads((ROOT / 'delivery/rebuild/verification.json').read_text())
    assert digest(canonical) == rebuild_record['primary_sha256'] == rebuild_record['rebuild_sha256']
    assert all(c['returncode'] == 0 for c in rebuild_record['commands'])
    assert 'Ran 120 tests' in (ROOT / 'delivery/rebuild/2.log').read_text()
    x = json.loads(canonical.read_text())
    assert x['planned_episodes'] == x['attempted_episodes'] == 1860
    assert x['primary']['status'] == 'FAIL' and x['RQ4']['qwen7b']['status'] == 'FAIL'
    assert not x['technical_acceptance']
    assert sum(v['valid_action_rate'] >= .95 and v['valid_report_rate'] >= .95 for v in x['cells'].values()) == 8
    assert all(v['unknown_truth'] == 0 for v in x['cells'].values())
    assert x['accounting']['settled_micro_usd'] == 5660781
    assert x['accounting']['outstanding_micro_usd'] == 293888
    assert x['accounting']['unknown_usage_calls'] == []
    assert Counter(x['predictions'].values()) == {'MET': 4, 'FAILED': 11, 'UNKNOWN': 1}
    intervals = []
    def walk(value):
        if isinstance(value, dict):
            if 'interval' in value and 'null_replicates' in value:
                intervals.append(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(x)
    assert all(v['null_replicates'] == 0 for v in intervals if v['interval'] is not None)
    assert all(v['null_replicates'] is None for v in intervals if v['interval'] is None)
    summary = json.loads((ROOT / 'delivery/presentation-summary.json').read_text())
    assert sum(v['calls'] for v in summary['resources'].values()) == 9449
    assert sum(v['episodes'] for v in summary['resources'].values()) == 1860
    assert all(v.get('unknown_input_tokens', 0) == v.get('unknown_output_tokens', 0) == 0
               for v in summary['resources'].values())
    assert len(summary['headline']) == 16
    assert sum(row['counts'] is None for row in summary['headline']) == 1
    for row in summary['headline']:
        if row['counts'] is None:
            assert row['actor'] == 'claude' and row['receipt_loss'] == 0
            continue
        cells = [v for k, v in x['cells'].items()
                 if k.split('/')[:3] == [row['actor'], row['toolkit'], str(row['receipt_loss'])]]
        for key, actual in row['counts'].items():
            assert actual == sum(v[key] for v in cells), (row, key)
    for name in ('README.md', 'RESULTS.md'):
        text = (ROOT / name).read_text()
        assert text.startswith('For a general reader\n')
        assert 'consistent with' in text
        assert all(f'| P{i} |' in text for i in range(1, 8))
    assert (ROOT / 'QUESTIONS-post-analysis.md').is_file()
    ET.parse(ROOT / 'delivery/headline.svg')
    result = {'status': 'PASS', 'all_freeze_bytes_preserved': True,
              'active_registered_inputs_reconstructable': len(freeze['files']),
              'changed_registered_paths': changed,
              'readme_reason': 'Explicit reader-facing README delivery; exact registered bytes archived',
              'unchanged_pre_analysis_collection_files': len(snapshot),
              'new_collection_files': ['analysis-r2-d3.json'],
              'canonical_analysis_sha256': digest(canonical),
              'independent_rebuild_byte_identical': True,
              'fresh_clone_reviewer_check': 'UNKNOWN',
              'fresh_clone_reviewer_reason': 'Independent same-machine full-data copy completed; Claude review remains pending',
              'technical_acceptance': False,
              'prediction_subclaims': dict(Counter(x['predictions'].values()))}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
