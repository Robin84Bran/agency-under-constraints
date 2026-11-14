"""Immutable manifest and GitHub server-event attestation. Never pushes."""
import argparse
import datetime as dt
from pathlib import Path
import re
import subprocess
from trl_core import ROOT, canonical, sha, strict_load
from trl_io import Stop, lock, now, read, save, timestamp

EXCLUDED = {'build','collection','__pycache__','.git','.agents','.codex','.aws'}


def inputs(root):
    result = []
    for p in Path(root).rglob('*'):
        rel = p.relative_to(root)
        if any(part in EXCLUDED or part.startswith('.') for part in rel.parts) or rel.as_posix() in ('freeze.json','freeze-d1.json','freeze-d2.json','freeze-d3.json','freeze-d3b.json','freeze-d3c.json','freeze-d3d.json','freeze-d4.json'):
            continue
        if p.is_symlink():
            raise Stop('symlink input forbidden: '+str(rel))
        if p.is_file():
            result.append(rel.as_posix())
    return sorted(result)


def freeze(root):
    root = Path(root)
    test = read(root/'evidence/test-report.json')
    if test['status']!='PASS' or test['failures'] or test['errors']:
        raise Stop('passing test evidence required')
    sizing = read(root/'config/sizing.json')
    if sizing['frontier_micro_usd']!=18083840 or sizing['including_protected_reserve_micro_usd']>25000000:
        raise Stop('reservation mismatch')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    if any(files.get(name)!=digest for name,digest in test.get('tested_files',{}).items()):
        raise Stop('tested inputs changed after verification')
    value = {'study':'three-rules-one-lunch','protocol_revision':'v0.1-build-r1','created_at':now(),
        'kind':'pre-inference offline freeze','files':files,'content_sha256':sha(canonical(files).encode()),
        'planned_episodes':960,'planned_calls':8960,'frontier_reservation_micro_usd':sizing['frontier_micro_usd'],
        'protected_reserve_micro_usd':1000000,'calls_made_by_builder':0,'push_status':'UNKNOWN',
        'frontier_readiness':read(root/'evidence/cli-contract.json')['readiness'],
        'dispatch_note':'Both cohorts HOLD before inference pending reviewed transport/budget readiness amendment and new freeze. No runtime override.'}
    save(root/'freeze.json',value)
    return verify(root)


ORIGINAL_FREEZE_SHA256 = '85d2dcc527e3c9fb37868109106939a1fe8eb4e24dbc4d03f3cbc8280253e6aa'
D1_CHANGED = {'trl_freeze.py','trl_collect.py','trl_transport.py','trl_validation.py',
              'tests/test_harness_analysis.py'}
D1_ADDED = {'DEVIATIONS.md','ERRATA.md','RUN-d1.md','PROJECT_STATE-d1.md',
            'tests/test_d1.py','evidence/test-report-d1.json','evidence/rebuild-d1.json'} | {
                'deviations/d1/baseline/'+name for name in D1_CHANGED}


def active_freeze(root):
    p = Path(root)/'freeze-d4.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d4.json'
    p = Path(root)/'freeze-d3d.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d3d.json'
    p = Path(root)/'freeze-d3c.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d3c.json'
    p = Path(root)/'freeze-d3b.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d3b.json'
    p = Path(root)/'freeze-d3.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d3.json'
    p = Path(root)/'freeze-d2.json'
    if p.exists() or p.is_symlink():
        return 'freeze-d2.json'
    p = Path(root)/'freeze-d1.json'
    return 'freeze-d1.json' if p.exists() or p.is_symlink() else 'freeze.json'


def d1_scope(root, f):
    p = Path(root)/'freeze.json'
    if p.is_symlink() or sha(p.read_bytes())!=ORIGINAL_FREEZE_SHA256:
        raise Stop('D1 original freeze identity mismatch')
    parent = read(p)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D1_CHANGED or
            added!=D1_ADDED|{'freeze.json'} or files.get('freeze.json')!=ORIGINAL_FREEZE_SHA256 or
            f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or f.get('deviation')!='D1'):
        raise Stop('D1 parent binding or permitted scope mismatch')
    for name in D1_CHANGED:
        if files.get('deviations/d1/baseline/'+name)!=parent['files'][name]:
            raise Stop('D1 baseline differs from original: '+name)
    mutable = {'files','content_sha256','created_at','kind','frontier_readiness','dispatch_note'}
    for key in set(parent)-mutable:
        if f.get(key)!=parent[key]:
            raise Stop('D1 changed scientific freeze metadata: '+key)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D1 predates original freeze')


