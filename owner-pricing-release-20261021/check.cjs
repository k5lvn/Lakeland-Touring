const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
const root='owner-pricing-release-20261021',m=JSON.parse(fs.readFileSync(`${root}/manifest.json`));
(async()=>{fs.mkdirSync(`${root}/qa`,{recursive:true});const b=await chromium.launch({headless:true}),results=[];
try{for(const width of [390,1440]){for(const name of Object.keys(m.files)){
const c=await b.newContext({viewport:{width,height:1000}}),p=await c.newPage();
await c.route('**/*',async r=>{const u=new URL(r.request().url());if(r.request().method()!=='GET'||/analytics|googletag|facebook|doubleclick/i.test(u.href))return r.abort();
const path=u.pathname==='/'?'index.html':u.pathname.slice(1);if(u.hostname==='lakelandtouring.uk'&&Object.hasOwn(m.files,path))return r.fulfill({contentType:'text/html',body:fs.readFileSync(`${root}/files/${path}`)});
if(u.hostname!=='lakelandtouring.uk'&&!['fonts.googleapis.com','fonts.gstatic.com'].includes(u.hostname))return r.abort();return r.continue();});
await p.goto(m.base_url+name,{waitUntil:'networkidle',timeout:60000});
await p.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}scrollTo(0,0)});await p.waitForTimeout(400);
assert.equal(await p.locator('h1').count(),1);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);
const broken=await p.evaluate(()=>[...document.images].filter(i=>i.getBoundingClientRect().width>0&&i.getBoundingClientRect().height>0&&getComputedStyle(i).visibility!=='hidden'&&(!i.complete||!i.naturalWidth)).map(i=>i.getAttribute('src')));assert.deepEqual(broken,[]);
if(name==='owners-garage.html'){await p.getByRole('heading',{name:/£49 a year/}).waitFor();assert.match(await p.locator('main').innerText(),/£25 per confirmed booking/);assert.match(await p.locator('main').innerText(),/not applied automatically/);}
if(name==='booking.html'){assert.match(await p.locator('body').innerText(),/Online checkout is currently unavailable/);assert.equal(await p.locator('#continueBtn').isDisabled(),true);}
await p.screenshot({path:`${root}/qa/${name}-${width}.png`,fullPage:true});results.push({page:name,width,overflow:false,brokenImages:broken});await c.close();
}}}finally{await b.close();fs.writeFileSync(`${root}/qa/results.json`,JSON.stringify(results,null,2));}console.log('Passed six phone/desktop public-copy checks with tracking and writes blocked.');})().catch(e=>{console.error(e);process.exit(1)});
