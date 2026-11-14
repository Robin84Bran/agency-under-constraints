"""Frozen request/non-start predicates; no network or provider imports."""
import base64
from trl_core import PINS, SYSTEM, canonical, schema, strict_load
from trl_io import Stop
OPTIONS = {'temperature': 0.6, 'top_k': 16, 'num_predict': 192, 'num_ctx': 8192}
ACTORS = tuple(PINS)

def request(actor, prompt, quota, seed):
    if actor not in ACTORS:
        raise Stop('v0.2 dispatch is local actors only; Claude cohort is reused')
    return {'model':PINS[actor][0],'prompt':prompt,'system':SYSTEM,
            'format':schema(quota),'stream':False,'options':dict(OPTIONS,seed=seed)}


def zero_limit(data):
    """Only an explicit zero-generation limit envelope proves a non-start."""
    try:
        e = strict_load(data.decode())
        return (type(e) is dict and e.get('error')=='usage_limit_reached' and
            all(type(e.get(k)) is int and e[k]==0 for k in ('prompt_eval_count','eval_count')) and
            type(e.get('total_cost_usd')) in (int,float) and e['total_cost_usd']==0 and
            e.get('response') in (None,'') and not e.get('tool_calls'))
    except (ValueError,UnicodeError):
        return False


def non_start(raw):
    if raw.get('non_start')=='DNS' and type(raw.get('dns_errno')) is int and not base64.b64decode(raw['stdout_b64']):
        return 'DNS'
    if raw.get('non_start')=='USAGE_LIMIT' and raw.get('http_status')==429 and zero_limit(base64.b64decode(raw['stdout_b64'])):
        return 'USAGE_LIMIT'
    return None
