const {chromium}=require('playwright');
const assert=require('assert');
(async()=>{const browser=await chromium.launch({headless:true});try{
 const context=await browser.newContext();const page=await context.newPage();const requests=[];
 page.on('request',r=>{if(/googletagmanager\.com|google-analytics\.com/.test(r.url()))requests.push(r.url());});
 await page.goto('https://lakelandtouring.uk/',{waitUntil:'networkidle'});
 await page.getByRole('button',{name:'Reject analytics',exact:true}).waitFor();assert.equal(requests.length,0,'Google requested before consent');
 await page.getByRole('button',{name:'Reject analytics',exact:true}).click();assert.equal(requests.length,0,'Google requested after rejection');
 await page.getByRole('button',{name:'Cookie settings',exact:true}).click();
 await page.getByRole('button',{name:'Accept analytics',exact:true}).waitFor();
 // Keep this automated browser rejected: do not send synthetic Analytics visits.
 await page.screenshot({path:'analytics-consent-live.png',fullPage:false});
 await page.getByRole('button',{name:'Reject analytics',exact:true}).click();
 assert.equal(requests.length,0);console.log('LIVE PRIVACY VERIFIED: no Google requests before consent or after rejection; settings reopen.');
 }finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
