"""Copy the entire package minus only specified transients, then rebuild offline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from reproduce import transient


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inventory(root):
    kept, omitted = {}, {}
    # Traverse excluded directories too to retain every omitted file's saved hash.
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise RuntimeError('symlink requires explicit handling: ' + str(p))
        if p.is_file():
            target = omitted if transient(p.relative_to(root)) else kept
            target[p.relative_to(root).as_posix()] = {'sha256': digest(p), 'bytes': p.stat().st_size}
    return kept, omitted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--output', type=Path, required=True, help='New external folder for package and rebuilt output')
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    if root == out or root in out.parents:
        p.error('copy destination must be outside source')
    out.mkdir(parents=True, exist_ok=False)
    kept, omitted = inventory(root)
    snap = root / 'delivery/package-snapshot.json'
    if not snap.exists():
        record = {'kind': 'pre-copy package snapshot', 'policy': 'Exclude only __pycache__, .DS_Store, .git and *.lock paths; preserve original source and archive bytes.',
                  'self_reference': 'This manifest is created after the listed snapshot; it is subsequently included and byte-checked in the copy.', 'files': kept, 'omitted_transients': omitted}
        with snap.open('x') as f: f.write(json.dumps(record, indent=2, sort_keys=True) + '\n')
        kept['delivery/package-snapshot.json'] = {'sha256': digest(snap), 'bytes': snap.stat().st_size}
    package = out / 'one-door-many-hands'
    for name, info in kept.items():
        dest = package / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/name, dest)
        if digest(dest) != info['sha256']:
            raise RuntimeError('copy differs: ' + name)
    copied, copied_omissions = inventory(package)
    if copied != kept or copied_omissions:
        raise RuntimeError('package set or content drift')
    cmd = [sys.executable, '-B', str(package/'delivery/reproduce.py'), '--root', str(package), '--output', str(out/'rebuilt')]
    with (out/'rebuild-command.log').open('x') as log:
        subprocess.run(cmd, cwd=package, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = json.loads((out/'rebuilt/verification.json').read_text())
    result['copy'] = {'kind': 'independent local copy with GitHub publication exclusions', 'package': str(package), 'copied_files': len(kept), 'all_copied_files_byte_identical': True,
                      'omitted_transients': omitted, 'normal_frozen_verifier_passed': True, 'fresh_clone_exception_mode_required': False,
                      'package_snapshot_sha256': digest(package/'delivery/package-snapshot.json'), 'network_clone_performed': False}
    source_after, omitted_after = inventory(root)
    result['source_preserved'] = source_after == kept and omitted_after == omitted
    if not result['source_preserved']:
        raise RuntimeError('source changed during independent rebuild')
    with (out/'rebuild-verification.json').open('x') as f: f.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'copy_files':len(kept), 'omitted_files':len(omitted), 'analysis_byte_identical':result['analysis']['byte_identical'], 'rendered_artifacts':len(result['rendered_artifacts']), 'source_preserved':result['source_preserved']},sort_keys=True))


if __name__ == '__main__':
    main()
