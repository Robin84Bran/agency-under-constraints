"""Independent saved-byte audit. No imports from the experiment harness."""
import collections
import hashlib
import json
import math
from pathlib import Path
import re


def load(raw):
    def pairs(entries):
        out={}
        for k,v in entries:
            if k in out: raise ValueError('duplicate '+k)
            out[k]=v
        return out
    def bad(v): raise ValueError('nonfinite '+v)
    def number(v):
        f=float(v)
        if not math.isfinite(f): raise ValueError('nonfinite')
        return f
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad,parse_float=number)


def validate(a,arm):
    """Reimplemented from the registered six-field contract, not action()."""
    if type(a) is not dict or set(a)!={'op','item','grams','mass_g','revision','target'}: raise ValueError('keys')
    if type(a['op']) is not str or a['op'] not in ('lookup','convert','submit','describe','finish'): raise ValueError('op')
    if a['item'] is not None and (type(a['item']) is not str or re.fullmatch('[a-z0-9-]{1,12}',a['item']) is None): raise ValueError('item')
    for key in ('grams','mass_g'):
        if a[key] is not None and (type(a[key]) is not int or a[key]<0 or a[key]>999999999): raise ValueError(key+' type/range')
    if a['revision'] is not None and (type(a['revision']) is not int or a['revision']!=1): raise ValueError('revision')
    if a['target'] is not None and (type(a['target']) is not str or a['target'] not in ('lookup','convert','submit')): raise ValueError('target')
    used={k for k in a if k!='op' and a[k] is not None}
    options={'lookup':[{'item'}], 'convert':[{'grams'},{'mass_g'}], 'submit':[{'grams'},{'grams','revision'}], 'describe':[{'target'}] if arm=='registry' else [], 'finish':[set()]}
    if used not in options[a['op']]: raise ValueError('fields/permission')
    return a


class Replay:
    def __init__(self,ep,descriptions):
        self.ep=ep; self.desc=descriptions
        self.mass=1000+(7919*ep['seed']+104729)%998000
        self.item='item-'+str(ep['seed']).zfill(6)
        self.looked=self.converted=self.committed=self.ended=False
        self.n=0
    def step(self,a):
        validate(a,self.ep['arm'])
        if self.ended: raise ValueError('post terminal')
        self.n+=1
        op=a['op'];code='OK';amount=unit=detail=None
        if op=='finish':
            self.ended=True; return None
        if op=='lookup':
            if a['item']==self.item: self.looked=True;amount=self.mass;unit='g'
            else: code='NOT_FOUND';detail='item not found'
        elif op=='describe':
            key=a['target']
            if key=='convert': key+='_'+(self.ep['world'] if self.looked and self.ep['world'] in ('rename','unit') else 'v0')
            elif key=='submit': key+='_'+('required' if self.looked and self.ep['world']=='required' else 'v0')
            detail=self.desc[key]
        elif op=='convert':
            rename=self.looked and self.ep['world']=='rename'
            key='mass_g' if rename else 'grams'
            if a[key] is None: code='SCHEMA';detail='convert requires mass_g; grams is not accepted' if rename else 'convert requires grams; mass_g is not accepted'
            elif not self.looked: code='ORDER';detail='lookup required'
            elif a[key]!=self.mass: code='VALUE';detail='mass does not match lookup'
            else: self.converted=True;unit='mg' if self.ep['world']=='unit' else 'g';amount=self.mass*(1000 if unit=='mg' else 1)
        elif op=='submit':
            required=self.looked and self.ep['world']=='required'
            if required and a['revision']!=1: code='SCHEMA';detail='submit requires revision=1'
            elif not required and a['revision'] is not None: code='SCHEMA';detail='submit does not accept revision'
            elif not self.converted: code='ORDER';detail='successful convert required'
            elif a['grams']!=self.mass: code='VALUE';detail='mass does not match lookup'
            else: self.committed=True
        self.ended=self.committed or self.n==6
        return dict(code=code,amount=amount,unit=unit,detail=detail)


