"""Code policies; never substitute these actions for model output."""
from bob_core import World, act


def run(ep,policy):
    w = World(ep['seed'],ep['world'],ep['arm'])
    def call(op,**kw):
        return w.step(act(op,**kw))
    receipt = call('lookup',item=w.item)
    mass = receipt['amount']
    if policy=='fixed_v0':
        call('convert',grams=mass)
        call('submit',grams=mass)
        if not w.ended:
            call('finish')
    elif policy=='reactive':
        c = call('convert',grams=mass)
        if c['code']=='SCHEMA':
            c = call('convert',mass_g=mass)
        value = c['amount']//1000 if c['unit']=='mg' else c['amount']
        s = call('submit',grams=value)
        if s['code']=='SCHEMA' and not w.ended:
            call('submit',grams=value,revision=1)
    elif policy=='oracle':
        if ep['arm']=='registry':
            call('describe',target='convert')
        c = call('convert',**{'mass_g' if ep['world']=='rename' else 'grams':mass})
        if ep['arm']=='registry':
            call('describe',target='submit')
        value = c['amount']//1000 if c['unit']=='mg' else c['amount']
        call('submit',grams=value,**({'revision':1} if ep['world']=='required' else {}))
    else:
        raise ValueError('baseline policy')
    return dict(episode=ep,events=w.events,committed=w.committed,ended=w.ended,
                decisions=w.decisions,trajectory_valid=True,report={'submitted':w.committed},error=None)
