from playwright.sync_api import sync_playwright
from pathlib import Path
import argparse, os
parser=argparse.ArgumentParser(description='Browser smoke test; storage/network are mocked; optionally compare the previous HTML.')
parser.add_argument('--baseline',type=Path)
parser.add_argument('--compare-settings',action='store_true',help='Also compare settings (not expected to match before 0.4.0 distribution controls)')
parser.add_argument('--chromium',default=os.environ.get('CHROMIUM_PATH'))
args=parser.parse_args()
html=(Path(__file__).resolve().parents[1]/'www/index.html').read_text(encoding='utf-8');old=args.baseline.read_text(encoding='utf-8') if args.baseline else None
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=args.chromium,args=['--no-sandbox','--disable-dev-shm-usage'])
 def page_for(content,w,h=840,native=False):
  ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=1,service_workers='block'); page=ctx.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  pre="<script>Object.defineProperty(window,'localStorage',{value:{data:new Map(),getItem(k){return this.data.get(k)??null},setItem(k,v){this.data.set(k,v)},removeItem(k){this.data.delete(k)}}});window.fetch=async()=>{throw Error('offline test')};</script>"
  if native:
   pre+='<script>window.exitCount=0;window.Capacitor={isNativePlatform:()=>true,Plugins:{Preferences:{get:async()=>({value:null}),set:async()=>{}},App:{getInfo:async()=>({version:"0.4.0",build:"4000"}),exitApp:async()=>{window.exitCount++}},VacationFiles:{}}};</script>'
  page.set_content(content.replace('<head>','<head>'+pre,1));page.wait_for_function("document.querySelector('#year-select').options.length>0"); return page,errors
 # Compare desktop pixels on all four tabs if the previous source is available.
 if old:
  from PIL import Image,ImageChops
  from io import BytesIO
  a,ea=page_for(old,1440,1000); n,en=page_for(html,1440,1000)
  for tab in ['calculator','planner','documentation']+(['settings'] if args.compare_settings else []):
   for page in [a,n]:
    page.locator(f'.tabs [data-tab={tab}]').click();page.evaluate('window.scrollTo(0,0)')
   im1=Image.open(BytesIO(a.screenshot(animations='disabled',full_page=True))).convert('RGB');im2=Image.open(BytesIO(n.screenshot(animations='disabled',full_page=True))).convert('RGB')
   assert im1.size==im2.size and not ImageChops.difference(im1,im2).getbbox(), tab
   print('desktop pixel match:',tab)
  assert not ea and not en
  a.context.close();n.context.close()
 def no_overflow(page):
  assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), page.evaluate('document.documentElement.dataset.mobileScreen+"/"+document.documentElement.dataset.mobileSub')
 for w in [320,360,390,430]:
  page,errors=page_for(html,w); page.wait_for_selector('.mobile-nav');
  assert page.locator('.results-card').is_visible(); assert not page.locator('#calendar').is_visible(); assert not page.locator('#salary').is_visible();
  page.locator('.mobile-salary-toggle').click();page.locator('#salary').fill('139000');page.locator('.mobile-salary-toggle').click();
  page.locator('#add').click();assert page.locator('.mobile-period-open').count()==1;page.locator('.mobile-period-open .mobile-period-toggle').click();
  assert page.locator('.mobile-period-open').count()==0;page.locator('.mobile-result-toggle').click();assert page.locator('#breakdown').is_visible();no_overflow(page)
  assert page.locator('#mobile-budget-value').inner_text()=='8 / 36';
  page.locator('.mobile-result-toggle').click();
  page.locator('[data-mobile-nav=calendar]').click();assert page.locator('.cal-month:visible').count()==1;no_overflow(page);page.locator('#mobile-month-select').select_option('5');
  page.locator('[data-cal-date="2027-06-29"]').click(); page.locator('[data-month-step="1"]').click();page.locator('[data-cal-date="2027-07-04"]').click();assert 'июн' in page.locator('#cal-preview').inner_text();page.locator('#cal-add').click();assert page.locator('.results-card').is_visible();
  page.locator('[data-mobile-nav=calendar]').click();page.locator('#tab-calculator [data-mobile-sub=heat]').click();assert page.locator('#heatmap').is_visible();no_overflow(page);page.locator('#tab-calculator [data-mobile-sub=reco]').click();assert page.locator('#recommendations').is_visible();no_overflow(page);
  page.locator('[data-mobile-nav=plan]').click();assert page.locator('#annual-plans').is_visible();no_overflow(page);page.locator('#tab-planner [data-mobile-sub=compare]').click();assert page.locator('#compare-grid').is_visible();no_overflow(page);
  page.locator('[data-mobile-nav=more]').click();page.locator('#tab-settings [data-mobile-sub=years]').click();assert page.locator('#year-tiles').is_visible();no_overflow(page);page.locator('#tab-settings [data-mobile-sub=data]').click();assert page.locator('#export-data').is_visible();no_overflow(page);page.locator('#tab-settings [data-mobile-sub=docs]').click();assert page.locator('#tab-documentation').is_visible();no_overflow(page);
  page.locator('[data-mobile-nav=calc]').click();assert page.locator('#mobile-salary-value').inner_text().replace('\u00a0',' ')=='139 000 ₽';
  overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth');print(w,'overflow',overflow,'errors',errors); assert not overflow and not errors
  if w==390:
   page.locator('[data-mobile-nav=calendar]').click();
   page.set_viewport_size({'width':1440,'height':900});page.locator('.tabs').wait_for(state='visible');assert page.locator('.tabs').is_visible();assert not page.locator('.mobile-nav').is_visible();assert page.locator('.cal-month:visible').count()==12
  page.context.close()
 # Native bridge simulation: back traverses mobile screens and closes edit panels.
 page,errors=page_for(html,390,native=True);page.wait_for_selector('.mobile-nav');
 def back():page.evaluate("document.dispatchEvent(new Event('vacation-native-back'))")
 page.locator('[data-mobile-nav=calendar]').click();page.locator('#tab-calculator [data-mobile-sub=heat]').click();back();assert page.locator('#calendar').is_visible();back();assert page.locator('.results-card').is_visible()
 page.locator('.mobile-salary-toggle').click();back();assert not page.locator('#salary').is_visible();assert page.evaluate('exitCount')==0
 back();page.wait_for_function('exitCount===1');assert not errors;print('native back (mock): OK');page.context.close()
 b.close()
