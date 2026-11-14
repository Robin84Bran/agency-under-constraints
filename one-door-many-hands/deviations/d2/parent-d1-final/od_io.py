"""Create-once records and hash-chained append-only logs with retained prefixes."""
import contextlib
import datetime as dt
import fcntl
import os
from pathlib import Path
import time
from od_core import canonical, strict_load, sha

class Stop(RuntimeError): pass

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def read(path): return strict_load(Path(path).read_bytes())
def syncdir(path):
    fd=os.open(str(path),os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def save_bytes(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink(): raise Stop('symlink output')
    with path.open('xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
    syncdir(path.parent)

def save(path,value): save_bytes(path,(canonical(value)+'\n').encode())

@contextlib.contextmanager
def lock(base):
    base=Path(base);base.mkdir(parents=True,exist_ok=True)
    if (base/'collector.lock').is_symlink(): raise Stop('symlink lock')
    with (base/'collector.lock').open('a') as f:
        try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise Stop('concurrent collector rejected')
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)

class Log:
    """Each append commits a byte-prefix hash in a distinct create-once checkpoint.

    A crash between log fsync and checkpoint is a fail-closed integrity stop;
    truncation/rewrite is detected even if the surviving JSON lines are valid.
    """
    def __init__(self,path):
        self.path=Path(path);self.checkpoints=self.path.with_suffix(self.path.suffix+'.prefixes')
        if self.path.is_symlink() or self.checkpoints.is_symlink(): raise Stop('symlink ledger')
        self.data=self.path.read_bytes() if self.path.exists() else b''
        self.events=[]; self.digest='0'*64; pos=0
        for i,line in enumerate(self.data.splitlines(keepends=True),1):
            if not line.endswith(b'\n'): raise Stop('torn log')
            e=strict_load(line); body=dict(e); digest=body.pop('sha256')
            if e['sequence']!=i or e['previous']!=self.digest or sha(canonical(body).encode())!=digest: raise Stop('log chain changed')
            pos+=len(line); cp=read(self.checkpoints/f'{i:08d}.json')
            if cp!={'bytes':pos,'sha256':sha(self.data[:pos])}: raise Stop('log prefix changed')
            self.events.append(e['value']);self.digest=digest
        actual={p.name for p in self.checkpoints.iterdir()} if self.checkpoints.exists() else set()
        if actual!={f'{i:08d}.json' for i in range(1,len(self.events)+1)}: raise Stop('log truncated or extra prefix checkpoint')
    def append(self,value):
        # Detect in-process modification as well as restart drift.
        current=self.path.read_bytes() if self.path.exists() else b''
        if current!=self.data: raise Stop('log changed since admission')
        body={'sequence':len(self.events)+1,'previous':self.digest,'value':value}
        digest=sha(canonical(body).encode());line=(canonical(dict(body,sha256=digest))+'\n').encode()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('ab') as f: f.write(line);f.flush();os.fsync(f.fileno())
        syncdir(self.path.parent)
        new=self.data+line
        save(self.checkpoints/f'{len(self.events)+1:08d}.json',{'bytes':len(new),'sha256':sha(new)})
        self.data=new;self.events.append(value);self.digest=digest

class Ledger:
    def __init__(self,path):
        self.log=Log(path);self.holds={};self.spent=0;self.reservations={};self.settlements={}
        for e in self.log.events: self.apply(e)
    @property
    def exposure(self): return self.spent+sum(self.holds.values())
    def apply(self,e):
        op,ident=e['event'],e['id']
        if op=='reserve':
            amount=e['amount']
            if type(amount) is not int or amount<=0 or ident in self.reservations or self.exposure+amount+1000000>25000000 or self.exposure+amount+1000000>=39000000: raise Stop('rolling reservation/cap/duplicate gate')
            self.reservations[ident]=amount;self.holds[ident]=amount
        elif op=='settle':
            amount=e['actual']
            if type(amount) is not int or amount<0 or ident not in self.holds or ident in self.settlements: raise Stop('invalid settlement')
            self.spent+=amount;self.holds[ident]=0;self.settlements[ident]=amount
        else: raise Stop('unknown ledger event')
    def event(self,**e):
        e['time']=now();self.apply(e);self.log.append(e)

class ActiveTime:
    def __init__(self,path,cap):
        self.log=Log(path);self.cap=cap;self.holds={};self.settled={};self.breaches=set()
        for e in self.log.events:
            ident=e['id'];seconds=e['seconds']
            if type(seconds) not in (int,float) or not 0<=seconds<float('inf'): raise Stop('invalid timer amount')
            if e['event']=='start' and ident not in self.holds:
                if self.charged+seconds>cap: raise Stop('timer admission exceeded frozen cap')
                self.holds[ident]=seconds
            elif e['event']=='settle' and ident in self.holds and ident not in self.settled:
                self.settled[ident]=seconds
                if self.charged>cap: self.breaches.add(ident)
            else: raise Stop('invalid timer log')
        self.pending=time.monotonic()
    @property
    def charged(self): return sum(self.settled.get(k,v) for k,v in self.holds.items())
    def begin(self,ident,seconds):
        overhead=max(0,time.monotonic()-self.pending)
        if ident in self.holds or self.charged+overhead+seconds>self.cap: raise Stop('cumulative active time limit')
        self.log.append({'event':'start','id':ident,'seconds':seconds+overhead,'time':now()});self.holds[ident]=seconds+overhead
        return self.pending
    def end(self,ident,began):
        elapsed=max(0,time.monotonic()-began)
        self.log.append({'event':'settle','id':ident,'seconds':elapsed,'time':now()});self.settled[ident]=elapsed;self.pending=time.monotonic()
        if self.charged>self.cap: self.breaches.add(ident)

def durable_stop(base,reason):
    base=Path(base)
    path=base/('STOP-after-usage-clearance.json' if (base/'usage-limit-clearance.json').exists() else 'STOP.json')
    if not path.exists(): save(path,{'time':now(),'reason':str(reason)})
