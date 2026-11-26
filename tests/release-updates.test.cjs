const {test}=require('node:test');
const assert=require('node:assert/strict');
const {versionCode,evaluateRelease,checkRelease}=require('../android-src/vacation-updates.js');
const info={id:'io.github.mragasferon.vacationplus',version:'0.3.0',build:'3000'};
function release(version){const name=`vacation-plus-${version}.apk`;return {tag_name:`v${version}`,draft:false,prerelease:false,assets:[{name,state:'uploaded',size:123,browser_download_url:`https://github.com/MrAgasferon/vacation-plus/releases/download/v${version}/${name}`}]}}
test('VersionCode numeric order and invalid values',()=>{assert.equal(versionCode('0.3.0'),3000);assert.equal(versionCode('1.2.3'),1002003);assert.ok(versionCode('1.0.0')>versionCode('0.999.999'));for(const v of ['0.0.0','01.2.3','1.1000.0','v1.0.0','1.0.0-beta','2101.0.0',null])assert.equal(versionCode(v),null)});
test('Newer official release is available',()=>assert.deepEqual(evaluateRelease(info,release('0.3.1')),{available:true,tag:'v0.3.1',version:'0.3.1'}));
test('Equal or older releases never prompt downgrade',()=>{assert.equal(evaluateRelease(info,release('0.3.0')).available,false);assert.equal(evaluateRelease(info,release('0.2.9')).available,false)});
test('Reject unexpected package or inconsistent build',()=>{assert.throws(()=>evaluateRelease({...info,id:info.id+'.preview'},release('1.0.0')));assert.throws(()=>evaluateRelease({...info,build:'1'},release('1.0.0')))});
test('Reject drafts, prereleases, missing APK and foreign download',()=>{for(const r of [{...release('1.0.0'),draft:true},{...release('1.0.0'),prerelease:true},{...release('1.0.0'),assets:[]}])assert.throws(()=>evaluateRelease(info,r));const r=release('1.0.0');r.assets[0].browser_download_url='https://example.com/apk';assert.throws(()=>evaluateRelease(info,r))});
test('Request only public release metadata without credentials',async()=>{const r=await checkRelease(info,async(url,options)=>{assert.equal(url,'https://api.github.com/repos/MrAgasferon/vacation-plus/releases/latest');assert.equal(options.credentials,'omit');return {ok:true,json:async()=>release('0.3.1')}});assert.ok(r.available)});
test('Network failures and HTTP errors do not invent releases',async()=>{await assert.rejects(checkRelease(info,async()=>{throw Error('offline')}),/offline/);await assert.rejects(checkRelease(info,async()=>({ok:false,status:404})),/404/)});
test('Timeout aborts slow request',async()=>{await assert.rejects(checkRelease(info,async(_,o)=>new Promise((resolve,reject)=>o.signal.addEventListener('abort',()=>reject(Error('aborted')))),5),/aborted/)});
