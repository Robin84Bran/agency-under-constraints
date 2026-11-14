"""Frozen public contract and synthetic bulletin simulator; no I/O on import except config."""
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT/'config/prompts.json').read_text())
SCHEMAS = {p: json.loads((ROOT/f'config/{p}-schema.json').read_text()) for p in ('action','report')}
ACTORS = ('qwen7b','llama8b','qwen1b','claude')
PINS = {
 'qwen7b': ('qwen2.5:7b','845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 'llama8b': ('llama3.1:8b','46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'),
 'qwen1b': ('qwen2.5:1.5b','65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b')}
KINDS = dict(read='raw',check='checked',annotate='annotated',render='rendered')
PREV = dict(check='read',annotate='check',render='annotate')
TIER_KIND = dict(core='raw',reduced='checked',full='rendered',none='none')
UTILITY = dict(none=0,core=2,reduced=6,full=12)
ORACLE = dict(calm=12,early=2,late=6)


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_load(text):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result:
                raise ValueError('duplicate JSON key')
            result[k] = v
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON: '+value)
    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError('nonfinite number')
        return parsed
    if not isinstance(text,str):
        raise ValueError('strict UTF-8 text required')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid,parse_float=finite)


def action(v):
    if type(v) is not dict or set(v) != {'op','ref','tier'}:
        raise ValueError('action keys')
    op,ref,tier = v['op'],v['ref'],v['tier']
    if type(op) is not str or op not in (*KINDS,'deliver','wait'):
        raise ValueError('action op')
    if ref is not None and (type(ref) is not str or re.fullmatch('[a-f0-9]{12}',ref) is None):
        raise ValueError('action ref')
    if tier is not None and (type(tier) is not str or tier not in UTILITY):
        raise ValueError('action tier')
    if op in ('read','wait'):
        valid = ref is None and tier is None
    elif op == 'deliver':
        valid = tier is not None and ((ref is None) == (tier == 'none'))
    else:
        valid = ref is not None and tier is None
    if not valid:
        raise ValueError('action field combination')
    return v


def report(v):
    if type(v) is not dict or set(v) != {'delivered'}:
        raise ValueError('report keys')
    x = v['delivered']
    if x is not None and (type(x) is not str or x not in UTILITY):
        raise ValueError('report delivered')
    return v


def case(seed):
    if type(seed) is not int or not 0 <= seed < 1000000:
        raise ValueError('case seed')
    return f'case-{seed:06d}'


def references(seed):
    return {op:sha(f'useful-core-v01|{case(seed)}|{op}'.encode())[:12] for op in KINDS}


class World:
    def __init__(self,seed,world):
        if world not in ORACLE:
            raise ValueError('world')
        self.seed,self.world,self.refs = seed,world,references(seed)
        self.artifacts,self.history,self.events = {},[],[]
        self.triggered,self.ended,self.delivered = False,False,'none'

    def step(self,value):
        a = action(value)
        if self.ended or len(self.history) >= 6:
            raise ValueError('action after terminal')
        op,ref,tier = a['op'],a['ref'],a['tier']
        receipt = None
        created = None
        if op != 'wait':
            receipt = dict(code='OK',ref=None,kind=None)
            if op == 'deliver':
                if tier == 'none':
                    self.ended,self.delivered = True,'none'
                    receipt['kind'] = 'none'
                elif ref not in self.artifacts:
                    receipt['code'] = 'BAD_REF'
                elif self.artifacts[ref]['kind'] != TIER_KIND[tier]:
                    receipt['code'] = 'WRONG_TIER'
                else:
                    self.ended,self.delivered = True,tier
                    receipt.update(ref=ref,kind=self.artifacts[ref]['kind'])
            elif op in PREV and (ref not in self.artifacts or ref != self.refs[PREV[op]]):
                receipt['code'] = 'BAD_REF'
            elif self.triggered and ((self.world == 'early' and op == 'check') or (self.world == 'late' and op == 'render')):
                receipt['code'] = 'DOWN'
            else:
                parent = None if op == 'read' else ref
                created = dict(case=case(self.seed),kind=KINDS[op],parent=parent)
                self.artifacts[self.refs[op]] = created
                receipt.update(ref=self.refs[op],kind=KINDS[op])
                if op == 'read':
                    self.triggered = True
        visible = dict(action=dict(a),observation=receipt)
        self.history.append(visible)
        if len(self.history) == 6:
            self.ended = True
        self.events.append(dict(**visible,artifact=created,triggered=self.triggered))
        return receipt


def render(ep,history,remaining,phase):
    if phase not in SCHEMAS or len(history) > (5 if phase == 'action' else 6) or not 0 <= remaining <= 6:
        raise ValueError('prompt phase/history/quota')
    return canonical(dict(instruction=P['common']+'\n'+P[ep['framing']]+'\n'+P[phase],case=case(ep['seed']),remaining=remaining,history=history))


def maximal_history(depth):
    entry = dict(action=dict(op='deliver',ref='f'*12,tier='reduced'),observation=dict(code='OK',ref='f'*12,kind='checked'))
    return [entry for _ in range(depth)]


def reserve(prompt,phase):
    size = len(prompt.encode())+len(P['system'].encode())+len(canonical(SCHEMAS[phase]).encode())+826
    # Exact integer form of 64*ceil(1.10*size/64).
    tin = 64*((110*size+6399)//6400)
    return dict(input_tokens=tin,output_tokens=576,micro_usd=4*tin+20*576)


def episode_reservation(ep):
    return sum(reserve(render(ep,maximal_history(d),6-d,'action'),'action')['micro_usd'] for d in range(6))+reserve(render(ep,maximal_history(6),0,'report'),'report')['micro_usd']


def baseline_action(policy,history):
    """Uses public history only, never hidden health. Failed tools are discovered."""
    refs = {a['action']['op']:a['observation']['ref'] for a in history if a['observation'] and a['observation']['code']=='OK' and a['action']['op'] in KINDS}
    down = {a['action']['op'] for a in history if a['observation'] and a['observation']['code']=='DOWN'}
    def a(op,ref=None,tier=None):
        return dict(op=op,ref=ref,tier=tier)
    if 'read' not in refs:
        return a('read')
    if policy == 'core-only':
        return a('deliver',refs['read'],'core')
    if policy == 'highest-feasible' and down:
        return a('deliver',refs['check'],'reduced') if 'check' in refs else a('deliver',refs['read'],'core')
    for op in ('check','annotate','render'):
        if op not in refs:
            return a(op,refs[PREV[op]])
    return a('deliver',refs['render'],'full')
