"""Optional Playwright smoke tests; simulate installed display mode and native bridge."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
html = (root/'www/index.html').read_text(encoding='utf-8')
updater = (root/'android-src/vacation-updates.js').read_text(encoding='utf-8')
old_build, new_build = 'a'*40, 'b'*40
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH'), args=['--no-sandbox','--disable-dev-shm-usage'])
    def setup(width, mode='web', phone=False):
        ctx = browser.new_context(viewport={'width':width,'height':850}, service_workers='block', **({'user_agent':'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/130.0.0.0 Mobile Safari/537.36'} if phone else {}))
        page=ctx.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        pre='''<base href="https://mragasferon.github.io/vacation-plus/">
<script>Object.defineProperty(window,'localStorage',{value:{data:new Map(),getItem(k){return this.data.get(k)??null},setItem(k,v){this.data.set(k,v)},removeItem(k){this.data.delete(k)}}});
window.updateCalls=0;window.remoteBuild='''+repr(old_build)+''';window.remoteVersion='0.4.0';window.openedTag=null;window.fetch=async(url,opts)=>{
 if(String(url).includes('vp-check=')){updateCalls++;if(remoteBuild==='offline')throw Error('offline');return {ok:true,text:async()=>'<meta name="vacation-build" content="'+remoteBuild+'">'}}
 if(String(url).includes('api.github.com')){updateCalls++;if(remoteVersion==='offline')throw Error('offline');const tag='v'+remoteVersion,name='vacation-plus-'+remoteVersion+'.apk';return {ok:true,json:async()=>({draft:false,prerelease:false,tag_name:tag,assets:[{name,state:'uploaded',size:123,browser_download_url:'https://github.com/MrAgasferon/vacation-plus/releases/download/'+tag+'/'+name}]})}}
 throw Error('calendar network blocked in test');};</script>'''
        if mode=='pwa':
            pre+="<script>const orig=matchMedia.bind(window);window.matchMedia=q=>q==='(display-mode: standalone)'?{matches:true,addEventListener(){}}:orig(q);</script>"
        if mode=='apk':
            pre+="<script>window.Capacitor={isNativePlatform:()=>true,Plugins:{Preferences:{get:async()=>({value:null}),set:async()=>{}},App:{getInfo:async()=>({id:'io.github.mragasferon.vacationplus',version:'0.4.0',build:'4000'}),exitApp:async()=>{}},VacationFiles:{},VacationUpdates:{openRelease:async({tag})=>{openedTag=tag}}}};</script>"
        content=html.replace('<head>','<head>'+pre,1).replace('name="vacation-build" content="dev"','name="vacation-build" content="'+old_build+'"')
        if mode=='apk':content=content.replace('</body>','<script>'+updater+'</script></body>')
        page.set_content(content);page.wait_for_function("document.querySelector('#year-select').options.length>0")
        return page,errors
    def settings(page,mobile):
        if mobile:
            page.locator('[data-mobile-nav=more]').click();page.locator('#tab-settings [data-mobile-sub=app]').click()
        else:page.locator('.tabs [data-tab=settings]').click()
        assert page.locator('#app-distribution').is_visible()
    for width,mode,phone,mobile in [(1440,'web',False,False),(390,'web',False,True),(900,'web',True,True),(1440,'pwa',False,True),(900,'apk',False,True),(390,'apk',False,True)]:
        page,errors=setup(width,mode,phone);assert page.locator('.mobile-nav').is_visible()==mobile,(width,mode)
        if mobile:
            page.locator('[data-mobile-nav=calendar]').click();assert page.locator('.cal-month:visible').count()==1
        settings(page,mobile)
        assert page.locator('#install-pwa').is_visible()==(mode=='web')
        assert page.locator('#install-apk').is_visible()==(mode=='web')
        assert page.locator('#pwa-check').is_visible()==(mode=='pwa')
        assert page.locator('#apk-check').is_visible()==(mode=='apk')
        if mode=='web':
            page.evaluate("""window.installPromptCalls=0;const ev=new Event('beforeinstallprompt',{cancelable:true});ev.prompt=async()=>{installPromptCalls++};ev.userChoice=Promise.resolve({outcome:'accepted'});window.dispatchEvent(ev);""")
            page.locator('#install-pwa').click();page.wait_for_function('installPromptCalls===1');assert 'Установка запущена' in page.locator('#install-status').inner_text()
            page.locator('#install-pwa').click();assert 'меню браузера' in page.locator('#install-status').inner_text()
        if mode=='pwa':
            assert page.evaluate('updateCalls')==0
            page.locator('#pwa-check').click();assert 'актуальная' in page.locator('#pwa-status').inner_text();assert not page.locator('#pwa-releases').is_visible()
            page.evaluate('remoteBuild='+repr(new_build));page.locator('#pwa-check').click();assert page.locator('#pwa-releases').is_visible()
            page.evaluate("remoteBuild='offline'");page.locator('#pwa-check').click();assert 'Не удалось' in page.locator('#pwa-status').inner_text();assert not page.locator('#pwa-releases').is_visible()
            page.set_viewport_size({'width':390,'height':800});assert page.locator('#pwa-check').is_visible() # selected subsection survives resize
        if mode=='apk':
            page.wait_for_timeout(2700);assert page.evaluate('updateCalls')==0 # old code checked at 2.5 seconds
            page.locator('#apk-check').click();assert 'актуальная' in page.locator('#apk-status').inner_text();assert not page.locator('#apk-open').is_visible()
            page.evaluate("remoteVersion='0.4.1'");page.locator('#apk-check').click();assert page.locator('#apk-open').is_visible();page.locator('#apk-open').click();assert page.evaluate('openedTag')=='v0.4.1'
            page.evaluate("remoteVersion='offline'");page.locator('#apk-check').click();assert not page.locator('#apk-open').is_visible();assert 'Не удалось' in page.locator('#apk-status').inner_text()
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,mode)
        assert not errors,errors
        print(width,mode,'phone' if phone else '', 'OK');page.context.close()
    browser.close()
