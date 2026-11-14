"""Stage the registered package for offline rebuilding after question-log appends.

This helper is delivery tooling, outside the frozen code inventory. It copies
saved files only; it never calls a model, changes a source file, or runs Git.
"""
import hashlib
import json
import shutil
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    freeze_bytes = (root / 'freeze.json').read_bytes()
    push = json.loads((root / 'collection' / 'push.json').read_text())
    if hashlib.sha256(freeze_bytes).hexdigest() != push['freeze_sha256']:
        raise ValueError('Freeze no longer matches the saved push attestation')
    freeze = json.loads(freeze_bytes)
    registered = root / 'delivery' / 'QUESTIONS.registered.md'
    original = registered.read_bytes()
    if not (root / 'QUESTIONS.md').read_bytes().startswith(original):
        raise ValueError('Question history no longer preserves its registered prefix')
    sources = {}
    for relative, expected in freeze['files'].items():
        if not (root / relative).resolve().is_relative_to(root):
            raise ValueError('Registered path escapes the project: ' + relative)
        source = registered if relative == 'QUESTIONS.md' else root / relative
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError('Registered file mismatch: ' + relative)
        sources[relative] = source
    target = root / 'results' / 'rebuild-workspace'
    target.mkdir(parents=True, exist_ok=False)
    for relative, source in sources.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    shutil.copy2(root / 'freeze.json', target / 'freeze.json')
    shutil.copytree(root / 'collection', target / 'collection')
    print('Prepared:', target)
    print('Run the offline commands from README.md in that folder.')


if __name__ == '__main__':
    main()
