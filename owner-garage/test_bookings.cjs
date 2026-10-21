const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const base=process.argv[2],out=path.join(process.cwd(),'booking-review-qa');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{for(const width of [390,1440]){
  const context=await browser.newContext({viewport:{width,height:1000}}),page=await context.newPage();
  await context.route('**/*',async r=>{
   if(new URL(r.request().url()).hostname!=='127.0.0.1')return r.abort();
   // The real application always redirects to its HTTPS production origin.
   // Keep fixture redirects on the disposable server; never forward them externally.
   const response=await r.fetch({maxRedirects:0}),headers=response.headers();
   if(headers.location?.startsWith('https://lakelandtouring.uk/garage.php'))headers.location=headers.location.replace('https://lakelandtouring.uk/garage.php',base);
   await r.fulfill({response,headers});
  });
  await page.goto(base);
  await page.locator('form').filter({has:page.locator('[name="action"][value="login"]')}).locator('[name="email"]').fill('a@example.test');
  await page.locator('form').filter({has:page.locator('[name="action"][value="login"]')}).locator('[name="password"]').fill('fixture-password-123');
  await page.getByRole('button',{name:'Open my garage'}).click();
  await page.getByRole('link',{name:'Bookings and payment confirmations'}).click();
  await page.getByRole('heading',{name:'Bookings',exact:true}).waitFor();
  assert.equal(await page.locator('.booking-card').count(),1);
  assert.equal(await page.locator('.customer-details').count(),1);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);
  await page.screenshot({path:path.join(out,`owner-bookings-${width}.png`),fullPage:true});
  await page.getByText('Booking history',{exact:true}).click();
  await page.getByText(/account 1/).first().waitFor();
  await context.close();
 }}finally{await browser.close();}
 console.log('Passed owner booking history and customer-details rendering at 390/1440px with no overflow; external requests blocked.');
})().catch(e=>{console.error(e);process.exit(1)});
