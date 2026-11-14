// Independent JS oracle: exact toy RNG import; deliberately changed study field.
import {random} from '../evidence/toy-model.mjs';
const seeds=[0,1,19,99,0xffffffff];
const rngVectors=seeds.map(seed=>{const r=random(seed);return {seed,values:Array.from({length:12},()=>r())};});
function world(seed){
 const r=random(seed), centers=Array.from({length:2},()=>[Math.floor(r()*8),Math.floor(r()*6)]);
 const moved=centers.map(([x,y])=>[(x+4)%8,(y+3)%6]);
 const fields=[centers,moved].map(cs=>Array.from({length:48},(_,i)=>{
  const value=Math.max(...cs.map(([x,y])=>{
   const dx=Math.min(Math.abs(i%8-x),8-Math.abs(i%8-x));
   const dy=Math.min(Math.abs(Math.floor(i/8)-y),6-Math.abs(Math.floor(i/8)-y));
   return Math.exp(-(dx*dx+dy*dy)/3);
  }));
  return Math.floor(1000*value+0.5);
 }));
 return {seed,centers,moved,fields};
}
console.log(JSON.stringify({rng:rngVectors,worlds:Array.from({length:100},(_,s)=>world(s))}));
