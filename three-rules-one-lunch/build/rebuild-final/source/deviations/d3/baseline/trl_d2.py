"""Offline, narrowly bound D2 STOP clearance. Never changes saved collection bytes."""
from pathlib import Path
from trl_core import sha
from trl_io import Stop, read, save, now

CLEARANCE = 'deviations/d2/clearance.json'
EPISODE = 'llama8b-s034-central'


def clearance(root):
    root = Path(root)
    c = read(root/CLEARANCE)
    if c.get('deviation')!='D2' or c.get('episode_id')!=EPISODE or c.get('disposition')!='SCORED_NO_RERUN':
        raise Stop('invalid D2 clearance')
    for n,h in c['preserved_files'].items():
        p = root/n
        if not n.startswith('collection/') or '..' in Path(n).parts or p.is_symlink() or sha(p.read_bytes())!=h:
            raise Stop('D2 preserved evidence changed: '+n)
    for d in c['terminal_episodes']:
        actual = {p.relative_to(root).as_posix() for p in (root/'collection/episodes'/d).rglob('*') if p.is_file()}
        expected = {n for n in c['preserved_files'] if n.startswith('collection/episodes/'+d+'/')}
        if actual!=expected:
            raise Stop('D2 historical episode received additional evidence')
    return c


def record_clearance(root):
    """Called under collector lock; verify/replay the received reply without generation."""
    from trl_analysis import replay
    from trl_validation import validate, stdout
    from trl_core import strict_load
    from trl_budget import maximum
    root = Path(root)
    directory = root/'collection/episodes'/EPISODE
    terminal = read(directory/'episode.json')
    raw = read(directory/'r1-j0.raw.json')
    env = strict_load(stdout(raw))
    if (read(root/'collection/STOP.json')['reason']!='local identity/truncation/stop mismatch' or
        terminal['error']!='local identity/truncation/stop mismatch' or not terminal['fatal'] or
        env.get('done_reason')!='length' or env.get('eval_count')!=192 or env.get('prompt_eval_count')!=240):
        raise Stop('D2 known stop evidence mismatch')
    try:
        validate(raw,'llama8b',3,maximum('central'))
    except ValueError as exc:
        if str(exc)!='local output-length limit; schema-invalid reply':
            raise Stop('D2 stop is not solely output-length failure') from exc
    else:
        raise Stop('D2 requires invalid output-length reply')
    row = replay(terminal['episode'],directory)
    if row['Y']!=0 or row['H']!=0 or row['calls']!=1 or row['complete'] or not row['attempted']:
        raise Stop('D2 disposition does not replay')
    episodes = sorted(p.parent.name for p in (root/'collection/episodes').glob('*/episode.json'))
    dirs = sorted(p.name for p in (root/'collection/episodes').iterdir() if p.is_dir())
    if episodes!=dirs or any(read(root/'collection/episodes'/d/'episode.json').get('fatal') for d in dirs if d!=EPISODE):
        raise Stop('D2 cannot clear partial or other fatal episodes')
    files = {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted((root/'collection').rglob('*'))
             if p.is_file() and p.name!='collector.lock'}
    save(root/CLEARANCE,{'deviation':'D2','recorded_at':now(),'agreement':'Claude reviewer / Codex builder',
        'episode_id':EPISODE,'disposition':'SCORED_NO_RERUN','attempted_calls':1,
        'technical_opportunities':3,'missing_opportunities':9,'Y':0,'H':0,
        'input_tokens':240,'output_tokens':192,'terminal_episodes':episodes,'preserved_files':files,
        'reason':'Only the output-length fatal classification is cleared; original STOP and fatal terminal remain immutable.'})
    return clearance(root)


def stop_gate(root):
    root = Path(root)
    c = clearance(root)
    if any(p.name!='STOP.json' for p in (root/'collection').glob('STOP*.json')):
        raise Stop('uncleared durable STOP exists')
    return c
