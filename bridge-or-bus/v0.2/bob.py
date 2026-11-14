#!/usr/bin/env python3
"""v0.2 entry point. Default commands operate offline; collection is explicit."""
import argparse
import io
from pathlib import Path
import unittest

from bob_core import ROOT,canonical,sha
from bob_collect import read,Stop


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    for name in ('test','dry-run','verify','freeze','freeze-r1','freeze-r2','freeze-r3','rebuild','analyze'):s.add_parser(name)
    freezes=('freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json')
    c=s.add_parser('collect');c.add_argument('--freeze',choices=freezes);c.add_argument('--models',nargs='+',required=True)
    a=s.add_parser('attest');a.add_argument('--freeze',choices=freezes);a.add_argument('--event',required=True);a.add_argument('--commit',required=True);a.add_argument('--clone-root',required=True);a.add_argument('--repo-path',default='bridge-or-bus/v0.2')
    args=p.parse_args()
    from bob_freeze import inventory,verify,create,create_revision,create_r2,freeze_path
    from bob_offline import dry_run,rebuild,write
    if args.cmd=='test':
        before=sha(canonical(inventory(ROOT)).encode())
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        folder=ROOT/'build';folder.mkdir(exist_ok=True)
        (folder/'test-output.txt').write_text(stream.getvalue())
        after=sha(canonical(inventory(ROOT)).encode())
        status='PASS' if result.wasSuccessful() and before==after else 'FAIL'
        out=dict(status=status,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),source_sha256=after,model_calls=0)
        write(folder/'test-report.json',out)
        if status!='PASS':print(stream.getvalue());raise SystemExit(1)
    elif args.cmd=='dry-run':out=dry_run(ROOT/'build/dry-run.json')
    elif args.cmd=='rebuild':out=rebuild(ROOT)
    elif args.cmd=='verify':
        out=verify(ROOT);out=dict(status='PASS',freeze_sha256=sha(freeze_path(ROOT).read_bytes()),tests=out['tests'])
    elif args.cmd=='freeze':out=create(ROOT)
    elif args.cmd=='freeze-r1':out=create_revision(ROOT)
    elif args.cmd=='freeze-r2':out=create_r2(ROOT)
    elif args.cmd=='freeze-r3':
        from bob_revision_r3 import create_r3
        out=create_r3(ROOT)
    elif args.cmd=='attest':
        from bob_freeze import attest
        out=attest(ROOT,args.event,args.commit,args.clone_root,args.repo_path,args.freeze)
    elif args.cmd=='collect':
        from bob_collect import collect
        out=collect(ROOT,args.models,args.freeze)
    elif args.cmd=='analyze':
        verify(ROOT)
        from bob_analysis import load_collection
        result=load_collection(ROOT,read(ROOT/'config/order.json'))
        v01=read(ROOT/'evidence/v01-replay.json')
        result['version']='0.2';result['v01_beside_v02']=dict(terminal=v01['terminal'],cells=v01['cells'],falsely_rejected_legal_actions=0,reason='v0.1 technical gate failed; zero correct submissions. v0.2 cannot erase that result.')
        write(ROOT/'build/results.json',result)
        out=dict(status='PASS',output='build/results.json',study_acceptance_status='UNKNOWN')
    if args.cmd=='dry-run':out={k:v for k,v in out.items() if k!='results'}
    print(canonical(out))

if __name__=='__main__':main()
