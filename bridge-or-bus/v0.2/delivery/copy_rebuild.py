#!/usr/bin/env python3
"""Retain a filtered independent copy, rebuild there once, save the proof here."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from reproduce import ROOT, transient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof', default='delivery/rebuild-proof.json')
    args = parser.parse_args()
    proof_path = ROOT / args.proof
    if proof_path.exists():
        raise ValueError('proof already exists; choose another proof path')
    destination = Path(tempfile.mkdtemp(prefix='bridge-or-bus-v02-rebuild-')) / 'v0.2'
    removed = {}

    def ignore(directory, names):
        omitted = []
        for name in names:
            path = Path(directory) / name
            rel = path.relative_to(ROOT).as_posix()
            if transient(rel) and (path.is_file() or name in ('__pycache__', '.git')):
                omitted.append(name)
                if path.is_file():
                    removed[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return omitted

    shutil.copytree(ROOT, destination, ignore=ignore)
    leftovers = [p.relative_to(destination).as_posix() for p in destination.rglob('*')
                 if transient(p.relative_to(destination).as_posix())]
    if leftovers:
        raise ValueError('copy retained transients: ' + repr(leftovers))
    command = [sys.executable, '-B', 'delivery/reproduce.py', '--fresh-clone', '--fixtures']
    result = subprocess.run(command, cwd=destination, text=True, capture_output=True)
    (destination/'build/independent-rebuild-stdout.txt').write_text(result.stdout)
    (destination/'build/independent-rebuild-stderr.txt').write_text(result.stderr)
    if result.returncode:
        raise RuntimeError(f'independent rebuild failed; evidence retained at {destination}: {result.stderr[-2000:]}')
    report = json.loads((destination/'build/reproduction-report.json').read_bytes())
    original = (ROOT/'build/results.json').read_bytes()
    rebuilt = (destination/'build/reproduced-results.json').read_bytes()
    assert original == rebuilt and report['byte_identical']
    proof = dict(report, copy_root=str(destination), command=command,
                 source_root=str(ROOT), removed_transient_files=removed,
                 copy_retained_transients=leftovers, subprocess_exit_status=result.returncode,
                 independent_direct_byte_comparison=original == rebuilt,
                 collection_invocations=0, original_empirical_analysis_invocations=1,
                 statement='Separate filesystem COPY with only the documented publication exclusions; not a network clone or a separate reviewer.')
    proof_path.write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print(json.dumps(proof, sort_keys=True))


if __name__ == '__main__':
    main()
