"""Entry point. Live collect is explicit and guarded by attestation."""
import argparse
from pathlib import Path
from od_core import ROOT
from od_contract import CLAUDE_BIN

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    c=s.add_parser('collect');c.add_argument('--cohort',choices=['local','claude'],required=True);c.add_argument('--claude-bin',default=CLAUDE_BIN);c.add_argument('--root',type=Path,default=ROOT)
    a=p.parse_args()
    from od_collect import collect
    print(collect(a.root,a.cohort,a.claude_bin))
if __name__=='__main__': main()
