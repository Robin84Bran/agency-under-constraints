"""D5: generated Claude replies terminate episodes, not cohorts. Offline clearance."""
from pathlib import Path
from trl_core import sha, strict_load, canonical, action
from trl_io import Stop, read, save, now, timestamp
from trl_validation import MODEL, stdout, usage, cost, positive_count
from trl_d3 import LEDGERS, verify_prefix

CLEARANCE = 'deviations/d5/clearance.json'
DISPOSITION = 'deviations/d5/episode.json'
EPISODE = 'claude-s007-central'
STOP_NAME = 'STOP-d3b-003.json'


class ModelReplyFailure(ValueError):
    """Known generated reply; charge it, end the episode, never resend it."""


def validate(raw, actor, quota, bound, expected_input_tokens=None):
    if actor != 'claude':
        from trl_validation import validate as local_validate
        return local_validate(raw,actor,quota,bound,expected_input_tokens)
    try:
        e = strict_load(stdout(raw))
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        raise Stop('transport failed/uncertain start; no parseable envelope; no resend') from exc
    if type(e) is not dict:
        raise Stop('transport failed/uncertain start; no result object; no resend')
    u = usage(e,'claude')
    if u is None:
        raise Stop('usage UNKNOWN')
    # A parseable failure is not made uncertain by the CLI exit status. Actual
    # identity/tool/accounting violations remain integrity failures in any reply.
    mu = e.get('modelUsage')
    if mu is not None and mu != {}:
        if type(mu) is not dict or set(mu) != {MODEL}:
            raise Stop('frontier identity mismatch')
        m = mu[MODEL]
        expected = {'inputTokens':u['input'],'outputTokens':u['output'],
            'cacheReadInputTokens':u['cache_read'],'cacheCreationInputTokens':u['cache_creation']}
        if type(m) is not dict or any(type(m.get(k)) is not int or m[k] != v for k,v in expected.items()):
            raise Stop('model/aggregate usage disagreement')
        if m.get('canonicalModel',MODEL) != MODEL:
            raise Stop('frontier canonical identity mismatch')
        if m.get('webSearchRequests',0) != 0:
            raise Stop('unexpected server tool activity')
    if e.get('effort','medium') != 'medium':
        raise Stop('conflicting returned effort')
    if (e.get('permission_denials',[]) or e.get('deferred_tool_use') or
        positive_count(e.get('subagent_stats')) or e.get('tool_uses') or e.get('tool_calls') or
        positive_count(e.get('usage',{}).get('server_tool_use'))):
        raise Stop('unexpected real tool/subagent activity')
    if (sum(u[k] for k in ('input','cache_read','cache_creation')) > bound['input_tokens'] or
        u['output'] > 1024 or cost(u) > bound['micro_usd']):
        raise Stop('frontier reservation/output overrun')
    if (e.get('type') != 'result' or e.get('subtype') != 'success' or
        e.get('is_error') is not False or e.get('stop_reason') not in ('end_turn','tool_use') or
        e.get('errors') or e.get('safety_stops') or raw.get('returncode') != 0 or
        raw.get('transport_error')):
        raise ModelReplyFailure('MODEL-CAUSED: generated Claude error/refusal/truncation')
    # Two turns are normal for the CLI's structured-output tool. No assumption
    # that num_turns == real tool use, or that stop_reason must be end_turn.
    if type(e.get('num_turns')) is not int or e['num_turns'] not in (1,2):
        raise ModelReplyFailure('MODEL-CAUSED: unexpected result turns')
    if type(e.get('structured_output')) is not dict:
        raise ModelReplyFailure('MODEL-CAUSED: structured_output missing/invalid; result is never parsed')
    try:
        value = action(e['structured_output'],quota)
    except (ValueError,KeyError,TypeError) as exc:
        raise ModelReplyFailure('MODEL-CAUSED: schema-invalid structured_output: '+str(exc)) from exc
    if not mu:
        raise Stop('frontier success identity UNKNOWN')
    st = e.get('usage',{}).get('server_tool_use')
    if type(st) is not dict or not {'web_search_requests','web_fetch_requests'} <= set(st) or any(type(v) is not int or v != 0 for v in st.values()):
        raise Stop('server tool activity UNKNOWN/nonzero')
    return value,e,u


