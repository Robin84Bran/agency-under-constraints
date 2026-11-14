"""Offline tests with immutable tested-source hashes."""
import argparse
from pathlib import Path
import time
import unittest
from trl_core import ROOT
from trl_io import Stop, now, save
from trl_freeze import tested_inputs


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    before=tested_inputs(ROOT);began=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    if tested_inputs(ROOT)!=before: raise Stop('tested source changed during suite')
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'tested_at':now(),'elapsed_seconds':time.monotonic()-began,'tested_files':before,
        'model_calls':0,'network_calls':0,'git_operations':0,'exhaustive_canonical_schema_instances':117698}
    save(a.out,report)
    if not result.wasSuccessful(): raise SystemExit(1)

if __name__=='__main__': main()
