#!/usr/bin/env python3
"""Portable Self: all live/network actions require explicit subcommands."""
import argparse
from pathlib import Path
from ps_core import ROOT, canonical

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','freeze','freeze-a1','verify','attest','collect','analyze','dry-run'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--clone-root',type=Path);p.add_argument('--repo-path',default='portable-self');p.add_argument('--commit')
    p.add_argument('--cohort',choices=['local','claude']);p.add_argument('--claude-bin');p.add_argument('--output',type=Path);p.add_argument('--data',type=Path);p.add_argument('--fake',action='store_true')
    a=p.parse_args()
    if a.command in ('prepare','freeze','freeze-a1','verify'):
        import ps_freeze
        result=getattr(ps_freeze,a.command.replace('-','_'))(a.root)
    elif a.command=='attest':
        if not a.clone_root or not a.commit: p.error('attest requires --clone-root and --commit')
        from ps_freeze import attest
        result=attest(a.root,a.clone_root,a.repo_path,a.commit)
    elif a.command=='collect':
        if not a.cohort: p.error('collect requires --cohort')
        from ps_collect import collect
        result=collect(a.root,a.cohort,a.claude_bin)
    elif a.command=='dry-run':
        if not a.output: p.error('dry-run requires a new --output outside collection')
        from ps_offline import dry_run
        result=dry_run(a.root,a.output)
    else:
        if not a.output: p.error('analyze requires a new --output file')
        from ps_freeze import verify, push_gate
        verify(a.root)
        base=a.data or a.root/'collection'
        if not a.fake: push_gate(a.root)
        from ps_analysis import analyze
        from ps_io import save
        result=analyze(a.root,base,a.fake);save(a.output,result)
        result={'output':str(a.output),'attempted_episodes':result['attempted_episodes'],'primary':result['primary'],'accounting':result['accounting']}
    print(canonical(result))

if __name__=='__main__': main()