def clearance(root):
    from trl_d4 import clearance as parent_clearance
    root = Path(root)
    c = read(root/CLEARANCE)
    parent = parent_clearance(root)
    if (c.get('deviation') != 'D5' or c.get('episode_id') != EPISODE or
        c.get('disposition') != 'MODEL_CAUSED_NO_RERUN_CONTINUE_COHORT' or
        c.get('stop_name') != STOP_NAME or not c.get('reviewer') or not c.get('reason') or
        c.get('parent_clearance_sha256') != sha((root/'deviations/d4/clearance.json').read_bytes()) or
        c.get('disposition_sha256') != sha((root/DISPOSITION).read_bytes()) or
        c.get('cleared_episodes') != parent['cleared_episodes']+[EPISODE] or
        timestamp(c['recorded_at']) < timestamp(read(root/'collection'/STOP_NAME)['time'])):
        raise Stop('invalid D5 clearance')
    if set(c['ledger_prefixes']) != set(c['preserved_files']) & LEDGERS:
        raise Stop('D5 ledger prefix inventory mismatch')
    for n,h in c['preserved_files'].items():
        p = root/n
        if n in LEDGERS:
            verify_prefix(root,n,c['ledger_prefixes'][n],h)
        elif p.is_symlink() or sha(p.read_bytes()) != h:
            raise Stop('D5 preserved evidence changed: '+n)
    return c


def record_clearance(root,reviewer,reason):
    """Create a separate effective terminal; never rewrite saved collection bytes."""
    from trl_d4 import clearance as parent_clearance, inventory, terminal_path as parent_terminal
    from trl_d3b import stop_paths
    from trl_budget import Ledger
    from trl_analysis import replay
    root = Path(root)
    if (root/CLEARANCE).exists() or (root/DISPOSITION).exists():
        raise FileExistsError('D5 clearance and disposition are create-once')
    if not reviewer.strip() or not reason.strip():
        raise Stop('named reviewer and reason required')
    parent = parent_clearance(root)
    d = root/'collection/episodes'/EPISODE
    t = read(d/'episode.json')
    raw,parsed,req,start = [read(d/('r4-j0.'+n+'.json')) for n in ('raw','parsed','request','start')]
    e = strict_load(stdout(raw));u = usage(e,'claude')
    try:
        validate(raw,'claude',3,req['reservation'])
    except ModelReplyFailure:
        pass
    else:
        raise Stop('D5 saved reply is not a model failure')
    ledger = Ledger(root/'collection/cost.jsonl')
    row = replay(t['episode'],d)
    if (ledger.stopped or any(ledger.holds.values()) or u is None or
        ledger.settled.get(start['id'],{}).get('actual') != cost(u) or
        t.get('fatal') is not True or t.get('complete') is not False or
        t.get('error') != 'transport failed/uncertain start; no resend' or
        parsed.get('error') != t['error'] or parsed.get('raw_envelope') != e or
        parsed.get('usage') != u or parsed.get('value') is not None or
        req['id'] != start['id'] or parsed['id'] != start['id'] or
        row['calls'] != 4 or row['coverage'] != .75 or row['complete'] or
        e.get('stop_reason') != 'max_tokens' or u['output'] != 1024 or
        read(root/'collection'/STOP_NAME).get('reason') != t['error'] or
        timestamp(read(root/'collection'/STOP_NAME)['time']) < timestamp(t['finished_at'])):
        raise Stop('D5 known harness stop does not match saved evidence/settlement')
    for p in stop_paths(root):
        if p.name == STOP_NAME or is_parent_cleared(root,p):
            continue
        raise Stop('D5 cannot clear unrelated integrity STOP')
    known_stops = {'STOP.json','STOP-d2.json'}|{p.name for p in stop_paths(root)}
    if {p.name for p in (root/'collection').glob('STOP*.json')} != known_stops:
        raise Stop('D5 unknown STOP inventory')
    for directory in (root/'collection/episodes').iterdir():
        terminal = parent_terminal(directory)
        if not terminal.exists() or (read(terminal).get('fatal') and directory.name not in parent['cleared_episodes']+[EPISODE]):
            raise Stop('D5 cannot clear unrelated partial/fatal episode')
    files = inventory(root)
    effective = {**t,'fatal':False,'error':'MODEL-CAUSED: generated Claude error/refusal/truncation',
        'deviation':'D5','classification':'MODEL-CAUSED','redisposition_of':sha((d/'episode.json').read_bytes()),
        'no_rerun':True}
    effective['events'] = [{**event,'reason':effective['error'] if event['reason'] == t['error'] else event['reason']} for event in t['events']]
    save(root/DISPOSITION,effective)
    c = {'deviation':'D5','recorded_at':now(),'reviewer':reviewer,'reason':reason,
        'episode_id':EPISODE,'stop_name':STOP_NAME,'disposition':'MODEL_CAUSED_NO_RERUN_CONTINUE_COHORT',
        'cleared_episodes':parent['cleared_episodes']+[EPISODE],
        'parent_clearance_sha256':sha((root/'deviations/d4/clearance.json').read_bytes()),
        'disposition_sha256':sha((root/DISPOSITION).read_bytes()),'settled_micro_usd':cost(u),
        'raw_sha256':sha((d/'r4-j0.raw.json').read_bytes()),'preserved_files':files,
        'ledger_prefixes':{n:{'bytes':(root/n).stat().st_size,'sha256':h} for n,h in files.items() if n in LEDGERS}}
    save(root/CLEARANCE,c)
    return clearance(root)