def verify_manifest(root, f):
    files = f['files']
    expected = set(inputs(root))
    if f.get('deviation') in ('D1','D2','D3','D3b','D3c','D3d','D4'):
        expected.add('freeze.json')
    if f.get('deviation') in ('D2','D3','D3b','D3c','D3d','D4'):
        expected.add('freeze-d1.json')
    if f.get('deviation') in ('D3','D3b','D3c','D3d','D4'):
        expected.add('freeze-d2.json')
    if f.get('deviation') in ('D3b','D3c','D3d','D4'):
        expected.add('freeze-d3.json')
    if f.get('deviation') in ('D3c','D3d','D4'):
        expected.add('freeze-d3b.json')
    if f.get('deviation') in ('D3d','D4'):
        expected.add('freeze-d3c.json')
    if f.get('deviation')=='D4':
        expected.add('freeze-d3d.json')
    if not files or set(files)!=expected or f['content_sha256']!=sha(canonical(files).encode()):
        raise Stop('freeze input set/content manifest changed')
    for name,digest in files.items():
        p = root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=digest:
            raise Stop('frozen input changed: '+name)
    if f['frontier_reservation_micro_usd']!=read(root/'config/sizing.json')['frontier_micro_usd']:
        raise Stop('reservation mismatch')


def verify(root):
    root = Path(root)
    name = active_freeze(root)
    if (root/name).is_symlink():
        raise Stop('symlink freeze')
    f = read(root/name)
    if name=='freeze-d1.json':
        d1_scope(root,f)
    if name=='freeze-d2.json':
        d2_scope(root,f)
    if name=='freeze-d3.json':
        d3_scope(root,f)
    if name=='freeze-d3b.json':
        d3b_scope(root,f)
    if name=='freeze-d3c.json':
        d3c_scope(root,f)
    if name=='freeze-d3d.json':
        d3d_scope(root,f)
    if name=='freeze-d4.json':
        d4_scope(root,f)
    verify_manifest(root,f)
    return sha((root/name).read_bytes())


