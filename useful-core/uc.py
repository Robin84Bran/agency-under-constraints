"""Explicit production command; importing it has no effects."""
import argparse
from uc_core import ROOT,canonical


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['collect']);p.add_argument('--cohort',choices=['local','claude'],required=True);p.add_argument('--claude-bin')
    a=p.parse_args()
    from uc_collect import collect
    print(canonical(collect(ROOT,a.cohort,a.claude_bin)))

if __name__=='__main__':
    main()
