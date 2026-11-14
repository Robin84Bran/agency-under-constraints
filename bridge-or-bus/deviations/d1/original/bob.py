#!/usr/bin/env python3
"""Bridge or Bus: explicit commands; no work occurs on import."""
import argparse
from pathlib import Path
import sys
import subprocess
import re
import unittest

from bob_core import ROOT,canonical,sha


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest='command',required=True)
    for name in ('prepare','test','dry-run','rebuild','freeze','verify','analyze'):
        s.add_parser(name)
    att=s.add_parser('record-push')
    att.add_argument('--remote',required=True)
    att.add_argument('--evidence',required=True,help='project-relative saved gh api --include commit response')
    col=s.add_parser('collect')
    col.add_argument('--models',choices=('local','qwen7b','llama8b','qwen1b','claude'),required=True)
    args=p.parse_args(argv)
    if args.command=='test':
        from bob_freeze import inventory
        from bob_offline import write
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        toy=subprocess.run(['node','--test','--test-reporter=tap',str(ROOT/'evidence/toy/tests.mjs')],capture_output=True)
        (ROOT/'build').mkdir(exist_ok=True)
        (ROOT/'build/toy-test-output.txt').write_bytes(toy.stdout+toy.stderr)
        match=re.search(rb'^# tests (\d+)$',toy.stdout,re.M)
        toy_count=int(match[1]) if match is not None else 0
        passed=result.wasSuccessful() and toy.returncode==0 and toy_count>0
        report=dict(status='PASS' if passed else 'FAIL',tests=result.testsRun+toy_count,python_tests=result.testsRun,toy_tests=toy_count,failures=len(result.failures),errors=len(result.errors),source_sha256=sha(canonical(inventory(ROOT)).encode()))
        write(ROOT/'build/test-report.json',report)
        print(canonical(report))
        return 0 if passed else 1
    if args.command in ('prepare','dry-run','rebuild'):
        from bob_offline import prepare,dry_run,rebuild
        output=prepare(ROOT) if args.command=='prepare' else dry_run(ROOT/'build/dry-run.json') if args.command=='dry-run' else rebuild(ROOT)
        if args.command=='dry-run':
            output={k:v for k,v in output.items() if k!='results'}
    elif args.command in ('freeze','verify','record-push'):
        from bob_freeze import create,verify,record_push,github_evidence
        if args.command=='freeze':
            output=create(ROOT)
        elif args.command=='verify':
            record=verify(ROOT)
            output=dict(status=record['status'],freeze_sha256=sha((ROOT/'freeze.json').read_bytes()),files=len(record['files']))
        else:
            output=record_push(ROOT,**github_evidence(ROOT,args.remote,args.evidence))
    elif args.command=='collect':
        from bob_collect import collect
        models=('qwen7b','llama8b','qwen1b') if args.models=='local' else (args.models,)
        output=collect(ROOT,models)
    else:
        from bob_analysis import load_collection
        from bob_collect import read,save
        from bob_freeze import verify
        verify(ROOT)
        output=load_collection(ROOT,read(ROOT/'config/order.json'))
        save(ROOT/'collection/analysis.json',output)
        output=dict(status='ANALYZED',path='collection/analysis.json',primary=output['cohorts']['qwen7b']['joint_status'])
    print(canonical(output))
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr)
        sys.exit(1)
