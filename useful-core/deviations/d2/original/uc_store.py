"""Create-once evidence and append-only journals, checked against retained prefixes."""
import contextlib
import datetime as dt
import fcntl
import os
from pathlib import Path
import time
from uc_core import canonical,sha,strict_load


class Stop(RuntimeError):
    """Collection integrity/accounting stop."""


class EpisodeFailure(ValueError):
    """Known technical reply/transport failure; do not retry episode."""


class TransportFailure(EpisodeFailure):
    """Episode-local local-provider transport failure; contributes to pause streak."""


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    return strict_load(Path(path).read_bytes().decode('utf-8'))


def syncdir(path):
    fd = os.open(str(path),os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save_bytes(path,value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink():
        raise Stop('symlink evidence target')
    with path.open('xb') as f:
        f.write(value);f.flush();os.fsync(f.fileno())
    syncdir(path.parent)


def save(path,value):
    save_bytes(path,(canonical(value)+'\n').encode())


@contextlib.contextmanager
def lock(base):
    base=Path(base);base.mkdir(parents=True,exist_ok=True)
    with (base/'collector.lock').open('a') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop('concurrent collector') from None
        try:
            yield
        finally:
            fcntl.flock(f,fcntl.LOCK_UN)


class Journal:
    """Each append records the hash AND byte count of its complete prior prefix.

    Create-once checkpoints pin every observed prefix, including the final tail.
    A missing tail/checkpoint, edit or truncation fails closed on reopen.
    """
    def __init__(self,path):
        self.path=Path(path);self.checks=self.path.with_suffix('.prefixes')
        self.events=[];self.raw=b''
        if self.path.is_symlink() or self.checks.is_symlink():
            raise Stop('symlink journal')
        if self.path.exists():
            self.raw=self.path.read_bytes()
        if self.raw and not self.raw.endswith(b'\n'):
            raise Stop('partial journal append')
        position=0
        for index,line in enumerate(self.raw.splitlines(keepends=True)):
            row=strict_load(line.decode())
            if row.get('seq')!=index or row.get('prefix_bytes')!=position or row.get('prefix_sha256')!=sha(self.raw[:position]):
                raise Stop('journal prefix mismatch')
            self.events.append(row['value']);position+=len(line)
            pin=read(self.checks/f'{index:06d}.json')
            if pin != dict(bytes=position,sha256=sha(self.raw[:position])):
                raise Stop('retained append-only prefix changed')
        if (len(list(self.checks.iterdir())) if self.checks.exists() else 0)!=len(self.events):
            raise Stop('journal truncation or incomplete checkpoint')

    def append(self,value):
        if (self.path.read_bytes() if self.path.exists() else b'')!=self.raw:
            raise Stop('journal concurrent change')
        self.checks.mkdir(parents=True,exist_ok=True)
        row=dict(seq=len(self.events),prefix_bytes=len(self.raw),prefix_sha256=sha(self.raw),value=value)
        data=(canonical(row)+'\n').encode()
        with self.path.open('ab') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        self.raw+=data
        save(self.checks/f'{len(self.events):06d}.json',dict(bytes=len(self.raw),sha256=sha(self.raw)))
        self.events.append(value)


class Ledger:
    RESERVE=2000000
    def __init__(self,path):
        self.journal=Journal(path);self.holds={};self.spent=0;self.calls={};self.finished=set();self.blocked=False;self.nonstarts={}
        for e in self.journal.events:
            self.apply(e)

    @property
    def exposure(self):
        return self.spent+sum(self.holds.values())

    def apply(self,e):
        op,ident=e['event'],e['id']
        if op=='reserve':
            amount=e['amount']
            if self.blocked or type(amount) is not int or amount<0 or ident in self.holds or self.exposure+amount+self.RESERVE>25000000 or self.exposure+amount+self.RESERVE>=39000000:
                raise Stop('reservation gate')
            self.holds[ident]=amount
        elif op=='settle':
            amount,held,episode=e['actual'],e['reserved'],e['episode']
            if any(type(v) is not int or v<0 for v in (amount,held)) or ident in self.calls or episode not in self.holds or episode in self.finished or held>self.holds[episode]:
                raise Stop('invalid settlement')
            self.spent+=amount;self.holds[episode]-=held;self.calls[ident]=amount
            if amount>held or self.exposure+self.RESERVE>25000000 or self.exposure+self.RESERVE>=39000000:
                self.blocked=True
        elif op=='nonstart':
            episode=e['episode'];held=e['reserved']
            if (type(held) is not int or held<0 or type(e.get('actual')) is not int or e['actual']!=0 or
                ident in self.nonstarts or episode not in self.holds or episode in self.finished or held>self.holds[episode] or self.blocked):
                raise Stop('invalid definite non-start settlement')
            # Zero cost; the identical future call retains its existing reservation.
            self.nonstarts[ident]=e
        elif op=='release':
            if self.blocked or ident not in self.holds or ident in self.finished:
                raise Stop('invalid release')
            self.holds[ident]=0;self.finished.add(ident)
        elif op=='stop':
            self.blocked=True
        else:
            raise Stop('unknown ledger event')

    def event(self,**e):
        e['time']=now();self.apply(e);self.journal.append(e)


class ActiveTime:
    def __init__(self,path,cap):
        self.journal=Journal(path);self.cap=cap;self.holds={};self.settled={}
        for e in self.journal.events:
            if e['event']=='start' and e['id'] not in self.holds:
                self.holds[e['id']]=e['seconds']
            elif e['event']=='settle' and e['id'] in self.holds and e['id'] not in self.settled:
                self.settled[e['id']]=e['seconds']
            else:
                raise Stop('invalid timer journal')
        self.charged=sum(self.settled.get(k,v) for k,v in self.holds.items())
        self.pending=time.monotonic()

    def begin(self,ident,seconds):
        overhead=max(0,time.monotonic()-self.pending)
        # Elapsed between calls is included; unknown interrupted starts keep full hold.
        if ident in self.holds or self.charged+overhead+seconds>self.cap:
            raise Stop('cumulative active-time cap')
        held=seconds+overhead
        self.journal.append(dict(event='start',id=ident,seconds=held,time=now()))
        self.holds[ident]=held;self.charged+=held
        return self.pending

    def end(self,ident,began):
        ended=time.monotonic();elapsed=max(0,ended-began)
        self.journal.append(dict(event='settle',id=ident,seconds=elapsed,time=now()))
        self.settled[ident]=elapsed;self.charged+=elapsed-self.holds[ident];self.pending=ended
