"""Revision-bound evidence paths; historical collection is never reused by r2."""
from pathlib import Path


def collection_dir(root):
    root = Path(root)
    return root / ('collection-r2' if (root / 'freeze-r2.json').exists() else 'collection')


def prior_path(root):
    root = Path(root)
    return root / 'config' / ('prior-spend-r2.json' if (root / 'freeze-r2.json').exists() else 'prior-spend.json')
