"""Post-analysis reproduction utility; never changes frozen scientific files.

Copies the exact freeze inventory and saved collection to a fresh tree, then
runs the original CLI in a fresh process. Report additions are excluded from
this frozen-input projection, not silently accepted by the original verifier.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('episodes.json', 'summary.json', 'tables.csv', 'tables.md',
         'frontier-seeds.csv', 'baselines.csv', 'headline.svg')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'source'
    source.mkdir()
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    source_hashes = dict(freeze['files'], **{'freeze.json': digest(ROOT / 'freeze.json')})
    for name, expected in source_hashes.items():
        assert digest(ROOT / name) == expected, name
        dest = source / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
        assert digest(dest) == expected, name
    shutil.copytree(ROOT / 'collection', source / 'collection')
    evidence_hashes = {p.relative_to(source / 'collection').as_posix(): digest(p)
                       for p in sorted((source / 'collection').rglob('*')) if p.is_file()}
    command = [sys.executable, '-B', 'trl_analysis.py', '--out', 'build/analysis-rebuilt']
    with (out / 'rebuild.log').open('x') as log:
        subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    files = {}
    for name in NAMES:
        original = ROOT / 'build/analysis-final' / name
        rebuilt = source / 'build/analysis-rebuilt' / name
        assert original.read_bytes() == rebuilt.read_bytes(), name
        files[name] = {'bytes': original.stat().st_size, 'sha256': digest(original)}
    for name, expected in source_hashes.items():
        assert digest(ROOT / name) == digest(source / name) == expected, name
    for name, expected in evidence_hashes.items():
        assert digest(ROOT / 'collection' / name) == digest(source / 'collection' / name) == expected, name
    report = {'status': 'PASS', 'scope': 'fresh copied frozen source/evidence; fresh interpreter; original frozen CLI and all gates',
              'command': command, 'frozen_files_including_freeze': len(source_hashes),
              'collection_files': len(evidence_hashes), 'source_hashes': source_hashes,
              'collection_hashes': evidence_hashes, 'byte_identical_outputs': files,
              'v01_byte_identity': json.loads((source / 'build/analysis-rebuilt/v01-rebuild/verification.json').read_text()),
              'model_calls': 0, 'network_calls': 0, 'git_operations': 0}
    with (out / 'byte-identity.json').open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    print('PASS: seven v0.2 outputs byte-identical; five archived v0.1 outputs byte-identical')


if __name__ == '__main__':
    main()
