// Rebuild offline: node fixtures/draw-vectors.mjs > NEW-VECTORS.json
import {draw} from '../evidence/toy-model.mjs';
const vectors=[];
for (const seed of [0,1,9,49,4294967295])
  for (const job of [0,1,2,3])
    for (const attempt of [0,1,9])
      for (const channel of [0,1])
        vectors.push({seed,job,attempt,channel,value:draw(seed,job,attempt,channel)});
console.log(JSON.stringify({source:'unmodified evidence/toy-model.mjs',vectors},null,2));
