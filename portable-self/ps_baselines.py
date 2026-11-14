"""Code-only sanity ceilings/references, never model observations."""
import random
from ps_core import fixture

BASELINES=('uniform','last-console','keyed-ledger','oracle')

def baseline(seed,world,kind):
    f=fixture(seed,world);rng=random.Random(20261113+seed)
    last=f['calibration'][f['cal_order'][-1]]
    correct=full=0;returns=[]
    for j in f['return_order']:
        if kind=='uniform': controls=[rng.randrange(1,5) for _ in range(4)]
        else:
            mapping=f['returns'][j] if kind=='oracle' else last if kind=='last-console' else f['calibration'][j]
            controls=[mapping.index(d)+1 for d in f['targets'][j]]
        hits=[f['returns'][j][k-1]==d for k,d in zip(controls,f['targets'][j])]
        correct+=sum(hits);full+=all(hits);returns.append({'console':f['labels'][j],'controls':controls,'hits':hits})
    return {'seed':seed,'world':world,'kind':kind,'Y':correct/16,'F':full/4,'returns':returns,
            'ceiling':kind=='oracle','model_result':False}
