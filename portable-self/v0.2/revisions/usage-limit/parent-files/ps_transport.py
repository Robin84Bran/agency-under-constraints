"""Explicit-only transports; imports and offline tests never call a model."""
import os
import json
import math
import base64
from pathlib import Path
import subprocess
import urllib.request
from decimal import Decimal, ROUND_CEILING
from ps_core import ROOT, P, PINS, SCHEMAS, canonical, sha, strict_load, validate
from ps_io import Stop, EpisodeFailure, TransportFailure, read

CLAUDE_BIN='<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude'
MODEL='claude-opus-5-5'

def clean_env():
    env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
    env.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS='512',CLAUDE_CODE_MAX_RETRIES='0',MAX_STRUCTURED_OUTPUT_RETRIES='0',
               CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
               CLAUDE_CODE_NO_MODEL_FALLBACK='1',DISABLE_AUTOUPDATER='1')
    return env

def claude_command(binary,phase,budget):
    return [str(binary),'--print','--safe-mode','--restricted','--strict-mcp-config','--mcp-config','{"mcpServers":{}}',
            '--tools','','--disable-slash-commands','--no-chrome','--no-session-persistence','--setting-sources','',
            '--output-format','json','--model',MODEL,'--effort','medium','--system-prompt',P['system'],
            '--json-schema',canonical(SCHEMAS[phase]),'--max-turns','2','--max-budget-usd',f'{budget/1000000:.6f}']

def local_request(ep,prompt,index):
    phase='write' if index<4 else 'act'
    # Intentionally omit system/template/raw: retain exact manifest defaults.
    return {'model':PINS[ep['actor']][0],'prompt':prompt,'format':SCHEMAS[phase],'stream':False,
            'options':{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192,'seed':1000*ep['seed']+index+1}}

def identity(root):
    models=read(Path(root)/'evidence/local-identity.json')['models']
    if set(models)!=set(PINS): raise Stop('identity inventory differs from pins')
    for actor,(tag,digest) in PINS.items():
        item=models[actor];raw=(Path(root)/item['manifest_file']).read_bytes()
        if item['tag']!=tag or item['digest']!=digest or sha(raw)!=digest: raise Stop('manifest hash mismatch')
        layers={x['mediaType'].split('.')[-1]:x['digest'] for x in strict_load(raw.decode())['layers']}
        for kind in ('template','system','params'):
            descriptor=item['layers'].get(kind)
            if (descriptor is None)!=(kind not in layers): raise Stop('missing/extra identity layer')
            if descriptor:
                data=(Path(root)/descriptor['file']).read_bytes()
                if 'sha256:'+sha(data)!=layers[kind] or sha(data)!=descriptor['sha256']: raise Stop('identity layer hash mismatch')
                if kind in ('template','system') and item[kind]!=data.decode(): raise Stop('template/system bytes mismatch')
        if 'system' not in layers and item['system']!='': raise Stop('invented default system')
    return models

