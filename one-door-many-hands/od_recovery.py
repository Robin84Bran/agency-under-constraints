"""Persistent three-episode transport pause. No clearance or override API."""
from pathlib import Path
from od_core import ACTORS
from od_io import Stop,read


def record_transport(state,ident,terminal):
    if state['reason']: raise Stop('dispatch continued after three transport failures')
    if terminal['status']=='TRANSPORT_FAILURE': state['streak'].append(ident)
    else: state['streak']=[]
    if len(state['streak'])==3:
        state['reason']='three consecutive episode transport failures: '+','.join(state['streak'])


def transport_state(base,jobs,cohort):
    """A success or content failure breaks the streak; resume never resets it.

    Return the first threshold breach, not just the final trailing streak, so
    later terminals cannot conceal dispatch past a mandatory pause. Callers
    validate raw evidence and append-only ledger prefixes separately.
    """
    actors=('claude',) if cohort=='claude' else ACTORS[:3]
    state={'streak':[],'reason':None}
    for ep in jobs:
        if ep['actor'] not in actors: continue
        from od_usage import episode_state
        directory,events=episode_state(base,ep['id'])
        if directory is None: continue
        path=directory/'episode.json'
        start=read(path.parent/'start.json')
        if start.get('revision')!='A1': continue  # Retained r1 fake evidence only.
        record_transport(state,ep['id'],read(path))
    return state


def transport_pause(base,jobs,cohort): return transport_state(base,jobs,cohort)['reason']
