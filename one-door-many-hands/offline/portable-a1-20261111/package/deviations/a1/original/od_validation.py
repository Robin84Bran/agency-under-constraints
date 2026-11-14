"""Strict provider envelopes. No network and no fallback extraction."""
import base64
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from od_core import MODEL,PINS,choice,strict_load
from od_io import Stop

class TransportFailure(ValueError): pass
class ReplyFailure(ValueError): pass

def stdout(raw): return base64.b64decode(raw['stdout_b64'],validate=True).decode('utf8',errors='strict')

def usage(e,actor):
    if type(e) is not dict: return None
    if actor!='claude':
        a,b=e.get('prompt_eval_count'),e.get('eval_count')
        return {'input':a,'output':b,'cache_read':0,'cache_creation':0,'reported_cost_micro_usd':None} if all(type(v) is int and v>=0 for v in (a,b)) else None
    u=e.get('usage')
    if type(u) is not dict: return None
    vals=[u.get(k) for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens')]
    if not all(type(v) is int and v>=0 for v in vals): return None
    try:
        value=e['total_cost_usd']
        if type(value) not in (float,int,str): return None
        d=Decimal(str(value))
        if not d.is_finite() or d<0: return None
        reported=int((d*1000000).to_integral_value(rounding=ROUND_CEILING))
    except (KeyError,TypeError,ValueError,InvalidOperation): return None
    return dict(zip(('input','cache_read','cache_creation','output'),vals),reported_cost_micro_usd=reported)

def cost(u): return max(4*sum(u[k] for k in ('input','cache_read','cache_creation'))+20*u['output'],u['reported_cost_micro_usd'])

def accounting(raw,actor):
    try: return usage(strict_load(stdout(raw)),actor)
    except (ValueError,KeyError,TypeError,UnicodeError): return None

def validate(raw,actor,bound,expected_input_tokens=None):
    paid=actor=='claude'
    if type(raw) is not dict or type(raw.get('returncode')) is not int or raw['returncode']!=0 or raw.get('transport_error'):
        raise (Stop if paid else TransportFailure)('transport failure/uncertain start; never resend')
    try: e=strict_load(stdout(raw))
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        raise (Stop if paid else TransportFailure)('unreadable transport envelope') from exc
    if type(e) is not dict: raise (Stop if paid else TransportFailure)('envelope object required')
    u=usage(e,actor)
    if not paid:
        if e.get('model')!=PINS[actor][0]: raise Stop('local model identity mismatch')
        if e.get('done') is not True or type(e.get('eval_count')) is not int or e['eval_count']<0: raise TransportFailure('local done/eval_count missing or incomplete')
        if u is None: raise TransportFailure('local usage UNKNOWN')
        if e.get('done_reason') not in ('stop','length'): raise Stop('unknown local stop reason')
        if u['input']<=0 or u['input']+192>=8192 or e.get('truncated') or e.get('input_truncated'): raise Stop('local input/context truncation')
        if expected_input_tokens is not None and (type(expected_input_tokens) is not int or expected_input_tokens<=0 or u['input']<expected_input_tokens): raise Stop('independent input count shortfall')
        running=raw.get('running',{}).get('models',[])
        if not any(type(m) is dict and m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] and m.get('context_length')==8192 for m in running): raise Stop('running identity/context mismatch')
        if u['output']>192: raise Stop('local output usage overrun')
        if e['done_reason']=='length' or u['output']==192: raise ReplyFailure('local output-length stop')
        try: n=choice(strict_load(e.get('response')))
        except (ValueError,TypeError): raise ReplyFailure('invalid local reply') from None
    else:
        turns=e.get('num_turns');stop=e.get('stop_reason')
        if e.get('type')!='result' or e.get('subtype')!='success' or e.get('is_error') is not False or type(turns) is not int or turns not in (1,2): raise Stop('unexpected Claude result/turn envelope')
        if stop not in ('end_turn','tool_use','max_tokens','length'): raise Stop('unknown Claude stop reason')
        if turns==2 and stop!='tool_use': raise Stop('unexpected second turn')
        mu=e.get('modelUsage')
        if type(mu) is not dict or set(mu)!={MODEL} or type(mu[MODEL]) is not dict: raise Stop('Claude model identity UNKNOWN/mismatch')
        if e.get('model',MODEL)!=MODEL or e.get('effort','medium')!='medium': raise Stop('Claude identity/effort conflict')
        if u is None: raise Stop('Claude usage/cost UNKNOWN; hold retained')
        expected={'inputTokens':u['input'],'outputTokens':u['output'],'cacheReadInputTokens':u['cache_read'],'cacheCreationInputTokens':u['cache_creation']}
        if any(type(mu[MODEL].get(k)) is not int or mu[MODEL][k]!=v for k,v in expected.items()): raise Stop('aggregate/model usage mismatch')
        if e.get('permission_denials')!=[] or any(e.get(k) for k in ('deferred_tool_use','subagent_stats','tool_uses','tool_calls','errors','safety_stops')): raise Stop('unexpected tools/errors')
        st=e['usage'].get('server_tool_use')
        if type(st) is not dict or not {'web_search_requests','web_fetch_requests'}<=set(st) or any(type(v) is not int or v!=0 for v in st.values()) or mu[MODEL].get('webSearchRequests')!=0: raise Stop('server tool activity UNKNOWN/nonzero')
        if sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>bound['output_tokens'] or cost(u)>bound['micro_usd']: raise Stop('Claude reservation overrun')
        if stop in ('max_tokens','length'): raise ReplyFailure('Claude output-length stop')
        v=e.get('structured_output')
        if type(v) is not dict: raise Stop('structured_output object required; no result fallback')
        try: n=choice(v)
        except ValueError: raise ReplyFailure('invalid Claude structured_output') from None
    return {'fleet':n,'schema_valid':True,'status':'ABSTENTION' if n is None else 'CHOICE','usage':u,
       'returned_effort':e.get('effort','UNKNOWN') if paid else None,'input_completeness':'UNKNOWN' if expected_input_tokens is None else 'VERIFIED_AGAINST_INDEPENDENT_COUNT'}
