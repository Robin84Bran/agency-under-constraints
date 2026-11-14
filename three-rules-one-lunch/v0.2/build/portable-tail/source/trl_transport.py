"""Local-only Ollama transport; the sole scientific change is format=schema(quota)."""
import base64
import socket
import urllib.error
import urllib.request
from trl_core import PINS, SYSTEM, canonical, schema, strict_load
from trl_io import Stop

from trl_contract import OPTIONS, ACTORS, request, zero_limit, non_start




def raw_record(data=b'', stderr=b'', returncode=0, **more):
    return dict(stdout_b64=base64.b64encode(data).decode(),
                stderr_b64=base64.b64encode(stderr).decode(),returncode=returncode,**more)


def http(path,body=None,timeout=10):
    req = urllib.request.Request('http://127.0.0.1:11435'+path,
        data=None if body is None else canonical(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return response.read()




class Local:
    def preflight(self,actor):
        if actor not in ACTORS:
            raise Stop('no frontier dispatch in v0.2')
        version = strict_load(http('/api/version').decode())
        tags = strict_load(http('/api/tags').decode())
        show = strict_load(http('/api/show',{'model':PINS[actor][0]}).decode())
        if not any(m.get('name')==PINS[actor][0] and m.get('digest')==PINS[actor][1] for m in tags.get('models',[])) or not show.get('template'):
            raise Stop('model identity/template preflight mismatch')
        return {'version':version,'tags':tags,'show':show,'options':OPTIONS,
                'actual_defaults':show.get('parameters'),'actual_system':show.get('system','')}

    def generate(self,actor,req,work):
        if actor not in ACTORS:
            raise Stop('no frontier dispatch in v0.2')
        try:
            data = http('/api/generate',req,180)
        except urllib.error.HTTPError as exc:
            data = exc.read()
            if exc.code==429 and zero_limit(data):
                return raw_record(data,non_start='USAGE_LIMIT',http_status=429)
            return raw_record(data,returncode=None,transport_error='HTTP '+str(exc.code))
        except (urllib.error.URLError,socket.gaierror) as exc:
            reason = exc.reason if isinstance(exc,urllib.error.URLError) else exc
            if isinstance(reason,socket.gaierror):
                return raw_record(stderr=str(reason).encode(),non_start='DNS',dns_errno=reason.errno)
            raise
        try:
            running = strict_load(http('/api/ps').decode())
        except Exception as exc:
            running = {'error':str(exc)}
        return raw_record(data,running=running)


class Fake:
    """Contract fixture, never real model evidence."""
    def __init__(self, fault=None):
        self.fault, self.calls = fault, []

    def preflight(self,actor):
        return {'kind':'FAKE','actor':actor}

    def generate(self,actor,req,work):
        self.calls.append(req)
        p = strict_load(req['prompt'].split('\n')[-1])
        cells = [((11*p['round']+7*p['role']+j)%48) for j in range(p['quota'])]
        if self.fault=='null': cells=[None]*p['quota']
        e = {'model':PINS[actor][0],'done':True,'done_reason':'stop',
             'response':canonical({'cells':cells}),'prompt_eval_count':300,'eval_count':20}
        if self.fault=='malformed': e['response']='{"cells":[true]}'
        if self.fault=='length': e.update(done_reason='length',eval_count=192)
        if self.fault=='incomplete': e['done']=False
        if self.fault=='unknown-usage': e.pop('eval_count')
        if self.fault=='identity': e['model']='wrong-model'
        if self.fault=='timeout': return raw_record(returncode=None,transport_error='timeout/uncertain start')
        if self.fault=='dns': return raw_record(non_start='DNS',dns_errno=socket.EAI_NONAME)
        if self.fault=='limit':
            return raw_record(canonical({'error':'usage_limit_reached','prompt_eval_count':0,
                'eval_count':0,'total_cost_usd':0}).encode(),non_start='USAGE_LIMIT',http_status=429)
        running={'models':[{'name':PINS[actor][0],'digest':PINS[actor][1],'context_length':8192}]}
        return raw_record(canonical(e).encode(),running=running)


