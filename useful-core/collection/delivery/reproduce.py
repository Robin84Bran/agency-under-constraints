"""Read-only fresh-clone adapter; never edit frozen source, prompts, or evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def transient(path):
    p = Path(path)
    return ('__pycache__' in p.parts or '.git' in p.parts or
            p.name == '.DS_Store' or p.name.endswith('.lock'))


def fresh_clone_mode(root):
    """Skip only absent, declared transient pins in the D2 historical inventory.

    The unchanged freeze verifier still hashes the original baseline JSON itself.
    Existing transient files remain subject to their original hash checks.
    The original baseline validator checks all other pins, journals, checkpoints,
    accounting, and time semantics. No scoring or statistics functions are patched.
    """
    import uc_d2
    from uc_store import read, Stop
    declared = read(root / 'collection/delivery/transient-exclusions.json')['files']
    baseline_path = (root / uc_d2.BASELINE).resolve()
    baseline = read(baseline_path)
    omitted = {}
    for name, pin in baseline['files'].items():
        full = 'collection/' + name
        if transient(full) and not (root / full).exists():
            claim = declared.get(full)
            if claim is None or any(claim.get(k) != pin[k] for k in ('bytes', 'sha256')):
                raise Stop('undeclared or inconsistent excluded transient: ' + full)
            omitted[name] = pin
    original_baseline = uc_d2.baseline
    original_read = uc_d2.read

    def filtered_baseline(root_arg, base):
        def filtered_read(path):
            value = original_read(path)
            if Path(path).resolve() == baseline_path:
                value = dict(value, files={k: v for k, v in value['files'].items() if k not in omitted})
            return value
        uc_d2.read = filtered_read
        try:
            return original_baseline(root_arg, base)
        finally:
            uc_d2.read = original_read
    uc_d2.baseline = filtered_baseline
    return {'collection/' + name: pin for name, pin in omitted.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fresh-clone', action='store_true', help='skip only declared absent transient pins')
    p.add_argument('--verify-only', action='store_true')
    p.add_argument('--output', type=Path, help='new output path; required unless --verify-only')
    args = p.parse_args()
    if not args.verify_only and args.output is None:
        p.error('--output is required for a rebuild')
    omitted = fresh_clone_mode(ROOT) if args.fresh_clone else {}
    if args.verify_only:
        from uc_d2 import provenance
        digest = provenance(ROOT, ROOT / 'collection')
        result = {'active_freeze_sha256': digest, 'omitted_transient_pins': omitted}
    else:
        from uc_analysis import analyze
        analyze(ROOT, ROOT / 'collection', args.output)
        rebuilt = args.output.read_bytes()
        expected = (ROOT / 'collection/analysis-d2-final.json').read_bytes()
        result = {'byte_identical': rebuilt == expected,
                  'sha256': hashlib.sha256(rebuilt).hexdigest(),
                  'bytes': len(rebuilt), 'omitted_transient_pins': omitted}
        if rebuilt != expected:
            print(json.dumps(result, sort_keys=True))
            raise SystemExit('rebuild differs from saved canonical analysis')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
