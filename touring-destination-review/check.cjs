const {chromium}=require('playwright'),fs=require('fs');
(async()=>{const browser=await chromium.launch({headless:true});fs.mkdirSync('touring-guide-qa',{recursive:true});const results=[];
try{for(const file of fs.readdirSync('touring-destination-review/files').filter(f=>f.endsWith('.html')))for(const width of [390,1440]){
 const page=await browser.newPage({viewport:{width,height:900}});await page.route('**/*',r=>{
  const u=new URL(r.request().url()),name=u.pathname.slice(1),p='touring-destination-review/files/'+name;
  if(u.hostname==='lakelandtouring.uk'&&fs.existsSync(p)&&fs.statSync(p).isFile())return r.fulfill({status:200,contentType:'text/html',body:fs.readFileSync(p)});
  if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname))return r.abort();return r.continue();
 });
 await page.goto('https://lakelandtouring.uk/'+file,{waitUntil:'networkidle',timeout:60000});const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();await page.evaluate(()=>document.fonts.ready);
 const m=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,canonical:document.querySelector('link[rel="canonical"]')?.href,brokenImages:Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src)}));
 if(m.width>width+1||m.h1!==1||m.brokenImages.length)throw Error(JSON.stringify({file,width,...m}));
 if(!await page.locator('.guide a[href="booking.html"]').first().isVisible())throw Error('Booking link missing');
 await page.screenshot({path:`touring-guide-qa/${file}-${width}.png`,fullPage:true});results.push({file,width,...m});await page.close();
}fs.writeFileSync('touring-guide-qa/results.json',JSON.stringify(results,null,2));console.log('All guide pages passed phone and desktop checks');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
