const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
(async()=>{
const root='site-release-20261020/files';
const files=fs.readdirSync(root).filter(f=>f.endsWith('.html')&&f!=='index.html');
if(!files.length){console.log('No new guide pages in this release');return;}
const browser=await chromium.launch({headless:true});fs.mkdirSync('release-qa',{recursive:true});const results=[];
try{for(const file of files)for(const width of [390,1440]){
 const page=await browser.newPage({viewport:{width,height:900}});
 await page.route('**/*',r=>{
  const u=new URL(r.request().url()),name=u.pathname.slice(1),p=path.join(root,name);
  if(u.hostname==='lakelandtouring.uk'&&fs.existsSync(p)&&fs.statSync(p).isFile())return r.fulfill({status:200,contentType:name.endsWith('.webp')?'image/webp':'text/html',body:fs.readFileSync(p)});
  if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname))return r.abort();
  if(!['GET','HEAD','OPTIONS'].includes(r.request().method()))return r.abort();
  return r.continue();
 });
 await page.goto('https://lakelandtouring.uk/'+file,{waitUntil:'networkidle',timeout:60000});
 const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();
 await page.evaluate(()=>document.fonts.ready);
 const m=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,canonical:document.querySelector('link[rel="canonical"]')?.href,brokenImages:Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src)}));
 if(m.width>width+1||m.h1!==1||m.brokenImages.length||m.canonical!=='https://lakelandtouring.uk/'+file)throw Error(JSON.stringify({file,width,...m}));
 if(!await page.locator('.guide a[href="booking.html"]').first().isVisible())throw Error('Booking link missing');
 await page.screenshot({path:`release-qa/${file}-${width}.png`,fullPage:true});results.push({file,width,...m});await page.close();
}fs.writeFileSync('release-qa/guides-results.json',JSON.stringify(results,null,2));console.log(files.length+' guide pages passed phone and desktop checks');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
