"""Offline A1 lineage validation; no transport or Git imports."""
from pathlib import Path
from uc_core import canonical,sha
from uc_store import read,Stop

PARENT_SHA256='fc497643b1e72f1e928ab8a36dc74d72bc2b82d6a70239c1e18868924a854d51'
CHANGED={'uc_core.py','uc_store.py','uc_transport.py','uc_collect.py','uc_freeze.py',
         'uc_analysis.py','tests/test_runtime.py','RUN.md','PROJECT_STATE.md'}


def active(root):
    root=Path(root)
    if (root/'freeze-d2.json').exists():
        from uc_d2 import validate_d2
        value=read(root/'freeze-d2.json');validate_d2(root,value)
        return 'freeze-d2.json',value
    if (root/'freeze-d1.json').exists():
        from uc_lineage import validate_d1
        value=read(root/'freeze-d1.json');validate_d1(root,value)
        if (root/'freeze-d1.json').is_symlink():raise Stop('symlink D1 freeze')
        return 'freeze-d1.json',value
    name='freeze-a1.json' if (root/'freeze-a1.json').exists() else 'freeze.json'
    if (root/name).is_symlink() or (root/'freeze.json').is_symlink():
        raise Stop('symlink active freeze')
    value=read(root/name)
    if name=='freeze-a1.json':
        validate_a1(root,value)
    return name,value


def validate_a1(root,value):
    root=Path(root)
    if sha((root/'freeze.json').read_bytes())!=PARENT_SHA256 or value.get('parent_sha256')!=PARENT_SHA256:
        raise Stop('A1 parent binding mismatch')
    parent=read(root/'freeze.json')
    if set(value.get('changed_inputs',[]))!=CHANGED:
        raise Stop('A1 amendment scope mismatch')
    if parent['content_sha256']!=sha(canonical(parent['files']).encode()):
        raise Stop('A1 parent content mismatch')
    for path,digest in parent['files'].items():
        archived='deviations/a1/original/'+path
        if path in CHANGED:
            if value['files'].get(archived)!=digest:
                raise Stop('A1 original archive mismatch: '+path)
        elif value['files'].get(path)!=digest:
            raise Stop('A1 changed a scientific or historical input: '+path)
