const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert');
const root='touring-upgrade-20261025/files',base='https://lakelandtouring.uk/';
fs.mkdirSync('touring-upgrade-qa',{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true});let results=[];
 async function setup(width){const ctx=await browser.newContext({viewport:{width,height:900}});let google=0,writes=0;
 await ctx.route('**/*',async r=>{let u=new URL(r.request().url()),n=u.pathname==='/'?'index.html':u.pathname.slice(1),p=path.join(root,n);
 if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname)){google++;return r.fulfill({status:204,body:''});}
 if(!['GET','HEAD'].includes(r.request().method())){writes++;return r.abort();}
 if(u.hostname==='lakelandtouring.uk'&&fs.existsSync(p)&&fs.statSync(p).isFile())return r.fulfill({status:200,contentType:n.endsWith('.js')?'text/javascript':'text/html',body:fs.readFileSync(p)});
 if(u.hostname==='lakelandtouring.uk'&&n==='api/availability.php')return r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Online booking is unavailable. Please contact us.'})});
 const aliases={'styles.css':'touring-upgrade-20261025/qa-assets/styles.css','brand.css':'touring-upgrade-20261025/qa-assets/brand.css','booking.js':'touring-upgrade-20261025/qa-assets/booking.js','gallery.css':'touring-gallery/gallery.css','gallery.js':'touring-gallery/gallery.js','seo-performance/buttermere-4k.webp':'touring-images/buttermere-4k.jpg','seo-performance/lakeland-touring-official.webp':'site/Assets/lakeland-touring-official.png'};
 let asset=aliases[n]||('site/'+n);if(n.startsWith('review-assets/'))asset='google-review-20261022/files/'+n;if(n==='garage.css')asset='owner-garage/garage.css';
 if(u.hostname==='lakelandtouring.uk'&&fs.existsSync(asset)&&fs.statSync(asset).isFile()){let type=asset.endsWith('.css')?'text/css':asset.endsWith('.js')?'text/javascript':asset.endsWith('.png')?'image/png':'image/jpeg';return r.fulfill({status:200,contentType:type,body:fs.readFileSync(asset)});}
 return r.abort();});return {ctx,google:()=>google,writes:()=>writes};}
 try{
 const pages=fs.readdirSync(root).filter(x=>x.endsWith('.html'));
 for(const width of [390,1440]){
 const c=await setup(width),page=await c.ctx.newPage();
 for(const name of pages){
 await page.goto(base+(name==='index.html'?'':name),{waitUntil:'networkidle',timeout:60000});
 const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();
 await page.locator('footer #lt-cookie-settings').waitFor();
 const state=await page.evaluate(()=>({width:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,cookiePosition:getComputedStyle(document.getElementById('lt-cookie-settings')).position,broken:[...document.images].filter(x=>x.getAttribute('src')&&x.complete&&x.naturalWidth===0&&new URL(x.src,location.href).hostname==='lakelandtouring.uk').map(x=>x.src)}));
 assert(state.width<=width+1,JSON.stringify({name,width,...state}));assert.equal(state.h1,1);assert(!['fixed','sticky'].includes(state.cookiePosition));assert.equal(state.broken.length,0,JSON.stringify({name,...state}));assert.equal(c.google(),0,'Google before consent/rejection');
 if(name==='booking.html'){await page.locator('#availabilityStatus').waitFor();assert.equal(await page.locator('#calendar .day:not(:disabled)').count(),0);assert(!(await page.locator('#continueBtn').isEnabled()));assert(!(await page.locator('#checkoutBtn').isEnabled()));assert(await page.getByRole('link',{name:'Ask about dates on WhatsApp ↗',exact:true}).isVisible());}
 if(name==='caravan-hire-faq.html'){await page.getByText('How do I check dates or book?',{exact:true}).click();assert(await page.getByText('An enquiry does not reserve dates.',{exact:false}).isVisible());}
 if(['index.html','booking.html','caravan-hire-faq.html','lake-district-caravan-guide.html'].includes(name))await page.screenshot({path:`touring-upgrade-qa/${name}-${width}.png`,fullPage:true});
 results.push({name,width,...state});
 }
 assert.equal(c.writes(),0);await c.ctx.close();
 }
 // Consent transitions, persistence, expiry and withdrawal with all Google calls blocked.
 const c=await setup(390),page=await c.ctx.newPage();await page.goto(base,{waitUntil:'networkidle'});
 assert.equal(c.google(),0);await page.getByRole('button',{name:'Accept analytics',exact:true}).click();
 assert(!(await page.locator('#lt-analytics-banner').isVisible()));assert(await page.evaluate(()=>window.WorxAnalytics.track('contact_phone_click')));
 await page.reload({waitUntil:'networkidle'});assert(!(await page.locator('#lt-analytics-banner').isVisible()));
 await page.locator('#lt-cookie-settings').click();await page.getByRole('button',{name:'Reject analytics',exact:true}).click();assert(!(await page.evaluate(()=>window.WorxAnalytics.track('contact_phone_click'))));
 await page.reload({waitUntil:'networkidle'});assert(!(await page.locator('#lt-analytics-banner').isVisible()));
 await page.evaluate(()=>localStorage.setItem('lt-analytics-consent-v1',JSON.stringify({allowed:true,at:Date.now()-181*86400000})));await page.reload({waitUntil:'networkidle'});assert(await page.getByRole('button',{name:'Reject analytics',exact:true}).isVisible());
 assert.equal(c.writes(),0);await c.ctx.close();
 fs.writeFileSync('touring-upgrade-qa/results.json',JSON.stringify({pages:results,consent:'accept/reject/persistence/expiry/withdrawal passed',googleRequestsForwarded:0,customerWrites:0},null,2));console.log('PASS: 38 page/viewport checks, consent lifecycle and disabled booking; no real submissions or Analytics forwarded.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
