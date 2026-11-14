import itertools
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import subprocess
import unittest
from od_core import *
from od_io import read
from od_transport import identity,check_identity

@lru_cache(None)
def distribution(n,f):
    p=Fraction(f,100);dp=[Fraction(1)]
    for _ in range(n):
        nxt=[Fraction()]*(len(dp)+1)
        for k,v in enumerate(dp):nxt[k]+=v*p;nxt[k+1]+=v*(1-p)
        dp=nxt
    return dp

class Core(unittest.TestCase):
    def test_hand_vectors(self):
        for c in read(ROOT/'fixtures/one-wave.json')['cases']:
            rows,best,optimal=oracle(c['target'],c['failure'],c['door'],c['mode'])
            self.assertEqual([str(rows[n]['value']) for n in FLEETS],c['values']);self.assertEqual(list(optimal),c['optimal'])
    def test_direct_subsets_small_and_dp_large(self):
        for f in (0,100,20,26,32,38,44,50,56,62,68,74):
            p=Fraction(f,100)
            for n in (1,6):
                direct=[Fraction()]*(n+1)
                for bits in itertools.product((0,1),repeat=n):
                    k=sum(bits);direct[k]+=(1-p)**k*p**(n-k)
                self.assertEqual(direct,distribution(n,f))
        for b in range(100):
            for B in (1,6,24):
                T=7+b%10;f=20+6*(b//10);rows,_,_=oracle(T,f,B,'independent')
                for n in FLEETS:
                    dp=distribution(n,f)
                    # Independent threshold comparison, no use of delivered()/required.
                    expected=sum((v for k,v in enumerate(dp) if 24*min(k,B)>=T*n),Fraction())
                    work=sum((v*Fraction(24*min(k,B),n) for k,v in enumerate(dp)),Fraction())
                    self.assertEqual(rows[n]['value'],expected);self.assertEqual(rows[n]['work'],work)
    def test_oracle_frequencies(self):
        counts={B:{} for B in (1,6,24)}
        for b in range(100):
            for B in counts:
                opt=oracle(7+b%10,20+6*(b//10),B,'independent')[2]
                self.assertEqual(len(opt),1);n=opt[0];counts[B][n]=counts[B].get(n,0)+1
        self.assertEqual(counts,{1:{1:100},6:{6:64,1:36},24:{24:59,6:9,1:32}})
    def test_delivery_and_common(self):
        for n in FLEETS:
            for B in range(25):
                self.assertLessEqual(delivered(n,n,B),24)
                self.assertEqual(delivered(n,0,B),0)
                self.assertEqual(delivered(n,n,24),24)
                for T in range(1,25):
                    rows,_,_=oracle(T,20,B,'common')
                    self.assertEqual(rows[n]['value'],Fraction(4,5) if delivered(n,n,B)>=T else 0)
    def test_schedule_pairs_no_leakage(self):
        jobs=schedule();self.assertEqual(len(jobs),3720);self.assertEqual(len({e['id'] for e in jobs}),3720)
        self.assertEqual([a for a,g in itertools.groupby(e['actor'] for e in jobs)],list(ACTORS))
        self.assertEqual(sorted({e['block'] for e in jobs if e['actor']=='claude'}),[0,13,26,39,42,55,68,71,84,97])
        paired={}
        for e in jobs:
            p=payload(e);self.assertEqual(set(p),{'target','failure_percent','mode','door_limit','options','rehearsal'})
            self.assertEqual(set(p['options']),set(FLEETS))
            for row in p['rehearsal']:
                self.assertEqual(row,{'carriers':row['carriers'],'crossings':min(row['carriers'],e['door']),'delivered':24//row['carriers']*min(row['carriers'],e['door'])})
            key=(e['actor'],e['block'],e['door'],e['mode']);p.pop('rehearsal')
            if key in paired:self.assertEqual(paired[key],p)
            paired[key]=p
    def test_sizing_literals(self):
        self.assertEqual([len(x.encode()) for x in (SYSTEM,INSTRUCTION,SCHEMA_TEXT)],[65,1052,139])
        jobs=[e for e in schedule() if e['actor']=='claude']
        self.assertEqual(sum(reserve(render(e))['micro_usd'] for e in jobs),2580480)
        for arm,size in [('rules',(1151,1158)),('rehearsal',(1281,1291))]:
            ns=[len(render(e).encode()) for e in jobs if e['evidence']==arm];self.assertEqual((min(ns),max(ns)),size)
    def test_strict_choice(self):
        for n in (1,6,24,None):self.assertEqual(choice(strict_load(canonical({'fleet':n}))),n)
        for s in ['{"fleet":true}','{"fleet":1.0}','{"fleet":"6"}','{"fleet":0}','{}','{"fleet":6,"x":1}','{"fleet":6,"fleet":1}','{"fleet":NaN}','{"fleet":6}{}','```{"fleet":6}```','[6]']:
            with self.assertRaises((ValueError,TypeError)):choice(strict_load(s))
    def test_pinned_identity(self):
        models=identity(ROOT)
        for actor,m in models.items():
            check_identity(ROOT,actor,{'template':m['template'],'system':m['system']})
            with self.assertRaises(Exception):check_identity(ROOT,actor,{'template':m['template']+'x','system':m['system']})
        self.assertEqual(models['llama8b']['system'],'');self.assertIn('Alibaba',models['qwen7b']['system'])
    def test_original_toy_node_parity(self):
        actual=json.loads(subprocess.check_output(['node','fixtures/toy-vectors.mjs'],cwd=ROOT))
        self.assertEqual(actual,read(ROOT/'fixtures/toy-vectors.json'))
    def test_original_toy_python_parity(self):
        # Independently implement original rotating queue to preserve the teaching source.
        mask=0xffffffff
        def rng(seed):
            x=seed
            while True:
                x=(x+0x6D2B79F5)&mask
                # JS: t ^= t + imul(t ^ t >>> 7, 61 | t), using original first t.
                a=((x^(x>>15))*(1|x))&mask
                t=a^((a+(((a^(a>>7))*(61|a))&mask))&mask)
                yield ((t^(t>>14))&mask)/4294967296
        vectors=read(ROOT/'fixtures/toy-vectors.json')
        for row in vectors['draws']:
            r=rng(row['seed']);self.assertEqual([next(r) for _ in range(8)],row['draws'])
        for row in vectors['worlds']:
            s=row['settings'];r=rng(s['seed']);common=next(r)<s['common'];shared=next(r)<s['failure'];loss=[next(r)<s['failure'] for _ in range(24)]
            summaries=[]
            for n in FLEETS:
                alive=[True]*n;ready=[1]*n;cursor=total=post=blocked=0
                for tick in range(1,121):
                    if tick==61:alive=[not (shared if common else loss[i]) for i in range(n)]
                    available=sum(alive[i] and ready[i]<=tick for i in range(n));served=[]
                    for offset in range(n):
                        i=(cursor+offset)%n
                        if len(served)<s['slots'] and alive[i] and ready[i]<=tick:served.append(i);ready[i]=tick+s['cycle']
                    if served:cursor=(served[-1]+1)%n
                    work=len(served)*(24//n);total+=work;post+=work if tick>=61 else 0;blocked+=available-len(served)
                summaries.append({'n':n,'capacity':24//n,'total':total,'post':post,'survivors':sum(alive),'outage':post==0,'blocked':blocked})
            self.assertEqual(summaries,row['summary'])
