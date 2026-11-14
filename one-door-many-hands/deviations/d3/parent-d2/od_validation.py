"""Strict provider envelopes. No network and no fallback extraction."""
import base64
import json
import math
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from od_core import MODEL,PINS,choice,strict_load
from od_io import Stop

class TransportFailure(ValueError): pass
class ReplyFailure(ValueError): pass

def stdout(raw): return base64.b64decode(raw['stdout_b64'],validate=True).decode('utf8',errors='strict')

def envelope(raw,actor,legacy=False):
    """Keep usable provider metadata when only the designated payload is invalid.

    This decodes one complete JSON document; it never repairs syntax or extracts
    substrings. Duplicate outer/metadata keys remain integrity failures.
    """
    if legacy: return strict_load(stdout(raw)),None
    class Pairs(list): pass
    class Nonfinite(str): pass
    def convert(value):
        if isinstance(value,Pairs):
            result={}
            for key,item in value:
                if key in result: raise ValueError('duplicate JSON key: '+key)
                result[key]=convert(item)
            return result
        if isinstance(value,list): return [convert(item) for item in value]
        if isinstance(value,Nonfinite) or (type(value) is float and not math.isfinite(value)):
            raise ValueError('nonfinite JSON value')
        return value
    pairs=json.loads(stdout(raw),object_pairs_hook=Pairs,parse_constant=Nonfinite)
    if not isinstance(pairs,Pairs): raise ValueError('envelope object required')
    result={};payload_error=None
    for key,value in pairs:
        if key in result: raise ValueError('duplicate envelope key: '+key)
        if actor=='claude' and key=='structured_output':
            try: result[key]=convert(value)
            except ValueError as exc: result[key]=None;payload_error=str(exc)
        else: result[key]=convert(value)
    return result,payload_error

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

def accounting(raw,actor,legacy=False):
    try: return usage(envelope(raw,actor,legacy)[0],actor)
    except (ValueError,KeyError,TypeError,UnicodeError): return None

def validate(raw,actor,bound,expected_input_tokens=None,legacy=False):
    paid=actor=='claude'
    if type(raw) is dict and raw.get('harness_error'): raise Stop('provider harness failure: '+raw['harness_error'])
    if paid and not legacy and type(raw) is dict:
        try: e,payload_error=envelope(raw,actor)
        except (ValueError,KeyError,TypeError,UnicodeError) as exc:
            raise Stop('unreadable transport envelope') from exc
        return validate_claude(raw,e,payload_error,bound,expected_input_tokens)
    if type(raw) is not dict or type(raw.get('returncode')) is not int or raw['returncode'] not in ((0,1) if paid and not legacy else (0,)) or raw.get('transport_error'):
        raise (Stop if paid else TransportFailure)('transport failure/uncertain start; never resend')
    try: e,payload_error=envelope(raw,actor,legacy)
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        raise (Stop if paid else TransportFailure)('unreadable transport envelope') from exc
    if type(e) is not dict: raise (Stop if paid else TransportFailure)('envelope object required')
    schema_failure=paid and not legacy and e.get('type')=='result' and e.get('subtype')=='error_max_structured_output_retries' and e.get('is_error') is True
    if raw['returncode']!=0 and not schema_failure: raise Stop('transport failure/uncertain start; never resend')
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
        success=e.get('subtype')=='success' and e.get('is_error') is False
        if e.get('type')!='result' or not (success or schema_failure) or type(turns) is not int or turns not in (1,2): raise Stop('unexpected Claude result/turn envelope')
        if stop not in ('end_turn','tool_use','max_tokens','length'): raise Stop('unknown Claude stop reason')
        if turns==2 and stop not in (('tool_use',) if legacy else ('tool_use','max_tokens','length')): raise Stop('unexpected second turn')
        mu=e.get('modelUsage')
        if type(mu) is not dict or set(mu)!={MODEL} or type(mu[MODEL]) is not dict: raise Stop('Claude model identity UNKNOWN/mismatch')
        if e.get('model',MODEL)!=MODEL or e.get('effort','medium')!='medium': raise Stop('Claude identity/effort conflict')
        if u is None: raise Stop('Claude usage/cost UNKNOWN; hold retained')
        expected={'inputTokens':u['input'],'outputTokens':u['output'],'cacheReadInputTokens':u['cache_read'],'cacheCreationInputTokens':u['cache_creation']}
        if any(type(mu[MODEL].get(k)) is not int or mu[MODEL][k]!=v for k,v in expected.items()): raise Stop('aggregate/model usage mismatch')
        descriptive_errors=schema_failure and type(e.get('errors')) is list and all(type(x) is str for x in e['errors'])
        if e.get('permission_denials')!=[] or any(e.get(k) for k in ('deferred_tool_use','tool_uses','tool_calls','safety_stops')) or (e.get('errors') and not descriptive_errors): raise Stop('unexpected tools/errors')
        from od_usage import zero_tree
        if e.get('subagent_stats') and not zero_tree(e['subagent_stats']): raise Stop('unexpected subagent activity')
        st=e['usage'].get('server_tool_use')
        if type(st) is not dict or not {'web_search_requests','web_fetch_requests'}<=set(st) or any(type(v) is not int or v!=0 for v in st.values()) or mu[MODEL].get('webSearchRequests')!=0: raise Stop('server tool activity UNKNOWN/nonzero')
        if sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>bound['output_tokens'] or cost(u)>bound['micro_usd']: raise Stop('Claude reservation overrun')
        if schema_failure: raise ReplyFailure('provider rejected model structured output')
        if stop in ('max_tokens','length'): raise ReplyFailure('Claude output-length stop')
        if payload_error: raise ReplyFailure(payload_error)
        v=e.get('structured_output')
        if type(v) is not dict: raise (Stop if legacy else ReplyFailure)('structured_output object required; no result fallback')
        try: n=choice(v)
        except ValueError: raise ReplyFailure('invalid Claude structured_output') from None
    return {'fleet':n,'schema_valid':True,'status':'ABSTENTION' if n is None else 'CHOICE','usage':u,
       'returned_effort':e.get('effort','UNKNOWN') if paid else None,'input_completeness':'UNKNOWN' if expected_input_tokens is None else 'VERIFIED_AGAINST_INDEPENDENT_COUNT'}


