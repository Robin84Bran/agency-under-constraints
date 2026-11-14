"""D3b durable cohort-run transport pause; clearance never resends an episode."""
from pathlib import Path
from trl_core import sha
from trl_io import Stop, now, read, save, timestamp


class PauseStop(Stop):
    pass


def stop_paths(root):
    return sorted((Path(root)/'collection').glob('STOP-d3b*.json'))


def next_stop(root):
    base = Path(root)/'collection'
    first = base/'STOP-d3b.json'
    if not first.exists():
        return first
    n = 2
    while (base/f'STOP-d3b-{n:03}.json').exists():
        n += 1
    return base/f'STOP-d3b-{n:03}.json'


def episode_files(root,ids):
    root = Path(root)
    result = {}
    for ident in ids:
        if type(ident) is not str or Path(ident).name!=ident or ident in ('.','..'):
            raise Stop('invalid paused episode id')
        d = root/'collection/episodes'/ident
        if d.is_symlink() or not d.resolve().is_relative_to(root.resolve()):
            raise Stop('invalid paused episode path')
        for p in sorted(d.rglob('*')):
            if p.is_symlink():
                raise Stop('symlink paused evidence')
            if p.is_file():
                result[p.relative_to(root).as_posix()] = sha(p.read_bytes())
        if not (d/'episode.json').is_file():
            raise Stop('paused episode must be terminal')
    return result


def _pause_record(root,p):
    from trl_freeze import verify
    if p.is_symlink():
        raise Stop('symlink durable STOP')
    s = read(p)
    if (s.get('kind')!='transport_failure_pause' or s.get('deviation')!='D3b' or
        s.get('threshold')!=3 or s.get('cohort') not in ('local','claude') or
        type(s.get('episode_ids')) is not list or len(s['episode_ids'])!=3 or
        len(set(s['episode_ids']))!=3 or not s.get('cohort_run_id') or
        s.get('freeze_sha256')!=verify(root) or
        s.get('episode_files')!=episode_files(root,s['episode_ids'])):
        raise Stop('invalid or changed D3b pause evidence; integrity STOP cannot be cleared')
    for ident in s['episode_ids']:
        t = read(Path(root)/'collection/episodes'/ident/'episode.json')
        if (t.get('cohort_run_id')!=s['cohort_run_id'] or t.get('transport_failure') is not True or
            t.get('fatal') or t.get('complete') or
            (t['episode']['actor']=='claude')!=(s['cohort']=='claude')):
            raise Stop('pause does not bind three terminal transport failures')
    return s


def pause_if_needed(root):
    """Recover even a crash between the third terminal write and STOP creation."""
    root = Path(root)
    recorded = {read(p).get('cohort_run_id') for p in stop_paths(root)}
    runs = {}
    for p in (root/'collection/episodes').glob('*/episode.json'):
        t = read(p)
        if t.get('cohort_run_id'):
            runs.setdefault(t['cohort_run_id'],[]).append(t)
    for run,terminals in sorted(runs.items()):
        streak = []
        for index,t in enumerate(sorted(terminals,key=lambda t:timestamp(t['finished_at']))):
            streak = streak+[t['episode']['id']] if t.get('transport_failure') is True and not t.get('fatal') else []
            if len(streak)==3:
                if run not in recorded:
                    cohort = 'claude' if t['episode']['actor']=='claude' else 'local'
                    from trl_freeze import verify
                    save(next_stop(root),{'deviation':'D3b','kind':'transport_failure_pause',
                        'reason':'3 consecutive episode-level transport failures within one cohort run',
                        'time':now(),'threshold':3,'cohort':cohort,'cohort_run_id':run,
                        'episode_ids':streak,'episode_files':episode_files(root,streak),
                        'freeze_sha256':verify(root)})
                    raise PauseStop('D3b transport pause; recorded reviewer clearance required')
                # Dispatch after a third failure in the same run is never allowed.
                if len(terminals)>index+1:
                    raise Stop('dispatch found after D3b pause within same cohort run')
                break


def pause_gate(root):
    from trl_d3c import is_cleared_stop
    from trl_d4 import is_cleared_stop as d4_cleared
    root = Path(root)
    for p in stop_paths(root):
        if is_cleared_stop(root,p) or d4_cleared(root,p):
            continue
        s = _pause_record(root,p)
        cpath = root/'collection/d3b-clearances'/p.name
        if not cpath.exists() or cpath.is_symlink():
            raise PauseStop('uncleared D3b durable STOP: '+p.name)
        c = read(cpath)
        if (c.get('deviation')!='D3b' or c.get('disposition')!='RESUME_UNATTEMPTED_ONLY' or
            c.get('stop_sha256')!=sha(p.read_bytes()) or c.get('freeze_sha256')!=s['freeze_sha256'] or
            not isinstance(c.get('reviewer'),str) or not c['reviewer'].strip() or
            not isinstance(c.get('reason'),str) or not c['reason'].strip() or
            timestamp(c['recorded_at'])<timestamp(s['time'])):
            raise Stop('invalid D3b pause clearance')


def stop_gate(root):
    from trl_d3 import clearance
    root = Path(root)
    c = clearance(root)
    allowed = {'STOP.json','STOP-d2.json'}|{p.name for p in stop_paths(root)}
    if any(p.name not in allowed for p in (root/'collection').glob('STOP*.json')):
        raise Stop('uncleared durable integrity STOP exists')
    pause_if_needed(root)
    pause_gate(root)
    return c


def record_clearance(root,stop_name,reviewer,reason):
    """Explicit review record only; no transport, episode rewrite or hold release."""
    from trl_freeze import verify, active_freeze
    root = Path(root)
    if active_freeze(root) not in ('freeze-d3b.json','freeze-d3d.json','freeze-d4.json'):
        raise Stop('D3b freeze required')
    verify(root)
    p = root/'collection'/stop_name
    if p not in stop_paths(root) or not reviewer.strip() or not reason.strip():
        raise Stop('exact D3b STOP, named reviewer and reason required')
    s = _pause_record(root,p)
    save(root/'collection/d3b-clearances'/p.name,{'deviation':'D3b',
        'disposition':'RESUME_UNATTEMPTED_ONLY','stop_sha256':sha(p.read_bytes()),
        'freeze_sha256':s['freeze_sha256'],'recorded_at':now(),'reviewer':reviewer,'reason':reason})
    pause_gate(root)
    return 'RESUME_UNATTEMPTED_ONLY'


def provenance_layers(root,active):
    """D3 was never pushed/run: bind D1/D2 starts, then the D3b push directly."""
    from trl_d3 import clearance
    root = Path(root)
    c = clearance(root)
    starts = {p.relative_to(root).as_posix() for p in (root/'collection/episodes').glob('*/*.start.json')}
    d2 = read(root/'deviations/d2/clearance.json')
    old = starts & set(d2['preserved_files'])
    prior = starts & set(c['preserved_files'])
    return [('freeze-d1.json','',old),('freeze-d2.json','-d2',prior-old),
            ('freeze-d3b.json','-d3b',starts-prior)]


def prepush_gate(root):
    from trl_d3 import clearance
    root = Path(root)
    c = clearance(root)
    if any(p.relative_to(root).as_posix() not in c['preserved_files']
           for p in (root/'collection/episodes').glob('*/*.start.json')):
        raise Stop('D3b attestation must precede all D3b starts')
    if any((root/'collection'/n).exists() for n in ('push-d3.json','push-event-d3.raw.json')):
        raise Stop('D3b requires the unpushed/unrun D3 parent')
    return c
