"""Provider adapters. Network/process access happens only in explicit methods."""
from decimal import Decimal,ROUND_CEILING,InvalidOperation
import os
from pathlib import Path
import subprocess
import urllib.request
from uc_core import ROOT,P,PINS,SCHEMAS,canonical,sha,strict_load,maximal_history,render,ModelOutputError
from uc_store import EpisodeFailure,TransportFailure,Stop,read

MODEL='claude-opus-5-5'
BINARY='<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude'
OPTIONS=dict(temperature=.6,top_k=16,num_predict=192,num_ctx=8192)


def identities(root=ROOT):
    models=read(Path(root)/'evidence/local-identity.json')['models']
    if set(models)!=set(PINS):
        raise Stop('identity inventory')
    template_pins={'llama8b':'948af2743fc78a328dcb3b0f5a31b3d75f415840fdb699e8b1235978392ecf85',
                   'qwen7b':'eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175',
                   'qwen1b':'eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175'}
    for actor,item in models.items():
        tag,digest=PINS[actor]
        raw=(Path(root)/item['manifest_file']).read_bytes()
        if item['tag']!=tag or item['digest']!=digest or sha(raw)!=digest:
            raise Stop('manifest identity')
        layers={x['mediaType'].split('.')[-1]:x['digest'] for x in strict_load(raw.decode())['layers']}
        for kind in ('template','system','params'):
            desc=item['layers'].get(kind)
            if (desc is None)!=(kind not in layers):
                raise Stop('missing/extra identity layer')
            if desc is not None:
                data=(Path(root)/desc['file']).read_bytes()
                if sha(data)!=desc['sha256'] or 'sha256:'+sha(data)!=layers[kind]:
                    raise Stop('identity layer hash')
                if kind in ('template','system') and item[kind]!=data.decode():
                    raise Stop('identity layer text')
        if sha(item['template'].encode())!=template_pins[actor] or item['system']!=('' if actor=='llama8b' else 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'):
            raise Stop('pinned template/system')
    return models


def check_identity(actor,show,root=ROOT):
    expected=identities(root)[actor]
    if show.get('template')!=expected['template'] or (show.get('system') or '')!=expected['system']:
        raise Stop('local template/system mismatch')


def local_request(ep,prompt,phase,decision):
    return dict(model=PINS[ep['actor']][0],prompt=prompt,system=P['system'],format='json',stream=False,
                options=dict(OPTIONS,seed=100*ep['seed']+decision))


def claude_command(binary,phase,budget):
    return [str(binary),'--print','--safe-mode','--restricted','--strict-mcp-config','--mcp-config','{"mcpServers":{}}',
            '--tools','','--disable-slash-commands','--no-chrome','--no-session-persistence','--setting-sources','',
            '--settings','{"disableAllHooks":true}',
            '--output-format','json','--model',MODEL,'--effort','medium','--system-prompt',P['system'],
            '--json-schema',canonical(SCHEMAS[phase]),'--max-turns','1','--max-budget-usd',format(budget/1000000,'.6f')]


def clean_env():
    env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
    env.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS='512',CLAUDE_CODE_MAX_RETRIES='0',MAX_STRUCTURED_OUTPUT_RETRIES='0',
               CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
               CLAUDE_CODE_NO_MODEL_FALLBACK='1',DISABLE_AUTOUPDATER='1')
    return env


