"""Run the offline suite and save immutable machine-readable verification evidence."""
import argparse
from pathlib import Path
import time
import unittest
from trl_core import ROOT, sha
from trl_io import now, save, Stop


def tested_inputs(root):
    root = Path(root)
    paths = list(root.glob('*.py'))+list((root/'tests').glob('*.py'))
    for folder in ('config','fixtures'):
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file())
    paths.append(root/'evidence/toy-model.mjs')
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(paths)}


def main():
    p = argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    before = tested_inputs(ROOT)
    began = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if tested_inputs(ROOT)!=before:
        raise Stop('tested inputs changed during suite')
    report = {'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'tested_at':now(),'elapsed_seconds':time.monotonic()-began,'tested_files':before,
        'model_calls':0,'network_calls':0}
    save(a.out,report)
    if not result.wasSuccessful():
        raise SystemExit(1)

if __name__=='__main__':
    main()
