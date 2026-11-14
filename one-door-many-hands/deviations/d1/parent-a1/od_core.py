"""Pure one-wave simulator, exact oracle, rendering and schedule. No providers."""
import hashlib
import itertools
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
FLEETS = (1, 6, 24)
ACTORS = ('qwen7b', 'llama8b', 'qwen1b', 'claude')
PINS = {'qwen7b':('qwen2.5:7b','845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 'llama8b':('llama3.1:8b','46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'),
 'qwen1b':('qwen2.5:1.5b','65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b')}
MODEL = 'claude-opus-5-5'
SYSTEM = 'You are a careful planner. Return only the requested JSON object.'
INSTRUCTION = 'Choose a fleet before damage to maximize the probability of delivering at least target work units by the deadline. Total payload capacity is 24. With n carriers each has payload 24/n; options are 1, 6, or 24. Damage happens before any crossing. In independent mode every carrier fails independently with failure_percent percent probability. In common mode all carriers fail together with that probability, or all survive. The door admits at most door_limit surviving bodies in total by the deadline. Each survivor crosses once at most, delivering its full payload immediately. The scheduler uses all available admissions. There are no returns, repairs, setup costs, or other constraints. Any fleet tied for the highest success probability is correct. Maximize deadline success probability, not survivor count or mean work. Optional rehearsal receipts show a failure-free dispatch with these same door rules; they do not predict future damage. Return exactly one object with fleet equal to 1, 6, 24, or null if you abstain. No explanation or other keys.'
# Preserve the registered literal's key order for schema sizing (139 bytes).
SCHEMA = {'type':'object','properties':{'fleet':{'type':['integer','null'],'enum':[1,6,24,None]}},'required':['fleet'],'additionalProperties':False}
SCHEMA_TEXT = json.dumps(SCHEMA,ensure_ascii=True,separators=(',',':'))


def canonical(x):
    return json.dumps(x, ensure_ascii=True, sort_keys=True, separators=(',',':'), allow_nan=False)


def sha(x):
    return hashlib.sha256(x).hexdigest()


def strict_load(s):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result: raise ValueError('duplicate key: '+k)
            result[k] = v
        return result
    def bad(x): raise ValueError('nonfinite JSON: '+x)
    return json.loads(s,object_pairs_hook=pairs,parse_constant=bad)


def choice(v):
    if type(v) is not dict or set(v)!={'fleet'}: raise ValueError('exact fleet object required')
    n = v['fleet']
    if n is not None and (type(n) is not int or n not in FLEETS): raise ValueError('fleet integer 1/6/24 or null required')
    return n


def delivered(n, survivors, door):
    if n not in FLEETS or type(n) is not int or type(survivors) is not int or not 0<=survivors<=n or type(door) is not int or not 0<=door<=24: raise ValueError('world bounds')
    return (24//n)*min(survivors,door)


@lru_cache(None)
def oracle(target, failure, door, mode):
    if type(target) is not int or not 0<=target<=25 or type(failure) is not int or not 0<=failure<=100 or type(door) is not int or not 0<=door<=24 or mode not in ('independent','common'): raise ValueError('oracle bounds')
    p = Fraction(failure,100)
    rows = {}
    for n in FLEETS:
        required = (target*n+23)//24
        if mode=='common':
            dist = [(0,p),(n,1-p)]
        else:
            dist = [(k,Fraction(math.comb(n,k))*(1-p)**k*p**(n-k)) for k in range(n+1)]
        value = sum((prob for k,prob in dist if delivered(n,k,door)>=target),Fraction())
        work = sum((prob*delivered(n,k,door) for k,prob in dist),Fraction())
        rows[n] = {'value':value,'work':work,'outage':p**n if mode=='independent' else p,'required':required}
    best = max(r['value'] for r in rows.values())
    return rows,best,tuple(n for n in FLEETS if rows[n]['value']==best)


def fraction(x): return {'numerator':x.numerator,'denominator':x.denominator}


def payload(ep):
    b,B = ep['block'],ep['door']
    options = list(itertools.permutations(FLEETS))[b%6]
    return {'target':7+b%10,'failure_percent':20+6*(b//10),'mode':ep['mode'],'door_limit':B,'options':list(options),
      'rehearsal':[] if ep['evidence']=='rules' else [{'carriers':n,'crossings':min(n,B),'delivered':delivered(n,n,B)} for n in options]}


def render(ep): return INSTRUCTION+'\n'+canonical(payload(ep))


def schedule():
    jobs = []
    for actor in ACTORS:
        blocks = [10*j+(3*j)%10 for j in range(10)] if actor=='claude' else list(range(100))
        items = sorted(itertools.product(blocks,(1,6,24),('common','independent'),('rehearsal','rules')))
        random.Random(20261111).shuffle(items)
        for b,B,m,e in items:
            jobs.append({'id':f'{actor}-b{b:02d}-d{B:02d}-{m}-{e}','actor':actor,'block':b,'door':B,'mode':m,'evidence':e})
    return jobs


def padded(n): return ((n*110+6399)//6400)*64


def reserve(prompt):
    i = padded(len(prompt.encode())+len(SYSTEM.encode())+len(SCHEMA_TEXT.encode())+826)
    o = padded(512)
    return {'input_tokens':i,'output_tokens':o,'micro_usd':4*i+20*o}


def score(ep,n,valid):
    p=payload(ep); rows,best,optimal=oracle(p['target'],p['failure_percent'],p['door_limit'],p['mode'])
    known = valid and n is not None
    value = rows[n]['value'] if known else Fraction()
    return {'operational_value':float(value),'regret':float(best-value),'optimal':int(known and n in optimal),
      'oracle_value':float(best),'optimal_set':list(optimal),'chosen_value':float(rows[n]['value']) if known else None,
      'chosen_work':float(rows[n]['work']) if known else None,'chosen_outage':float(rows[n]['outage']) if known else None}
