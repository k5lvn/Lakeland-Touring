// Candidate layout and journey QA. Every request is fulfilled from fixtures or
// local repository files; no traffic, enquiry or payment leaves this process.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'booking-review-qa');
const iso=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
(async()=>{
 fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch();const results=[];
 try{for(const width of [390,1440]){
  const ctx=await browser.newContext({viewport:{width,height:1000}}),page=await ctx.newPage();
  const month=new Date();month.setDate(1);month.setMonth(month.getMonth()+1);
  const day=n=>{const d=new Date(month);d.setDate(n);return iso(d)};
  let own=null,quotes=0,releases=0;const now=()=>Math.floor(Date.now()/1000);
  const availability=()=>({csrf:'a'.repeat(64),server_time:now(),available_through:day(28),periods:[{start:day(1),end:day(28),peak:true}],bookings:[{start:day(15),end:day(17)}],holds:[{start:day(10),end:day(12),hold_until:now()+600}],own_hold:own});
  await page.route('**/*',async route=>{
   const u=new URL(route.request().url());if(u.hostname!=='fixture.invalid')return route.abort();
   if(u.pathname==='/api/availability.php')return route.fulfill({json:availability()});
   if(u.pathname==='/api/quote.php'){
    quotes++;const input=route.request().postDataJSON();own={start:input.start,end:input.end,state:'held',hold_until:own?.hold_until||now()+900};
    return route.fulfill({json:{...own,server_time:now(),hire_pence:59500,pay_now_pence:25000,balance_pence:34500,nights:7,balance_due_date:day(1)}});
   }
   if(u.pathname==='/api/release-hold.php'){own=null;releases++;return route.fulfill({json:{released:true}});}
   if(u.pathname.startsWith('/api/'))throw Error('Unexpected API operation: '+u.pathname);
   if(u.pathname==='/analytics-consent.js'||u.pathname==='/gigi.js')return route.fulfill({contentType:'application/javascript',body:''});
   let file=u.pathname==='/booking.html'?path.join(root,'tracking-release-20261020/files/booking.html'):u.pathname==='/booking.js'?path.join(root,'booking-backend/frontend/booking.js'):path.join(root,'site',u.pathname.slice(1));
   if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:''});
   return route.fulfill({path:file});
  });
  await page.goto('http://fixture.invalid/booking.html');
  await page.getByText('Choose your collection and return dates.',{exact:true}).waitFor();
  await page.locator('#nextMonth').click();
  const held=page.locator('.day.held').first(),booked=page.locator('.day.booked').first();
  assert.equal(await held.isDisabled(),true);assert.equal(await booked.isDisabled(),true);
  assert.match(await held.getAttribute('aria-label'),/held by another customer/);
  const fmt=n=>new Date(month.getFullYear(),month.getMonth(),n).toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
  await page.getByRole('button',{name:fmt(1)+', available, peak period',exact:true}).click();
  await page.getByRole('button',{name:fmt(8)+', available, peak period',exact:true}).click();
  await page.locator('#availabilityStatus').filter({hasText:/Your dates are held for (15|14):/}).waitFor();
  assert.equal(await page.locator('#continueBtn').isEnabled(),true);
  const before=quotes;await page.evaluate(()=>loadAvailability(true));assert.equal(quotes,before,'Polling must not POST another quote');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);
  await page.locator('.calendar-card').screenshot({path:path.join(out,`calendar-${width}.png`)});
  await page.getByRole('button',{name:'Release selected dates',exact:true}).click();
  await page.getByText('Choose your collection and return dates.',{exact:true}).waitFor();assert.equal(releases,1);
  results.push({width,exclusiveHeldDatesDisabled:true,bookedDatesDisabled:true,countdown:true,pollDoesNotRenew:true,release:true,noOverflow:true,externalRequestsForwarded:0});await ctx.close();
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify(results,null,2));console.log('Passed candidate calendar and hold/release journey at phone and desktop widths.');
})().catch(e=>{console.error(e);process.exit(1)});
