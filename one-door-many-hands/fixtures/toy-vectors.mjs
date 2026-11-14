// Cross-language fixtures for the original 120-round toy, not the one-wave study.
import {simulate,random} from '../evidence/toy-model.mjs';
const settings=[{seed:1,slots:2,failure:.35,common:0,cycle:6},{seed:4,slots:24,failure:0,common:0,cycle:6},{seed:7,slots:1,failure:1,common:1,cycle:3},{seed:4294967295,slots:6,failure:.7,common:.5,cycle:12}];
console.log(JSON.stringify({kind:'ORIGINAL_TOY_PARITY_NOT_STUDY_ORACLE',draws:[0,1,42,4294967295].map(seed=>{const rng=random(seed);return {seed,draws:Array.from({length:8},()=>rng())}}),worlds:settings.map(s=>{const r=simulate(s);return {settings:r.settings,shock:r.shock,summary:r.summary}})}));
