"""Rebuild the saved final analysis in a new, hash-verified source snapshot.
Run from the project root: python3 -B build/delivery/rebuild.py --out build/rebuild-final
No collection, provider imports, Git mutations, or network access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(out)
    preflight = json.loads((root/'build/delivery/preflight.json').read_text())
    source = out/'source'
    source.mkdir(parents=True)
    for name, entry in preflight['files'].items():
        original = root/name
        if digest(original) != entry['sha256']:
            raise RuntimeError('Original input changed: '+name)
        target = source/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        if digest(target) != entry['sha256']:
            raise RuntimeError('Copy differs: '+name)
    commands = [
        [sys.executable, '-B', 'trl_freeze.py', 'verify'],
        [sys.executable, '-B', 'trl_analysis.py', '--base', 'collection', '--out', '../analysis'],
    ]
    for index, command in enumerate(commands):
        with (out/('verify.log' if index == 0 else 'analysis.log')).open('x') as log:
            subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    files = {}
    names = ('episodes.json','summary.json','tables.csv','tables.md','frontier-seeds.csv')
    if {p.name for p in (out/'analysis').iterdir()} != set(names):
        raise RuntimeError('Unexpected rebuild output set')
    for name in names:
        first, rebuilt = root/'build/analysis-first'/name, out/'analysis'/name
        files[name] = {'first_sha256':digest(first), 'rebuilt_sha256':digest(rebuilt),
                       'bytes':first.stat().st_size,'byte_identical':first.read_bytes()==rebuilt.read_bytes()}
    unchanged = all(digest(root/name)==entry['sha256'] and digest(source/name)==entry['sha256']
                    for name,entry in preflight['files'].items())
    report = {'status':'PASS' if unchanged and all(v['byte_identical'] for v in files.values()) else 'FAIL',
              'scope':'Separate copied source/evidence tree, fresh process and output directory; builder rebuild, not independent Claude review',
              'source_files_verified':len(preflight['files']), 'original_and_copy_unchanged':unchanged,
              'freeze_sha256':preflight['active_freeze_sha256'], 'commands':commands,'files':files}
    with (out/'byte-identity.json').open('x') as f:
        json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))
    if report['status'] != 'PASS':
        raise RuntimeError('Rebuild mismatch')

if __name__ == '__main__':
    main()
