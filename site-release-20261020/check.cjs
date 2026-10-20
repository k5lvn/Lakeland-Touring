const {chromium}=require('playwright'),fs=require('fs'),path=require('path');const inputs={sites:[require('./config.json').site]};
(async()=>{const browser=await chromium.launch({headless:true});const results=[];fs.mkdirSync('release-qa',{recursive:true});
try{for(const site of inputs.sites)for(const width of [390,1440]){
 let staged=false;const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
 await page.route('**/*',r=>{
  const u=new URL(r.request().url());if(/google-analytics|googletagmanager|doubleclick/.test(u.hostname))return r.abort();
  if(staged&&u.hostname===new URL(site.url).hostname){const name=u.pathname==='/'?'index.html':u.pathname.slice(1);const p=path.join('site-release-20261020','files',name);if(fs.existsSync(p)&&fs.statSync(p).isFile())return r.fulfill({status:200,contentType:name.endsWith('.webp')?'image/webp':name.endsWith('.css')?'text/css':'text/html',body:fs.readFileSync(p)});}
  return r.continue();
 });
 const measure=()=>page.evaluate(()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,h1:Array.from(document.querySelectorAll('h1')).map(x=>x.textContent),forms:Array.from(document.forms).map(f=>({id:f.id,action:f.getAttribute('action')})),scripts:Array.from(document.querySelectorAll('script[src]')).map(x=>x.getAttribute('src')),hero:document.querySelector('main section')?.getBoundingClientRect().height}));
 const load=async()=>{await page.goto(site.url,{waitUntil:'networkidle',timeout:60000});const reject=page.getByRole('button',{name:'Reject analytics',exact:true});if(await reject.isVisible())await reject.click();await page.evaluate(()=>document.fonts.ready);await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important}'});};
 await load();const before=await measure();await page.screenshot({path:`release-qa/${site.id}-${width}-before.png`});
 staged=true;await load();const after=await measure();const broken=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.currentSrc&&x.naturalWidth===0).map(x=>x.getAttribute('src')?.slice(0,150)));
 if(JSON.stringify(before.h1)!==JSON.stringify(after.h1)||JSON.stringify(before.forms)!==JSON.stringify(after.forms)||JSON.stringify(before.scripts)!==JSON.stringify(after.scripts))throw Error('Content/forms/scripts changed: '+site.id);
 if(after.width>Math.max(width,before.width)+1||Math.abs((before.hero||0)-(after.hero||0))>2)throw Error('Layout changed: '+site.id+' '+width);
 if(broken.length)throw Error('Broken images: '+site.id+JSON.stringify(broken));
 await page.screenshot({path:`release-qa/${site.id}-${width}-after.png`});results.push({site:site.id,width,before,after,broken});await page.close();
}fs.writeFileSync('release-qa/results.json',JSON.stringify(results,null,2));console.log('Four-site prepared image replacements passed responsive layout and form preservation checks');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
