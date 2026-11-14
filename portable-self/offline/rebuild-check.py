#!/usr/bin/env python3
"""Fresh local Git clone replay; network/providers forbidden; no remote or push."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists(): raise SystemExit('output exists; choose a new evidence path')
env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
with tempfile.TemporaryDirectory(prefix='portable-self-offline-rebuild-') as tmp:
    snapshot=Path(tmp)/'snapshot';clone=Path(tmp)/'fresh-clone'
    shutil.copytree(ROOT,snapshot,ignore=shutil.ignore_patterns('.git','__pycache__','collection'))
    def run(args,cwd): return subprocess.check_output(args,cwd=cwd,env=env,stderr=subprocess.PIPE)
    run(['git','init','--quiet'],snapshot)
    run(['git','add','.'],snapshot)
    run(['git','-c','user.name=Offline fixture','-c','user.email=offline-fixture@invalid','-c','commit.gpgsign=false','-c','core.hooksPath=/dev/null','commit','--quiet','-m','Portable Self offline fixture snapshot; no model calls'],snapshot)
    commit=run(['git','rev-parse','HEAD'],snapshot).decode().strip()
    run(['git','clone','--quiet','--no-hardlinks',str(snapshot),str(clone)],Path(tmp))
    # Both source and clone replay run with sockets, HTTP and subprocesses forbidden.
    code='''import json,socket,subprocess,urllib.request
from pathlib import Path
from unittest.mock import patch
from ps_core import canonical
from ps_analysis import analyze
with patch('socket.socket',side_effect=AssertionError('network forbidden')), patch('urllib.request.urlopen',side_effect=AssertionError('HTTP forbidden')), patch('subprocess.Popen',side_effect=AssertionError('subprocess forbidden')):
 if Path('freeze.json').exists():
  from ps_freeze import verify
  verify(Path('.'))
 report=analyze(Path('.'),Path('offline/dry-run-v2'),True)
 print(canonical(report))
'''
    source=run([sys.executable,'-B','-c',code],ROOT)
    rebuilt=run([sys.executable,'-B','-c',code],clone)
    if source!=rebuilt: raise SystemExit('fresh clone analysis differs')
    report=json.loads(rebuilt)
    result={'kind':'OFFLINE-FAKE fresh local Git clone rebuild','same_analysis_bytes':True,'network_disabled_during_analysis':True,
            'fresh_clone_commit':commit,'analysis_sha256':hashlib.sha256(rebuilt).hexdigest(),'attempted_fake_episodes':report['attempted_episodes'],
            'planned_episodes':len(report['episodes']),'primary_status':report['primary']['status'],'real_model_calls':0,
            'remote_operations':0,'note':'Synthetic fake transports only; genuine pushed research clone and empirical independent review remain later work.'}
    with a.output.open('x') as f: json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(result,sort_keys=True))
