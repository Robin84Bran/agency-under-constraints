from pathlib import Path
import hashlib,json,shutil,subprocess,sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from trl_freeze import inputs,tested_inputs
from trl_io import save
before=tested_inputs(root)
out=root/'build/portable';source=out/'source';source.mkdir(parents=True,exist_ok=False)
files=inputs(root)
for n,h in files.items():
    p=source/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h,n
shutil.copytree(root/'build/offline-sealed/collection',source/'collection')
command=[sys.executable,'-B','-c','from pathlib import Path; from trl_analysis import analyze; analyze(Path.cwd(),Path("collection"),Path("analysis"),reuse_check=False)']
with (out/'process.log').open('x') as log:
    subprocess.run(command,cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
names=('episodes.json','summary.json','tables.csv','tables.md','frontier-seeds.csv','baselines.csv','headline.svg')
outputs={}
for n in names:
    a,b=(root/'build/offline-sealed/analysis'/n).read_bytes(),(source/'analysis'/n).read_bytes()
    assert a==b,n;outputs[n]=hashlib.sha256(a).hexdigest()
assert tested_inputs(root)==before
report={'status':'PASS','scope':'Fresh copied source/evidence tree, fresh interpreter; fake v0.2 locals with unchanged v0.1 Claude','source_files':files,'command':command,'byte_identical_outputs':outputs,'model_calls':0,'network_calls':0,'git_operations':0,'tested_files':before}
save(root/'evidence/portable-rebuild.json',report)
print('PASS: fresh source/process, seven byte-identical outputs')
