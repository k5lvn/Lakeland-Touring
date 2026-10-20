const {chromium}=require('playwright'),fs=require('node:fs');
(async()=>{const browser=await chromium.launch(),results=[];fs.mkdirSync('booking-standby-qa',{recursive:true});try{
 for(const width of [390,1440]){
 const ctx=await browser.newContext({viewport:{width,height:1000}}),page=await ctx.newPage();let writes=0;
 await page.route('**/*',route=>{const req=route.request(),u=new URL(req.url());if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname))return route.abort();if(!['GET','HEAD'].includes(req.method())){writes++;return route.abort();}return route.continue();});
 const response=await page.goto('https://lakelandtouring.uk/booking.html',{waitUntil:'networkidle',timeout:60000});if(response.status()!==200)throw Error('Booking page unavailable');
 const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();
 await page.locator('#availabilityStatus').waitFor();
 const state=await page.evaluate(()=>({enabled:document.querySelectorAll('#calendar .day:not(:disabled)').length,continueDisabled:document.querySelector('#continueBtn').disabled,checkoutDisabled:document.querySelector('#checkoutBtn').disabled,message:document.querySelector('#availabilityStatus').textContent,overflow:document.documentElement.scrollWidth>innerWidth+2}));
 if(state.enabled||!state.continueDisabled||!state.checkoutDisabled||!state.message.includes('contact us')||state.overflow||writes)throw Error(JSON.stringify(state));
 await page.locator('.booking-section').screenshot({path:'booking-standby-qa/locked-booking-'+width+'.png'});results.push({width,...state,writesForwarded:0});await ctx.close();
 }
 fs.writeFileSync('booking-standby-qa/results.json',JSON.stringify(results,null,2));console.log('Live standby calendar and checkout remain disabled at phone/desktop widths.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
