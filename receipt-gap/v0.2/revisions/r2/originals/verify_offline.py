"""Offline unit verification with network and model/Git process execution blocked."""
import argparse
import io
import os
from pathlib import Path
import sys
import unittest
from rg_core import ROOT, canonical


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    attempts={'network':0,'blocked_processes':0,'allowed_processes':[]}
    def guard(event,values):
        if event=='socket.connect':
            attempts['network']+=1
            raise RuntimeError('offline verification forbids network')
        if event=='subprocess.Popen':
            executable=os.path.basename(os.fsdecode(values[0]))
            if executable!='node':
                attempts['blocked_processes']+=1
                raise RuntimeError('offline verification forbids '+executable)
            attempts['allowed_processes'].append(executable)
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT/'tests'))
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    value={'tests_run':result.testsRun,'passed':result.wasSuccessful(),
           'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
           'real_model_calls':0,'actual_git_commands':0,**attempts,'test_output':stream.getvalue()}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:f.write(canonical(value)+'\n')
    print(canonical({k:v for k,v in value.items() if k!='test_output'}))
    if not result.wasSuccessful() or attempts['network'] or attempts['blocked_processes']:
        raise SystemExit(1)

if __name__=='__main__':main()