def http(path,body=None,timeout=10,raw_bytes=False):
    data=None if body is None else canonical(body).encode()
    req=urllib.request.Request('http://127.0.0.1:11435'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r: data=r.read()
    return data if raw_bytes else data.decode('utf8')

class Local:
    def __init__(self,root): self.root=Path(root)
    def preflight(self,actor):
        expected=identity(self.root)[actor];tag,digest=PINS[actor]
        ev={'version':strict_load(http('/api/version')),'tags':strict_load(http('/api/tags')),'show':strict_load(http('/api/show',{'model':tag}))}
        if ev['version'].get('version')!='0.33.3': raise Stop('Ollama version differs from pinned 0.33.3')
        if {m['name']:m['digest'] for m in ev['tags']['models']}.get(tag)!=digest: raise Stop('live manifest mismatch')
        shown=ev['show']
        if shown.get('template')!=expected['template'] or (shown.get('system') or '')!=expected['system']: raise Stop('live template/system mismatch')
        return ev
    def request(self,ep,prompt,phase,bound,index): return local_request(ep,prompt,index)
    def generate(self,request,work):
        raw=http('/api/generate',request,180,raw_bytes=True)
        try: ps=strict_load(http('/api/ps'))
        except Exception as e: ps={'error':str(e)}
        return {'stdout':raw.decode('utf8',errors='replace'),'stdout_b64':base64.b64encode(raw).decode(),'stderr':'','returncode':0,'running':ps}

class Claude:
    def __init__(self,root,binary): self.root=Path(root);self.binary=Path(binary).resolve()
    def preflight(self,actor):
        ev=read(self.root/'evidence/cli-contract.json')
        if sha(self.binary.read_bytes())!=ev['binary_sha256']: raise Stop('CLI binary hash changed')
        version=subprocess.check_output([str(self.binary),'--version'],timeout=30)
        helptext=subprocess.check_output([str(self.binary),'--help'],timeout=30)
        if version!=(self.root/'evidence/claude-version.txt').read_bytes() or helptext!=(self.root/'evidence/claude-help.txt').read_bytes(): raise Stop('CLI metadata changed')
        return {'binary_sha256':ev['binary_sha256'],'version':version.decode(),'requested_effort':'medium','reported_effort':'UNKNOWN',
                'schema_turns':[1,2],'hidden_token_allowance':826,'live_contract':'UNKNOWN until first frozen scored call'}
    def request(self,ep,prompt,phase,bound,index):
        return {'argv':claude_command(self.binary,phase,bound['micro_usd']),'stdin':prompt,
                'environment_controls':{k:v for k,v in clean_env().items() if k not in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}}
    def generate(self,request,work):
        # Empty temporary cwd avoids project discovery; safe-mode disables customizations.
        import tempfile
        with tempfile.TemporaryDirectory(prefix='portable-self-') as cwd:
            try:
                p=subprocess.run(request['argv'],input=request['stdin'].encode(),capture_output=True,cwd=cwd,env=clean_env(),timeout=420)
                return {'stdout':p.stdout.decode('utf8',errors='replace'),'stderr':p.stderr.decode('utf8',errors='replace'),
                        'stdout_b64':base64.b64encode(p.stdout).decode(),'stderr_b64':base64.b64encode(p.stderr).decode(),'returncode':p.returncode}
            except subprocess.TimeoutExpired as e:
                return {'stdout':(e.stdout or b'').decode('utf8',errors='replace'),'stderr':(e.stderr or b'').decode('utf8',errors='replace'),
                        'stdout_b64':base64.b64encode(e.stdout or b'').decode(),'stderr_b64':base64.b64encode(e.stderr or b'').decode(),
                        'returncode':None,'transport_error':'timeout; uncertain paid outcome'}

def usage(envelope,actor):
    if actor=='claude':
        u=envelope.get('usage',{});vals=[u.get(k) for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens')]
        tin=sum(vals) if all(type(v) is int and v>=0 for v in vals) else None
        tout=u.get('output_tokens')
    else: tin,tout=envelope.get('prompt_eval_count'),envelope.get('eval_count')
    return (tin if type(tin) is int and tin>=0 else None,tout if type(tout) is int and tout>=0 else None)

def cost_micro(tin,tout,envelope):
    cost=4*tin+20*tout;reported=envelope.get('total_cost_usd')
    if reported is not None:
        if isinstance(reported,bool): raise Stop('invalid reported cost')
        v=Decimal(str(reported))
        if not v.is_finite() or v<0: raise Stop('invalid reported cost')
        cost=max(cost,int((v*1000000).to_integral_value(rounding=ROUND_CEILING)))
    return cost

def provider_envelope(text, actor):
    """Keep strict metadata/accounting usable when only schema-tool content is bad."""
    class Pairs(list): pass
    class Nonfinite: pass
    tree=json.loads(text,object_pairs_hook=Pairs,parse_constant=lambda _:Nonfinite())
    def unpack(node):
        if isinstance(node,Pairs):
            result={}
            for key,value in node:
                if key in result: raise ValueError('duplicate key: '+key)
                result[key]=unpack(value)
            return result
        if isinstance(node,list): return [unpack(v) for v in node]
        if isinstance(node,Nonfinite) or (isinstance(node,float) and not math.isfinite(node)):
            raise ValueError('nonfinite number')
        return node
    if not isinstance(tree,Pairs): raise ValueError('provider envelope must be object')
    result={};payload_error=None
    for key,value in tree:
        if key in result: raise ValueError('duplicate envelope key: '+key)
        if actor=='claude' and key=='structured_output':
            try: result[key]=unpack(value)
            except ValueError as exc: result[key]=None;payload_error=str(exc)
        else: result[key]=unpack(value)
    return result,payload_error


def positive_activity(value):
    """Nested activity counters: zero-count summaries do not imply tool activity."""
    if isinstance(value,dict): return any(positive_activity(v) for v in value.values())
    if isinstance(value,list): return any(positive_activity(v) for v in value)
    return isinstance(value,(int,float)) and value>0


def decode(raw,ep,payload,bound,fake=False):
    paid=ep['actor']=='claude'
    if payload.get('mode') not in ('write','act'): raise Stop('unknown harness phase')
    for field in ('stdout','stderr'):
        if field+'_b64' in raw:
            try: original=base64.b64decode(raw[field+'_b64'],validate=True).decode('utf8')
            except (ValueError,UnicodeDecodeError): raise Stop('non-UTF8 transport bytes retained') from None
            if original!=raw[field]: raise Stop('transport text differs from raw bytes')
    # Paid schema-tool exhaustion has a known terminal CLI exit code 1.
    if raw.get('transport_error'):
        raise (Stop if paid else TransportFailure)('transport failure or uncertain outcome')
    if raw.get('returncode')!=0 and not (paid and raw.get('returncode')==1):
        raise (Stop if paid else TransportFailure)('transport failure or uncertain outcome')
    try: e,payload_error=provider_envelope(raw['stdout'],ep['actor'])
    except (ValueError,KeyError,TypeError):
        raise (Stop if paid else TransportFailure)('provider envelope is not strict JSON object') from None
    tin,tout=usage(e,ep['actor'])
    if paid:
        if type(e.get('modelUsage')) is not dict or set(e['modelUsage'])!={MODEL}: raise Stop('frontier identity mismatch')
        if e.get('effort','medium')!='medium': raise Stop('frontier effort conflict')
        turns=e.get('num_turns');reason=e.get('stop_reason')
        exhausted=e.get('subtype')=='error_max_structured_output_retries'
        length=reason in ('max_tokens','length')
        if (e.get('type')!='result' or type(turns) is not int or turns not in (1,2) or
            (exhausted and (e.get('is_error') is not True or raw['returncode'] not in (0,1))) or
            (not exhausted and (e.get('subtype')!='success' or e.get('is_error') is not False or raw['returncode']!=0)) or
            (not exhausted and not length and (reason not in ('end_turn','tool_use') or (turns==2 and reason!='tool_use')))):
            raise Stop('frontier success/turn envelope mismatch')
        if e.get('permission_denials',[]) or e.get('deferred_tool_use') or e.get('tool_calls') or e.get('tool_use'):
            raise Stop('unexpected tool activity')
        if positive_activity(e.get('subagent_stats',{})) or positive_activity(e.get('usage',{}).get('server_tool_use',{})):
            raise Stop('unexpected subagent/server tool activity')
        for m in e['modelUsage'].values():
            if not isinstance(m,dict) or m.get('webSearchRequests',0)!=0: raise Stop('unexpected model tool usage')
        if tin is None or tout is None: raise Stop('missing frontier usage')
        if tin>bound['input_tokens'] or tout>bound['output_tokens']: raise Stop('frontier token reservation overrun')
        if exhausted: raise EpisodeFailure('completed schema-output exhaustion')
        if length: raise EpisodeFailure('completed output-length stop')
        if payload_error: raise EpisodeFailure('invalid structured_output JSON: '+payload_error)
        v=e.get('structured_output')
        if type(v) is not dict: raise EpisodeFailure('structured_output object required; no prose fallback')
    else:
        if e.get('model')!=PINS[ep['actor']][0]: raise Stop('local identity mismatch')
        if tin is not None and tin+192>=8192: raise Stop('input sufficiency cannot be established')
        if e.get('truncated') is True or e.get('input_truncated') is True: raise Stop('input truncated')
        if not fake and not any(m.get('name')==PINS[ep['actor']][0] and m.get('digest')==PINS[ep['actor']][1] and m.get('context_length')==8192 for m in raw.get('running',{}).get('models',[])):
            raise Stop('running model digest/context mismatch')
        if tout is not None and tout>192: raise Stop('local output reservation overrun')
        if e.get('done') is not True or tout is None or tin is None:
            raise TransportFailure('local transport incomplete: done/usage')
        if e.get('done_reason')=='length': raise EpisodeFailure('completed output-length stop')
        if e.get('done_reason')!='stop': raise Stop('unexpected local stop envelope')
        try: v=strict_load(e['response'])
        except (ValueError,KeyError,TypeError) as exc: raise EpisodeFailure('invalid inner JSON: '+str(exc)) from None
    try: validate(v,payload['mode'],payload['writable_slot'])
    except ValueError as exc: raise EpisodeFailure(str(exc)) from None
    return v,{'input_tokens':tin,'output_tokens':tout,'reported_effort':e.get('effort','UNKNOWN'),
              'stop_reason':e.get('stop_reason',e.get('done_reason')),'num_turns':e.get('num_turns')}
