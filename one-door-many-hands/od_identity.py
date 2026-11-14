"""Portable manifest/layer and runtime metadata checks; no service imports."""
from pathlib import Path
from od_core import PINS,sha,strict_load
from od_io import read,Stop

def identity(root):
    models=read(Path(root)/'evidence/local-identity.json')['models']
    if set(models)!=set(PINS): raise Stop('identity inventory mismatch')
    for actor,(tag,digest) in PINS.items():
        m=models[actor];raw=(Path(root)/m['manifest_file']).read_bytes()
        if m['tag']!=tag or m['digest']!=digest or sha(raw)!=digest: raise Stop('manifest pin mismatch')
        layers={x['mediaType'].split('.')[-1]:x['digest'] for x in strict_load(raw)['layers']}
        for kind in ('template','system','params'):
            d=m['layers'].get(kind)
            if (d is None)!=(kind not in layers): raise Stop('missing/extra pinned layer')
            if d:
                data=(Path(root)/d['file']).read_bytes()
                if 'sha256:'+sha(data)!=layers[kind] or sha(data)!=d['sha256']: raise Stop('pinned layer mismatch')
                if kind in ('template','system') and data.decode()!=m[kind]: raise Stop('pinned metadata byte mismatch')
        if 'system' not in layers and m['system']!='': raise Stop('invented default system')
    return models

def check_identity(root,actor,show):
    m=identity(root)[actor]
    if show.get('template')!=m['template'] or (show.get('system') or '')!=m['system']: raise Stop('pinned template/default system mismatch')


def verify_preflight(root,actor,metadata):
    if actor=='claude':
        expected=read(Path(root)/'evidence/cli-contract.json')
        if metadata.get('binary_sha256')!=expected['binary_sha256'] or metadata.get('version')!=expected['version']:
            raise Stop('CLI binary/version drift')
    else:
        if not any(m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] for m in metadata.get('tags',{}).get('models',[])):
            raise Stop('local digest mismatch')
        check_identity(root,actor,metadata['show'])
