// Node-only oracle: imported toy draw is unchanged; mass/g/mg is the new study.
import {draw} from '../evidence/toy/model.mjs';
const draws=[];
for (const seed of [0,1,9,49,0xffffffff]) {
  for (const tick of [-1,0,17,159]) {
    for (const salt of ['arrival','schema-drift','hub-outage','random-repair']) {
      for (const index of [0,7]) draws.push({seed,tick,index,salt,value:draw(seed,tick,index,salt)});
    }
  }
}
const masses=Array.from({length:50},(_,seed)=>{
  const grams=1000+(7919*seed+104729)%998000;
  return {seed,item:`item-${String(seed).padStart(6,'0')}`,grams,milligrams:grams*1000};
});
console.log(JSON.stringify({format:1,draws,masses}));
