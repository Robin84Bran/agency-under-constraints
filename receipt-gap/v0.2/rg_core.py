"""Frozen synthetic world and strict public contract. Standard library only."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'config/prompts.json').read_text())
ACTION_SCHEMAS = {t: json.loads((ROOT / ('config/action-' + t + '-schema.json')).read_text())
                  for t in ('plain', 'keyed', 'check')}
SCHEMAS = {'action': ACTION_SCHEMAS['plain'],
           'report': json.loads((ROOT / 'config/report-schema.json').read_text())}
ACTORS = ['qwen7b', 'llama8b', 'qwen1b', 'claude']
PINS = {
 'qwen7b': ('qwen2.5:7b', '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 'llama8b': ('llama3.1:8b', '46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'),
 'qwen1b': ('qwen2.5:1.5b', '65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b')}


class ModelOutputError(ValueError):
    """Frozen model-content rejection: episode technical failure, never repair."""


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_load(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    def invalid(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError('nonfinite JSON number')
        return parsed
    if not isinstance(text, str):
        raise ValueError('text required')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite_float)


def strict_envelope(text, actor):
    """Validate metadata strictly; retain payload JSON violations as model failures.

    Pairs stay lossless until validated, so a duplicate inside structured_output
    cannot either disappear or prevent settlement of independently valid usage.
    Never extract text, repair JSON, or select an alternative payload field.
    """
    class Pairs(list):
        pass

    def convert(value):
        if isinstance(value, Pairs):
            out = {}
            for key, item in value:
                if key in out:
                    raise ValueError('duplicate JSON key')
                out[key] = convert(item)
            return out
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('nonfinite JSON number')
        return value

    try:
        pairs = json.loads(text, object_pairs_hook=Pairs)
        if not isinstance(pairs, Pairs):
            raise ValueError('provider envelope must be an object')
        envelope, payload_error = {}, None
        for key, item in pairs:
            if key in envelope:
                raise ValueError('duplicate envelope key')
            try:
                envelope[key] = convert(item)
            except (ValueError, RecursionError) as exc:
                if actor != 'claude' or key != 'structured_output':
                    raise
                envelope[key], payload_error = None, str(exc)
        return envelope, payload_error
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise ValueError('invalid provider envelope: '+str(exc)) from exc


def action(value, toolkit):
    if toolkit not in ('plain', 'keyed', 'check'):
        raise ValueError('toolkit')
    if type(value) is not dict or set(value) != {'op', 'job', 'key'}:
        raise ModelOutputError('action fields')
    op, j, key = value['op'], value['job'], value['key']
    if op not in ('send', 'status', 'finish'):
        raise ModelOutputError('op')
    if op == 'finish':
        if j is not None or key is not None:
            raise ModelOutputError('finish fields')
    else:
        if type(j) is not int or j not in range(1, 5):
            raise ModelOutputError('job')
        if op == 'status' and (toolkit != 'check' or key is not None):
            raise ModelOutputError('status unavailable or key')
        if key is not None and (op != 'send' or toolkit != 'keyed' or type(key) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,16}', key, re.ASCII) is None):
            raise ModelOutputError('key')
    return value


def report(value):
    if type(value) is not dict or set(value) != {'all_done', 'any_duplicate'}:
        raise ModelOutputError('report fields')
    if any(v is not None and type(v) is not bool for v in value.values()):
        raise ModelOutputError('report boolean/null required')
    return value


def draw(seed, job, attempt, channel):
    """Unsigned Math.imul parity with toy model.mjs; job and attempt zero based."""
    mask = 0xffffffff
    x = (seed ^ (((job + 1) * 0x9e3779b1) & mask) ^ (((attempt + 1) * 0x85ebca6b) & mask) ^ (((channel + 1) * 0xc2b2ae35) & mask)) & mask
    x = ((x ^ (x >> 16)) * 0x7feb352d) & mask
    x = ((x ^ (x >> 15)) * 0x846ca68b) & mask
    return ((x ^ (x >> 16)) & mask) / 4294967296


class World:
    def __init__(self, seed, toolkit, loss, request_loss=.2):
        self.seed, self.toolkit, self.loss, self.request_loss = seed, toolkit, loss, request_loss
        self.counts, self.attempts, self.keys = [0]*4, [0]*4, {}
        self.events, self.history, self.decisions, self.ended = [], [], 0, False

    def step(self, value):
        action(value, self.toolkit)
        if self.ended or self.decisions >= 10:
            raise ValueError('action horizon ended')
        self.decisions += 1
        if value['op'] == 'finish':
            self.ended = True
            self.events.append({'action': value, 'observation': None})
            return None
        j, key = value['job']-1, value['key']
        hidden = {}
        if value['op'] == 'status':
            result = 'done' if self.counts[j] else 'not_done'
        else:
            n = self.attempts[j]
            self.attempts[j] += 1
            lost = draw(self.seed, j, n, 0) < self.request_loss
            receipt_lost = draw(self.seed, j, n, 1) < self.loss
            processed = 'dropped'
            if not lost:
                if key is not None and key in self.keys:
                    processed = 'suppressed' if self.keys[key] == j else 'conflict'
                else:
                    self.counts[j] += 1
                    if key is not None:
                        self.keys[key] = j
                    processed = 'new'
            result = 'unknown' if lost or receipt_lost else ('conflict' if processed == 'conflict' else 'ok')
            hidden = {'attempt': n, 'request_lost': lost, 'receipt_lost': receipt_lost, 'processed': processed}
        observation = {'result': result}
        self.history.append({'action': value, 'observation': observation})
        self.events.append({'action': value, 'observation': observation, **hidden})
        if self.decisions == 10:
            self.ended = True
        return observation


def render(ep, history, remaining, phase):
    # Deliberate whitelist: hidden state never enters the prompt.
    return canonical({'instruction': P['common']+'\n'+P[phase], 'task': P[ep['framing']],
                      'tools': P[ep['toolkit']], 'remaining': remaining, 'history': history})


def padded(n):
    return ((n * 110 + 6399) // 6400) * 64


def schema_for(phase, toolkit='plain'):
    if phase == 'action':
        return ACTION_SCHEMAS[toolkit]
    if phase != 'report':
        raise ValueError('unknown phase')
    return SCHEMAS['report']


def reserve(prompt, phase, toolkit='plain'):
    tin = padded(len(prompt.encode()) + len(P['system'].encode()) + len(canonical(schema_for(phase, toolkit)).encode()) + 826)
    tout = padded(512)
    return {'input_tokens': tin, 'output_tokens': tout, 'micro_usd': 4*tin+20*tout}


def maximal_history(depth):
    return [{'action': {'op':'send','job':4,'key':'X'*16}, 'observation':{'result':'not_done'}} for _ in range(depth)]


def episode_reservation(ep):
    rows = [reserve(render(ep, maximal_history(d), 10, 'action'), 'action', ep['toolkit']) for d in range(10)]
    rows.append(reserve(render(ep, maximal_history(10), 10, 'report'), 'report', ep['toolkit']))
    return sum(r['micro_usd'] for r in rows)
