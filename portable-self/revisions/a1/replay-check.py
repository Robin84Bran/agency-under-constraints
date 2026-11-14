"""Rebuild historical fake evidence without Git, providers or network access."""
import argparse
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from ps_core import ROOT, canonical, sha
from ps_io import read, save
from ps_analysis import analyze


def replay():
    with patch('socket.socket',side_effect=AssertionError('network forbidden')), patch('urllib.request.urlopen',side_effect=AssertionError('HTTP forbidden')), patch('subprocess.Popen',side_effect=AssertionError('subprocess forbidden')):
        report=analyze(ROOT,ROOT/'offline/dry-run-v2',True)
    actual=(canonical(report)+'\n').encode();expected=(ROOT/'offline/analysis-fixture.json').read_bytes()
    if actual!=expected: raise AssertionError('A1 historical fake replay differs')
    return {'kind':'A1 historical OFFLINE-FAKE replay; no Git','same_analysis_bytes':True,
            'analysis_sha256':sha(actual),'original_rebuild_sha256':read(ROOT/'offline/rebuild-verification.json')['analysis_sha256'],
            'attempted_fake_episodes':report['attempted_episodes'],'planned_episodes':len(report['episodes']),
            'network_http_subprocess_blocked':True,'model_calls':0,'git_operations':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=replay();save(a.output,result);print(canonical(result))