def audit(root):
    root=Path(root);coll=root/'collection'
    # Descriptions are literals, not validation or transition code.
    import ast
    tree=ast.parse((root/'bob_core.py').read_text())
    desc=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DESCRIPTIONS' for t in n.targets))
    counts=collections.Counter();terminal=collections.Counter();details=[];hashes={};cells=collections.defaultdict(collections.Counter)
    def read(p):
        raw=p.read_bytes();hashes[p.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest();return load(raw)
    for p in sorted((coll/'episodes').glob('*.json')):
        saved=read(p);ep=saved['episode'];state=Replay(ep,desc);used=0;observed_report=None
        terminal[ep['model']+'/'+saved['terminal_reason']]+=1
        cell=cells[ep['model']+'/'+ep['world']+'/'+ep['arm']];cell['n']+=1
        for cid in saved['calls']:
            c=read(coll/'calls'/(cid+'.json'));req=read(coll/'requests'/(cid+'.json'))
            start=read(coll/'starts'/(cid+'.json'))
            assert start['request_sha256']==hashes['collection/requests/'+cid+'.json']
            prompt=load(req['prompt'])
            assert prompt['history']==[e for e in saved['events'][:used] if e['observation'] is not None]
            assert prompt['remaining']==6-state.n
            rawpath=coll/'raw'/(cid+'.stdout')
            if not rawpath.exists():
                assert c['response_sha256'] is None and c['envelope'] is None and c['error'] is not None
                counts['preflight_no_reply']+=1;continue
            env=read(rawpath)
            assert hashes[rawpath.relative_to(root).as_posix()]==c['response_sha256'] and env==c['envelope']
            counts['saved_model_replies']+=1
            if c['phase']=='report':
                v=load(env['response']);assert set(v)=={'submitted'} and (v['submitted'] is None or type(v['submitted']) is bool)
                observed_report=v;counts['valid_reports']+=1;cell['valid_report']+=1;continue
            counts['action_replies']+=1
            try:
                a=validate(load(env['response']),ep['arm'])
            except ValueError as exc:
                assert c['error'] is not None
                key=ep['model']+'/'+c['error'];counts[key]+=1;counts['rejected_actions']+=1
                details.append(dict(id=cid,recorded_error=c['error'],independent_error=str(exc),looked=state.looked,world=ep['world'],arm=ep['arm'],legal=False,raw_sha256=c['response_sha256']))
                continue
            obs=state.step(a)
            if c['error'] is not None:
                counts['falsely_rejected_legal_actions']+=1
                details.append(dict(id=cid,legal=True,would_return=obs,raw_sha256=c['response_sha256']))
            else:
                assert saved['events'][used]==dict(action=a,observation=obs)
                assert c['parsed']==a
                used+=1;counts['accepted_action_replies']+=1
                if obs is not None and obs['code']!='OK': counts['tool_rejections']+=1
        assert used==len(saved['events']) and observed_report==saved['report']
        assert (state.committed,state.ended,state.n)==(saved['committed'],saved['ended'],saved['decisions'])
        cell['Sstar']+=state.committed;cell['Astar']+=state.committed and observed_report is not None and observed_report['submitted'] is True
        cell['valid_trajectory']+=saved['trajectory_valid']
        counts['episodes']+=1
    return dict(status='PASS',method='Independent parser, six-field validator and transition reducer; raw replies plus original prompt histories; no harness validator imports',counts=dict(counts,falsely_rejected_legal_actions=counts['falsely_rejected_legal_actions']),terminal=dict(terminal),cells=dict(cells),rejections=details,evidence_files=hashes,rescoring='No legal rejected reply found: original saved-byte scores stand. No started episode is rerun. One preflight failure has no reply and is not classified as a rejected action.')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=audit(args.root)
    args.output.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps(dict(counts=result['counts'],terminal=result['terminal']),indent=2))
