"""Post-analysis integrity checks; never collect or modify frozen inputs.

--fresh-clone permits ONLY absent __pycache__, .DS_Store, .git, and *.lock.
Every omission is reported with its saved hash. Present files must still match.
Historical manifests are checked against exact later amendment witnesses.
"""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def transient(name):
    parts = Path(name).parts
    return any(p in ('__pycache__', '.DS_Store', '.git') for p in parts) or parts[-1].endswith('.lock')


def digest(path):
    if path.is_symlink():
        raise ValueError('symlink: ' + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def verify(root=ROOT, fresh=False):
    omitted = {}

    def check(name, expected):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('unsafe inventory path: ' + name)
        path = root/name
        if any((root/Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts)+1)):
            raise ValueError('symlink inventory path: ' + name)
        if not path.exists() and fresh and transient(name):
            omitted[name] = expected
        elif digest(path) != expected:
            raise ValueError('hash mismatch: ' + name)

    names = ['freeze.json'] + ['freeze-r%d.json' % i for i in range(1, 6)]
    before = load(root/'delivery/pre-analysis.json')['freezes']
    records = []
    for i, name in enumerate(names):
        check(name, before[name])
        manifest = load(root/name)
        for filename, expected in manifest['files'].items():
            current = root/filename
            if current.is_file() and digest(current) == expected:
                continue
            witnesses = [root/'revisions'/('r%d' % j)/'originals'/filename for j in range(1, 6)]
            if not any(p.is_file() and digest(p) == expected for p in witnesses):
                check(filename, expected)
        if i:
            parent = load(root/names[i-1])
            assert manifest['parent_sha256'] == digest(root/names[i-1])
            changed = {f for f, h in parent['files'].items() if manifest['files'].get(f) != h}
            assert changed == set(manifest['changed_parent_files'])
            for f in changed:
                check('revisions/r%d/originals/%s' % (i, f), parent['files'][f])
            if i >= 2:
                assert manifest['parents'] == {n: digest(root/n) for n in names[:i]}
        records.append({'manifest': name, 'sha256': digest(root/name), 'files': len(manifest['files'])})
    # Check all preservation snapshots, including ledger prefixes that grew later.
    for revision in ('r2', 'r4', 'r5'):
        saved = load(root/'revisions'/revision/'preservation.json')
        for f, expected in saved['parents'].items():
            check(f, expected)
        for f, expected in saved['files'].items():
            if f in saved.get('prefixes', {}):
                entry = saved['prefixes'][f]
                prefix = (root/entry['snapshot']).read_bytes()
                assert len(prefix) == entry['bytes']
                assert hashlib.sha256(prefix).hexdigest() == entry['sha256']
                assert (root/f).read_bytes().startswith(prefix)
            else:
                check(f, expected)
    collection = load(root/'delivery/collection-before-analysis.json')['files']
    for f, entry in collection.items():
        check(f, entry['sha256'])
    current = {p.relative_to(root).as_posix() for p in (root/'collection').rglob('*') if p.is_file()}
    assert not current - set(collection), 'unexpected collection files'
    package = root/'delivery/package-manifest.json'
    if package.exists():
        inventory = load(package)
        for f, entry in inventory['files'].items():
            check(f, entry['sha256'])
        paths = list(root.rglob('*'))
        if any(p.is_symlink() for p in paths):
            raise ValueError('symlink in package')
        actual = {p.relative_to(root).as_posix() for p in paths if p.is_file() and not transient(p.relative_to(root).as_posix())}
        expected = {f for f in inventory['files'] if not transient(f)} | {'delivery/package-manifest.json'}
        assert actual == expected, 'package file inventory changed'
    return {'status': 'PASS', 'mode': 'fresh-clone' if fresh else 'strict', 'freezes': records,
            'collection_files_verified': len(collection) - len([f for f in omitted if f in collection]),
            'omitted_transients_with_saved_sha256': omitted,
            'scientific_code_or_evidence_changes': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fresh-clone', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    result = verify(fresh=a.fresh_clone)
    value = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if a.output:
        with a.output.open('x') as stream:
            stream.write(value)
    print(value)