def freeze_d1(root):
    root = Path(root)
    if (root/'freeze-d1.json').exists():
        raise FileExistsError('freeze-d1.json is create-once')
    if any((root/'collection/episodes').glob('*/*.start.json')):
        raise Stop('D1 must precede inference')
    from trl_test import tested_inputs
    test = read(root/'evidence/test-report-d1.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
            not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D1 tests for current inputs required')
    parent = read(root/'freeze.json')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    files['freeze.json'] = ORIGINAL_FREEZE_SHA256
    f = {**parent,'created_at':now(),'kind':'pre-inference operational amendment',
         'deviation':'D1','original_freeze_sha256':ORIGINAL_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'frontier_readiness':'UNKNOWN',
         'dispatch_note':'D1 replaces advance transport certainty with empirical accounting and first scheduled Claude envelope verification; fresh push attestation still required.'}
    d1_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d1.json',f)
    return verify(root)


D1_FREEZE_SHA256 = 'f1985141e400d843ecd24f95f30445f85d67b45bd7e9e4a5b1b29f150ee6bb2b'
D2_CHANGED = {'DEVIATIONS.md','trl_freeze.py','trl_collect.py','trl_validation.py','trl_io.py',
              'tests/test_transport.py','tests/test_d1.py'}
D2_ADDED = {'trl_d2.py','tests/test_d2.py','RUN-d2.md','PROJECT_STATE-d2.md',
            'deviations/d2/clearance.json','evidence/test-report-d2.json','evidence/rebuild-d2.json'} | {
                'deviations/d2/baseline/'+n for n in D2_CHANGED}


def d2_scope(root,f):
    root = Path(root)
    p = root/'freeze-d1.json'
    if p.is_symlink() or sha(p.read_bytes())!=D1_FREEZE_SHA256:
        raise Stop('D2 D1 freeze identity mismatch')
    parent = read(p)
    d1_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D2_CHANGED or
        added!=D2_ADDED|{'freeze-d1.json'} or files.get('freeze-d1.json')!=D1_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D1_FREEZE_SHA256 or f.get('deviation')!='D2' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D2 parent binding or permitted scope mismatch')
    for n in D2_CHANGED:
        if files.get('deviations/d2/baseline/'+n)!=parent['files'][n]:
            raise Stop('D2 baseline differs from D1: '+n)
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D2 changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D2 predates D1')


def freeze_d2(root):
    from trl_test import tested_inputs
    from trl_d2 import stop_gate
    root = Path(root)
    if (root/'freeze-d2.json').exists():
        raise FileExistsError('freeze-d2.json is create-once')
    stop_gate(root)
    test = read(root/'evidence/test-report-d2.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D2 tests for current inputs required')
    parent = read(root/'freeze-d1.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':D1_FREEZE_SHA256})
    f = {**parent,'created_at':now(),'kind':'pre-analysis harness amendment',
         'deviation':'D2','parent_freeze_sha256':D1_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D2 clears only the bound local output-length STOP. Historical D1 starts remain bound to their original push; future starts require a fresh D2 push attestation.'}
    d2_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d2.json',f)
    return verify(root)


D2_FREEZE_SHA256 = 'c0869906324152f8d9fcc4cf48413b2da9f33aab360a42236142cd2e83e4f5a3'
D3_CHANGED = {'DEVIATIONS.md','trl_d2.py','trl_collect.py','trl_validation.py','trl_freeze.py',
              'trl_io.py','tests/test_d2.py'}
D3_ADDED = {'trl_d3.py','tests/test_d3.py','RUN-d3.md','PROJECT_STATE-d3.md',
            'deviations/d3/clearance.json','deviations/d3/scan.json',
            'evidence/test-report-d3.json','evidence/rebuild-d3.json'} | {
                'deviations/d3/baseline/'+n for n in D3_CHANGED}


def d3_scope(root,f):
    root = Path(root)
    p = root/'freeze-d2.json'
    if p.is_symlink() or sha(p.read_bytes())!=D2_FREEZE_SHA256:
        raise Stop('D3 D2 freeze identity mismatch')
    parent = read(p)
    d2_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D3_CHANGED or
        added!=D3_ADDED|{'freeze-d2.json'} or files.get('freeze-d2.json')!=D2_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D2_FREEZE_SHA256 or f.get('deviation')!='D3' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D3 parent binding or permitted scope mismatch')
    for n in D3_CHANGED:
        if files.get('deviations/d3/baseline/'+n)!=parent['files'][n]:
            raise Stop('D3 baseline differs from D2: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D3 must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D3 changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D3 predates D2')


def freeze_d3(root):
    from trl_test import tested_inputs
    from trl_d3 import stop_gate
    root = Path(root)
    if (root/'freeze-d3.json').exists():
        raise FileExistsError('freeze-d3.json is create-once')
    stop_gate(root)
    test = read(root/'evidence/test-report-d3.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D3 tests for current inputs required')
    parent = read(root/'freeze-d2.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':D1_FREEZE_SHA256,
                  'freeze-d2.json':D2_FREEZE_SHA256})
    f = {**parent,'created_at':now(),'kind':'pre-analysis harness amendment',
         'deviation':'D3','parent_freeze_sha256':D2_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D3 preserves ledger prefixes and clears only the bound local incomplete-envelope STOP. All historical starts retain their D1/D2 pushes; new starts need a fresh D3 push.'}
    d3_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d3.json',f)
    return verify(root)


D3_FREEZE_SHA256 = '8ed5be8d014db3f53ee2ec79d6ab6bbbb16eb6a9f410b5a4b03350eafc1077e9'
D3B_CHANGED = {'DEVIATIONS.md','trl_collect.py','trl_validation.py','trl_freeze.py','trl_io.py',
               'tests/test_d3.py','tests/test_transport.py'}
D3B_ADDED = {'trl_d3b.py','tests/test_d3b.py','RUN-d3b.md','PROJECT_STATE-d3b.md',
             'evidence/test-report-d3b.json','evidence/rebuild-d3b.json'} | {
                'deviations/d3b/baseline/'+n for n in D3B_CHANGED}


def d3b_scope(root,f):
    root = Path(root)
    p = root/'freeze-d3.json'
    if p.is_symlink() or sha(p.read_bytes())!=D3_FREEZE_SHA256:
        raise Stop('D3b D3 freeze identity mismatch')
    parent = read(p)
    d3_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D3B_CHANGED or
        added!=D3B_ADDED|{'freeze-d3.json'} or files.get('freeze-d3.json')!=D3_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D3_FREEZE_SHA256 or f.get('deviation')!='D3b' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D3b parent binding or permitted scope mismatch')
    for n in D3B_CHANGED:
        if files.get('deviations/d3b/baseline/'+n)!=parent['files'][n]:
            raise Stop('D3b baseline differs from D3: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3b/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D3b must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D3b changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D3b predates D3')


def freeze_d3b(root):
    from trl_test import tested_inputs
    from trl_d3b import stop_gate, prepush_gate
    root = Path(root)
    if (root/'freeze-d3b.json').exists():
        raise FileExistsError('freeze-d3b.json is create-once')
    stop_gate(root)
    prepush_gate(root)
    test = read(root/'evidence/test-report-d3b.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D3b tests for current inputs required')
    parent = read(root/'freeze-d3.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256,'freeze-d1.json':D1_FREEZE_SHA256,
                  'freeze-d2.json':D2_FREEZE_SHA256,'freeze-d3.json':D3_FREEZE_SHA256})
    f = {**parent,'created_at':now(),'kind':'pre-analysis harness amendment',
         'deviation':'D3b','parent_freeze_sha256':D3_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D3b adds a durable three-episode transport pause and strict Claude schema-tool two-turn acceptance. Unrun D3 needs no intermediate push; new starts require a fresh D3b push.'}
    d3b_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d3b.json',f)
    return verify(root)


D3B_FREEZE_SHA256 = '1e6b54b75fdf9d858b8e7093f857488c86cede67a996842e65e0cd487a9f07f0'
D3C_CHANGED = {'DEVIATIONS.md','trl_validation.py','trl_freeze.py',
               'tests/test_d3.py','tests/test_d3b.py'}
D3C_ADDED = {'tests/historical.py','tests/test_d3c.py','RUN-d3c.md','PROJECT_STATE-d3c.md',
             'deviations/d3c/disposition.json','evidence/test-report-d3c.json',
             'evidence/rebuild-d3c.json'} | {
                 'deviations/d3c/baseline/'+n for n in D3C_CHANGED} | {
                 'fixtures/d3c/'+n for n in ('r1-j0.raw.json','r1-j0.request.json',
                     'r1-j0.parsed.json','r1-j0.start.json','episode.json')}


def d3c_scope(root,f):
    root = Path(root)
    p = root/'freeze-d3b.json'
    if p.is_symlink() or sha(p.read_bytes())!=D3B_FREEZE_SHA256:
        raise Stop('D3c D3b freeze identity mismatch')
    parent = read(p)
    d3b_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D3C_CHANGED or
        added!=D3C_ADDED|{'freeze-d3b.json'} or files.get('freeze-d3b.json')!=D3B_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D3B_FREEZE_SHA256 or f.get('deviation')!='D3c' or
        f.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256):
        raise Stop('D3c parent binding or permitted scope mismatch')
    for n in D3C_CHANGED:
        if files.get('deviations/d3c/baseline/'+n)!=parent['files'][n]:
            raise Stop('D3c baseline differs from D3b: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3c/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D3c must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D3c changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D3c predates D3b')


