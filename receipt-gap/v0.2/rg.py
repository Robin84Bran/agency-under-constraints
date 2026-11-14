"""Explicit collection entrypoint; no default action or provider side effects."""
import argparse
from pathlib import Path
from rg_collect import collect, Stop
from rg_core import ROOT, canonical


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['collect'])
    p.add_argument('--cohort',choices=['local','claude'],required=True);p.add_argument('--claude-bin')
    p.add_argument('--freeze',choices=['freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json','freeze-r4.json','freeze-r5.json'],default='freeze.json')
    a=p.parse_args()
    try:
        print(canonical(collect(ROOT,a.cohort,a.claude_bin,freeze_file=a.freeze)))
    except (Stop,ValueError,KeyError) as exc:
        raise SystemExit('STOP: '+str(exc))

if __name__=='__main__':
    main()
