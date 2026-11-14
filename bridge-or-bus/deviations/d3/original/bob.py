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
    for name in ('prepare','test','dry-run','rebuild','freeze','freeze-d1','freeze-d2','reconcile-d2','verify','analyze'):
        s.add_parser(name)
    d1=s.add_parser('attest')
    d1.add_argument('--event',required=True,help='raw GitHub /activity push or /events PushEvent JSON record')
    d1.add_argument('--commit',required=True)
    d1.add_argument('--clone-root',required=True,type=Path)
    d1.add_argument('--repo-path',required=True,help='project path inside the research repository')
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
        suffix='-d2' if (ROOT/'deviations/d2').exists() else ''
        (ROOT/f'build/toy-test-output{suffix}.txt').write_bytes(toy.stdout+toy.stderr)
        match=re.search(rb'^# tests (\d+)$',toy.stdout,re.M)
        toy_count=int(match[1]) if match is not None else 0
        passed=result.wasSuccessful() and toy.returncode==0 and toy_count>0
        report=dict(status='PASS' if passed else 'FAIL',tests=result.testsRun+toy_count,python_tests=result.testsRun,toy_tests=toy_count,failures=len(result.failures),errors=len(result.errors),source_sha256=sha(canonical(inventory(ROOT)).encode()))
        write(ROOT/f'build/test-report{suffix}.json',report)
        print(canonical(report))
        return 0 if passed else 1
    if args.command in ('prepare','dry-run','rebuild'):
        from bob_offline import prepare,dry_run,rebuild
        output=prepare(ROOT) if args.command=='prepare' else dry_run(ROOT/'build/dry-run.json') if args.command=='dry-run' else rebuild(ROOT)
        if args.command=='dry-run':
            output={k:v for k,v in output.items() if k!='results'}
    elif args.command in ('freeze-d2','reconcile-d2'):
        from bob_d2 import freeze_d2,reconcile_d2
        output=freeze_d2(ROOT) if args.command=='freeze-d2' else reconcile_d2(ROOT)
    elif args.command in ('freeze','freeze-d1','verify','record-push','attest'):
        from bob_freeze import create,freeze_d1,verify,record_push,github_evidence,attest,active_freeze
        if args.command=='freeze':
            output=create(ROOT)
        elif args.command=='freeze-d1':
            output=freeze_d1(ROOT)
        elif args.command=='attest':
            output=attest(ROOT,args.event,args.commit,args.clone_root,args.repo_path)
        elif args.command=='verify':
            record=verify(ROOT)
            output=dict(status=record['status'],freeze_file=active_freeze(ROOT),freeze_sha256=sha((ROOT/active_freeze(ROOT)).read_bytes()),files=len(record['files']))
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
