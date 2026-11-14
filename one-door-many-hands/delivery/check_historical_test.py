"""Run the frozen pre-D3 recovery test against its exact saved baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    if out == root or root in out.parents:
        p.error('use a new directory outside the study')
    out.mkdir(parents=True, exist_ok=False)
    fixture = out/'pre-d3-baseline'
    f = json.loads((root/'freeze-d3.json').read_text())
    for name in list(f['files']) + [v.name for v in root.glob('freeze*.json')]:
        dest=fixture/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/name, dest)
    b=json.loads((root/'evidence/d3-baseline.json').read_text())
    for name, h in b['files'].items():
        data=(root/'collection'/name).read_bytes()
        if digest(data)!=h: raise RuntimeError('baseline mismatch: '+name)
        dest=fixture/'collection'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    for name, prefix in b['prefixes'].items():
        data=(root/'collection'/name).read_bytes()[:prefix['bytes']]
        if digest(data)!=prefix['sha256']: raise RuntimeError('baseline prefix mismatch: '+name)
        dest=fixture/'collection'/name
        dest.write_bytes(data)
        checkpoints=dest.with_suffix(dest.suffix+'.prefixes')
        checkpoints.mkdir()
        for i in range(1,len(data.splitlines())+1):
            namecp=f'{i:08d}.json'
            shutil.copy2(root/'collection'/(name+'.prefixes')/namecp, checkpoints/namecp)
    sys.path[:0]=[str(root),str(root/'tests')]
    from od_d3 import verify_d3, verify_baseline
    verify_d3(fixture)
    verify_baseline(fixture)
    import test_d3
    suite=unittest.TestSuite([test_d3.D3('test_real_clearance_attestation_and_prefixes')])
    with (out/'historical-test.txt').open('x') as stream, patch.object(test_d3, 'ROOT', fixture):
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    record={'test':'test_d3.D3.test_real_clearance_attestation_and_prefixes','fixture':'exact immutable D3 collection baseline plus saved ledger byte prefixes/checkpoints','frozen_source_or_test_changes':False,'baseline_verified':True,'tests_run':result.testsRun,'success':result.wasSuccessful(),'errors':len(result.errors),'failures':len(result.failures)}
    (out/'historical-test.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record,sort_keys=True))
    if not result.wasSuccessful():sys.exit(1)


if __name__=='__main__':
    main()
