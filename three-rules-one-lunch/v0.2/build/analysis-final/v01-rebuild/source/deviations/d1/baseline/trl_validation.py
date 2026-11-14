"""Provider-independent strict envelope validation; no network or subprocess imports."""
import base64
from trl_core import PINS, strict_load, action
from trl_io import Stop
MODEL = 'claude-opus-5-5'

def stdout(raw):
    return base64.b64decode(raw['stdout_b64'],validate=True).decode('utf8',errors='strict')


def usage(envelope,actor):
    if type(envelope) is not dict:
        return None
    if actor != 'claude':
        vals = [envelope.get('prompt_eval_count'),envelope.get('eval_count')]
        return {'input':vals[0],'output':vals[1],'cache_read':0,'cache_creation':0,'reasoning':None} if all(type(v) is int and v>=0 for v in vals) else None
    u = envelope.get('usage')
    if type(u) is not dict:
        return None
    vals = [u.get(k) for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens')]
    if not all(type(v) is int and v>=0 for v in vals):
        return None
    return {'input':vals[0],'cache_read':vals[1],'cache_creation':vals[2],'output':vals[3],
            'reasoning':None, 'reasoning_note':'Provider aggregate output includes charged reasoning; no second charge.'}


def cost(u):
    # Cache creation charged at 4/20 planning basis ONLY while dispatch is blocked.
    # Live price verification must account for creation premiums in reviewed amendment.
    return 4*(u['input']+u['cache_read']+u['cache_creation'])+20*u['output']


def validate(raw,actor,quota,bound):
    if type(raw) is not dict or type(raw.get('returncode')) is not int or raw.get('returncode')!=0 or raw.get('transport_error'):
        raise Stop('transport failed/uncertain start; no resend')
    e = strict_load(stdout(raw))
    u = usage(e,actor)
    if u is None:
        raise Stop('usage UNKNOWN')
    if actor == 'claude':
        if e.get('type')!='result' or e.get('subtype')!='success' or e.get('is_error') is not False or type(e.get('num_turns')) is not int or e['num_turns']!=1:
            raise Stop('unsuccessful/unexpected result envelope')
        if e.get('stop_reason') not in ('end_turn','tool_use'):
            raise Stop('truncated or unknown frontier stop reason')
        if type(e.get('modelUsage')) is not dict or set(e['modelUsage'])!={MODEL}:
            raise Stop('frontier identity UNKNOWN/mismatch')
        mu = e['modelUsage'][MODEL]
        if type(mu) is not dict:
            raise Stop('modelUsage object required')
        expected = {'inputTokens':u['input'],'outputTokens':u['output'],
                    'cacheReadInputTokens':u['cache_read'],'cacheCreationInputTokens':u['cache_creation']}
        if any(type(mu.get(k)) is not int or mu[k]!=v for k,v in expected.items()):
            raise Stop('model/aggregate usage disagreement')
        if e.get('effort','medium')!='medium':
            raise Stop('conflicting returned effort')
        if e.get('permission_denials')!=[] or e.get('deferred_tool_use') or e.get('subagent_stats') or e.get('tool_uses') or e.get('tool_calls'):
            raise Stop('unexpected real tool/subagent activity')
        st = e.get('usage',{}).get('server_tool_use')
        if type(st) is not dict or not {'web_search_requests','web_fetch_requests'}.issubset(st) or any(type(v) is not int or v!=0 for v in st.values()) or mu.get('webSearchRequests')!=0:
            raise Stop('server tool activity UNKNOWN/nonzero')
        if any(e.get(k) for k in ('errors','safety_stops')):
            raise Stop('frontier errors/safety stops')
        if sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>1024 or cost(u)>bound['micro_usd']:
            raise Stop('frontier reservation/output overrun')
        v = e.get('structured_output')
        if type(v) is not dict:
            raise Stop('structured_output object required; result is never parsed')
    else:
        if e.get('model')!=PINS[actor][0] or e.get('done') is not True or e.get('done_reason')!='stop':
            raise Stop('local identity/truncation/stop mismatch')
        if u['output']>=192 or u['input']+192>=8192:
            raise Stop('local output/context truncation')
        running_record = raw.get('running')
        if type(running_record) is not dict or type(running_record.get('models')) is not list:
            raise Stop('running model evidence UNKNOWN')
        running = running_record['models']
        if not any(type(m) is dict and m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] and m.get('context_length')==8192 for m in running):
            raise Stop('effective local identity/context mismatch')
        v = strict_load(e.get('response'))
    return action(v,quota),e,u

