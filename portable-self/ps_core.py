"""Frozen synthetic console world, renderer and independent strict contracts."""
import hashlib
import itertools
import json
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACTORS = ('qwen7b', 'llama8b', 'qwen1b', 'claude')
ARMS = ('keyed', 'shared', 'discard')
WORLDS = ('different-stable', 'same-stable', 'stale-remap')
DIRECTIONS = ('north', 'east', 'south', 'west')
PINS = {
 'qwen7b': ('qwen2.5:7b', '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 'llama8b': ('llama3.1:8b', '46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'),
 'qwen1b': ('qwen2.5:1.5b', '65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b')}
P = json.loads((ROOT/'config/prompts.json').read_text())
SCHEMAS = {p:json.loads((ROOT/f'config/{p}-schema.json').read_text()) for p in ('write','act')}


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_load(text):
    def pairs(items):
        out = {}
        for k,v in items:
            if k in out:
                raise ValueError('duplicate key: '+k)
            out[k] = v
        return out
    def invalid(v):
        raise ValueError('nonfinite number: '+v)
    def number(v):
        n = float(v)
        if not math.isfinite(n):
            raise ValueError('nonfinite number')
        return n
    if type(text) is not str:
        raise ValueError('JSON text required')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=number)


def validate(value, phase, writable=None):
    if type(value) is not dict:
        raise ValueError('object required')
    if phase == 'write':
        if set(value) != {'slot','note'} or type(value['slot']) is not int or value['slot'] not in range(1,5):
            raise ValueError('invalid write keys/slot')
        if type(value['note']) is not str or not re.fullmatch(r'[ -~]{0,96}', value['note']):
            raise ValueError('invalid note')
        if writable is not None and value['slot'] != writable:
            raise ValueError('write to inaccessible slot')
    elif phase == 'act':
        if set(value) != {'controls'} or type(value['controls']) is not list or len(value['controls']) != 4:
            raise ValueError('invalid action keys/length')
        if any(x is not None and (type(x) is not int or x not in range(1,5)) for x in value['controls']):
            raise ValueError('invalid control')
    else:
        raise ValueError('unknown phase')
    return value


def digest(kind, seed, *parts):
    return sha(('|'.join(map(str,('portable-self-v01',kind,seed,*parts)))).encode())


def fixture(seed, world):
    if type(seed) is not int or seed not in range(100) or world not in WORLDS:
        raise ValueError('unknown world/seed')
    permutations = list(itertools.permutations(range(4)))
    ranked = sorted(permutations,key=lambda p:(digest('map',seed,''.join(map(str,p))),p))[:4]
    maps = [list(ranked[0] if world == 'same-stable' else p) for p in ranked]
    labels = ['c-'+digest('label',seed,j)[:8] for j in range(4)]
    if len(set(labels)) != 4:
        raise ValueError('label collision; no resampling')
    orders = {kind:sorted(range(4),key=lambda j:(digest(kind,seed,j),j)) for kind in ('cal','return')}
    targets = [sorted(range(4),key=lambda d:(digest('target',seed,j,d),d)) for j in range(4)]
    return {'seed':seed,'world':world,'labels':labels,'calibration':maps,
            'returns': [[(v+1)%4 for v in m] for m in maps] if world == 'stale-remap' else maps,
            'cal_order':orders['cal'],'return_order':orders['return'],'targets':targets,
            'slots':[orders['cal'].index(j)+1 for j in range(4)]}


def schedule():
    out = []
    for actor in ACTORS:
        cells = []
        for world in WORLDS:
            n = (10 if world != 'same-stable' else 0) if actor == 'claude' else (100 if world == 'different-stable' and actor != 'qwen1b' else 20)
            cells.extend((s,world,a) for s in range(n) for a in ARMS)
        cells.sort(); random.Random(20261111).shuffle(cells)
        out.extend({'id':f'{actor}-{s:02d}-{w}-{a}','actor':actor,'seed':s,'world':w,'arm':a} for s,w,a in cells)
    return out


class World:
    def __init__(self, ep):
        self.ep = ep
        self.f = fixture(ep['seed'],ep['world'])
        self.notes = ['']*4
        self.index = 0

    def payload(self):
        i = self.index
        if i not in range(8):
            raise ValueError('episode ended')
        write = i < 4
        j = self.f['cal_order'][i] if write else self.f['return_order'][i-4]
        slot = self.f['slots'][j]
        slots = [slot] if self.ep['arm'] == 'keyed' else list(range(1,5))
        return {'console':self.f['labels'][j],'visit':i+1,'mode':'write' if write else 'act',
                'memory':[{'slot':k,'note':self.notes[k-1]} for k in slots],
                'writable_slot':slot if write and self.ep['arm'] == 'keyed' else None,
                'calibration':[[k+1,DIRECTIONS[d]] for k,d in enumerate(self.f['calibration'][j])] if write else None,
                'targets':None if write else [DIRECTIONS[d] for d in self.f['targets'][j]]}

    def step(self, value):
        p = self.payload();validate(value,p['mode'],p['writable_slot'])
        if p['mode'] == 'write' and self.ep['arm'] != 'discard':
            self.notes[value['slot']-1] = value['note']
        self.index += 1


def render(payload):
    return P['instruction']+'\n'+canonical(payload)


def maximal_payload(arm, phase):
    write = phase == 'write'
    return {'console':'c-ffffffff','visit':4 if write else 8,'mode':phase,
            'memory':[{'slot':k,'note':('\\'*96 if arm != 'discard' else '')} for k in ([4] if arm=='keyed' else range(1,5))],
            'writable_slot':4 if write and arm=='keyed' else None,
            'calibration':[[k,'north'] for k in range(1,5)] if write else None,
            'targets':None if write else ['north']*4}


def pad(n):
    return 64*math.ceil(1.10*n/64)


def reservation(arm, phase):
    prompt = render(maximal_payload(arm,phase))
    tin = pad(len(prompt.encode())+len(P['system'].encode())+len(canonical(SCHEMAS[phase]).encode())+826)
    return {'input_tokens':tin,'output_tokens':pad(512),'micro_usd':4*tin+20*pad(512),
            'prompt_bytes':len(prompt.encode())}


def episode_reservation(ep):
    return sum(4*reservation(ep['arm'],phase)['micro_usd'] for phase in ('write','act'))


def literal_map(note):
    """Only a literal 1=north ... convention; other representations UNKNOWN."""
    found = re.findall(r'(?<!\w)([1-4])=(north|east|south|west)(?!\w)',note)
    if len(found)!=4 or len({k for k,v in found})!=4 or len({v for k,v in found})!=4:
        return None
    return {int(k):v for k,v in found}
