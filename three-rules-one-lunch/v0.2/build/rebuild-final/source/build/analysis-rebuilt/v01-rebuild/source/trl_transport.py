"""Lazy live transports; fake transport is the only builder-executed path."""
import base64
import os
from pathlib import Path
import subprocess
import urllib.request
from trl_core import ROOT, PINS, SYSTEM, canonical, schema, strict_load, action, sha
from trl_io import Stop, read
from trl_validation import stdout, usage, cost, validate

CLAUDE_BIN = '<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude'
MODEL = 'claude-opus-5-5'
OPTIONS = {'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192}


def controls():
    return {'CLAUDE_CODE_MAX_OUTPUT_TOKENS':'1024','CLAUDE_CODE_MAX_RETRIES':'0',
        'MAX_STRUCTURED_OUTPUT_RETRIES':'0','CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES':'0',
        'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','DISABLE_AUTOUPDATER':'1',
        'CLAUDE_CODE_NO_MODEL_FALLBACK':'1'}


def clean_env():
    # No API keys, provider overrides, arbitrary MAX_TOKENS or env prompt injection.
    # Subscription auth remains in its existing store. HOME is preserved, never reassigned.
    e = {k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}
    e.update(controls())
    return e


def claude_command(binary,quota,budget):
    return [str(binary),'--print','--safe-mode','--restricted','--strict-mcp-config',
        '--mcp-config','{"mcpServers":{}}','--tools','','--disable-slash-commands','--no-chrome',
        '--no-session-persistence','--setting-sources','','--settings','{"disableAllHooks":true}',
        '--output-format','json','--json-schema',canonical(schema(quota)),
        '--model',MODEL,'--effort','medium','--system-prompt',SYSTEM,'--max-turns','1',
        '--max-budget-usd',format(budget/1000000,'.6f')]


def request(actor,prompt,quota,seed,bound):
    if actor == 'claude':
        return {'stdin_utf8':prompt,'argv':claude_command(CLAUDE_BIN,quota,bound['micro_usd']),
                'environment_controls':controls(),'seed_supported':False,'timeout_seconds':420}
    return {'model':PINS[actor][0],'prompt':prompt,'system':SYSTEM,'format':'json','stream':False,
            'options':dict(OPTIONS,seed=seed)}


def raw_record(stdout,stderr=b'',returncode=0,**more):
    return dict(stdout_b64=base64.b64encode(stdout).decode(),stderr_b64=base64.b64encode(stderr).decode(),returncode=returncode,**more)



def http(path,body=None,timeout=10):
    req = urllib.request.Request('http://127.0.0.1:11435'+path,
        data=None if body is None else canonical(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read()


class Local:
    def preflight(self,actor):
        version = strict_load(http('/api/version').decode())
        tags = strict_load(http('/api/tags').decode())
        show = strict_load(http('/api/show',{'model':PINS[actor][0]}).decode())
        if not any(m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] for m in tags.get('models',[])) or not show.get('template'):
            raise Stop('model identity/template preflight mismatch')
        return {'version':version,'tags':tags,'show':show,'options':OPTIONS,'actual_defaults':show.get('parameters'),'actual_system':show.get('system','')}

    def generate(self,actor,req,work):
        raw = http('/api/generate',req,180)
        try:
            running = strict_load(http('/api/ps').decode())
        except Exception as exc:
            running = {'error':str(exc)}
        return raw_record(raw,running=running)


class Claude:
    def __init__(self,root=ROOT):
        self.root = Path(root)

    def preflight(self,actor):
        contract = read(self.root/'evidence/cli-contract.json')
        from trl_collect import readiness
        readiness(self.root)
        binary = Path(CLAUDE_BIN).resolve()
        if sha(binary.read_bytes())!=contract['binary_sha256']:
            raise Stop('CLI binary hash drift')
        return {'binary_sha256':contract['binary_sha256'],'returned_effort':'UNKNOWN'}

    def generate(self,actor,req,work):
        if type(req) is not dict or not {'argv','stdin_utf8'}.issubset(req) or type(req['argv']) is not list:
            raise Stop('unfrozen CLI request')
        self.preflight(actor)  # Mandatory even if called outside harness.
        if req['argv']!=claude_command(CLAUDE_BIN,3 if '"maxItems":3' in req['argv'][req['argv'].index('--json-schema')+1] else 1,
                                               int(round(float(req['argv'][-1])*1000000))):
            raise Stop('unfrozen CLI request')
        try:
            p = subprocess.run(req['argv'],input=req['stdin_utf8'].encode(),capture_output=True,
                cwd=work,env=clean_env(),timeout=420)
            return raw_record(p.stdout,p.stderr,p.returncode)
        except subprocess.TimeoutExpired as exc:
            return raw_record(exc.stdout or b'',exc.stderr or b'',None,transport_error='timeout/uncertain start')


class Fake:
    """Deterministic contract fixture; never a model result."""
    def __init__(self,fault=None):
        self.fault,self.calls = fault,[]

    def preflight(self,actor):
        return {'kind':'FAKE','actor':actor}

    def generate(self,actor,req,work):
        self.calls.append(req)
        prompt = req['stdin_utf8'] if actor=='claude' else req['prompt']
        p = strict_load(prompt.split('\n')[-1])
        cells = [((11*p['round']+7*p['role']+j)%48) for j in range(p['quota'])]
        if self.fault=='null':
            cells = [None]*p['quota']
        v = {'cells':cells}
        if actor=='claude':
            e = {'type':'result','subtype':'success','is_error':False,'num_turns':1,'stop_reason':'tool_use',
                'permission_denials':[],'structured_output':v,'result':'ignored prose',
                'usage':{'input_tokens':300,'cache_read_input_tokens':0,'cache_creation_input_tokens':0,
                         'output_tokens':20,'server_tool_use':{'web_search_requests':0,'web_fetch_requests':0}},
                'modelUsage':{MODEL:{'inputTokens':300,'outputTokens':20,'cacheReadInputTokens':0,
                                   'cacheCreationInputTokens':0,'webSearchRequests':0}}}
        else:
            e = {'model':PINS[actor][0],'done':True,'done_reason':'stop','response':canonical(v),'prompt_eval_count':300,'eval_count':20}
        if self.fault=='malformed':
            if actor=='claude': e['structured_output']={'cells':[True]*p['quota']}
            else: e['response']='{"cells":[true]}'
        if self.fault=='usage':
            if actor=='claude': del e['usage']['output_tokens']
            else: del e['eval_count']
        if self.fault=='overrun' and actor=='claude':
            e['usage']['output_tokens']=2048
            e['modelUsage'][MODEL]['outputTokens']=2048
        if self.fault=='timeout':
            return raw_record(b'partial',b'timeout',None,transport_error='timeout/uncertain start')
        running = {'models':[{'name':PINS[actor][0],'digest':PINS[actor][1],'context_length':8192}]} if actor!='claude' else {}
        return raw_record(canonical(e).encode(),running=running)
