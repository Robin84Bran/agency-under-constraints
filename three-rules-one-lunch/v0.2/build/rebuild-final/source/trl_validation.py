"""Provider-independent strict envelope validation; no network or subprocess imports."""
import base64
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from trl_core import PINS, strict_load, action
from trl_io import Stop
MODEL = 'claude-opus-5-5'


class LocalTransportFailure(ValueError):
    """An attempted local episode ends; no action, retry or invented usage."""
    pass

def stdout(raw):
    return base64.b64decode(raw['stdout_b64'],validate=True).decode('utf8',errors='strict')


def positive_count(value):
    """CLI statistics can be present at zero; only positive numeric leaves count."""
    if type(value) is dict:
        return any(positive_count(v) for v in value.values())
    if type(value) is list:
        return any(positive_count(v) for v in value)
    return type(value) in (int, float) and value > 0


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
    value = {'input':vals[0],'cache_read':vals[1],'cache_creation':vals[2],'output':vals[3],
             'reasoning':None, 'reasoning_note':'Provider aggregate output includes charged reasoning; no second charge.'}
    # As in Receipt Gap: settle the greater of planning accounting and the
    # CLI-reported API-equivalent amount; this can include cache premiums.
    if 'total_cost_usd' in envelope:
        try:
            reported = Decimal(str(envelope['total_cost_usd']))
            if not reported.is_finite() or reported<0:
                return None
            value['reported_cost_micro_usd'] = int((reported*1000000).to_integral_value(rounding=ROUND_CEILING))
        except (InvalidOperation,ValueError,TypeError,OverflowError):
            return None
    return value


def cost(u):
    # Historical API-equivalent accounting; current rates/cash billing UNKNOWN.
    planned = 4*(u['input']+u['cache_read']+u['cache_creation'])+20*u['output']
    return max(planned,u.get('reported_cost_micro_usd',0))


def validate(raw,actor,quota,bound,expected_input_tokens=None):
    if type(raw) is not dict or type(raw.get('returncode')) is not int or raw.get('returncode')!=0 or raw.get('transport_error'):
        failure = Stop if actor=='claude' else LocalTransportFailure
        raise failure('transport failed/uncertain start; no resend')
    try:
        e = strict_load(stdout(raw))
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        if actor=='claude':
            raise
        raise LocalTransportFailure('local unreadable envelope; no resend') from exc
    if actor!='claude':
        if type(e) is not dict:
            raise LocalTransportFailure('local envelope object missing; no resend')
        if e.get('model')!=PINS[actor][0]:
            raise Stop('local identity/truncation/stop mismatch')
        running_record = raw.get('running')
        if type(running_record) is not dict or type(running_record.get('models')) is not list:
            raise Stop('running model evidence UNKNOWN')
        if not any(type(m) is dict and m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] and m.get('context_length')==8192 for m in running_record['models']):
            raise Stop('effective local identity/context mismatch')
        # Known resource/input violations remain fatal even in an incomplete reply.
        tin,tout = e.get('prompt_eval_count'),e.get('eval_count')
        if (type(tout) is int and tout>192) or (type(tin) is int and tin+192>=8192):
            raise Stop('local output overrun/context truncation')
        if expected_input_tokens is not None:
            if type(expected_input_tokens) is not int or expected_input_tokens<1 or (type(tin) is int and tin<expected_input_tokens):
                raise Stop('local input truncation/expected count mismatch')
        if e.get('done') is not True or usage(e,actor) is None:
            raise LocalTransportFailure('local incomplete envelope/usage UNKNOWN; no resend')
    u = usage(e,actor)
    if u is None:
        raise Stop('usage UNKNOWN')
    if actor == 'claude':
        if e.get('type')!='result' or e.get('subtype')!='success' or e.get('is_error') is not False or type(e.get('num_turns')) is not int or e['num_turns'] not in (1,2):
            raise Stop('unsuccessful/unexpected result envelope')
        if (e.get('stop_reason') not in ('end_turn','tool_use') or
            (e['num_turns']==2 and e.get('stop_reason')!='tool_use')):
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
        if e.get('permission_denials')!=[] or e.get('deferred_tool_use') or positive_count(e.get('subagent_stats')) or e.get('tool_uses') or e.get('tool_calls'):
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
        if e.get('model')!=PINS[actor][0] or e.get('done') is not True or e.get('done_reason') not in ('stop','length'):
            raise Stop('local identity/truncation/stop mismatch')
        if e.get('done_reason')=='length' or u['output']==192:
            raise ValueError('local output-length limit; schema-invalid reply')
        v = strict_load(e.get('response'))
    return action(v,quota),e,u

