"""Inventory the complete delivery; never modify scientific inputs or collection."""
import hashlib
import json
from pathlib import Path
from verify_delivery import ROOT, transient

path = ROOT/'delivery/package-manifest.json'
record = json.loads(path.read_text())
files, excluded = {}, {}
for item in sorted(ROOT.rglob('*')):
    if item.is_symlink():
        raise ValueError('symlink: '+str(item))
    if not item.is_file() or item == path:
        continue
    name = item.relative_to(ROOT).as_posix()
    value = item.read_bytes()
    entry = {'bytes':len(value), 'sha256':hashlib.sha256(value).hexdigest()}
    if transient(name):
        excluded[name] = entry['sha256']
    files[name] = entry
record['files'] = files
record['excluded_transient_files_with_saved_sha256'] = excluded
path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':'))+'\n')
print(json.dumps({'files':len(files), 'transients':excluded}))
