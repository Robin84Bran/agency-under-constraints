"""Rebuild saved fake outputs from a verified archive without live providers."""
import argparse
from pathlib import Path
import tarfile
from od_core import ROOT,schedule
from od_io import Stop,save_bytes,save,read
from od_archive import verify_archive
from od_analysis import analysis


def rebuild(output,root=ROOT):
    output=Path(output);root=Path(root)
    if output.exists(): raise Stop('rebuild output exists')
    count=verify_archive(root/'offline/dry-run-r1.tar.gz')
    output.mkdir(parents=True)
    with tarfile.open(root/'offline/dry-run-r1.tar.gz','r:gz') as t:
        for member in t.getmembers(): save_bytes(output/'saved'/member.name,t.extractfile(member).read())
    saved=output/'saved';comparisons=[]
    for expected in sorted(saved.glob('*-analysis.json')):
        name=expected.name[:-len('-analysis.json')];data=saved/name
        observed={p.name for p in (data/'episodes').iterdir()}
        actors={e['actor'] for e in schedule() if e['id'] in observed}
        jobs=[e for e in schedule() if e['block']==0 and e['actor'] in actors]
        actual=analysis(root,data,output/expected.name,allow_fake=True,jobs=jobs)
        if actual!=read(expected): raise Stop('offline saved analysis differs: '+name)
        comparisons.append(name)
    failed_count=verify_archive(root/'offline/failed-first-dry-run.tar.gz')
    result={'kind':'FAKE_OFFLINE_REBUILD_NOT_EMPIRICAL_RESULTS','matched_saved_analyses':comparisons,'archive_files':count,'retained_failed_archive_files':failed_count}
    save(output/'rebuild.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(rebuild(a.output,a.root))