def freeze_d3c(root):
    """Seal the offline harness repair; never clears a STOP or enables dispatch."""
    from trl_test import tested_inputs
    root = Path(root)
    if (root/'freeze-d3c.json').exists():
        raise FileExistsError('freeze-d3c.json is create-once')
    test = read(root/'evidence/test-report-d3c.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D3c tests for current inputs required')
    parent = read(root/'freeze-d3b.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    for n in ('freeze.json','freeze-d1.json','freeze-d2.json','freeze-d3.json','freeze-d3b.json'):
        files[n] = sha((root/n).read_bytes())
    f = {**parent,'created_at':now(),'kind':'offline harness amendment',
         'deviation':'D3c','parent_freeze_sha256':D3B_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D3c fixes zero-count subagent statistics. The stopped episode is scored without rerun; STOP and all collection evidence remain unchanged. This offline amendment grants no clearance, attestation or dispatch.'}
    d3c_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d3c.json',f)
    return verify(root)


D3C_FREEZE_SHA256 = 'fbd156d7df3540acdd9d6264ce588257629b8177d41005a0f42a6415b0a28697'
D3D_CHANGED = {'DEVIATIONS.md','trl_freeze.py','trl_collect.py','trl_d3b.py','trl_io.py',
               'tests/test_d3c.py'}
D3D_ADDED = {'trl_d3c.py','tests/test_d3d.py','RUN-d3d.md','PROJECT_STATE-d3d.md',
             'deviations/d3c/clearance.json','evidence/test-report-d3d.json',
             'evidence/rebuild-d3d.json'} | {'deviations/d3d/baseline/'+n for n in D3D_CHANGED}


def d3d_scope(root,f):
    root = Path(root)
    p = root/'freeze-d3c.json'
    if p.is_symlink() or sha(p.read_bytes())!=D3C_FREEZE_SHA256:
        raise Stop('D3d D3c freeze identity mismatch')
    parent = read(p)
    d3c_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n)!=h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files'])<=set(files) or not changed<=D3D_CHANGED or
        added!=D3D_ADDED|{'freeze-d3c.json'} or files.get('freeze-d3c.json')!=D3C_FREEZE_SHA256 or
        f.get('parent_freeze_sha256')!=D3C_FREEZE_SHA256 or f.get('deviation')!='D3d'):
        raise Stop('D3d parent binding or permitted scope mismatch')
    for n in D3D_CHANGED:
        if files.get('deviations/d3d/baseline/'+n)!=parent['files'][n]:
            raise Stop('D3d baseline differs from D3c: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3d/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D3d must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k)!=parent[k]:
            raise Stop('D3d changed scientific freeze metadata: '+k)
    if timestamp(f['created_at'])<timestamp(parent['created_at']):
        raise Stop('D3d predates D3c')


def freeze_d3d(root):
    from trl_test import tested_inputs
    from trl_d3c import stop_gate, prepush_gate
    root = Path(root)
    if (root/'freeze-d3d.json').exists():
        raise FileExistsError('freeze-d3d.json is create-once')
    stop_gate(root)
    prepush_gate(root,'D3d')
    test = read(root/'evidence/test-report-d3d.json')
    if (test.get('status')!='PASS' or test.get('failures')!=0 or test.get('errors')!=0 or
        not test.get('tests') or test.get('tested_files')!=tested_inputs(root)):
        raise Stop('passing D3d tests for current inputs required')
    parent = read(root/'freeze-d3c.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    for n in ('freeze.json','freeze-d1.json','freeze-d2.json','freeze-d3.json','freeze-d3b.json','freeze-d3c.json'):
        files[n] = sha((root/n).read_bytes())
    f = {**parent,'created_at':now(),'kind':'pre-analysis operational continuation amendment',
         'deviation':'D3d','parent_freeze_sha256':D3C_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D3d binds the D3c STOP clearance and forward-only D3c and D3d push attestations. Preserve all historical evidence; skip all attempted episodes.'}
    d3d_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d3d.json',f)
    return verify(root)


D3D_FREEZE_SHA256 = 'b2c23ed1a03d50d125a6b3b06b8ca23dbb15ded10c76d89ee4fe1fd4947a1289'
D4_CHANGED = {'DEVIATIONS.md','trl_freeze.py','trl_collect.py','trl_io.py','trl_d3b.py',
              'trl_analysis.py','tests/test_d3d.py','tests/test_d1.py','tests/test_d2.py'}
D4_ADDED = {'trl_d4.py','tests/test_d4.py','RUN-d4.md','PROJECT_STATE-d4.md',
            'deviations/d4/clearance.json','deviations/d4/preservation.json',
            'evidence/test-report-d4.json','evidence/rebuild-d4.json',
            'fixtures/d4/usage-limit.raw.json','fixtures/d4/real-claude-envelope.json'} | {
                'deviations/d4/baseline/'+n for n in D4_CHANGED}


def d4_scope(root,f):
    root = Path(root)
    p = root/'freeze-d3d.json'
    if p.is_symlink() or sha(p.read_bytes()) != D3D_FREEZE_SHA256:
        raise Stop('D4 D3d freeze identity mismatch')
    parent = read(p)
    d3d_scope(root,parent)
    files = f['files']
    changed = {n for n,h in parent['files'].items() if files.get(n) != h}
    added = set(files)-set(parent['files'])
    if (not set(parent['files']) <= set(files) or not changed <= D4_CHANGED or
        added != D4_ADDED|{'freeze-d3d.json'} or files.get('freeze-d3d.json') != D3D_FREEZE_SHA256 or
        f.get('parent_freeze_sha256') != D3D_FREEZE_SHA256 or f.get('deviation') != 'D4'):
        raise Stop('D4 parent binding or permitted scope mismatch')
    for n in D4_CHANGED:
        if files.get('deviations/d4/baseline/'+n) != parent['files'][n]:
            raise Stop('D4 baseline differs from D3d: '+n)
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d4/baseline/DEVIATIONS.md').read_bytes()):
        raise Stop('D4 must append to deviation history')
    mutable = {'files','content_sha256','created_at','kind','dispatch_note','deviation','parent_freeze_sha256'}
    for k in set(parent)-mutable:
        if f.get(k) != parent[k]:
            raise Stop('D4 changed scientific freeze metadata: '+k)
    if timestamp(f['created_at']) < timestamp(parent['created_at']):
        raise Stop('D4 predates D3d')


def freeze_d4(root):
    from trl_test import tested_inputs
    from trl_d4 import stop_gate,prepush_gate
    root = Path(root)
    if (root/'freeze-d4.json').exists():
        raise FileExistsError('freeze-d4.json is create-once')
    stop_gate(root)
    prepush_gate(root)
    test = read(root/'evidence/test-report-d4.json')
    if (test.get('status') != 'PASS' or test.get('failures') != 0 or test.get('errors') != 0 or
        not test.get('tests') or test.get('tested_files') != tested_inputs(root)):
        raise Stop('passing D4 tests for current inputs required')
    parent = read(root/'freeze-d3d.json')
    files = {n:sha((root/n).read_bytes()) for n in inputs(root)}
    for n in ('freeze.json','freeze-d1.json','freeze-d2.json','freeze-d3.json','freeze-d3b.json','freeze-d3c.json','freeze-d3d.json'):
        files[n] = sha((root/n).read_bytes())
    f = {**parent,'created_at':now(),'kind':'post-push harness-only usage-limit amendment',
         'deviation':'D4','parent_freeze_sha256':D3D_FREEZE_SHA256,'files':files,
         'content_sha256':sha(canonical(files).encode()),
         'dispatch_note':'D4 treats exact zero-usage subscription 429 refusals as definite non-starts; resume identical saved requests after reset, preserve all other frozen error handling. Fresh D4 push attestation required.'}
    d4_scope(root,f)
    verify_manifest(root,f)
    save(root/'freeze-d4.json',f)
    return verify(root)


def push_record(event, commit):
    """Same two GitHub server evidence forms accepted by Receipt Gap D1."""
    if type(event) is not dict or type(commit) is not str or not re.fullmatch('[0-9a-f]{40}',commit):
        raise Stop('invalid server record or full commit')
    if event.get('type')=='PushEvent':
        payload, repo = event.get('payload'),event.get('repo')
        if (type(payload) is not dict or type(repo) is not dict or
                repo.get('name')!='Robin84Bran/research' or payload.get('head',payload.get('after'))!=commit):
            raise Stop('server PushEvent repository/commit mismatch')
        ref, when = payload.get('ref'),event.get('created_at')
    elif event.get('activity_type')=='push':
        if event.get('after')!=commit:
            raise Stop('server activity commit mismatch')
        ref, when = event.get('ref'),event.get('timestamp')
    else:
        raise Stop('server PushEvent or push activity required')
    if type(ref) is not str or not re.fullmatch(r'refs/heads/[A-Za-z0-9_][A-Za-z0-9._/-]*',ref):
        raise Stop('server branch ref required')
    try:
        pushed = timestamp(when)
    except (ValueError,TypeError,AttributeError):
        raise Stop('invalid server timestamp') from None
    if pushed>=dt.datetime.now(dt.timezone.utc) or type(event.get('id')) not in (str,int) or not str(event['id']):
        raise Stop('invalid server timestamp or id')
    return ref,when


def attest(root,event_file,commit,repo_path,clone_root=None,freeze_file=None):
    root = Path(root)
    active_digest = verify(root)
    active = active_freeze(root)
    name = freeze_file or active
    if name!=active and not (active=='freeze-d3d.json' and name=='freeze-d3c.json'):
        raise Stop('only the D3c parent may be attested separately')
    digest = sha((root/name).read_bytes())
    raw_event = Path(event_file).read_bytes()
    event = strict_load(raw_event.decode())
    ref,when = push_record(event,commit)
    if not timestamp(read(root/name)['created_at'])<=timestamp(when):
        raise Stop('push must follow active freeze')
    if Path(repo_path).is_absolute() or '..' in Path(repo_path).parts or not repo_path or ':' in repo_path:
        raise Stop('invalid repository path')
    clone_root = Path(clone_root) if clone_root is not None else root
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=clone_root)
    if git('rev-parse','HEAD').decode().strip()!=commit:
        raise Stop('checkout differs from pushed commit')
    remote = git('remote','get-url','origin').decode().strip()
    if remote not in ('git@github.com:Robin84Bran/research.git','https://github.com/Robin84Bran/research.git',
                      'https://github.com/Robin84Bran/research','ssh://git@github.com/Robin84Bran/research.git'):
        raise Stop('unexpected origin')
    # Bind both freeze blobs and every active input in the committed package.
    committed = dict(read(root/name)['files'])
    committed['freeze.json'] = sha((root/'freeze.json').read_bytes())
    committed[name] = digest
    for name,expected in committed.items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=expected:
            raise Stop('pushed commit omits or changes frozen file: '+name)
    remotes = git('ls-remote','origin',ref).decode()
    if not any(line.split()==[commit,ref] for line in remotes.splitlines()):
        raise Stop('remote ref does not match server event')
    with lock(root/'collection/collector.lock'):
        if verify(root)!=active_digest or active_freeze(root)!=active:
            raise Stop('active package changed during attestation')
        d4 = name=='freeze-d4.json'
        d3c = name=='freeze-d3c.json'
        d3d = name=='freeze-d3d.json'
        d3b = name=='freeze-d3b.json'
        d3 = name=='freeze-d3.json'
        d2 = name=='freeze-d2.json'
        if d4:
            from trl_d4 import prepush_gate, provenance_layers
            from trl_collect import _push_layer
            prepush_gate(root)
            for layer in provenance_layers(root)[:-1]:
                _push_layer(root,*layer)
        elif d3c or d3d:
            from trl_d3c import prepush_gate, provenance_layers
            from trl_collect import _push_layer
            prepush_gate(root,name)
            layers = provenance_layers(root,active)
            index = next(i for i,layer in enumerate(layers) if layer[0]==name)
            for layer in layers[:index]:
                _push_layer(root,*layer)
        elif d3b:
            from trl_d3b import stop_gate, prepush_gate
            from trl_collect import push_gate
            stop_gate(root)
            prepush_gate(root)
            push_gate(root,historical=True)
        elif d3:
            from trl_d3 import stop_gate
            from trl_collect import push_gate
            c = stop_gate(root)
            push_gate(root,historical=True)
            if any(p.relative_to(root).as_posix() not in c['preserved_files'] for p in (root/'collection/episodes').glob('*/*.start.json')):
                raise Stop('D3 attestation must precede all D3 starts')
        elif d2:
            from trl_d2 import stop_gate
            from trl_collect import push_gate
            c = stop_gate(root)
            push_gate(root,historical=True)
            if any(p.relative_to(root).as_posix() not in c['preserved_files'] for p in (root/'collection/episodes').glob('*/*.start.json')):
                raise Stop('D2 attestation must precede all D2 starts')
        elif list((root/'collection/episodes').glob('*/*.start.json')):
            raise Stop('push attestation cannot be recorded after starts')
        suffix = '-d4' if d4 else '-d3d' if d3d else ('-d3c' if d3c else ('-d3b' if d3b else ('-d3' if d3 else ('-d2' if d2 else ''))))
        path = root/('collection/push-event'+suffix+'.raw.json')
        receipt = root/('collection/push'+suffix+'.json')
        if path.exists() or receipt.exists():
            raise FileExistsError('push evidence is create-once')
        with path.open('xb') as f:
            f.write(raw_event);f.flush();__import__('os').fsync(f.fileno())
        __import__('trl_io').syncdir(path.parent)
        save(receipt,{'freeze_sha256':digest,'freeze_file':name,'attested_at':now(),
            'original_freeze_sha256':sha((root/'freeze.json').read_bytes()),'commit':commit,'repo':'Robin84Bran/research',
            'pushed_at':when,'server_event_id':event['id'],'event_sha256':sha(raw_event),
            'source_api':'/repos/Robin84Bran/research/'+('events' if event.get('type')=='PushEvent' else 'activity'),
            'repo_path':repo_path,'remote_ref':ref,'origin':remote})
    return digest


def select_event(events_file,commit,out):
    events = read(events_file)
    if type(events) is not list:
        raise Stop('expected saved GitHub events array/pages')
    if events and type(events[0]) is list:
        events = [e for page in events for e in page]
    matches = []
    for e in events:
        try:
            push_record(e,commit)
        except Stop:
            continue
        matches.append(e)
    if not matches:
        raise Stop('no server event for exact pushed commit; retain response and wait for real evidence')
    save(out,max(matches,key=lambda e:timestamp(push_record(e,commit)[1])))
    return str(out)


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=['freeze','freeze-d1','freeze-d2','clear-d2','freeze-d3','clear-d3','freeze-d3b','freeze-d3c','freeze-d3d','freeze-d4','clear-d4','clear-d3c','clear-pause-d3b','verify','attest','select-event'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--event',type=Path);p.add_argument('--events',type=Path);p.add_argument('--out',type=Path);p.add_argument('--commit');p.add_argument('--repo-path',default='three-rules-one-lunch')
    p.add_argument('--clone-root',type=Path,help='separate research clone; Git checks only, no writes')
    p.add_argument('--stop-name',default='STOP-d3b.json')
    p.add_argument('--reviewer');p.add_argument('--reason')
    p.add_argument('--freeze-file',choices=['freeze-d3c.json','freeze-d3d.json','freeze-d4.json'])
    a = p.parse_args()
    if a.command=='select-event':
        if not a.events or not a.commit or not a.out:
            p.error('select-event requires --events, --commit, --out')
        print(select_event(a.events,a.commit,a.out))
    elif a.command=='attest':
        if not a.event or not a.commit or not a.clone_root:
            p.error('attest requires --event, --commit and --clone-root')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root,a.freeze_file))
    elif a.command=='clear-d4':
        if not a.reviewer or not a.reason:
            p.error('clear-d4 requires --reviewer and --reason')
        from trl_d4 import record_clearance
        with lock(a.root/'collection/collector.lock'):
            print(record_clearance(a.root,a.reviewer,a.reason)['disposition'])
    elif a.command=='clear-d3c':
        if not a.reviewer or not a.reason:
            p.error('clear-d3c requires --reviewer and --reason')
        from trl_d3c import record_clearance
        with lock(a.root/'collection/collector.lock'):
            print(record_clearance(a.root,a.reviewer,a.reason)['disposition'])
    elif a.command=='clear-pause-d3b':
        if not a.reviewer or not a.reason:
            p.error('clear-pause-d3b requires --reviewer and --reason')
        from trl_d3b import record_clearance
        with lock(a.root/'collection/collector.lock'):
            print(record_clearance(a.root,a.stop_name,a.reviewer,a.reason))
    elif a.command in ('clear-d2','clear-d3'):
        if a.command=='clear-d3':
            from trl_d3 import record_clearance
        else:
            from trl_d2 import record_clearance
        with lock(a.root/'collection/collector.lock'):
            c = record_clearance(a.root)
        print(c['disposition'])
    else:
        print({'freeze':freeze,'freeze-d1':freeze_d1,'freeze-d2':freeze_d2,'freeze-d3':freeze_d3,'freeze-d3b':freeze_d3b,'freeze-d3c':freeze_d3c,'freeze-d3d':freeze_d3d,'freeze-d4':freeze_d4,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
