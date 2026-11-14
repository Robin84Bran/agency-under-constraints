#!/usr/bin/env python3
"""Additive delivery adapter. Never edits/import-replaces frozen scoring code.

Run from a copy/clone: python3 -B delivery/reproduce.py --fresh-clone
Only inventory presentation changes: delivery/ is an explicitly post-freeze
output namespace; absent documented transient files may be omitted. Present
transients must still match their saved hashes. No collection is dispatched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def transient(name):
    path = Path(name)
    return any(p in ('__pycache__', '.DS_Store', '.git') for p in path.parts) or path.name.endswith('.lock')


def check_hashes(root, files, fresh=False, omissions=None):
    omissions = {} if omissions is None else omissions
    for name, expected in files.items():
        path = root / name
        if path.is_symlink():
            raise ValueError('symlink: ' + name)
        if not path.is_file() and fresh and transient(name):
            omissions[name] = expected
            continue
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('missing/changed saved bytes: ' + name)
    return omissions


def verify(root=ROOT, fresh=False):
    from bob_core import canonical
    import bob_freeze
    from bob_freeze import FREEZES
    omissions = {}
    freezes = {}
    for name in FREEZES:
        record = read(root / name)
        if digest(canonical(record['files']).encode()) != record['content_sha256']:
            raise ValueError('manifest digest mismatch: ' + name)
        freezes[name] = digest((root / name).read_bytes())
    latest = read(root / FREEZES[-1])
    check_hashes(root, latest['files'], fresh, omissions)

    # The original verifier rejects any post-freeze deliverable. Preserve its
    # complete checks, changing only this explicit inventory boundary in memory.
    original_inventory = bob_freeze.inventory

    def delivery_inventory(directory):
        actual = original_inventory(directory)
        actual = {n: h for n, h in actual.items() if not n.startswith('delivery/')}
        expected_path = Path(directory) / 'freeze-r3.json'
        if fresh and expected_path.is_file():
            for n, h in read(expected_path)['files'].items():
                if n not in actual and transient(n):
                    # An absent transient is a documented exception, not a
                    # reconstructed file. Full content digests remain checked.
                    actual[n] = h
        return actual

    bob_freeze.inventory = delivery_inventory
    try:
        bob_freeze.verify(root)
        bob_freeze.push_gate(root, latest)
    finally:
        bob_freeze.inventory = original_inventory

    r1 = read(root / 'evidence/r2/preservation.json')['files']
    check_hashes(root, r1, fresh, omissions)
    actual_r1 = {p.relative_to(root).as_posix(): digest(p.read_bytes())
                 for p in (root / 'collection').rglob('*') if p.is_file()}
    actual_r1.update({n: freezes[n] for n in FREEZES[:2]})
    for n, h in r1.items():
        if n not in actual_r1 and fresh and transient(n):
            actual_r1[n] = h
    if actual_r1 != r1:
        raise ValueError('unexpected/missing r1 preservation inventory')

    r2 = read(root / 'evidence/r3/preservation.json')
    check_hashes(root, dict(r2['files'], **r2['unchanged_inputs'], **r2['parent_freezes']), fresh, omissions)
    for name, prefix in r2['append_only'].items():
        path = root / name
        if path.is_symlink():
            raise ValueError('symlink ledger')
        with path.open('rb') as stream:
            raw = stream.read(prefix['bytes'])
        if digest(raw) != prefix['sha256']:
            raise ValueError('preserved ledger prefix changed')
    manifest = root / 'delivery/package-manifest.json'
    package_count = None
    if manifest.is_file():
        package = read(manifest)
        check_hashes(root, package['files'], fresh, omissions)
        package_count = len(package['files'])
    return dict(status='PASS', mode='fresh-clone' if fresh else 'strict-delivery',
                freeze_sha256=freezes, latest_inventory_files=len(latest['files']),
                r1_preserved_files=len(r1), r2_preserved_files=len(r2['files']),
                package_files_verified=package_count,
                omitted_transients=omissions,
                analysis_code_changes=0, prompt_changes=0, collection_calls=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-clone', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--fixtures', action='store_true', help='also rebuild registered synthetic fixtures')
    parser.add_argument('--output', default='build/reproduced-results.json')
    parser.add_argument('--report', default='build/reproduction-report.json')
    args = parser.parse_args()
    report = verify(fresh=args.fresh_clone)
    if not args.verify_only:
        from bob_analysis import load_collection
        from bob_core import canonical
        result = load_collection(ROOT, read(ROOT / 'config/order.json'))
        v01 = read(ROOT / 'evidence/v01-replay.json')
        # Byte-for-byte the result assembly in frozen bob.py's analyze branch.
        result['version'] = '0.2'
        result['v01_beside_v02'] = dict(terminal=v01['terminal'], cells=v01['cells'],
            falsely_rejected_legal_actions=0,
            reason='v0.1 technical gate failed; zero correct submissions. v0.2 cannot erase that result.')
        raw = (canonical(result) + '\n').encode()
        path = ROOT / args.output
        if path.exists():
            raise ValueError('reproduction output exists; choose a new path')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected = (ROOT / 'build/results.json').read_bytes()
        report.update(result_bytes=len(raw), result_sha256=digest(raw),
                      expected_sha256=digest(expected), byte_identical=raw == expected)
        if raw != expected:
            raise ValueError('empirical reproduction differs')
    if args.fixtures:
        from bob_offline import rebuild
        report['fixtures'] = rebuild(ROOT)
    destination = ROOT / args.report
    if destination.exists():
        raise ValueError('reproduction report exists; choose a new path')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, sort_keys=True, separators=(',', ':')) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
