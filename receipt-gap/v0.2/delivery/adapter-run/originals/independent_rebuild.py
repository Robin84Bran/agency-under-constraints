"""Rebuild once in a full publication-shaped COPY; never collect.

The original failed frozen invocation is replayed once in the copy. Descriptive
terminal replay and post hoc baseline outputs are compared byte for byte.
No successful frozen-analysis byte identity is claimed when no output exists.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    work = args.output_root.resolve()
    if ROOT == work or ROOT in work.parents or work in ROOT.parents:
        parser.error('output-root must be outside source')
    work.mkdir(exist_ok=False)
    package = work/'v0.2'
    records = []

    def run(argv, cwd=ROOT, expected=0):
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        index = len(records)
        (work/f'{index}.stdout').write_text(proc.stdout)
        (work/f'{index}.stderr').write_text(proc.stderr)
        records.append({'argv': argv, 'returncode': proc.returncode, 'expected_returncode': expected})
        if proc.returncode != expected:
            raise ValueError(f'unexpected command result: {records[-1]}\n{proc.stderr}')
        return proc

    run([sys.executable, '-B', 'delivery/prepare_rebuild.py', '--fresh-clone', '--output', str(package)])
    run([sys.executable, '-B', 'delivery/verify_delivery.py', '--fresh-clone', '--output', str(work/'integrity.json')], package)
    run([sys.executable, '-B', 'rg_freeze.py', 'verify', '--freeze', 'freeze-r5.json'], package)
    p = run([sys.executable, '-B', 'rg_analysis.py', '--root', str(package), '--output', str(work/'analysis-v02.json')], package, 1)
    original = (ROOT/'delivery/frozen-analysis.stderr').read_text().splitlines()[-1]
    failure_identity = p.stderr.splitlines()[-1] == original
    assert failure_identity
    assert not (work/'analysis-v02.json').exists()
    run([sys.executable, '-B', 'delivery/summarize_saved.py', '--output', str(work/'descriptive-replay-v02.json')], package)
    run([sys.executable, '-B', 'delivery/code_baselines.py', '--output', str(work/'code-baselines')], package)
    checks = {}
    for relative in ('descriptive-replay-v02.json', 'code-baselines/summary.json', 'code-baselines/episodes.jsonl'):
        source, rebuilt = ROOT/'delivery'/relative, work/relative
        assert source.read_bytes() == rebuilt.read_bytes(), relative
        checks[relative] = {'byte_identical': True, 'sha256': digest(source)}
    # A copied verification tool must reject a substantive saved-evidence change.
    victim = package/'collection/STOP.json'
    original_bytes = victim.read_bytes()
    try:
        victim.write_bytes(original_bytes+b' ')
        run([sys.executable, '-B', 'delivery/verify_delivery.py', '--fresh-clone'], package, 1)
    finally:
        victim.write_bytes(original_bytes)
    omitted = json.loads((work/'integrity.json').read_text())['omitted_transients_with_saved_sha256']
    result = {'status': 'PASS', 'package_copy': str(package), 'commands': records,
              'copy_excluded_only': ['__pycache__', '.DS_Store', '.git', '*.lock'],
              'omitted_transients_with_saved_sha256': omitted, 'frozen_analysis_status': 'UNKNOWN',
              'frozen_analysis_reason': 'Both original and copy fail before scoring on the same r5 receipt allowlist defect.',
              'frozen_analysis_byte_identity': None, 'failure_signature_identical': failure_identity,
              'descriptive_rebuilds': checks, 'tampered_saved_evidence_rejected': True,
              'real_model_calls': 0, 'collection_repeated': False,
              'summary': 'Full sanitized copy: native r5 freeze PASS; original frozen-analysis failure reproduced. Descriptive replay and both post hoc baseline artifacts are byte-identical. Frozen numerical analysis identity is UNKNOWN because neither invocation produced a result.'}
    (work/'verification.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
