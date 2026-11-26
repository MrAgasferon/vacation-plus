const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../www/index.html'),'utf8');
const code=html.split('// NATIVE_ADAPTER_START')[1].split('// NATIVE_ADAPTER_END')[0];
const create=vm.runInNewContext(code+'\ncreateVacationNative');
const key='vacation-plus-v2';
function setup(value=null,old=null){
 const data=new Map();if(old!==null)data.set(key,old);
 const writes=[],warnings=[];
 const options={value,fail:false,readFail:false};
 const plugins={Preferences:{async get(){if(options.readFail)throw Error('read failed');return {value:options.value}},async set({key:k,value:v}){assert.equal(k,key);if(options.fail)throw Error('write failed');options.value=v;writes.push(v)}},App:{async getInfo(){return {version:'0.2',build:'3'}}},VacationFiles:{}};
 const local={getItem:k=>data.get(k)??null,removeItem:k=>data.delete(k)};
 return {data,writes,warnings,options,open:()=>create(plugins,local,m=>warnings.push(m))};
}
test('Migrates WebView data only after successful Preferences save',async()=>{
 const s=setup(null,'{"salary":139000}');const a=await s.open();assert.equal(a.initial.salary,139000);assert.equal(a.allowLegacy,true);assert.ok(s.data.has(key));await a.save(JSON.stringify(a.initial));assert.equal(s.data.has(key),false);assert.equal(s.options.value,'{"salary":139000}');
});
test('Preferences is authoritative even if stale WebView data exists',async()=>{
 const s=setup('{"salary":160000}','{"salary":139000}');const a=await s.open();assert.equal(a.initial.salary,160000);assert.equal(a.allowLegacy,false);
});
test('Writes are serialized and last snapshot wins',async()=>{
 const s=setup(),a=await s.open();await Promise.all([a.save('1'),a.save('2'),a.save('3')]);await a.flush();assert.deepEqual(s.writes,['1','2','3']);
});
test('Failed write preserves old data and next save can recover',async()=>{
 const s=setup(null,'{"salary":139000}'),a=await s.open();s.options.fail=true;await assert.rejects(a.save('{}'),/write failed/);await assert.rejects(a.flush(),/write failed/);assert.ok(s.data.has(key));s.options.fail=false;await a.save('{"salary":139000}');await a.flush();assert.equal(s.data.has(key),false);
});
test('Reset tombstone prevents legacy data resurrection',async()=>{
 const s=setup('{}','{"salary":139000}'),a=await s.open();await a.replace('null');s.data.set(key,'{"salary":139000}');const b=await s.open();assert.equal(b.initial,null);assert.equal(b.allowLegacy,false);
});
test('Corrupt native state or read error fails closed',async()=>{
 const s=setup('{invalid','{}');await assert.rejects(s.open());assert.equal(s.writes.length,0);const b=setup();b.options.readFail=true;await assert.rejects(b.open(),/read failed/);assert.equal(b.writes.length,0);
});
test('Missing native plugin does not silently fall back',async()=>{
 await assert.rejects(create({}, {}, ()=>{}),/Android/);
});
test('Import replacement queues after existing writes',async()=>{
 const s=setup(),a=await s.open();const old=a.save('{"salary":1}');const next=a.replace('{"salary":2}');await Promise.all([old,next]);const b=await s.open();assert.equal(b.initial.salary,2);
});
