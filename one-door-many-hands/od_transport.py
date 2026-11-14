"""Lazy transports. Imports never start a provider or contact a service."""
import base64
import os
from pathlib import Path
import subprocess
import urllib.request
from od_core import ROOT,PINS,MODEL,SYSTEM,SCHEMA_TEXT,canonical,strict_load,sha,payload,oracle
from od_io import Stop,read

from od_contract import CLAUDE_BIN,OPTIONS,controls,claude_command,request

def clean_env():
    e={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')};e.update(controls());return e

def raw_record(out,err=b'',returncode=0,**more):
    return dict(stdout_b64=base64.b64encode(out).decode(),stderr_b64=base64.b64encode(err).decode(),returncode=returncode,**more)

from od_identity import identity,check_identity,verify_preflight

def http(path,body=None,timeout=10):
    req=urllib.request.Request('http://127.0.0.1:11435'+path,data=None if body is None else canonical(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()

class Local:
    def __init__(self,root=ROOT): self.root=Path(root)
    def preflight(self,actor):
        version=strict_load(http('/api/version'));tags=strict_load(http('/api/tags'));show=strict_load(http('/api/show',{'model':PINS[actor][0]}))
        return {'version':version,'tags':tags,'show':show,'options':OPTIONS,'input_completeness':'UNKNOWN'}
    def generate(self,ep,req,work):
        raw=http('/api/generate',req,180)
        try: running=strict_load(http('/api/ps'))
        except Exception as exc: running={'error':str(exc)}
        return raw_record(raw,running=running)

class Claude:
    def __init__(self,root=ROOT,binary=CLAUDE_BIN): self.root=Path(root);self.binary=Path(binary)
    def preflight(self,actor):
        c=read(self.root/'evidence/cli-contract.json')
        if str(self.binary)!=CLAUDE_BIN: raise Stop('CLI path drift')
        actual=sha(self.binary.resolve().read_bytes())
        # Hash binds the installed version and source-inspected controls without a model probe.
        return {'binary_sha256':actual,'version':c['version'] if actual==c['binary_sha256'] else 'UNKNOWN','requested_effort':'medium','returned_effort':'UNKNOWN'}
    def generate(self,ep,req,work):
        verify_preflight(self.root,'claude',self.preflight('claude'))
        if req['argv']!=claude_command(self.binary,int(round(float(req['argv'][-1])*1000000))) or req['environment_controls']!=controls(): raise Stop('unfrozen CLI request')
        try:
            p=subprocess.run(req['argv'],input=req['stdin_utf8'].encode(),capture_output=True,cwd=work,env=clean_env(),timeout=300)
            return raw_record(p.stdout,p.stderr,p.returncode)
        except subprocess.TimeoutExpired as exc: return raw_record(exc.stdout or b'',exc.stderr or b'',None,transport_error='timeout/uncertain start')

class Fake:
    """Synthetic deterministic fixtures, never empirical model results."""
    def __init__(self,fault=None): self.fault=fault;self.calls=[]
    def preflight(self,actor): return {'kind':'FAKE','actor':actor}
    def generate(self,ep,req,work):
        self.calls.append(ep['id']);p=payload(ep)
        n=oracle(p['target'],p['failure_percent'],p['door_limit'],p['mode'])[2][0]
        v={'fleet':None if self.fault=='null' else n}
        if self.fault=='invalid': v={'fleet':True}
        actor=ep['actor']
        if actor=='claude':
            e={'type':'result','subtype':'success','is_error':False,'num_turns':2,'stop_reason':'tool_use','permission_denials':[],
               'structured_output':v,'result':'ignored prose','total_cost_usd':.002,
               'usage':{'input_tokens':100,'cache_read_input_tokens':100,'cache_creation_input_tokens':50,'output_tokens':20,
                        'server_tool_use':{'web_search_requests':0,'web_fetch_requests':0}},
               'modelUsage':{MODEL:{'inputTokens':100,'cacheReadInputTokens':100,'cacheCreationInputTokens':50,'outputTokens':20,'webSearchRequests':0}}}
            if self.fault=='missing_payload': del e['structured_output']
            if self.fault=='cost': del e['total_cost_usd']
            if self.fault=='overrun': e['total_cost_usd']=26
        else:
            e={'model':PINS[actor][0],'done':True,'done_reason':'stop','response':canonical(v),'prompt_eval_count':300,'eval_count':20}
            if self.fault=='length': e['done_reason']='length'
            if self.fault=='done': e['done']=False
            if self.fault=='usage': del e['eval_count']
            if self.fault=='input': e['prompt_eval_count']=8100
            if self.fault=='identity': e['model']='other'
        if self.fault=='timeout': return raw_record(b'partial',b'timeout',None,transport_error='timeout/uncertain start')
        running={'models':[{'name':PINS[actor][0],'digest':PINS[actor][1],'context_length':8192}]} if actor!='claude' else {}
        return raw_record(canonical(e).encode(),running=running)
