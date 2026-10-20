const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const root='tracking-release-20261020',m=JSON.parse(fs.readFileSync(root+'/manifest.json'));const base=m.base_url;
const ids={dk:'G-4GXPB3HJTP',ld:'G-NBE6ZXQ03J',touring:'G-5W12LPB0KK',group:'G-ZDVM9T129T'};
const keys={dk:'dk',ld:'ld',touring:'lt',group:'w365'};
const script=fs.readFileSync(root+'/files/analytics-consent.js','utf8');
const storageKey=script.match(/key='([^']+)'/)[1];
fs.mkdirSync('tracking-qa',{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true});const results=[];
async function context(width=390){
 const ctx=await browser.newContext({viewport:{width,height:900}});let writes=0,collections=0;
 await ctx.route('**/*',async r=>{
  const u=new URL(r.request().url()),name=u.pathname==='/'?'index.html':u.pathname.slice(1),f=path.join(root,'files',name);
  if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname)){collections++;return r.fulfill({status:204,body:''});}
  if(u.hostname===new URL(base).hostname&&fs.existsSync(f)&&fs.statSync(f).isFile())return r.fulfill({status:200,contentType:name.endsWith('.js')?'text/javascript':'text/html',body:fs.readFileSync(f)});
  if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes++;return r.abort();}
  return r.continue();
 });return {ctx,writes:()=>writes,collections:()=>collections};
}
try{
 // Execute the real consent script against controlled success/error HTML. All
 // Google requests and every write are intercepted, never forwarded.
 for(const marker of ['', 'contact','quote','group','not-a-valid-form']){
  const c=await context();const page=await c.ctx.newPage();
  await page.route('**/tracking-fixture.html',r=>r.fulfill({status:200,contentType:'text/html',body:'<!doctype html><html><head><meta charset="utf-8">'+(marker?'<meta name="worx-lead" content="'+marker+'">':'')+'<script defer src="/analytics-consent.js"></script></head><body><h1>Tracking test</h1><a href="tel:+441228000000">Phone</a></body></html>'}));
  await page.goto(base+'tracking-fixture.html');await page.getByRole('button',{name:'Reject analytics',exact:true}).waitFor();
  if(c.collections()!==0)throw Error('Google request before consent');
  if(await page.evaluate(()=>window.WorxAnalytics.track('contact_phone_click')))throw Error('Tracking before consent');
  await page.getByRole('button',{name:'Reject analytics',exact:true}).click();
  if(c.collections()!==0)throw Error('Google request after rejection');
  await page.getByRole('button',{name:'Cookie settings',exact:true}).click();await page.getByRole('button',{name:'Accept analytics',exact:true}).click();
  const eventState=await page.evaluate(()=>{window.WorxAnalytics.track('contact_phone_click');window.WorxAnalytics.track('unknown_event');return Array.from(window.dataLayer).filter(x=>x[0]==='event').map(x=>({name:x[1],params:x[2]}));});
  const leads=eventState.filter(x=>x.name==='generate_lead');const expected=['contact','quote','group'].includes(marker)?1:0;
  if(leads.length!==expected||eventState.some(x=>x.name==='unknown_event'))throw Error('Invalid lead event semantics');
  if(!eventState.some(x=>x.name==='contact_phone_click'))throw Error('Contact click not tracked');
  if(expected&&JSON.stringify(leads[0].params)!==JSON.stringify({form_name:marker,lead_source:'website_form'}))throw Error('Unexpected lead parameters');
  await page.getByRole('button',{name:'Cookie settings',exact:true}).click();await page.getByRole('button',{name:'Reject analytics',exact:true}).click();
  const n=await page.evaluate(()=>window.dataLayer.length);if(await page.evaluate(()=>window.WorxAnalytics.track('contact_phone_click')))throw Error('Tracking after withdrawal');
  if(await page.evaluate(()=>window.dataLayer.length)!==n)throw Error('Queued event after withdrawal');
  results.push({case:'consent-and-lead-marker',marker,expectedLeads:expected,googleHitsForwarded:0,writes:c.writes()});await c.ctx.close();
 }
 // Verify actual affected page layouts. PHP is tested with stubbed transport.
 const pages=Object.keys(m.files).filter(n=>n.endsWith('.html'));
 for(const file of pages)for(const width of [390,1440]){
  const c=await context(width);const page=await c.ctx.newPage();
  await page.goto(base+(file==='index.html'?'':file),{waitUntil:'networkidle',timeout:60000});
  const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();
  const state=await page.evaluate(()=>({width:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,broken:Array.from(document.images).filter(x=>x.complete&&x.naturalWidth===0).map(x=>x.src)}));
  if(state.width>width+1||state.h1!==1||state.broken.length)throw Error(JSON.stringify({file,width,...state}));
  await page.screenshot({path:'tracking-qa/'+file+'-'+width+'.png',fullPage:file==='analytics-privacy.html'});results.push({case:'page',file,width,...state});await c.ctx.close();
 }
 if(m.site==='touring')for(const state of ['404','malformed','valid']){
  const c=await context();const page=await c.ctx.newPage();let quoteRequests=0;
  await page.route('**/api/availability.php',r=>r.fulfill({status:state==='404'?404:200,contentType:'application/json',body:JSON.stringify(state==='valid'?{bookings:[]}:{unexpected:true})}));
  await page.route('**/api/quote.php',r=>{quoteRequests++;return r.abort();});
  await page.goto(base+'booking.html',{waitUntil:'networkidle',timeout:60000});
  const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();await page.locator('#availabilityStatus').waitFor();
  const booking=await page.evaluate(()=>({enabled:document.querySelectorAll('#calendar .day:not(:disabled)').length,continueDisabled:document.querySelector('#continueBtn').disabled,checkoutDisabled:document.querySelector('#checkoutBtn').disabled,message:document.querySelector('#availabilityStatus').textContent}));
  if(state!=='valid'&&(booking.enabled||!booking.continueDisabled||!booking.checkoutDisabled||!booking.message.includes('contact us')))throw Error('Availability did not fail closed: '+JSON.stringify(booking));
  if(state==='valid'&&booking.enabled===0)throw Error('Valid availability not enabled');
  if(quoteRequests)throw Error('Quote requested without dates');
  results.push({case:'availability',state,...booking,writes:c.writes()});
  if(state==='404')await page.locator('.booking-section').screenshot({path:'tracking-qa/booking-unavailable-390.png'});await c.ctx.close();
 }
 fs.writeFileSync('tracking-qa/results.json',JSON.stringify(results,null,2));console.log('Consent, lead semantics, affected layouts and availability checks passed. No Google hits or real submissions forwarded.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
