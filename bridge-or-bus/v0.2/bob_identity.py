"""Pinned local manifest/layer identity; no model or network access."""
from pathlib import Path
from bob_core import PINS,sha,strict_load
from bob_collect import Stop,read
IDENTITY="evidence/local-identity.json"

def identity(root):
    """Verify the archived manifest -> layer chain; no dependency on model store."""
    root=Path(root)
    models=read(root/IDENTITY)['models']
    if set(models)!=set(PINS):
        raise Stop('D2 local identity inventory mismatch')
    for model,(tag,digest) in PINS.items():
        item=models[model]
        raw=(root/item['manifest_file']).read_bytes()
        if item['tag']!=tag or item['digest']!=digest or sha(raw)!=digest:
            raise Stop('D2 local manifest digest mismatch')
        layers={x['mediaType'].split('.')[-1]:x['digest'] for x in strict_load(raw)['layers']}
        for kind in ('template','system','params'):
            descriptor=item['layers'].get(kind)
            if (descriptor is None)!=(kind not in layers):
                raise Stop('D2 missing/extra identity layer')
            if descriptor is not None:
                data=(root/descriptor['file']).read_bytes()
                if 'sha256:'+sha(data)!=layers[kind] or sha(data)!=descriptor['sha256']:
                    raise Stop('D2 identity layer hash mismatch')
                if kind in ('template','system') and item[kind]!=data.decode():
                    raise Stop('D2 expected identity differs from pinned layer')
        if 'system' not in layers and item['system']!='':
            raise Stop('D2 invented system text')
    return models


def check_local_identity(root,model,show):
    expected=identity(root)[model]
    system=show.get('system')
    if system is None:
        system=''
    if show.get('template')!=expected['template'] or system!=expected['system']:
        raise Stop('local pinned template/system mismatch')


