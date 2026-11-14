"""Create-once synthetic run and full analysis; never contacts providers."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True

def deny(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn'):
        raise RuntimeError('offline verification prohibits '+event)
sys.addaudithook(deny)
from ps_offline import dry_run
from ps_analysis import analyze
from ps_io import save
from ps_core import sha,canonical
out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'offline/dry-run'
report=dry_run(ROOT,out)
result=analyze(ROOT,out,True)
save(out/'analysis.json',result)
summary={k:report[k] for k in ('kind','real_model_calls','fake_episodes','fake_calls','all_schema_valid','accounting')}
summary.update(analysis_sha256=sha((out/'analysis.json').read_bytes()),primary=result['primary'],predictions=result['predictions'],network_and_subprocess_guard=True)
save(out/'summary.json',summary)
print(canonical(summary))
