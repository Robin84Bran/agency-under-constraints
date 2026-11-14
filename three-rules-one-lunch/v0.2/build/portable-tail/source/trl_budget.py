"""SoS D1 byte sizing and episode holds, in integer microdollars."""
from pathlib import Path
import time
from trl_core import SYSTEM, canonical, schema, render, maximal_receipts, roles, sha
from trl_io import Stop, append, lock, now, read

RESERVE = 1000000
FRONTIER = 25000000
PROJECT_STOP = 39000000
ABSOLUTE = 40000000


def padded(n):
    return ((n*110+6399)//6400)*64


def reservation(prompt, quota):
    tin = padded(len(prompt.encode())+len(SYSTEM.encode())+len(canonical(schema(quota)).encode())+826)
    tout = padded(1024)
    return {'input_tokens':tin,'output_tokens':tout,'micro_usd':4*tin+20*tout}


def maximum(regime):
    return reservation(render(regime,4,0 if regime=='central' else 3,maximal_receipts(4)),3 if regime=='central' else 1)


def episode_hold(regime):
    return maximum(regime)['micro_usd']*4*len(roles(regime))


class Ledger:
    """Each mutation locks, reloads, validates, appends and fsyncs. No stale admission."""
    def __init__(self,path):
        self.path = Path(path)
        self.reload()

    def reload(self):
        self.holds, self.starts, self.settled, self.finished = {}, {}, {}, set()
        self.spent, self.stopped, self.head = 0, False, '0'*64
        if self.path.exists():
            raw = self.path.read_bytes()
            if raw and not raw.endswith(b'\n'):
                raise Stop('torn cost ledger; no dispatch')
            for line in raw.decode().splitlines():
                from trl_core import strict_load
                record = strict_load(line)
                e = record['data']
                if record['previous'] != self.head or record['sha256'] != sha(canonical({'previous':self.head,'data':e}).encode()):
                    raise Stop('cost ledger hash chain broken')
                self.apply(e)
                self.head = record['sha256']

    @property
    def exposure(self):
        return self.spent+sum(self.holds.values())

    def apply(self,e):
        kind, ident = e['event'], e['id']
        if kind == 'reserve':
            amount = e['amount']
            if self.stopped or ident in self.holds or type(amount) is not int or amount < 0 or self.exposure+amount+RESERVE>FRONTIER or self.exposure+amount+RESERVE>=PROJECT_STOP:
                raise Stop('reservation cap, durable stop or duplicate episode')
            self.holds[ident] = amount
        elif kind == 'start':
            ep, amount = e['episode'],e['amount']
            outstanding = sum(v['amount'] for k,v in self.starts.items() if v['episode']==ep and k not in self.settled)
            if self.stopped or ident in self.starts or ep not in self.holds or ep in self.finished or type(amount) is not int or amount < 0 or amount+outstanding>self.holds[ep]:
                raise Stop('invalid/duplicate call allocation')
            self.starts[ident] = e
        elif kind == 'settle':
            if ident not in self.starts or ident in self.settled or type(e['actual']) is not int or e['actual']<0:
                raise Stop('invalid settlement')
            v = self.starts[ident]
            self.holds[v['episode']] -= v['amount']
            self.spent += e['actual']
            self.settled[ident] = e
            # Save actual even if larger than reservation; the stop survives reconstruction.
            self.stopped |= e['actual']>v['amount'] or e.get('overrun',False) or self.exposure+RESERVE>FRONTIER or self.exposure+RESERVE>=PROJECT_STOP or self.spent>=ABSOLUTE
        elif kind == 'unknown':
            if ident not in self.starts or ident in self.settled:
                raise Stop('invalid unknown usage')
            self.stopped = True
        elif kind == 'release':
            if ident not in self.holds or ident in self.finished or any(v['episode']==ident and k not in self.settled for k,v in self.starts.items()):
                raise Stop('release with uncertain call or duplicate terminal')
            self.holds[ident] = 0
            self.finished.add(ident)
        else:
            raise Stop('unknown ledger event')

    def event(self,**e):
        with lock(str(self.path)+'.lock'):
            self.reload()
            e['time'] = now()
            self.apply(e)
            payload = {'previous':self.head,'data':e}
            payload['sha256'] = sha(canonical(payload).encode())
            append(self.path,payload)
            self.head = payload['sha256']
        return self


class ActiveTime:
    """Crash retains the entire remaining session allowance; no free time on resume."""
    def __init__(self,path,cap):
        self.path, self.cap = Path(path),cap
        self.starts, self.ends = {}, {}
        if self.path.exists():
            from trl_core import strict_load
            for line in self.path.read_text().splitlines():
                e = strict_load(line)
                if e['event']=='start' and e['id'] not in self.starts:
                    self.starts[e['id']] = e['allowance']
                elif e['event']=='end' and e['id'] in self.starts and e['id'] not in self.ends and e['seconds']>=0:
                    self.ends[e['id']] = e['seconds']
                else:
                    raise Stop('invalid time ledger')
        self.used = sum(self.ends.get(k,v) for k,v in self.starts.items())
        self.began = None

    def begin(self,ident):
        if ident in self.starts or self.used>=self.cap:
            raise Stop('cumulative active-time cap / uncertain prior session')
        self.ident, self.allowance = ident,self.cap-self.used
        append(self.path,{'event':'start','id':ident,'allowance':self.allowance,'time':now()})
        self.began = time.monotonic()

    def admit(self,timeout):
        if self.began is None or time.monotonic()-self.began+timeout+10>=self.allowance:
            raise Stop('cannot reserve timeout in remaining active time')

    def end(self):
        elapsed = time.monotonic()-self.began
        append(self.path,{'event':'end','id':self.ident,'seconds':elapsed,'time':now()})
        if elapsed>self.allowance:
            raise Stop('active time overrun')