def is_parent_cleared(root,p):
    from trl_d4 import is_cleared_stop as d4_cleared
    from trl_d3c import is_cleared_stop as d3c_cleared
    from trl_d3b import _pause_record
    if d4_cleared(root,p) or d3c_cleared(root,p):
        return True
    # A prior D3b pause still needs its ordinary validated clearance.
    cp = Path(root)/'collection/d3b-clearances'/p.name
    if cp.exists():
        s,c = _pause_record(root,p),read(cp)
        return (c.get('disposition') == 'RESUME_UNATTEMPTED_ONLY' and c.get('stop_sha256') == sha(p.read_bytes()) and c.get('freeze_sha256') == s['freeze_sha256'])
    return False


def is_cleared_stop(root,p):
    if p.name != STOP_NAME or not (Path(root)/CLEARANCE).exists():
        return False
    c = clearance(root)
    return c['preserved_files'].get('collection/'+p.name) == sha(p.read_bytes())


def terminal_path(directory):
    from trl_d4 import terminal_path as parent_terminal
    directory = Path(directory)
    root = directory.parent.parent.parent
    if directory.name == EPISODE and (root/CLEARANCE).exists():
        clearance(root)
        return root/DISPOSITION
    return parent_terminal(directory)


def stop_gate(root):
    from trl_d4 import stop_gate as parent_gate
    c = clearance(root)
    parent_gate(root)
    return c


def admission(root):
    # Preserve D4's orphan-overlay, pause/reset and stop checks in full.
    from trl_d4 import admission as parent_admission
    c = clearance(root)
    _,resumable = parent_admission(root)
    return c,resumable


def provenance_layers(root,active='freeze-d5.json'):
    from trl_d4 import provenance_layers as parent_layers
    c = clearance(root)
    layers = parent_layers(root)
    old = set(c['preserved_files'])
    layers[-1] = (*layers[-1][:2],layers[-1][2] & old)
    starts = {p.relative_to(root).as_posix() for folder in ('episodes','d4-episodes') for p in (Path(root)/'collection'/folder).rglob('*.start.json')}
    layers.append(('freeze-d5.json','-d5',starts-old))
    return layers


def prepush_gate(root):
    c = stop_gate(root)
    if provenance_layers(root)[-1][2]:
        raise Stop('D5 attestation must precede all D5 starts')
    return c


def episode(*args,**kwargs):
    from trl_d4 import episode as parent_episode
    return parent_episode(*args,**kwargs,programme=True)
