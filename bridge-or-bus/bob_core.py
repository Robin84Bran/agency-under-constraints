"""Synthetic interface drift; exact public contract. No provider I/O."""
import hashlib
import json
import math
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT/'config/prompts.json').read_text())
SCHEMAS = {p: json.loads((ROOT/f'config/{p}-schema.json').read_text()) for p in ('action','report')}
ACTORS = ('qwen7b','llama8b','qwen1b','claude')
WORLDS = ('stable','rename','unit','required')
ARMS = ('stale','registry')
PINS = {
 'qwen7b': ('qwen2.5:7b','845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 'llama8b': ('llama3.1:8b','46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'),
 'qwen1b': ('qwen2.5:1.5b','65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b')}
ERRORS = {
 'rename': 'convert requires mass_g; grams is not accepted',
 'convert_v0': 'convert requires grams; mass_g is not accepted',
 'required': 'submit requires revision=1',
 'submit_v0': 'submit does not accept revision',
 'lookup': 'lookup required',
 'convert': 'successful convert required',
 'item': 'item not found',
 'value': 'mass does not match lookup'}
DESCRIPTIONS = {
 'lookup': 'lookup(item): returns mass amount with unit g.',
 'convert_v0': 'convert(grams): requires lookup; returns amount with unit g.',
 'convert_rename': 'convert(mass_g): requires lookup; returns amount with unit g.',
 'convert_unit': 'convert(grams): requires lookup; returns amount with unit mg. Divide amount by 1000 for grams.',
 'submit_v0': "submit(grams): requires successful convert; accepts the item's exact mass in grams.",
 'submit_required': "submit(grams,revision=1): requires successful convert; accepts the item's exact mass in grams."}


def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_load(raw):
    def pairs(entries):
        out = {}
        for k,v in entries:
            if k in out:
                raise ValueError('duplicate key: '+k)
            out[k] = v
        return out
    def bad(value):
        raise ValueError('nonfinite constant: '+value)
    if type(raw) is bytes:
        raw = raw.decode('utf8',errors='strict')
    if type(raw) is not str:
        raise ValueError('raw JSON text required')
    def number(value):
        v=float(value)
        if not math.isfinite(v):
            raise ValueError('nonfinite JSON number')
        return v
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad,parse_float=number)


def action(v, arm):
    if arm not in ARMS or type(v) is not dict or set(v) != {'op','item','grams','mass_g','revision','target'}:
        raise ValueError('action keys/arm')
    op = v['op']
    if type(op) is not str or op not in ('lookup','convert','submit','describe','finish'):
        raise ValueError('operation')
    if v['item'] is not None and (type(v['item']) is not str or re.fullmatch(r'[a-z0-9-]{1,12}',v['item'],re.ASCII) is None):
        raise ValueError('item')
    for k in ('grams','mass_g'):
        if v[k] is not None and (type(v[k]) is not int or not 0 <= v[k] <= 999999999):
            raise ValueError(k)
    if v['revision'] is not None and (type(v['revision']) is not int or v['revision'] != 1):
        raise ValueError('revision')
    if v['target'] is not None and (type(v['target']) is not str or v['target'] not in ('lookup','convert','submit')):
        raise ValueError('target')
    used = {k for k in ('item','grams','mass_g','revision','target') if v[k] is not None}
    legal = (op=='lookup' and used=={'item'} or
             op=='convert' and used in ({'grams'},{'mass_g'}) or
             op=='submit' and used in ({'grams'},{'grams','revision'}) or
             op=='describe' and arm=='registry' and used=={'target'} or
             op=='finish' and not used)
    if not legal:
        raise ValueError('cross-field legality or unavailable operation')
    return strict_load(canonical(v))


def report(v):
    if type(v) is not dict or set(v) != {'submitted'} or (v['submitted'] is not None and type(v['submitted']) is not bool):
        raise ValueError('report requires boolean/null submitted only')
    return v


def act(op, **fields):
    return dict(op=op,item=None,grams=None,mass_g=None,revision=None,target=None,**{}) | fields


def observation(code='OK',amount=None,unit=None,detail=None):
    v = dict(code=code,amount=amount,unit=unit,detail=detail)
    validate_observation(v)
    return v


def validate_observation(v):
    if type(v) is not dict or set(v) != {'code','amount','unit','detail'} or v['code'] not in ('OK','SCHEMA','VALUE','ORDER','NOT_FOUND'):
        raise ValueError('observation fields/code')
    if v['amount'] is not None and (type(v['amount']) is not int or not 0 <= v['amount'] <= 999999999):
        raise ValueError('observation amount')
    if v['unit'] not in (None,'g','mg'):
        raise ValueError('observation unit')
    s = v['detail']
    if s is not None and (type(s) is not str or len(s)>192 or any(ord(c)<32 or ord(c)>126 or c in '\\"' for c in s)):
        raise ValueError('observation detail')
    if v['code']!='OK' and (v['amount'] is not None or v['unit'] is not None or s not in ERRORS.values()):
        raise ValueError('error observation')
    if v['code']=='OK' and s is not None and s not in DESCRIPTIONS.values():
        raise ValueError('unfrozen description')
    return v


