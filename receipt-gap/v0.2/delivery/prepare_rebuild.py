"""Copy the ENTIRE v0.2 package, excluding only the publication transients.

No model, Git, network, freeze, or scientific analysis operation is performed.
The output must be a new directory outside the source tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from verify_delivery import ROOT, transient, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fresh-clone', action='store_true')
    args = parser.parse_args()
    verify(fresh=args.fresh_clone)
    target = args.output.resolve()
    if target == ROOT or ROOT in target.parents or target in ROOT.parents or target.exists():
        parser.error('output must be a new directory outside the package')
    excluded = {}
    for path in ROOT.rglob('*'):
        if path.is_symlink():
            raise ValueError('symlink: ' + str(path))
        if path.is_file() and transient(path.relative_to(ROOT).as_posix()):
            excluded[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    def ignore(directory, names):
        return [name for name in names if transient(name)]
    shutil.copytree(ROOT, target, ignore=ignore)
    print(json.dumps({'copied_to': str(target), 'excluded_files_with_saved_sha256': excluded,
                      'collection_repeated': False, 'analysis_executed': False}, indent=2))


if __name__ == '__main__':
    main()
