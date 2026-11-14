#!/usr/bin/env python3
"""Create and audit an independent publication-filtered COPY, never collect."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ignored(path):
    p=Path(path)
    return any(x in ('__pycache__','.git') for x in p.parts) or p.name=='.DS_Store' or p.name.endswith('.lock')


def inventory(root):
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*')) if p.is_file() and not ignored(p.relative_to(root))}


def save(name,value):
    with (OUT/name).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n')


def main():
    from ps_freeze import verify,push_gate
    from ps_core import sha
    active=verify(ROOT)
    assert push_gate(ROOT)==active
    freezes={n:{'sha256':digest(ROOT/n),'files':len(json.loads((ROOT/n).read_text())['files'])} for n in ['freeze.json','freeze-usage-limit.json','freeze-claude-envelope.json']}
    save('freeze-verification.json',{'active_sha256':active,'freezes':freezes,'predecessor_source_reconstruction':'verified by frozen verifier',
        'all_saved_push_receipts_and_start_generations':'verified by frozen push_gate',
        'frozen_analysis_sha256':digest(ROOT/'ps_analysis.py'),'analysis_output_sha256':digest(ROOT/'collection/analysis-claude-envelope.json'),
        'source_analysis_invocations_in_this_delivery':1,'collection_invocations_in_this_delivery':0,
        'offline_tests':{'tests':139,'passed':138,'failures':1,'errors':0,'log':'collection/post-analysis-offline-check.log'},
        'historical_v01_raw_archive':'separate parent package; immutable v01 inventory and hashes bundled',
        'authority':'Claude delegated analysis and delivery under the Claude/Codex agreement; no new model calls or publication',
        'claim_context':'Delegating reviewer holds the project claim. Its recorded collection task and a malformed sibling Codex claim are left untouched; this task follows the explicit delegated v0.2 scope. Shared claim metadata is outside this session write boundary.'})
    source_before=inventory(ROOT)
    holder=Path(tempfile.mkdtemp(prefix='portable-self-v02-independent-',dir='/private/tmp'))
    clone=holder/'v0.2'
    def ignore(directory,names):
        return [n for n in names if ignored(Path(n))]
    shutil.copytree(ROOT,clone,ignore=ignore)
    copy_before=inventory(clone)
    assert copy_before==source_before,'copy bytes differ'
    excluded=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and ignored(p.relative_to(ROOT))]
    assert not any(ignored(p.relative_to(clone)) for p in clone.rglob('*'))
    commands=[]
    def run(args,success=True):
        p=subprocess.run([sys.executable,'-B',str(clone/'collection/delivery/reproduce.py'),*args],cwd=clone,capture_output=True,text=True)
        commands.append({'arguments':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert (p.returncode==0)==success,p.stdout+p.stderr
        return p
    run(['--fresh-clone'])
    mutation_checks=[]
    target=clone/'config/prompts.json';old=target.read_bytes()
    target.write_bytes(old+b' ')
    run(['--fresh-clone'],False);target.write_bytes(old)
    mutation_checks.append('changed substantive frozen bytes rejected')
    held=holder/'held-prompts.json';target.rename(held)
    run(['--fresh-clone'],False);held.rename(target)
    mutation_checks.append('missing substantive frozen file rejected')
    extra=clone/'unexpected-substantive-file.txt';extra.write_text('inventory rejection probe\n')
    run(['--fresh-clone'],False);extra.unlink()
    mutation_checks.append('extra substantive frozen-root input rejected')
    assert inventory(clone)==copy_before,'tamper probes were not fully restored'
    rebuilt=holder/'analysis-rebuilt.json'
    p=run(['--fresh-clone','--output',str(rebuilt)])
    comparison=json.loads(p.stdout)
    assert rebuilt.read_bytes()==(ROOT/'collection/analysis-claude-envelope.json').read_bytes()
    assert inventory(ROOT)==source_before,'source substantive bytes changed during rebuild'
    assert inventory(clone)==copy_before,'independent replay mutated clone inputs'
    # Exact export checks, including missing numeric fields remaining blank.
    x=json.loads((ROOT/'collection/analysis-claude-envelope.json').read_text())
    counts={}
    for name,expected in [('episodes.csv',1080),('facts.csv',17280),('calls.csv',6411),('notes.csv',sum(len(r['notes']) for r in x['episodes'])),('baseline-seeds.csv',1440)]:
        with (OUT/name).open() as f: rows=list(csv.DictReader(f))
        assert len(rows)==expected,(name,len(rows),expected)
        counts[name]=len(rows)
    ET.parse(OUT/'headline.svg')
    save('rebuild-commands.json',commands)
    save('rebuild-report.json',{'copy_root':str(clone),'rebuilt_output':str(rebuilt),'copy_is_independent':True,
        'exclusions_only':['__pycache__','.DS_Store','.git','*.lock'],'removed_files':excluded,
        'copied_files':len(copy_before),'copy_inventory_byte_identical':True,
        'analysis_byte_identical':comparison['byte_identical'],'analysis_sha256':comparison['analysis_sha256'],
        'analysis_bytes':comparison['bytes'],'frozen_analysis_rebuilds_in_copy':1,'source_analysis_invocations':1,
        'network_and_subprocess_guard':comparison['network_and_subprocess_guard'],
        'tamper_checks':mutation_checks,'source_inputs_unchanged':True,'copy_inputs_unchanged':True,
        'flat_export_rows':counts,'standalone_svg_parses':True,
        'frozen_offline_suite':'138/139 passed; historical STOP fixture assertion failed; original log retained',
        'commands_log':'rebuild-commands.json'})
    # Include the final verification receipts in the retained copy too.
    for name in ['rebuild-commands.json','rebuild-report.json']:
        shutil.copyfile(OUT/name,clone/'collection/delivery'/name)
    print(json.dumps({'copy':str(clone),'analysis_byte_identical':True,'sha256':comparison['analysis_sha256'],'exports':counts}))


if __name__=='__main__':
    main()
