const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN});try{
for(const width of [390,1440]){const ctx=await browser.newContext({viewport:{width,height:900}});
await ctx.route('**/*',async route=>{const req=route.request(),u=new URL(req.url());if(u.hostname!=='lakelandtouring.uk'||req.method()!=='GET')return route.abort();let n=u.pathname.slice(1)||'index.html';if(n==='analytics-consent.js')return route.fulfill({body:''});if(fs.existsSync('navigation-qa/'+n)&&n.endsWith('.html'))return route.fulfill({contentType:'text/html',body:fs.readFileSync('navigation-qa/'+n)});return route.continue();});
const p=await ctx.newPage();await p.goto('https://lakelandtouring.uk/',{waitUntil:'networkidle'});
const link=p.locator('.topbar nav a[href="explore-destinations.html"]');assert.equal(await link.innerText(),'Explore Destinations');
if(!await link.isVisible())await p.locator('.menu-toggle').click();await link.click();await p.waitForURL('**/explore-destinations.html');
assert.equal(await p.locator('.guide-card').count(),11);const borders=p.locator('.guide-card').filter({has:p.locator('a[href="scottish-borders-caravan-guide.html"]')});await borders.scrollIntoViewIfNeeded();assert(await borders.isVisible());
assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:`navigation-qa/destinations-${width}.png`,fullPage:true});await borders.getByRole('link').click();await p.waitForURL('**/scottish-borders-caravan-guide.html');assert(await p.locator('h1').isVisible());await ctx.close();console.log('PASS: homepage menu → destinations → Scottish Borders at',width);}
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
