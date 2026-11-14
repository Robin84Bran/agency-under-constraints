"""Copy registered inputs and saved collection into a new offline package.

Presentation-only helper, added after analysis. Does not analyze, collect, alter
the source, or replace any freeze. The delivered root README is intentionally
reader-facing; README.registered.md supplies its original frozen bytes here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    target = args.output.resolve()
    if target == root or target in root.parents:
        parser.error('output must be a new task-owned directory')
    target.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((root / 'freeze-d3.json').read_text())
    inputs = dict(manifest['files'])
    for name in ('freeze.json', 'freeze-d1.json', 'freeze-d2.json', 'freeze-d3.json'):
        inputs[name] = digest(root / name)
    for name, expected in inputs.items():
        source = root / ('delivery/README.registered.md' if name == 'README.md' else name)
        if source.is_symlink() or digest(source) != expected:
            raise ValueError('registered source mismatch: ' + name)
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    evidence = json.loads((root / 'delivery/collection-before-analysis.json').read_text())['files']
    for name, expected in evidence.items():
        source = root / name
        if source.is_symlink() or digest(source) != expected['sha256']:
            raise ValueError('saved collection changed: ' + name)
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    print(json.dumps({'package': str(target), 'registered_files_and_freezes': len(inputs),
                      'collection_files': len(evidence), 'analysis_executed': False}, sort_keys=True))


if __name__ == '__main__':
    main()
