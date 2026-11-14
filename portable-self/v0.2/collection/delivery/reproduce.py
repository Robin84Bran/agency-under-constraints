#!/usr/bin/env python3
"""Offline fresh-clone adapter. Never edits frozen source or collection evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def transient(path):
    p = Path(path)
    return any(x in ('__pycache__', '.git') for x in p.parts) or p.name == '.DS_Store' or p.name.endswith('.lock')


def fresh_verify(root):
    """Use the exact original verifier on a private compatibility snapshot.

    All substantive bytes come from the clone. Only omitted frozen transient
    bytes are reconstructed in this disposable validation view, from saved hex
    and SHA-256, so the original exact-inventory verifier needs no source edit.
    The real data and the analysis run directly from the clone, without locks.
    """
    import ps_freeze
    root = Path(root).resolve()
    manifest = ps_freeze.active_manifest(root)
    active = json.loads(manifest.read_text())
    expected = set(active['files'])
    actual = set(ps_freeze.inputs(root))
    assert {n for n in actual if not transient(n)} == {n for n in expected if not transient(n)}, 'substantive inventory changed'
    omitted = json.loads((root/'collection/delivery/transient-files.json').read_text())['files']
    saved = {x['path']: x for x in omitted}
    with tempfile.TemporaryDirectory(prefix='portable-self-validation-') as tmp:
        view = Path(tmp)
        names = expected | set(active.get('parents', {})) | {'freeze.json', 'freeze-usage-limit.json', manifest.name}
        for name in sorted(names):
            p = root/name
            assert not p.is_symlink(), name
            dest = view/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if transient(name):
                entry = saved[name]
                data = bytes.fromhex(entry['saved_hex'])
                assert hashlib.sha256(data).hexdigest() == entry['sha256'] == active['files'][name], name
                dest.write_bytes(data)
            else:
                shutil.copyfile(p, dest)
        digest = ORIGINAL_VERIFY(view)
    return digest


def deny(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system', 'os.posix_spawn'):
        raise RuntimeError('offline rebuild prohibits ' + event)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fresh-clone', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    sys.addaudithook(deny)
    import ps_freeze
    global ORIGINAL_VERIFY
    ORIGINAL_VERIFY = ps_freeze.verify
    if a.fresh_clone:
        # Compatibility changes only verification; analyze() remains frozen.
        ps_freeze.verify = fresh_verify
    freeze = ps_freeze.push_gate(ROOT)
    if a.output is None:
        print(json.dumps({'freeze_sha256': freeze, 'fresh_clone': a.fresh_clone, 'verified': True}))
        return
    from ps_analysis import analyze
    from ps_io import save
    result = analyze(ROOT, ROOT/'collection', False)
    save(a.output, result)
    original = ROOT/'collection/analysis-claude-envelope.json'
    actual = a.output.read_bytes()
    assert actual == original.read_bytes(), 'rebuild is not byte-identical'
    print(json.dumps({'freeze_sha256': freeze, 'analysis_sha256': hashlib.sha256(actual).hexdigest(),
                      'byte_identical': True, 'bytes': len(actual), 'fresh_clone': a.fresh_clone,
                      'network_and_subprocess_guard': True}))


if __name__ == '__main__':
    main()
