"""Offline verification and one saved-evidence rebuild; never imports transport."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def transient(path):
    return any(n in ('__pycache__', '.git') for n in path.parts) or path.name == '.DS_Store' or path.name.endswith('.lock')


def verify(root):
    sys.path.insert(0, str(root))
    from od_freeze import verify as frozen_verify
    from od_d1 import verify_baseline as d1
    from od_d2 import verify_baseline as d2
    from od_d3 import verify_baseline as d3
    active = frozen_verify(root)
    f = json.loads((root / 'freeze-d3.json').read_text())
    by_hash = {}
    for n, h in f['files'].items():
        by_hash.setdefault(h, []).append(n)
    report = {}
    for p in sorted(root.glob('freeze*.json')):
        old = json.loads(p.read_text())
        resolved = {}
        for n, h in old['files'].items():
            choices = ([n] if f['files'].get(n) == h else []) + [v for v in by_hash.get(h, []) if v.endswith('/' + n)]
            if not choices or digest(root / choices[0]) != h:
                raise RuntimeError('historical frozen bytes missing: ' + str(p) + ':' + n)
            resolved[n] = {'saved_path': choices[0], 'sha256': h}
        report[p.name] = {'sha256': digest(p), 'files_verified': len(resolved), 'resolved_files': resolved}
    d1(root)
    d2(root)
    d3(root)
    report['baseline_verification'] = ['D1', 'D2', 'D3']
    report['active_sha256'] = active
    report['transient_policy'] = 'Normal frozen verifier; no missing-frozen-file exceptions or substitutions.'
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--output', type=Path, required=True, help='New directory outside the study root')
    p.add_argument('--verify-only', action='store_true')
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    if out == root or root in out.parents:
        p.error('output must be outside the study folder to preserve the package')
    out.mkdir(parents=True, exist_ok=False)
    result = verify(root)
    if not a.verify_only:
        analysis = out / 'analysis.json'
        subprocess.run([sys.executable, '-B', str(root / 'od_analysis.py'), '--root', str(root), '--data', str(root / 'collection'), '--output', str(analysis)], cwd=root, check=True)
        saved = root / 'collection/analysis-final-d3.json'
        result['analysis'] = {'saved_sha256': digest(saved), 'rebuilt_sha256': digest(analysis), 'byte_identical': saved.read_bytes() == analysis.read_bytes()}
        if not result['analysis']['byte_identical']:
            raise RuntimeError('analysis byte mismatch')
        subprocess.run([sys.executable, '-B', str(root / 'delivery/render_report.py'), '--root', str(root), '--analysis', str(analysis), '--output', str(out / 'rendered')], cwd=root, check=True)
        comparisons = {}
        for rebuilt in sorted((out / 'rendered').iterdir()):
            original = root / 'delivery' / rebuilt.name
            same = original.read_bytes() == rebuilt.read_bytes()
            comparisons[rebuilt.name] = {'sha256': digest(rebuilt), 'byte_identical': same}
            if not same:
                raise RuntimeError('report byte mismatch: ' + rebuilt.name)
        result['rendered_artifacts'] = comparisons
    (out / 'verification.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'verified_freezes': 6, 'output': str(out), 'analysis': result.get('analysis'), 'rendered_artifacts': len(result.get('rendered_artifacts', {}))}, sort_keys=True))


if __name__ == '__main__':
    main()