def http(path,body=None,timeout=10):
    req=urllib.request.Request('http://127.0.0.1:11435'+path,data=None if body is None else canonical(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return response.read()


class Local:
    def __init__(self,root=ROOT):
        self.root=Path(root)

    def preflight(self,actor):
        raw={k:http(path,body) for k,path,body in (
            ('version','/api/version',None),('tags','/api/tags',None),('show','/api/show',{'model':PINS[actor][0]}))}
        value={k:strict_load(v.decode()) for k,v in raw.items()}
        tag,digest=PINS[actor]
        matches=[m for m in value['tags'].get('models',[]) if m.get('name')==tag]
        if len(matches)!=1 or matches[0].get('digest') not in (digest,'sha256:'+digest):
            raise Stop('manifest digest mismatch')
        check_identity(actor,value['show'],self.root)
        contexts=[v for k,v in value['show'].get('model_info',{}).items() if k.endswith('.context_length') and type(v) is int]
        if not contexts or min(contexts)<8192 or not value['version'].get('version'):
            raise Stop('local model/runtime/context metadata')
        max_size=max(len(render(dict(seed=49,framing=f),maximal_history(d),6-d,p).encode()) for f in ('full','fallback') for p in ('action','report') for d in (range(6) if p=='action' else [6]))
        allowance=max_size+len(P['system'].encode())+len(value['show']['template'].encode())+192+512
        if allowance>=8192:
            raise Stop('conservative full-input byte allowance exceeds context')
        return dict(**value,raw_hex={k:v.hex() for k,v in raw.items()},context_byte_allowance=allowance,
                    requested_system=P['system'],default_system=value['show'].get('system',''),exact_prompt_tokens=None)

    def request(self,ep,prompt,phase,decision,bound):
        return local_request(ep,prompt,phase,decision)

    def generate(self,request,work):
        try:
            stdout=http('/api/generate',request,180)
        except Exception as exc:
            return dict(stdout=getattr(exc,'partial',b''),stderr=str(exc).encode(),returncode=None,transport_error='ordinary local transport failure')
        try:
            ps=http('/api/ps')
            running=strict_load(ps.decode())
        except Exception as exc:
            running={'error':str(exc)};ps=b''
        return dict(stdout=stdout,stderr=b'',returncode=0,running=running,running_raw_hex=ps.hex())


class Claude:
    def __init__(self,binary,root=ROOT):
        self.binary=Path(binary).resolve();self.root=Path(root)

    def preflight(self,actor):
        expected=read(self.root/'evidence/cli-offline.json')
        if sha(self.binary.read_bytes())!=expected['binary_sha256']:
            raise Stop('Claude binary hash mismatch')
        # Offline inspection must not become an inference or startup model probe.
        return dict(binary_sha256=expected['binary_sha256'],version=expected['version'],requested_model=MODEL,
                    requested_effort='medium',returned_effort='UNKNOWN',compatibility='UNKNOWN')

    def request(self,ep,prompt,phase,decision,bound):
        return dict(stdin=prompt,argv=claude_command(self.binary,phase,bound['micro_usd']),
                    environment={k:v for k,v in clean_env().items() if k.startswith(('CLAUDE_','MAX_','DISABLE_'))})

    def generate(self,request,work):
        try:
            p=subprocess.run(request['argv'],input=request['stdin'].encode(),capture_output=True,cwd=work,
                             env=clean_env(),timeout=420)
            return dict(stdout=p.stdout,stderr=p.stderr,returncode=p.returncode)
        except subprocess.TimeoutExpired as exc:
            return dict(stdout=exc.stdout or b'',stderr=exc.stderr or b'',returncode=None,transport_error='timeout; ambiguous paid start')
        except OSError as exc:
            return dict(stdout=b'',stderr=str(exc).encode(),returncode=None,transport_error='ambiguous paid start')


def usage(e,actor):
    if actor=='claude':
        u=e.get('usage')
        if type(u) is not dict:
            return None,None
        vals=[u.get(k) for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens')]
        tin=sum(vals) if all(type(v) is int and v>=0 for v in vals) else None
        tout=u.get('output_tokens')
    else:
        tin,tout=e.get('prompt_eval_count'),e.get('eval_count')
    return (tin if type(tin) is int and tin>=0 else None,tout if type(tout) is int and tout>=0 else None)


def cost_micro(tin,tout,e):
    """Output includes reasoning; do not add a second reasoning charge."""
    if tin is None or tout is None:
        raise Stop('missing paid usage; hold retained')
    value=e.get('total_cost_usd')
    if type(value) not in (int,float):
        raise Stop('missing/invalid aggregate paid cost; hold retained')
    try:
        amount=Decimal(str(value))
        if not amount.is_finite() or amount<0:
            raise ValueError()
        reported=int((amount*1000000).to_integral_value(rounding=ROUND_CEILING))
    except (InvalidOperation,ValueError):
        raise Stop('invalid aggregate paid cost') from None
    return max(4*tin+20*tout,reported)


def decode(envelope,raw,ep,phase,bound,fake=False):
    e=envelope;paid=ep['actor']=='claude'
    if type(e) is not dict:
        raise Stop('invalid returned envelope')
    tin,tout=usage(e,ep['actor'])
    if paid:
        cost_micro(tin,tout,e)
        if type(e.get('modelUsage')) is not dict or any(type(v) is not dict for v in e['modelUsage'].values()):
            raise Stop('invalid frontier model usage envelope')
        if set(e['modelUsage'])!={MODEL} or e.get('model',MODEL)!=MODEL:
            raise Stop('frontier identity mismatch')
        if any(v.get('webSearchRequests',0)!=0 for v in e['modelUsage'].values()):
            raise Stop('unexpected frontier web search')
        if e.get('effort','medium')!='medium':
            raise Stop('frontier effort mismatch')
        if e.get('permission_denials') or e.get('tool_calls') or e.get('deferred_tool_use'):
            raise Stop('unexpected tool activity')
        tools=e.get('usage',{}).get('server_tool_use',{})
        if type(tools) is not dict or any(v!=0 for v in tools.values()):
            raise Stop('unexpected server tool activity')
        if tin>bound['input_tokens'] or tout>512:
            raise Stop('frontier token overrun')
        if e.get('input_truncated') or e.get('context_truncated'):
            raise Stop('input truncation')
        turns=e.get('num_turns')
        exhausted=e.get('subtype')=='error_max_structured_output_retries'
        length=e.get('stop_reason') in ('max_tokens','length') or tout==512
        if (e.get('type')!='result' or
            (not exhausted and (e.get('subtype')!='success' or e.get('is_error') is not False)) or
            (exhausted and e.get('is_error') is not True) or
            type(turns) is not int or turns not in (1,2)):
            raise Stop('frontier envelope/turn contract')
        if raw.get('transport_error') or raw.get('returncode') not in ((0,1) if exhausted else (0,)):
            raise Stop('uncertain frontier transport/execution')
        if exhausted:
            raise ModelOutputError('frontier structured-output generation exhausted')
        if length:
            raise EpisodeFailure('frontier output-length reply failure')
        if e.get('stop_reason') not in ('end_turn','tool_use') or (turns==2 and e.get('stop_reason')!='tool_use'):
            raise Stop('frontier stop/turn contract')
        v=e.get('structured_output')
        if type(v) is not dict:
            raise ModelOutputError('missing object structured_output; no result fallback')
    else:
        if e.get('model')!=PINS[ep['actor']][0]:
            raise Stop('returned local identity mismatch')
        # Known integrity failures take precedence over incomplete transport.
        if (tin is not None and tin+192>=8192) or (tout is not None and tout>192):
            raise Stop('local context/usage envelope overrun')
        if e.get('input_truncated') or e.get('context_truncated'):
            raise Stop('input truncation')
        if not fake:
            tag,digest=PINS[ep['actor']]
            if not any(m.get('name')==tag and m.get('digest') in (digest,'sha256:'+digest) and m.get('context_length')==8192 for m in raw.get('running',{}).get('models',[])):
                raise Stop('running model/digest/context mismatch')
        if raw.get('returncode')!=0 or raw.get('transport_error'):
            raise TransportFailure('ordinary local transport failure; no retry')
        if e.get('done') is not True or tin is None or tout is None:
            raise TransportFailure('local incomplete transport: done true and usage required')
        if e.get('done_reason')=='length' or tout==192:
            raise EpisodeFailure('local output-length reply failure')
        if e.get('done_reason')!='stop':
            raise Stop('unknown local stop envelope')
        try:
            v=strict_load(e.get('response'))
        except (ValueError,TypeError,UnicodeError) as exc:
            raise ModelOutputError('invalid model JSON payload: '+str(exc)) from exc
    from uc_core import action,report
    return action(v) if phase=='action' else report(v)
