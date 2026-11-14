"""Reconstruct frozen test evidence without importing later collection state."""
from pathlib import Path
from trl_core import ROOT, sha
from trl_io import read


def frozen_bytes(name, digest):
    candidates = [ROOT/name, *sorted((ROOT/'deviations').glob('*/baseline/'+name))]
    for p in candidates:
        if p.is_file() and sha(p.read_bytes()) == digest:
            return p.read_bytes()
    raise AssertionError('missing historical bytes: '+name)


def collection_snapshot(target):
    """D3 scan inventories the exact collection used by D3/D3b regressions."""
    c = read(ROOT/'deviations/d3/clearance.json')
    for name, digest in read(ROOT/'deviations/d3/scan.json')['collection_files'].items():
        data = (ROOT/name).read_bytes()
        if sha(data) != digest:
            record = c['ledger_prefixes'][name]
            data = data[:record['bytes']]
        if sha(data) != digest:
            raise AssertionError('historical collection changed: '+name)
        p = Path(target)/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
