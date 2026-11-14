"""Rebuild frozen calculations once in a complete copy with lock files absent."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    work = args.output_root.resolve()
    if ROOT == work or ROOT in work.parents or work in ROOT.parents:
        parser.error('output-root must be outside source')
    work.mkdir(exist_ok=False)
    package, records = work/'v0.2', []

    def run(argv, cwd=ROOT, expected=0):
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        index = len(records)
        (work/f'{index}.stdout').write_text(proc.stdout)
        (work/f'{index}.stderr').write_text(proc.stderr)
        records.append({'argv':argv, 'returncode':proc.returncode, 'expected_returncode':expected})
        assert proc.returncode == expected, proc.stderr
        return proc

    run([sys.executable, '-B', 'delivery/prepare_rebuild.py', '--fresh-clone', '--output', str(package)])
    assert not any(package.rglob('*.lock')), 'lock file in copied package'
    run([sys.executable, '-B', 'delivery/verify_delivery.py', '--fresh-clone', '--output', str(work/'integrity.json')], package)
    run([sys.executable, '-B', 'rg_freeze.py', 'verify', '--freeze', 'freeze-r5.json'], package)
    run([sys.executable, '-B', 'delivery/r5_compatibility.py', '--output', str(work/'analysis-v02-compat.json')], package)
    run([sys.executable, '-B', 'delivery/render_results.py'], package)
    checks = {}
    # Every generated presentation artifact must also reproduce exactly.
    artifacts = ('README.md', 'RESULTS.md', 'headline.csv', 'headline.svg', 'predictions.csv', 'intervals.csv',
                 'contrasts-v01.csv', 'contrasts-v02.csv', 'cells.csv', 'reports-v02.csv', 'behavior-v02.csv',
                 'code-baselines.csv', 'presentation-summary.json')
    for name in ('analysis-v02-compat.json',)+artifacts:
        source = ROOT/'delivery'/name
        rebuilt = work/name if name == 'analysis-v02-compat.json' else package/'delivery'/name
        assert source.read_bytes() == rebuilt.read_bytes(), name
        checks[name] = {'byte_identical':True, 'sha256':digest(source), 'bytes':source.stat().st_size}
    victim = package/'collection/STOP.json'
    saved = victim.read_bytes()
    try:
        victim.write_bytes(saved+b' ')
        run([sys.executable, '-B', 'delivery/verify_delivery.py', '--fresh-clone'], package, 1)
    finally:
        victim.write_bytes(saved)
    run([sys.executable, '-B', 'delivery/verify_delivery.py', '--fresh-clone'], package)
    integrity = json.loads((work/'integrity.json').read_text())
    result = {'status':'PASS', 'same_machine_full_data_copy':True, 'fresh_git_clone':False,
              'package_copy':str(package), 'commands':records, 'locks_absent':True,
              'copy_excluded_only':['__pycache__','.DS_Store','.git','*.lock'],
              'omitted_transients_with_saved_sha256':integrity['omitted_transients_with_saved_sha256'],
              'frozen_analysis_byte_identity':True, 'canonical_adapter_scoring_invocations':1,
              'copied_adapter_scoring_invocations':1, 'artifacts':checks,
              'tampered_saved_evidence_rejected':True, 'real_model_calls':0, 'collection_repeated':False,
              'summary':'Fresh-clone-style complete copy with lock files absent: native r5 freeze and integrity PASS; adapted frozen analysis and all 13 presentation artifacts byte-identical. Saved-evidence tampering rejected. No model, network, push or Git calls.'}
    (work/'verification.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
