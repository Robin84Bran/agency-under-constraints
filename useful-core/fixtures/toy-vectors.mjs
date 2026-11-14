// Execute only the archived playable toy; never an inference transport.
import {draw,canRun,simulateWorld} from '../evidence/toy/model.mjs';
const draws=[];
for(const seed of [0,1,64,4294967295]) for(const tick of [0,1,30,119]) for(const index of [0,7,91]) for(const salt of ['repair','failure','shock','random-policy']) draws.push({seed,tick,index,salt,value:draw(seed,tick,index,salt)});
const feasibility=[];
for(let mask=0;mask<256;mask++) {const health=Array.from({length:8},(_,i)=>!!(mask&(1<<i)));feasibility.push({mask,full:canRun('full',health),reduced:canRun('reduced',health),core:canRun('core',health)});}
const worlds=[];
for(const seed of [0,1,64]) for(const config of [{},{failureRate:0,shockSize:0},{repairRate:0}]) {const w=simulateWorld(config,seed,false);worlds.push({seed,config:w.config,policies:w.policies});}
process.stdout.write(JSON.stringify({draws,feasibility,worlds})+'\n');