def validate_claude(raw,e,payload_error,bound,expected_input_tokens=None):
    """D2 separates generated content errors from independent integrity gates."""
    from od_usage import zero_tree
    from od_contract import controls
    output_cap=int(controls()['CLAUDE_CODE_MAX_OUTPUT_TOKENS'])
    u=usage(e,'claude');turns=e.get('num_turns');error=e.get('is_error') is True
    if e.get('type')!='result' or type(e.get('is_error')) is not bool or type(turns) is not int or turns not in ((0,1,2) if error else (1,2)):
        raise Stop('unexpected Claude result/turn envelope')
    interrupted=raw.get('transport_error') or raw.get('returncode') is None
    if not interrupted and (type(raw.get('returncode')) is not int or raw['returncode'] not in (0,1)): raise Stop('unexpected Claude process exit')
    if not interrupted and raw['returncode']!=0 and not error: raise Stop('inconsistent Claude exit/error envelope')
    if e.get('model',MODEL)!=MODEL or e.get('effort','medium')!='medium': raise Stop('Claude identity/effort conflict')
    if u is None: raise Stop('Claude usage/cost UNKNOWN; hold retained')
    mu=e.get('modelUsage')
    # Errors can precede model attribution; absence is not a conflicting identity.
    if mu not in (None,{}) or not error:
        if type(mu) is not dict or set(mu)!={MODEL} or type(mu[MODEL]) is not dict: raise Stop('Claude model identity UNKNOWN/mismatch')
        expected={'inputTokens':u['input'],'outputTokens':u['output'],'cacheReadInputTokens':u['cache_read'],'cacheCreationInputTokens':u['cache_creation']}
        if any(type(mu[MODEL].get(k)) is not int or mu[MODEL][k]!=v for k,v in expected.items()): raise Stop('aggregate/model usage mismatch')
        if mu[MODEL].get('canonicalModel',MODEL)!=MODEL: raise Stop('Claude canonical model conflict')
        if mu[MODEL].get('webSearchRequests')!=0: raise Stop('server tool activity UNKNOWN/nonzero')
    if e.get('permission_denials',[] if error else None)!=[] or any(e.get(k) for k in ('deferred_tool_use','tool_uses','tool_calls')): raise Stop('unexpected tools/errors')
    if e.get('errors') and (not error or type(e['errors']) is not list or any(type(x) is not str for x in e['errors'])): raise Stop('unexpected tools/errors')
    if e.get('subagent_stats') and not zero_tree(e['subagent_stats']): raise Stop('unexpected subagent activity')
    st=e['usage'].get('server_tool_use')
    if not (error and st is None):
        if type(st) is not dict or not {'web_search_requests','web_fetch_requests'}<=set(st) or any(type(v) is not int or v!=0 for v in st.values()): raise Stop('server tool activity UNKNOWN/nonzero')
    if sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'] or u['output']>bound['output_tokens'] or cost(u)>bound['micro_usd']: raise Stop('Claude reservation overrun')
    generated=any(u[k]>0 for k in ('input','output','cache_read','cache_creation'))
    if interrupted:
        if generated: raise ReplyFailure('Claude generated output before transport termination')
        raise Stop('transport failure/uncertain start; never resend')
    if e.get('safety_stops'):
        if generated: raise ReplyFailure('Claude generated safety refusal')
        raise Stop('unclassified zero-use Claude safety stop')
    if error:
        if not generated: raise Stop('unclassified zero-use Claude error; no automatic resend')
        if e.get('subtype')=='error_max_structured_output_retries': raise ReplyFailure('provider rejected model structured output')
        if e.get('stop_reason') in ('max_tokens','length') or u['output']>=output_cap: raise ReplyFailure('Claude output-length stop')
        raise ReplyFailure('Claude generated error/refusal')
    if e.get('subtype')!='success': raise ReplyFailure('Claude generated non-success result') if generated else Stop('unexpected Claude result envelope')
    stop=e.get('stop_reason')
    if stop in ('max_tokens','length') or u['output']>=output_cap: raise ReplyFailure('Claude output-length stop')
    if stop not in ('end_turn','tool_use','stop_sequence'):
        if generated: raise ReplyFailure('Claude generated unsupported stop result')
        raise Stop('unknown Claude stop reason')
    if payload_error: raise ReplyFailure(payload_error)
    if type(e.get('structured_output')) is not dict: raise ReplyFailure('structured_output object required; no result fallback')
    try: n=choice(e['structured_output'])
    except ValueError: raise ReplyFailure('invalid Claude structured_output') from None
    return {'fleet':n,'schema_valid':True,'status':'ABSTENTION' if n is None else 'CHOICE','usage':u,
        'returned_effort':e.get('effort','UNKNOWN'),'input_completeness':'UNKNOWN' if expected_input_tokens is None else 'VERIFIED_AGAINST_INDEPENDENT_COUNT'}
