"""Rebuild the A1 audit to new output files; never overwrite retained evidence."""
import argparse
import json
from pathlib import Path
from deviations.a1.audit import scan

# Original source coordinates are immutable in the retained parent-bound archive.
FIXED={
 'uc_collect.py:38:handler':'Unexpected adapter exceptions are harness failures, not ordinary local transport.',
 'uc_collect.py:53:raise':'Split strict structured_output payload validation from metadata decoding; payload duplicates/nonfinite values retain usage and end only the episode.',
 'uc_collect.py:66:raise':'Known paid execution/transport uncertainty is immediately fatal; only ordinary local transport is episode-local.',
 'uc_collect.py:72:handler':'Narrow episode handling to typed content/transport failures; implementation TypeError/KeyError/ValueError is fatal.',
 'uc_collect.py:81:fatal-flag':'Remove first-call blanket escalation of model content/length failures.',
 'uc_collect.py:118:raise':'Resume may retain a first content-failed contract after strict independent revalidation.',
 'uc_collect.py:126:raise':'Revalidate a retained first model failure as well as strict successes; changed evidence remains fatal.',
 'uc_collect.py:175:streak':'Count typed transport failures only, across local actors and resumes; success/content breaks streak.',
 'uc_collect.py:177:durable-stop':'Pause only after three consecutive transport-failed episodes, with terminal hashes and journal prefixes.',
 'uc_collect.py:178:raise':'A content streak cannot trigger a cohort pause; reconstruct the transport pause after a crash.',
 'uc_transport.py:197:raise':'Check known envelope/turn integrity before classifying a model output-length stop.',
 'uc_transport.py:202:raise':'Completed structured-output generation exhaustion is content failure with verified identity, turns and known accounting.',
 'uc_transport.py:205:raise':'Missing/nonobject/string structured_output is model-content failure; never recover result prose.',
 'uc_transport.py:211:raise':'Incomplete local response is transport-local only after known identity/context/truncation gates.',
 'uc_transport.py:213:raise':'Missing local input count is incomplete transport; known context/token overruns remain fatal.',
 'uc_analysis.py:192:classification':'Match paid transport uncertainty fatal precedence and local-only transport scope.',
 'uc_analysis.py:201:classification':'Match envelope/turn integrity precedence over length classification.',
 'uc_analysis.py:205:classification':'Distinguish accounted structured-output generation exhaustion from broken envelopes.',
 'uc_analysis.py:207:classification':'Missing/nonobject structured_output is content, not fatal.',
 'uc_analysis.py:210:classification':'Known local integrity gates precede incomplete-transport classification.',
 'uc_analysis.py:212:classification':'Missing local input count is transport; measured context/output overruns are fatal.',
 'uc_analysis.py:258:handler':'Decode strict metadata independently of invalid designated structured_output values, preserving known settlement.',
 'uc_analysis.py:283:raise':'Remove first-call blanket fatal expectation; check the independent content/transport/fatal class.',
 'uc_analysis.py:420:raise':'Retained first content failure has MODEL_FAILURE status; strict_valid remains false.',
 'uc_analysis.py:421:raise':'Permit continuation after first content failure; continued fatal first call still rejects the evidence.',
}


