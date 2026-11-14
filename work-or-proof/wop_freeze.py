"""Offline, append-only freeze and verification. No runtime/model imports."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    """Exclusive creation and fsync: evidence is never silently replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def frozen_paths(root):
    root = Path(root)
    paths = list(root.glob('*.py'))
    # Operational state and later delivery prose can evolve; registered design,
    # execution instructions and prior-exposure records remain frozen.
    paths += [root / name for name in ('PROTOCOL.md', 'RUN.md', 'SURVEY.md', 'QUESTIONS.md')
              if (root / name).is_file()]
    paths += [root / 'agreement_sizing.json', root / 'survey_inventory.json']
    for directory in ('config', 'evidence', 'imported', 'tests'):
        paths += [p for p in (root / directory).rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    return sorted(set(paths))


def make_freeze(root):
    root = Path(root).resolve()
    if (root / 'freeze.json').exists():
        raise FileExistsError('Existing freeze must never be overwritten')
    report = json.loads((root / 'imported/reconciliation.json').read_text())
    if report.get('status') != 'PASS':
        raise ValueError('Reconciliation must PASS before freeze')
    manifest = {'schema': 1, 'created_at': utcnow(),
                'protocol_status': 'APPROVED',
                'authority': 'Offline build only; no inference performed',
                'runtime_status': 'UNKNOWN',
                'runtime_reason': 'Server was not contacted. Frozen expected identity; actual metadata is recorded before first collection and checked on every resume.',
                'files': {p.relative_to(root).as_posix(): sha256(p) for p in frozen_paths(root)}}
    write_new(root / 'freeze.json', manifest)
    return sha256(root / 'freeze.json')


def verify_freeze(root):
    root = Path(root).resolve()
    manifest = json.loads((root / 'freeze.json').read_text())
    for relative, expected in manifest['files'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != expected:
            raise ValueError('Frozen file mismatch: ' + relative)
    actual = {p.relative_to(root).as_posix() for p in frozen_paths(root)}
    if actual != set(manifest['files']):
        raise ValueError('Frozen code/config/evidence inventory changed')
    return manifest
