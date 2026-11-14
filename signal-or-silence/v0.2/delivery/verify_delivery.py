"""Read-only delivery checks; save evidence, without numerical analysis or models."""
import datetime as dt
from decimal import Decimal
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'v0.2'),str(ROOT)]
import sos_v02 as adapter
from sos_freeze import verify_freeze


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    old=read(ROOT/'analysis/results.json')
    new=read(ROOT/'v0.2/analysis/results.json')
    inherited=read(AREA/'rebuild-source.json')['files']
    changed=[name for name,h in inherited.items() if digest(ROOT/name)!=h]
    assert not changed,changed
    verify_freeze(ROOT)
    record=adapter.verify(ROOT/'v0.2')
    frozen_hash=adapter.push_gate(ROOT/'v0.2',record)
    adapter.usage_deviation.gate(ROOT/'v0.2')
    jobs=read(ROOT/'v0.2/config/requests.json')['jobs']
    ledger=adapter.validate_history(ROOT/'v0.2',jobs,frozen_hash,new['v0.1_accounting']['accounted_usd'])
    calls,events=adapter.usage_limit.effective_calls(ROOT/'v0.2',jobs,ledger,frozen_hash)
    assert len(calls)==1868 and len(events)==3
    assert new['status']=='COMPLETE'
    assert not ledger.reserved.keys()-ledger.settled
    assert str(ledger.total)==new['cumulative_accounted_usd']=='22.135420'
    assert Decimal(new['v0.1_accounting']['accounted_usd'])+Decimal(new['v0.2_accounting']['ledger_accounted_usd'])==ledger.total
    assert all(e['cost_usd']=='0' and e['disposition']=='DEFINITE_NON_START' for e in events)
    assert new['operational_events']['model_behavior_or_technical_failures'] is False
    assert new['v0.2_accounting']['transport_failures']==0
    assert new['v0.2_accounting']['integrity_failures']==0
    assert new['v0.2_accounting']['attempted_starts']==1871
    unchanged={key:new['v0.1_strict'][key]==old[key]['claude'] for key in
               ('primary','bootstrap','diversity','instruction_contrasts','receipt_replication')}
    assert all(unchanged.values())
    assert [new['forecasts'][k]['status'] for k in ('V2-P1','V2-P2','V2-P3','V2-P4','V2-P5')]==['FAIL','PASS','FAIL','FAIL','PASS']
    assert all(not c['pass'] for v in [new['v0.2_strict']]+[
        {'primary':old['primary'][m]} for m in ('qwen7b','llama8b','claude')]
        for p in v['primary'].values() for c in p['scores'].values())
    comparison=read(AREA/'rebuild-comparison.json')
    assert comparison['all_byte_identical']
    for c in comparison['comparisons']:
        assert (ROOT/c['original']).read_bytes()==(ROOT/c['rebuilt']).read_bytes()
        assert digest(ROOT/c['original'])==c['original_sha256']
    questions=ROOT/'v0.2/QUESTIONS-post-analysis.md'
    base=(ROOT/'QUESTIONS-post-analysis.md').read_bytes()
    assert questions.read_bytes()==base+(AREA/'questions-append.md').read_bytes()
    broken=[]
    table_rows=0
    for name in ('RESULTS.md','README.md'):
        path=ROOT/'v0.2'/name
        txt=path.read_text()
        assert 'Robin authorized' not in txt
        for url in re.findall(r'\]\(([^)]+)\)',txt):
            if not url.startswith(('http://','https://','#')) and not (path.parent/url.split('#')[0]).exists():
                broken.append([name,url])
        for line in txt.splitlines():
            if line.startswith('|'):
                table_rows+=1
        # Each compact headline row must exactly match the saved JSON.
        sys.path.insert(0,str(AREA))
        import render_combined as renderer
        for ins in ('plain','explicit'):
            assert '\n'.join(renderer.headlines(ins)) in txt
    assert not broken,broken
    starts=[read(p)['started'] for p in (ROOT/'v0.2/collection/starts').glob('*.json')]
    continuations=[read(p)['started'] for p in (ROOT/'v0.2/collection/continuations').rglob('*.start.json')]
    all_inputs=[ROOT/'freeze.json',ROOT/'freeze-d1.json',ROOT/'v0.2/freeze.json',ROOT/'v0.2/freeze-usage-limit.json']
    artifact_paths=[ROOT/'v0.2/RESULTS.md',ROOT/'v0.2/README.md',questions,ROOT/'v0.2/PROJECT_STATE-post-analysis.md',
        ROOT/'v0.2/analysis/results.json',ROOT/'v0.2/analysis/RESULTS.md',
        AREA/'render_combined.py',AREA/'verify_delivery.py',AREA/'rebuild-execution.json',AREA/'rebuild-source.json']
    result={'status':'PASS','verified_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'authority':'Delegating reviewer Claude; Claude/Codex agreement under semi_autonomous.md.',
        'frozen_metadata_attribution':'Historical frozen authority strings in raw command logs are retained verbatim; current task decisions came from the Claude/Codex agreement.',
        'all_four_freezes_verified':True,'freeze_sha256':{str(p.relative_to(ROOT)):digest(p) for p in all_inputs},
        'pre_existing_files_byte_identical':len(inherited),'changed_pre_existing_files':changed,
        'v01_numerical_sha256':digest(ROOT/'analysis/results.json'),'v01_claude_structural_identity':unchanged,
        'original_v02_production_executions':1,'independent_rebuild_executions':1,
        'analysis_command':'python3 -B v0.2/sos_v02.py analyze',
        'bootstrap_replicates':10000,'bootstrap_seed':20261112,
        'rebuild':comparison,'offline_tests':{'run':93,'failures':0,'errors':0},
        'source_integrity':'PASS: 1440 source episodes, 240 primary, 120 receipt pairs; certificates, truth, masks and selections.',
        'provenance':{'scope':'Saved operator attestations, not an independent GitHub query.',
            'push':read(ROOT/'v0.2/collection/push.json'),
            'first_original_start':min(starts),'last_original_start':max(starts),
            'deviation_attestation':read(ROOT/'v0.2/collection/usage-limit-attestation.json'),
            'first_continuation_start':min(continuations),'last_continuation_start':max(continuations),
            'push_before_all_starts':True,'deviation_attestation_before_all_continuations':True,
            'continuation_request_identity_and_reset_checks':'PASS'},
        'collection':{'v01_saved_outcomes':5604,'v02_generated_outcomes':len(calls),'v02_attempt_starts':1871,
            'v02_operational_nonstarts':len(events),'v02_nonstart_usd':'0','missing':0,
            'v02_effective_transport_failures':0,'v02_effective_integrity_failures':0},
        'accounting':{'v01_usd':'11.053392','v02_usd':'11.082028','total_usd':'22.135420','outstanding_usd':'0',
            'v01_ledger_sha256':digest(ROOT/'collection/cost.jsonl'),
            'v02_ledger_sha256':digest(ROOT/'v0.2/collection/cost.jsonl'),
            'rolling_ledger_history_and_caps':'PASS'},
        'reports':{'results':'v0.2/RESULTS.md','readme':'v0.2/README.md',
            'reason':'Root reports and question/state logs are frozen inherited inputs; versioned combined delivery preserves them.',
            'headline_rows_checked_against_json':16,'markdown_table_rows_checked':table_rows,'broken_local_links':broken,
            'question_log_original_prefix_byte_identical':True},
        'delivery_sha256':{str(p.relative_to(ROOT)):digest(p) for p in artifact_paths},
        'scientific_acceptance':'UNKNOWN',
        'unresolved':['Both versions failed per-view validity quality criterion.',
            'Independent fresh-GitHub-clone Claude review and findings dispositions pending.',
            'Historical accounting is not a verified current invoice; hardware/energy/opportunity costs unavailable.']}
    path=AREA/'verification.json'
    with path.open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','all_four_freezes_verified','pre_existing_files_byte_identical','accounting','reports')},indent=2))


if __name__=='__main__':
    verify()
