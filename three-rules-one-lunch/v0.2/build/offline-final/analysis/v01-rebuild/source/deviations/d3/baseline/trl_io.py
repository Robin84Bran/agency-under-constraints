"""Exclusive immutable records and advisory process locks (POSIX)."""
import contextlib
import datetime as dt
import fcntl
import os
from pathlib import Path
from trl_core import canonical, strict_load


class Stop(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def timestamp(s):
    v = dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    if v.tzinfo is None:
        raise Stop('timezone required')
    return v


def read(path):
    return strict_load(Path(path).read_text())


def syncdir(path):
    fd = os.open(str(path),os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        f.write(canonical(value)+'\n'); f.flush(); os.fsync(f.fileno())
    syncdir(path.parent)


def save_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    syncdir(path.parent)


def append(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        f.write(canonical(value)+'\n'); f.flush(); os.fsync(f.fileno())
    syncdir(path.parent)


@contextlib.contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop('concurrent admission rejected')
        try:
            yield
        finally:
            fcntl.flock(f,fcntl.LOCK_UN)


def stop(base, reason):
    p = Path(base)/'STOP.json'
    if (Path(base).parent/'deviations/d2/clearance.json').exists():
        p = Path(base)/'STOP-d2.json'
    if not p.exists():
        save(p,{'reason':reason,'time':now()})