def classify(row,original,root):
    file,fn,expr,guard=row['file'],row['function'],row['expression'],row['guard'] or ''
    if original and row['site'] in FIXED:
        dispositions={
          'uc_collect.py:38:handler':'Fatal harness',
          'uc_collect.py:53:raise':'Content / Fatal metadata',
          'uc_collect.py:66:raise':'Local transport / Fatal paid',
          'uc_collect.py:72:handler':'Content / Fatal harness',
          'uc_collect.py:81:fatal-flag':'Episode content',
          'uc_collect.py:118:raise':'Fatal tamper; retain content failure',
          'uc_collect.py:126:raise':'Fatal tamper; retain content failure',
          'uc_collect.py:175:streak':'Transport pause',
          'uc_collect.py:177:durable-stop':'Transport pause',
          'uc_collect.py:178:raise':'Transport pause',
          'uc_transport.py:197:raise':'Content / Fatal integrity first',
          'uc_transport.py:202:raise':'Content exhausted / Fatal contract',
          'uc_transport.py:205:raise':'Episode content',
          'uc_transport.py:211:raise':'Transport / Fatal integrity first',
          'uc_transport.py:213:raise':'Transport missing / Fatal overrun',
          'uc_analysis.py:192:classification':'Local transport / Fatal paid',
          'uc_analysis.py:201:classification':'Content / Fatal integrity first',
          'uc_analysis.py:205:classification':'Content exhausted / Fatal contract',
          'uc_analysis.py:207:classification':'Episode content',
          'uc_analysis.py:210:classification':'Transport / Fatal integrity first',
          'uc_analysis.py:212:classification':'Transport missing / Fatal overrun',
          'uc_analysis.py:258:handler':'Content / Fatal metadata',
          'uc_analysis.py:283:raise':'Fatal mismatched evidence',
          'uc_analysis.py:420:raise':'Fatal mismatched evidence',
          'uc_analysis.py:421:raise':'Fatal continued fatal; permit content',
        }
        return dispositions[row['site']],FIXED[row['site']]
    if row['kind']=='streak':return 'Transport pause','Only typed transport episodes count; never content failures.'
    if row['kind']=='classification':
        if 'transport' in expr and 'fatal' in expr:return 'Transport / Fatal','Local empty or explicitly failed transport is episode-local; unreadable metadata without transport evidence is fatal.'
        if "'fatal'" in expr:return 'Fatal','Independent retained-evidence/identity/envelope/accounting check; see guard.'
        if "'transport'" in expr:return 'Episode transport','No action/report effect; contributes once to durable three-episode pause.'
        if "'episode'" in expr and ('returncode' in guard or 'done' in guard):return 'Episode transport','Original local transport route, subject to the corrected precedence sites.'
        return 'Episode content','Frozen technical failure; preserve prior effects and continue cohort.'
    if file=='uc_core.py' and (fn.startswith('strict_load') or fn.startswith('transport_load')):
        return 'Context','Model JSON payload: episode content. Provider metadata/configuration/evidence: fatal. transport_load isolates only the designated structured_output value.'
    if file=='uc_core.py' and fn in ('action','report'):
        return 'Episode content','Exact schema/types/conditional fields; no effect or report after invalid action.'
    if row['kind']=='handler':
        if file=='uc_collect.py' and fn=='run_episode':
            if 'TransportFailure' in expr:return 'Episode transport','Known ordinary local transport; no resend; pause streak.'
            if 'EpisodeFailure' in expr:return 'Episode content','Only typed model/length failures are caught here.'
            if 'ValueError, UnicodeError' in expr:return 'Context','Explicitly failed local transport with partial bytes: transport-local; other unreadable envelopes: fatal.'
            return 'Fatal','Stop or unexpected implementation/adapter exception; retain evidence and holds.'
        if file=='uc_collect.py' and expr=='except EpisodeFailure':return 'Transport pause','Propagate durable pause without inventing a global integrity failure.'
        if file=='uc_collect.py' and fn=='check_frontier_contract':return 'Episode content','Revalidate the retained first model failure; metadata or evidence conflicts still stop.'
        if file=='uc_transport.py' and fn=='Local.generate':
            if row['guard']:return 'Fatal','Metadata failure remains observable; running identity/context validation stops dispatch.'
            if 'running=' in expr:return 'Fatal','Running metadata cannot be verified.'
            # The second handler checks /api/ps; identify it by order in the source.
            source=(Path(root)/(('deviations/a1/original/' if original else '')+file)).read_text().splitlines()
            around='\n'.join(source[max(0,row['line']-5):row['line']])
            if "'/api/ps'" in around:return 'Fatal','Running identity/context metadata failure is retained and rejected by decode.'
            return 'Episode transport','Ordinary local request failure; preserve any partial bytes.'
        if file=='uc_transport.py' and fn=='Claude.generate':return 'Fatal','Ambiguous paid start/timeout retains uncertain usage and holds.'
        if file=='uc_core.py' and fn=='transport_load':return 'Episode content','Only designated payload conversion is caught; metadata stays strict.'
        if file=='uc_analysis.py' and fn=='classify_reply':return 'Episode content','Strict model payload rejection independently reconstructed.'
        if file=='uc_analysis.py' and fn=='audit_episode':return 'Context','Undecodable envelope remains unknown; independent classifier decides fatal versus ordinary local transport.'
        return 'Fatal','Invalid configuration, evidence, accounting or resource state; no dispatch.'
    if 'TransportFailure' in expr:return 'Episode transport','No action or further report; no retry/replacement; contributes to pause.'
    if 'ModelOutputError' in expr:return 'Episode content','Model payload/generation failure after all applicable integrity/accounting gates.'
    if 'EpisodeFailure' in expr:
        if 'paused' in expr:return 'Transport pause','Durable pause after three consecutive transport failures; never clear/delete automatically.'
        if 'transport' in expr:return 'Episode transport','Ordinary local transport failure; prior effects retained.'
        return 'Episode content','Output-length technical failure, preserving prior effects and accounting.'
    if row['kind']=='durable-stop' and 'cohort' in expr:return 'Transport pause','Durable cohort pause; no override or clearance mechanism is introduced.'
    if expr=='raise' and file=='uc_collect.py' and fn=='collect' and guard is None:
        return 'Context','Reraise typed pause as pause; all unexpected/integrity exceptions durably stop dispatch.'
    return 'Fatal','Harness, retained-evidence, identity/digest, provenance, accounting or resource integrity guard; see expression/condition.'


def build(root):
    output={}
    for label,original in (('original',True),('final',False)):
        rows=scan(root,original)
        for row in rows:
            row['classification'],row['reason']=classify(row,original,root)
            row['disposition']='fixed' if original and row['site'] in FIXED else ('already right' if original else 'A1 final')
        output[label]=rows
    assert set(FIXED)<=set(r['site'] for r in output['original'])
    output['counts']=dict(original_sites=len(output['original']),fixed=len(FIXED),
        already_right=len(output['original'])-len(FIXED),final_sites=len(output['final']))
    return output


def tables(result):
    text=[]
    for label,title in (('original','Original freeze: every audited site'),('final','A1: every final audited site')):
        text.extend(['\n## '+title,'','| Site / function | Guard and expression | Class | Disposition / reason |',
                     '|---|---|---|---|'])
        for r in result[label]:
            clean=lambda s:s.replace('|','&#124;').replace('\n',' ')
            expression=(('if '+r['guard']+' → ') if r['guard'] else '')+r['expression']
            text.append('| `'+r['site']+'` '+r['function']+' | '+clean(expression)+' | '+r['classification']+' | '+r['disposition']+': '+clean(r['reason'])+' |')
    return '\n'.join(text)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--output-prefix',type=Path,required=True);a=p.parse_args()
    result=build(a.root)
    with Path(str(a.output_prefix)+'.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    with Path(str(a.output_prefix)+'.md').open('x') as f:f.write(tables(result))
    print(json.dumps(result['counts'],sort_keys=True))


if __name__=='__main__':main()
