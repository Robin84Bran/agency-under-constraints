"""Verify published inputs, permitting only two explicitly recorded absent locks.

Then invoke the existing frozen-inventory projection and unchanged analysis CLI.
No collection, model, network, or Git commands are invoked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT.parent
EMPTY_SHA256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
OPTIONAL_LOCKS = {
    'collection/collector.lock': EMPTY_SHA256,
    'v0.2/collection/collector.lock': EMPTY_SHA256,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inventory(base, expected, missing):
    for name, saved in expected.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('unsafe inventory path: ' + name)
        path = base / relative
        key = path.relative_to(STUDY).as_posix()
        if path.is_symlink():
            raise ValueError('symlink input: ' + key)
        if not path.exists() and OPTIONAL_LOCKS.get(key) == saved:
            missing[key] = saved
            continue
        if not path.is_file() or digest(path) != saved:
            raise ValueError('missing or changed saved input: ' + key)


def verify_inputs():
    saved = json.loads((ROOT / 'build/rebuild-final/byte-identity.json').read_text())
    original = json.loads((ROOT / 'reuse/manifest.json').read_text())
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    expected_source = dict(freeze['files'], **{'freeze.json': digest(ROOT / 'freeze.json')})
    if saved['source_hashes'] != expected_source:
        raise ValueError('saved rebuild source inventory differs from freeze')
    missing = {}
    verify_inventory(STUDY, original, missing)
    verify_inventory(ROOT, saved['source_hashes'], missing)
    verify_inventory(ROOT / 'collection', saved['collection_hashes'], missing)
    actual = {p.relative_to(ROOT / 'collection').as_posix()
              for p in (ROOT / 'collection').rglob('*') if p.is_file()}
    expected = set(saved['collection_hashes'])
    allowed_missing = {key.removeprefix('v0.2/collection/') for key in missing
                       if key.startswith('v0.2/collection/')}
    if actual != expected - allowed_missing:
        raise ValueError('unexpected collection inventory entries')
    return {
        'status': 'PASS', 'absent_transient_locks': missing,
        'permitted_absent_locks_with_saved_sha256': OPTIONAL_LOCKS,
        'v01_inventory_entries': len(original),
        'v02_source_entries_including_freeze': len(saved['source_hashes']),
        'v02_collection_inventory_entries': len(saved['collection_hashes']),
        'source_projection_excludes_post_freeze_reports': ['README.md', 'RESULTS.md'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    # Validate before creating any artifacts or launching the existing rebuilder.
    report = verify_inputs()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError('choose a never-used output path: ' + str(out))
    if args.verify_only:
        out.mkdir(parents=True, exist_ok=False)
    else:
        # Frozen v0.1 detects paid starts with 'claude-' in the absolute path.
        # A neutral execution directory prevents parent names (e.g. claude-501)
        # from misclassifying local episodes. Never patch archived source.
        work = Path(tempfile.mkdtemp(prefix='trl-clone-', dir='/private/tmp'))
        stage = work / 'rebuild'
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run([sys.executable, '-B', str(ROOT / 'build/rebuild-frozen-results.py'),
                            '--out', str(stage)], check=True)
        finally:
            # Preserve all logs and partial outputs on failure, too.
            if stage.exists():
                shutil.move(str(stage), str(out))
            work.rmdir()
        rebuilt = json.loads((out / 'byte-identity.json').read_text())
        report['byte_identical_v02_outputs'] = rebuilt['byte_identical_outputs']
        report['v01_byte_identity'] = rebuilt['v01_byte_identity']
    # Recheck inputs after the child exits; no original inputs may change.
    if verify_inputs() != {k: v for k, v in report.items()
                           if k not in ('byte_identical_v02_outputs', 'v01_byte_identity')}:
        raise ValueError('inputs changed during reproduction')
    report.update(model_calls=0, network_calls=0, git_operations=0)
    with (out / 'published-inventory-verification.json').open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print('PASS: published inventories verified; absent lock exceptions explicitly recorded')


if __name__ == '__main__':
    main()
