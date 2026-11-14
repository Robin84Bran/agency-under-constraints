"""Offline fake-transports exercise and portable evidence archive. Never live."""
import argparse
from pathlib import Path
import tarfile
import tempfile
from od_core import ROOT,schedule,sha
from od_io import read,save,Stop
from od_collect import collect
from od_transport import Fake
from od_analysis import analysis


def dryrun(out,root=ROOT):
    out=Path(out)
    if out.exists(): raise Stop('offline output must be new')
    out.mkdir(parents=True)
    # One complete block (all twelve cells) for each identity.
    jobs=[e for e in schedule() if e['block']==0]
    for cohort in ('local','claude'): collect(root,cohort,fake_transport=Fake(),output=out/'success',jobs_override=jobs)
    result=analysis(root,out/'success',out/'success-analysis.json',allow_fake=True,jobs=jobs)
    fault_summary={}
    for actor,fault in [('qwen7b','length'),('qwen7b','done'),('qwen7b','usage'),('qwen7b','identity'),('qwen7b','input'),('claude','missing_payload'),('claude','invalid'),('claude','cost'),('claude','overrun'),('claude','timeout')]:
        eps=[e for e in jobs if e['actor']==actor]
        base=out/(actor+'-'+fault);fake=Fake(fault)
        try: collect(root,'claude' if actor=='claude' else 'local',fake_transport=fake,output=base,jobs_override=eps)
        except Stop: pass
        analysis(root,base,out/(actor+'-'+fault+'-analysis.json'),allow_fake=True,jobs=eps)
        fault_summary[actor+'/'+fault]={'calls':len(fake.calls),'durable_stop':(base/'STOP.json').exists()}
    summary={'kind':'FAKE_OFFLINE_NOT_STUDY_RESULTS','success_episodes':len(jobs),'model_calls':0,'successful_fake_calls':48,
       'faults':fault_summary,'success_ledger':result['ledger']}
    save(out/'summary.json',summary);return summary


from od_archive import archive,verify_archive

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(dryrun(a.output))
