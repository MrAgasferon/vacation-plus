/* Release-only UI; no user data is sent and no code is fetched/executed. */
(function(root){
 'use strict';
 const repo='https://github.com/MrAgasferon/vacation-plus';
 const api='https://api.github.com/repos/MrAgasferon/vacation-plus/releases/latest';
 const appId='io.github.mragasferon.vacationplus';
 function versionCode(version){
  if(typeof version!=='string'||! /^(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})$/.test(version))return null;
  const [a,b,c]=version.split('.').map(Number), n=a*1000000+b*1000+c;
  return n>0&&n<=2100000000?n:null;
 }
 function evaluateRelease(info,release){
  if(info?.id!==appId||versionCode(info.version)!==Number(info.build)||versionCode(info.version)===null)throw Error('Не удалось определить версию приложения.');
  if(!release||release.draft!==false||release.prerelease!==false||typeof release.tag_name!=='string'||!release.tag_name.startsWith('v'))throw Error('Некорректные данные релиза.');
  const tag=release.tag_name, version=tag.slice(1), code=versionCode(version);
  if(code===null)throw Error('Некорректный номер релиза.');
  const filename='vacation-plus-'+version+'.apk', expected=repo+'/releases/download/'+tag+'/'+filename;
  if(!Array.isArray(release.assets)||!release.assets.some(a=>a.name===filename&&a.state==='uploaded'&&a.browser_download_url===expected&&a.size>0))throw Error('В релизе отсутствует установочный APK.');
  return {available:code>Number(info.build),tag,version};
 }
 async function checkRelease(info,fetcher,timeout=10000){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeout);
  try{
   const response=await fetcher(api,{signal:controller.signal,cache:'no-store',credentials:'omit',headers:{Accept:'application/vnd.github+json'}});
   if(!response.ok)throw Error('GitHub недоступен (HTTP '+response.status+').');
   return evaluateRelease(info,await response.json());
  }finally{clearTimeout(timer)}
 }
 if(typeof module==='object'&&module.exports){module.exports={versionCode,evaluateRelease,checkRelease};return}
 if(!root.Capacitor?.isNativePlatform?.())return;
 const panel=document.createElement('section'); panel.className='panel local-data-panel';
 panel.innerHTML='<h2>Обновление приложения</h2><p class="info-line" id="apk-version">Проверяем версию…</p><div class="local-data-actions"><button type="button" class="btn btn-primary" id="apk-check">Проверить обновление APK</button><button type="button" class="btn" id="apk-open" hidden style="display:none">Открыть релиз</button></div><p id="apk-status" class="feedback" role="status" aria-live="polite">Проверка требует интернета. Калькулятор работает и без него.</p><p class="info-line">APK загружается с GitHub Releases. Установка подтверждается в Android. Перед обновлением рекомендуется сохранить резервный JSON.</p>';
 const grid=document.querySelector('#tab-settings .settings-grid'); if(!grid)return; grid.append(panel);
 const byId=id=>document.getElementById(id), status=byId('apk-status'), btn=byId('apk-check'), open=byId('apk-open');
 const banner=document.createElement('section');banner.className='note';banner.style.margin='0 0 16px';banner.hidden=true;
 banner.innerHTML='<div class="row-between"><strong id="apk-banner-text"></strong><div class="slot-compare"><button type="button" id="apk-banner-open" class="btn btn-primary">Открыть релиз</button><button type="button" id="apk-banner-dismiss" class="btn">Позже</button></div></div>';
 const nav=document.querySelector('.tabs');if(nav)nav.before(banner);
 let info=null, current=null, busy=false;
 function message(text,kind=''){status.textContent=text;status.className='feedback '+kind}
 function showOpen(result){current=result;open.hidden=!result;open.style.display=result?'':'none';banner.hidden=!result;if(result&&nav)byId('apk-banner-text').textContent='Доступно обновление '+result.version;}
 async function check(manual){
  if(busy)return;busy=true;btn.disabled=true;showOpen(null);message('Проверяем GitHub…');
  try{if(!info)info=await root.Capacitor.Plugins.App.getInfo(); byId('apk-version').textContent='Установлена '+info.version+' ('+info.build+')';
   const result=await checkRelease(info,root.fetch.bind(root));
   if(result.available){showOpen(result);message('Доступна версия '+result.version+'.','ok')}
   else message('Установлена актуальная версия.','ok');
  }catch(e){message(manual?'Не удалось проверить обновление. '+(e.name==='AbortError'?'Время ожидания истекло.':e.message):'Автоматическая проверка недоступна. Можно повторить вручную.','err')}
  finally{busy=false;btn.disabled=false}
 }
 btn.addEventListener('click',()=>check(true));
 async function openRelease(){if(!current)return;try{await root.Capacitor.Plugins.VacationUpdates.openRelease({tag:current.tag})}catch(e){message('Не удалось открыть релиз: '+e.message,'err');if(nav)byId('apk-banner-text').textContent='Не удалось открыть релиз. Повтори попытку.';}}
 open.addEventListener('click',openRelease);
 if(nav){byId('apk-banner-open').addEventListener('click',openRelease);byId('apk-banner-dismiss').addEventListener('click',()=>{banner.hidden=true});}
 // A single delayed request per cold start; never awaited by calculator initialization.
 setTimeout(()=>check(false),2500);
})(globalThis);
