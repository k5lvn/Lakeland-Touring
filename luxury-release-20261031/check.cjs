const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const sitemap=fs.readFileSync('luxury-qa/sitemap.xml','utf8');
 for(const retired of ['garage.php?view=browse','owners-garage.html','owner-terms.html','garage-privacy.html'])if(sitemap.includes(retired))throw Error('Obsolete URL remains in sitemap: '+retired);
 for(const kept of ['scottish-borders-caravan-guide.html','/reviews/'])if(!sitemap.includes(kept))throw Error('Required indexable URL missing from sitemap: '+kept);
 const homeHtml=fs.readFileSync('luxury-qa/index.html','utf8');
 const title=(homeHtml.match(/<title>(.*?)<\/title>/i)||[])[1]||'';
 if(title.length>60||!title.includes('Cumbria')||!title.includes('Delivered'))throw Error('Homepage SEO title is missing or too long: '+title);
 if(!homeHtml.includes('href="/reviews/"'))throw Error('Homepage Reviews link is missing');
 if((homeHtml.match(/data-hire-option=/g)||[]).length!==2)throw Error('Homepage must show exactly two hire options');
 for(const detail of ['£1.50 per mile','£600','£10 per day','£69 per week'])if(!homeHtml.includes(detail))throw Error('Missing approved hire detail: '+detail);
 if((homeHtml.match(/<div[^>]*\bdata-dk-review-banner=/g)||[]).length!==1)throw Error('Google Reviews banner was not preserved');
 for(const retired of ['garage.php?view=browse','owners-garage.html','owner-terms.html','garage-privacy.html'])if(homeHtml.includes(retired))throw Error('Obsolete homepage reference remains: '+retired);
 const browser=await chromium.launch({headless:true});
 try {
 for(const width of [390,1440]){
  const page=await browser.newPage({viewport:{width,height:950}});
  await page.route('https://lakelandtouring.uk/**',async route=>{
   const u=new URL(route.request().url());const name=u.pathname==='/'?'index.html':u.pathname.slice(1);
   if(fs.existsSync('luxury-qa/'+name)&&/\.(html|css|webp)$/.test(name))return route.fulfill({status:200,contentType:name.endsWith('.css')?'text/css':name.endsWith('.webp')?'image/webp':'text/html',body:fs.readFileSync('luxury-qa/'+name)});
   if(/google-analytics|googletagmanager|facebook\.net/.test(u.hostname))return route.abort();
   return route.continue();
  });
  for(const name of ['','booking.html','caravan-hire-faq.html','explore-destinations.html','lake-district-caravan-guide.html','scottish-borders-caravan-guide.html','analytics-privacy.html']){
   await page.goto('https://lakelandtouring.uk/'+name,{waitUntil:'domcontentloaded'});
   await page.locator('h1').waitFor();
   const bg=await page.locator('body').evaluate(x=>getComputedStyle(x).backgroundColor);if(bg!=='rgb(16, 31, 33)')throw Error('Theme mismatch '+name+' '+bg);
   if(name==='explore-destinations.html'){const bg=await page.locator('.guide').evaluate(x=>getComputedStyle(x).backgroundColor);if(bg!=='rgb(16, 31, 33)')throw Error('Guide theme mismatch');await page.screenshot({path:'luxury-qa/destinations-'+width+'.png',fullPage:true});}
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Overflow '+width+' '+name);
   if(name==='booking.html'||name==='caravan-hire-faq.html'){const content=(await page.locator('body').innerText()).replace(/\s+/g,' ');for(const detail of ['£1.50 per mile','£600','£10 per day','£69 per week'])if(!content.includes(detail))throw Error('Missing hire details on '+name+': '+detail);if((await page.locator('[data-hire-option]').count())!==2)throw Error('Expected two hire options on '+name);}
   if(name===''){
    if(width===390){await page.locator('.lt-menu').click();await page.locator('#lt-navigation').getByText('Our Experience',{exact:true}).click();if(await page.locator('.lt-menu').getAttribute('aria-expanded')!=='false')throw Error('Menu did not close');}
    await page.waitForFunction(()=>{const x=document.querySelector('.lt-main-logo');return x&&x.complete&&x.naturalWidth>0});
    if(await page.locator('a[href^="mailto:"]').count()<1)throw Error('Missing email quote link');
    await page.waitForFunction(()=>{const x=document.querySelector('.lt-hero>img');return x.complete&&x.naturalWidth>0});
    await page.locator('[data-photo]').first().click();await page.locator('dialog[open]').waitFor();await page.keyboard.press('Escape');if(await page.locator('dialog').isVisible())throw Error('Gallery did not close');
    await page.screenshot({path:'luxury-qa/home-'+width+'.png',fullPage:true});
   }
  }
  await page.close();
 }
 console.log('PASS: mobile/desktop, no overflow, menu, enquiry links, hero, booking and FAQ routes');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
