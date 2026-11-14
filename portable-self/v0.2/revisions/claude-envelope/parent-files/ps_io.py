"""Create-once evidence and append-only, externally anchored prefix journals."""
import contextlib
import datetime as dt
import fcntl
import hashlib
import os
from pathlib import Path
from ps_core import canonical, sha, strict_load

class Stop(RuntimeError):
    pass
class UsageLimitPause(RuntimeError):
    """Definite non-start; never a model/content or transport failure."""
    pass

class EpisodeFailure(ValueError):
    pass
class TransportFailure(EpisodeFailure):
    """Local unavailable/incomplete reply; counts toward the durable pause."""
    pass

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read(path):
    path=Path(path)
    if path.is_symlink(): raise Stop('evidence symlink')
    return strict_load(path.read_text())

def syncdir(path):
    fd=os.open(str(path),os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        f.write(canonical(value)+'\n');f.flush();os.fsync(f.fileno())
    syncdir(path.parent)

def save_bytes(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(value);f.flush();os.fsync(f.fileno())
    syncdir(path.parent)

@contextlib.contextmanager
def lock(directory):
    directory=Path(directory)
    if directory.is_symlink(): raise Stop('collection directory symlink')
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'collector.lock').open('a') as f:
        try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise Stop('collector already locked') from None
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)

class Journal:
    def __init__(self,path):
        self.path=Path(path);self.prefix=self.path.parent/(self.path.name+'.prefixes')
        self.rows=[];self.raw=b''
        if self.path.is_symlink() or self.prefix.is_symlink(): raise Stop('journal symlink')
        raw=self.path.read_bytes() if self.path.exists() else b''
        parts=raw.splitlines(keepends=True)
        anchors=sorted(self.prefix.glob('*.json'))
        if len(parts)!=len(anchors): raise Stop('unanchored journal tail or missing prefix; reconcile offline')
        offset=0;previous='0'*64;prefix_hash=hashlib.sha256()
        for i,line in enumerate(parts):
            if not line.endswith(b'\n'): raise Stop('partial journal event')
            row=strict_load(line.decode());offset+=len(line);prefix_hash.update(line)
            if row.get('seq')!=i or row.get('previous')!=previous: raise Stop('journal chain mismatch')
            expected={'bytes':offset,'sha256':prefix_hash.hexdigest(),'seq':i}
            if read(self.prefix/f'{i:06d}.json')!=expected: raise Stop('append-only prefix changed')
            self.rows.append(row);previous=sha(line)
        self.raw=raw

    def append(self,event):
        # Recheck the old prefix before mutation, even within an acquired lock.
        if (self.path.read_bytes() if self.path.exists() else b'')!=self.raw: raise Stop('journal concurrently changed')
        row={**event,'time':now(),'seq':len(self.rows),'previous':sha(self.raw.splitlines(keepends=True)[-1]) if self.rows else '0'*64}
        data=(canonical(row)+'\n').encode();self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('ab') as f: f.write(data);f.flush();os.fsync(f.fileno())
        self.raw+=data
        save(self.prefix/f'{len(self.rows):06d}.json',{'seq':len(self.rows),'bytes':len(self.raw),'sha256':sha(self.raw)})
        self.rows.append(row)
        return row

class Ledger:
    """Caller must hold collection lock; starts allocated from whole-episode holds."""
    def __init__(self,path):
        self.journal=Journal(path);self.holds={};self.started={};self.settled={};self.finished=set();self.sealed={};self.spent=0;self.blocked=False;self.usage_pauses={}
        for e in self.journal.rows: self.apply(e)

    @property
    def exposure(self): return self.spent+sum(self.holds.values())

    def apply(self,e):
        op=e['event'];ident=e['id']
        if op=='stop': self.blocked=True;return
        if self.blocked: raise Stop('ledger durably stopped')
        if op=='usage-limit-pause':
            start=self.started.get(ident)
            if start is None or self.settled.get(ident)!=0 or ident in self.usage_pauses or start['episode'] in self.finished:
                raise Stop('invalid usage-limit non-start settlement')
            self.holds[start['episode']]+=start['reserved']
            self.usage_pauses[ident]=e
        elif op=='seal':
            if ident in self.sealed or not isinstance(e.get('terminal_sha256'),str) or len(e['terminal_sha256'])!=64: raise Stop('invalid/duplicate episode seal')
            self.sealed[ident]=e['terminal_sha256']
        elif op=='reserve':
            amount=e['amount']
            if type(amount) is not int or amount<0 or ident in self.holds or self.exposure+amount+1000000>25000000 or self.exposure+amount+1000000>=39000000: raise Stop('rolling resource gate')
            self.holds[ident]=amount
        elif op=='start':
            ep=e['episode'];held=e['reserved']
            pending=sum(v['reserved'] for k,v in self.started.items() if v['episode']==ep and k not in self.settled)
            if ident in self.started or ep not in self.holds or ep in self.finished or type(held) is not int or held<0 or pending+held>self.holds[ep]: raise Stop('invalid subhold/start')
            self.started[ident]=e
        elif op=='settle':
            amount=e['actual'];s=self.started.get(ident)
            if s is None or ident in self.settled or type(amount) is not int or amount<0: raise Stop('invalid settlement')
            self.holds[s['episode']]-=s['reserved'];self.spent+=amount;self.settled[ident]=amount
        elif op=='release':
            if ident not in self.holds or ident in self.finished or any(v['episode']==ident and k not in self.settled for k,v in self.started.items()): raise Stop('uncertain hold cannot release')
            self.holds[ident]=0;self.finished.add(ident)
        else: raise Stop('unknown ledger event')

    def event(self,**e):
        self.apply(e);self.journal.append(e)

class ActiveTime:
    def __init__(self,path,cap):
        import time
        self.journal=Journal(path);self.cap=cap;self.holds={};self.settled={}
        for e in self.journal.rows:
            if e['event']=='start' and e['id'] not in self.holds: self.holds[e['id']]=e['seconds']
            elif e['event']=='settle' and e['id'] in self.holds and e['id'] not in self.settled: self.settled[e['id']]=e['seconds']
            else: raise Stop('invalid active-time ledger')
        self.charged=sum(self.settled.get(k,v) for k,v in self.holds.items());self.pending=time.monotonic()

    def begin(self,ident,seconds):
        import time
        overhead=max(0,time.monotonic()-self.pending)
        if ident in self.holds or self.charged+overhead+seconds>self.cap: raise Stop('active-time cap')
        self.journal.append({'event':'start','id':ident,'seconds':seconds+overhead});self.holds[ident]=seconds+overhead;self.charged+=seconds+overhead
        return self.pending

    def end(self,ident,began):
        import time
        ended=time.monotonic();elapsed=max(0,ended-began)
        self.journal.append({'event':'settle','id':ident,'seconds':elapsed});self.charged+=elapsed-self.holds[ident];self.settled[ident]=elapsed;self.pending=ended
        if self.charged>self.cap: raise Stop('measured cumulative active-time overrun')
