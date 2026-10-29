import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
const source=fs.readFileSync(new URL('../assets/study.js',import.meta.url),'utf8');
const context={Date};vm.createContext(context);vm.runInContext(source.slice(source.indexOf('function wordTransition'),source.indexOf('function studyButton')),context);
const transition=context.wordTransition;
test('unknown word completes exactly three spaced rounds before confirmation',()=>{let t=1000;let p=transition(null,'unknown',t);assert.equal(p.due,t+600000);assert.equal(p.status,'review');for(let round=1;round<=3;round++){t=p.due;p=transition(p,'remember',t);assert.equal(p.round,round);assert.equal(p.status,round===3?'confirm':'review');if(round<3)assert.equal(p.due-t,round===1?86400000:259200000)}assert.notEqual(p.status,'mastered');p=transition(p,'known',t);assert.equal(p.status,'mastered');assert.equal(p.due,0)});
test('forgotten words restart all three rounds and survive JSON backup',()=>{const p=transition({round:2,status:'review'},'unknown',700);assert.equal(p.round,0);assert.equal(p.due,600700);assert.equal(JSON.parse(JSON.stringify(p)).status,'review')});
