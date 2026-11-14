"""Offline test entrypoint; fail on actual network, Git or model subprocesses."""
from pathlib import Path
import sys,unittest,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True

def deny(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn'):
        raise RuntimeError('offline verification prohibits '+event)
sys.addaudithook(deny)
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'success':result.wasSuccessful(),'real_model_calls':0,'network_and_subprocess_guard':True}))
raise SystemExit(0 if result.wasSuccessful() else 1)
