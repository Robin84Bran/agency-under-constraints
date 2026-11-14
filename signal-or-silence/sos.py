"""Signal or Silence: stdlib-only offline rebuild and gated collection."""
import argparse
import json
from pathlib import Path


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('import');sub.add_parser('sample');sub.add_parser('verify');sub.add_parser('freeze')
    sub.add_parser('freeze-d1')
    c=sub.add_parser('collect');c.add_argument('--models',nargs='+',choices=['qwen7b','llama8b','claude'])
    a=sub.add_parser('analyze');a.add_argument('--bootstrap-replicates',type=int,default=10000);a.add_argument('--output',type=Path)
    push=sub.add_parser('record-push');push.add_argument('--github-time',required=True);push.add_argument('--commit',required=True);push.add_argument('--remote',required=True);push.add_argument('--source',required=True)
    push.add_argument('--deviation',choices=['D1'])
    recovery=sub.add_parser('recover');recovery.add_argument('--reason',required=True)
    sub.add_parser('test')
    args=p.parse_args(argv);root=args.root.resolve()
    if args.command=='import':
        from sos_import import import_evidence
        out=import_evidence(root)
    elif args.command=='sample':
        from sos_design import build_design
        from sos_prepare import prepare_requests
        design=build_design(root);out={'primary':len(design['primary_ids']),'receipt':len(design['receipt_ids']),'requests':prepare_requests(root)}
    elif args.command in ('freeze','verify'):
        from sos_freeze import freeze,verify_freeze
        out=freeze(root) if args.command=='freeze' else verify_freeze(root)
        if args.command=='verify':out={k:v for k,v in out.items() if k not in ('files','_d1')};out['d1_verified']=(root/'freeze-d1.json').exists()
    elif args.command=='freeze-d1':
        from sos_d1 import create
        out=create(root)
    elif args.command=='record-push':
        from sos_freeze import record_push
        out=record_push(root,args.github_time,args.commit,args.remote,args.source,deviation=args.deviation)
    elif args.command=='recover':
        from sos_freeze import verify_freeze
        verify_freeze(root)
        from sos_collect import acknowledge_recovery
        out=acknowledge_recovery(root,args.reason)
    elif args.command=='collect':
        from sos_collect import run_collection
        out=run_collection(root,models=args.models)
    elif args.command=='analyze':
        from sos_freeze import verify_freeze
        verify_freeze(root)
        from sos_analysis import run_analysis
        out=run_analysis(root,bootstrap_replicates=args.bootstrap_replicates,output_root=(root/args.output) if args.output else None)
    else:
        import io
        import tempfile
        import unittest
        import datetime as dt
        scratch=root/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(scratch)
        stream=io.StringIO()
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(root/'tests')))
        print(stream.getvalue())
        out={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,
             'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
             'tested_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
        # Test runs after freeze never edit frozen evidence.
        path=root/'build'/('test_report.json' if not (root/'freeze.json').exists() else 'postfreeze_test_report.json')
        if path.exists():
            path=path.with_name(path.stem+'-'+dt.datetime.now(dt.timezone.utc).strftime('%H%M%S%f')+'.json')
        path.write_text(json.dumps(out,indent=2)+'\n')
        if not result.wasSuccessful(): return 1
    print(json.dumps(out,indent=2,default=str))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
