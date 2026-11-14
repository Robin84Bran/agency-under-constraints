"""Append-only dispatch journal; exact preserved prefixes plus fully verified tails."""
from pathlib import Path
from trl_core import canonical, sha, strict_load
from trl_io import Stop, append, now


def prefix(path):
    path=Path(path)
    raw=path.read_bytes() if path.exists() else b''
    if path.is_symlink() or (raw and not raw.endswith(b'\n')): raise Stop('torn/symlink ledger')
    return {'bytes':len(raw),'sha256':sha(raw)}


def verify_prefix(path, expected):
    path=Path(path);raw=path.read_bytes() if path.exists() else b'';n=expected.get('bytes')
    if (path.is_symlink() or type(n) is not int or n<0 or len(raw)<n or sha(raw[:n])!=expected.get('sha256') or
        (n and raw[n-1:n]!=b'\n') or (raw and not raw.endswith(b'\n'))):
        raise Stop('preserved ledger prefix changed/truncated/torn')


class Journal:
    """Caller owns collector lock. Parse once; reverify on any observed file change."""
    def __init__(self,path):
        self.path=Path(path);self.reload()

    def fingerprint(self):
        if self.path.is_symlink(): raise Stop('symlink ledger')
        if not self.path.exists(): return None
        s=self.path.stat();return (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

    def apply(self,e):
        ident=e['id'];kind=e['event']
        if kind=='start':
            if ident in self.ids: raise Stop('duplicate dispatch id')
            self.open.add(ident);self.ids.add(ident)
        elif kind=='finish':
            if ident not in self.open: raise Stop('orphan/duplicate finish')
            self.open.remove(ident)
        elif kind=='checkpoint':
            if ident in self.ids: raise Stop('duplicate checkpoint')
            self.ids.add(ident)
        else: raise Stop('invalid dispatch ledger event')

    def reload(self):
        before=self.fingerprint()
        self.head='0'*64;self.events=[];self.ids=set();self.open=set()
        raw=self.path.read_bytes() if self.path.exists() else b''
        if raw and not raw.endswith(b'\n'): raise Stop('torn ledger')
        for line in raw.decode().splitlines():
            r=strict_load(line);e=r['data']
            if r['previous']!=self.head or r['sha256']!=sha(canonical({'previous':self.head,'data':e}).encode()):
                raise Stop('dispatch ledger hash chain broken')
            self.apply(e);self.head=r['sha256'];self.events.append(e)
        self.observed=self.fingerprint()
        if before!=self.observed: raise Stop('ledger changed during verification')

    def event(self,**e):
        if self.fingerprint()!=self.observed: self.reload()
        e['time']=now()
        # Validate state transition before appending. The outer collector lock owns writes.
        self.apply(e)
        r={'previous':self.head,'data':e};r['sha256']=sha(canonical(r).encode())
        append(self.path,r);self.head=r['sha256'];self.events.append(e);self.observed=self.fingerprint()