class World:
    def __init__(self, seed, world, arm):
        if type(seed) is not int or seed not in range(50) or world not in WORLDS or arm not in ARMS:
            raise ValueError('world assignment')
        self.seed,self.world,self.arm = seed,world,arm
        self.item = f'item-{seed:06d}'
        self.mass = 1000 + ((7919*seed+104729)%998000)
        self.looked = self.converted = self.committed = self.ended = False
        self.decisions = 0
        self.events,self.history = [],[]

    def description(self,target):
        key = target
        if target=='convert':
            key = 'convert_'+(self.world if self.looked and self.world in ('rename','unit') else 'v0')
        elif target=='submit':
            key = 'submit_'+('required' if self.looked and self.world=='required' else 'v0')
        return DESCRIPTIONS[key]

    def step(self,value):
        a = action(value,self.arm)
        if self.ended or self.decisions>=6:
            raise ValueError('episode terminal')
        self.decisions += 1
        op = a['op']
        obs = None
        if op=='finish':
            self.ended = True
        elif op=='describe':
            obs = observation(detail=self.description(a['target']))
        elif op=='lookup':
            if a['item']!=self.item:
                obs = observation('NOT_FOUND',detail=ERRORS['item'])
            else:
                self.looked = True
                obs = observation(amount=self.mass,unit='g')
        elif op=='convert':
            rename = self.looked and self.world=='rename'
            if (a['mass_g'] is None) if rename else (a['grams'] is None):
                obs = observation('SCHEMA',detail=ERRORS['rename' if rename else 'convert_v0'])
            elif not self.looked:
                obs = observation('ORDER',detail=ERRORS['lookup'])
            elif (a['mass_g'] if rename else a['grams']) != self.mass:
                obs = observation('VALUE',detail=ERRORS['value'])
            else:
                self.converted = True
                mg = self.world=='unit'
                obs = observation(amount=self.mass*(1000 if mg else 1),unit='mg' if mg else 'g')
        elif op=='submit':
            required = self.looked and self.world=='required'
            if (a['revision']!=1) if required else (a['revision'] is not None):
                obs = observation('SCHEMA',detail=ERRORS['required' if required else 'submit_v0'])
            elif not self.converted:
                obs = observation('ORDER',detail=ERRORS['convert'])
            elif a['grams'] != self.mass:
                obs = observation('VALUE',detail=ERRORS['value'])
            else:
                self.committed = self.ended = True
                obs = observation()
        event = {'action':a,'observation':obs}
        self.events.append(event)
        if obs is not None:
            self.history.append(event)
        self.ended |= self.decisions==6
        return obs


def render(ep,history,remaining,phase):
    if phase not in ('action','report') or ep['arm'] not in ARMS or type(remaining) is not int or remaining not in range(7):
        raise ValueError('render parameters')
    return canonical({'instruction':P['common']+'\n'+P[phase],
                      'item':f"item-{ep['seed']:06d}",
                      'tools':P['initial']+'\n'+P[ep['arm']],
                      'remaining':remaining,'history':history})


def schedule():
    rows = []
    for model in ACTORS:
        cells = sorted((s,w,a) for s in range(10 if model=='claude' else 50) for w in WORLDS for a in ARMS)
        random.Random(20261111).shuffle(cells)
        for s,w,a in cells:
            rows.append(dict(id=f'{model}-{s:02d}-{w}-{a}',model=model,seed=s,world=w,arm=a))
    return rows


def padded(n):
    return ((110*n+6399)//6400)*64


def reserve(prompt,phase):
    tin = padded(len(prompt.encode())+len(P['system'].encode())+len(canonical(SCHEMAS[phase]).encode())+826)
    tout = padded(512)
    return {'input_tokens':tin,'output_tokens':tout,'micro_usd':4*tin+20*tout}


def maximal_history(depth):
    return [{'action':act('describe',item='x'*12,grams=999999999,mass_g=999999999,target='convert'),
             'observation':{'code':'NOT_FOUND','amount':999999999,'unit':'mg','detail':'X'*192}} for _ in range(depth)]


def bound_prompt(ep,depth,phase):
    v=strict_load(render(ep,maximal_history(depth),6,phase))
    v['item']='x'*12
    return canonical(v)


def subholds(ep):
    return [reserve(bound_prompt(ep,d,'action'),'action') for d in range(6)] + [reserve(bound_prompt(ep,6,'report'),'report')]


def sizing():
    rows = []
    for arm in ARMS:
        ep = dict(seed=49,arm=arm)
        for phase in ('action','report'):
            for d in range(7):
                prompt = bound_prompt(ep,d,phase)
                rows.append(dict(arm=arm,phase=phase,depth=d,prompt_bytes=len(prompt.encode()),prompt_sha256=sha(prompt.encode()),**reserve(prompt,phase)))
    holds = {a:sum(x['micro_usd'] for x in subholds(dict(seed=49,arm=a))) for a in ARMS}
    total = 40*sum(holds.values())
    if total+2000000>25000000 or total+2000000>=39000000:
        raise ValueError('mandatory frontier reservation infeasible')
    return dict(envelopes=rows,episode_micro_usd=holds,frontier_micro_usd=total,
                protected_micro_usd=2000000,total_micro_usd=total+2000000,
                prices={'input_per_million_usd':4,'output_per_million_usd':20,'status':'UNKNOWN','basis':'historical API-equivalent; current authoritative rates unresolved'},
                hidden_input_tokens=826,accounted_output_assumption=512,output_hold=576,
                exact_tokenization_status='UNKNOWN',dispatch_status='UNKNOWN')


def toy_draw(seed,tick,index,salt):
    """Toy model.mjs draw parity only; new task mass has no toy counterpart."""
    mask=0xffffffff
    h=2166136261
    for c in salt:
        h=((h^ord(c))*16777619)&mask
    x=(seed ^ (((tick+1)&mask)*0x9e3779b1&mask) ^ (((index+17)&mask)*0x85ebca6b&mask) ^ h)&mask
    x=((x^(x>>16))*0x7feb352d)&mask
    x=((x^(x>>15))*0x846ca68b)&mask
    return ((x^(x>>16))&mask)/4294967296
