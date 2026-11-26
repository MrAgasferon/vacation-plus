const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../www/index.html'),'utf8');
const create=vm.runInNewContext(html.split('// NATIVE_BACK_START')[1].split('// NATIVE_BACK_END')[0]+'\ncreateVacationBackHandler');
function setup(tab='calculator'){
 const calls=[], state={tab,busy:false,focused:false,fail:false};
 const back=create({busy:()=>state.busy,activeTab:()=>state.tab,showCalculator:()=>{calls.push('calculator');state.tab='calculator'},blurInput:()=>{if(!state.focused)return false;calls.push('blur');state.focused=false;return true},flush:async()=>{calls.push('flush');if(state.fail)throw Error('write')},exit:async()=>calls.push('exit'),warn:()=>calls.push('warn')});
 return {state,calls,back};
}
test('Back from each secondary tab returns to calculator without exit',async()=>{for(const tab of ['settings','planner','documentation']){const s=setup(tab);await s.back();assert.deepEqual(s.calls,['calculator']);}});
test('Back on calculator blurs input first, then flushes before exit',async()=>{const s=setup();s.state.focused=true;await s.back();await s.back();assert.deepEqual(s.calls,['blur','flush','exit']);});
test('Back during file operation does nothing',async()=>{const s=setup('settings');s.state.busy=true;await s.back();assert.deepEqual(s.calls,[]);});
test('Failed flush prevents exit',async()=>{const s=setup();s.state.fail=true;await s.back();assert.deepEqual(s.calls,['flush','warn']);});
test('Concurrent back during exit does not duplicate calls',async()=>{const s=setup();await Promise.all([s.back(),s.back()]);assert.deepEqual(s.calls,['flush','exit']);});
