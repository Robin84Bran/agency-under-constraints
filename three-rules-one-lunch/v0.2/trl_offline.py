"""Complete fake-only v0.2 study and portable replay. No live transport instances."""
import argparse
from pathlib import Path
import shutil
import tempfile
from trl_core import ROOT, sha
from trl_io import lock, read, save
from trl_budget import ActiveTime
from trl_journal import Journal, prefix
from trl_collect import episode
from trl_transport import Fake
from trl_analysis import analyze
from trl_reuse import rebuild


def dry_run(root,out):
    root,out=Path(root),Path(out);out.mkdir(parents=True,exist_ok=False)
    from trl_freeze import tested_inputs
    before=tested_inputs(root)
    base=out/'collection';timer=ActiveTime(base/'time-local.jsonl',43200);actor=Fake()
    with lock(base/'collector.lock'):
        journal=Journal(base/'dispatch.jsonl');timer.begin('offline')
        journal.event(event='checkpoint',id='offline-begin',ledger='collection/time-local.jsonl',prefix=prefix(base/'time-local.jsonl'))
        try:
            for ep in read(root/'config/episodes.json'):
                episode(ep,actor,base,journal,timer,'FAKE-NO-PUSH-NO-MODEL','offline')
        finally:
            timer.end()
            journal.event(event='checkpoint',id='offline-end',ledger='collection/time-local.jsonl',prefix=prefix(base/'time-local.jsonl'))
    summary=analyze(root,base,out/'analysis')
    assert summary['kind']=='FAKE' and len(read(out/'analysis/episodes.json'))==960
    assert len(actor.calls)==8400
    # Analyze a separate copied evidence tree in a fresh path; exact same outputs.
    with tempfile.TemporaryDirectory(prefix='trl-v02-replay-') as temporary:
        copy=Path(temporary)/'collection';shutil.copytree(base,copy)
        second=analyze(root,copy,Path(temporary)/'analysis',reuse_check=False)
        assert summary==second
        names=('episodes.json','summary.json','tables.csv','tables.md','frontier-seeds.csv','baselines.csv','headline.svg')
        for n in names: assert (out/'analysis'/n).read_bytes()==(Path(temporary)/'analysis'/n).read_bytes(),n
    result={'status':'PASS','kind':'FAKE_LOCAL_WITH_REUSED_V01_CLAUDE','local_episodes':900,
        'local_fake_calls':8400,'reused_v01_claude_episodes':60,'model_calls':0,'network_calls':0,
        'full_raw_v01_rebuild':read(out/'analysis/v01-rebuild/verification.json'),
        'byte_identical_copied_replay':[n for n in names],
        'analysis_outputs':{n:sha((out/'analysis'/n).read_bytes()) for n in names}}
    if tested_inputs(root)!=before: raise RuntimeError('offline-tested source changed during dry run')
    result['tested_files']=before
    save(out/'run.json',result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['dry-run','reuse-rebuild'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--legacy-tests',action='store_true');a=p.parse_args()
    print(dry_run(a.root,a.out) if a.command=='dry-run' else rebuild(a.root,a.out,a.legacy_tests))

if __name__=='__main__': main()
