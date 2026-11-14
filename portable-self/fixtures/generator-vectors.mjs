// Independent Node implementation of protocol hash-ranked generator test vectors.
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
const hash=(kind,s,...p)=>createHash('sha256').update(['portable-self-v01',kind,s,...p].join('|')).digest('hex');
const perms=(a)=>a.length?a.flatMap((v,i)=>perms(a.filter((_,j)=>j!==i)).map(p=>[v,...p])):[[]];
const rank=(a,fn)=>[...a].sort((x,y)=>fn(x).localeCompare(fn(y))||String(x).localeCompare(String(y)));
function fixture(s,w){
 const ranked=rank(perms([0,1,2,3]),p=>hash('map',s,p.join(''))).slice(0,4);
 const calibration=ranked.map(p=>w==='same-stable'?ranked[0]:p);
 const cal_order=rank([0,1,2,3],j=>hash('cal',s,j));
 return {seed:s,world:w,labels:[0,1,2,3].map(j=>'c-'+hash('label',s,j).slice(0,8)),calibration,
 returns:calibration.map(p=>w==='stale-remap'?p.map(d=>(d+1)%4):p),cal_order,
 return_order:rank([0,1,2,3],j=>hash('return',s,j)),targets:[0,1,2,3].map(j=>rank([0,1,2,3],d=>hash('target',s,j,d))),slots:[0,1,2,3].map(j=>cal_order.indexOf(j)+1)};
}
const vectors=[0,1,19,99].flatMap(s=>['different-stable','same-stable','stale-remap'].map(w=>fixture(s,w)));
const text=JSON.stringify(vectors,null,2)+'\n';
if(process.argv.includes('--verify')){
 const expected=JSON.parse(readFileSync(new URL('generator-vectors.json',import.meta.url),'utf8'));
 if(JSON.stringify(expected)!==JSON.stringify(vectors))throw Error('generator vectors differ');
 console.log('PASS: 12 independent Node generator vectors');
}else process.stdout.write(text);
