const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const width of [390,768,1440]){
   const page=await browser.newPage({viewport:{width,height:950}});
   await page.route('https://lakelandtouring.uk/**',route=>{
    const u=new URL(route.request().url());const n=u.pathname==='/'?'index.html':u.pathname.slice(1);
    if(fs.existsSync('destinations-qa/'+n))return route.fulfill({status:200,contentType:n.endsWith('.png')?'image/png':n.endsWith('.css')?'text/css':'text/html',body:fs.readFileSync('destinations-qa/'+n)});
    return route.continue();
   });
   for(const n of ['','explore-destinations.html']){
    await page.goto('https://lakelandtouring.uk/'+n,{waitUntil:'domcontentloaded'});
    if(await page.locator('.lt-place').count()!==6)throw Error('Six destination cards required');
    if(await page.locator('.lt-nearby a').count()!==3)throw Error('Three nearby regions required');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Horizontal overflow '+width);
    await page.evaluate(()=>new Promise((resolve,reject)=>{const img=new Image();img.onload=resolve;img.onerror=reject;img.src='/touring-approved-destinations-20261031.png'}));
    await page.waitForFunction(()=>{const img=document.querySelector('.lt-main-logo');return img&&img.complete&&img.naturalWidth>0});
    for(const href of await page.locator('.lt-place,.lt-nearby a').evaluateAll(xs=>xs.map(x=>x.getAttribute('href')))){
     const [path,id]=href.split('#');if(fs.existsSync('destinations-qa/'+path)){const text=fs.readFileSync('destinations-qa/'+path,'utf8');if(id&&!text.includes('id="'+id+'"'))throw Error('Missing anchor '+href);}else{const res=await page.request.get('https://lakelandtouring.uk/'+path);if(!res.ok())throw Error('Broken nearby link '+href);}
    }
    await page.locator('#destinations').screenshot({path:'destinations-qa/preview-'+(n?'destinations':'home')+'-'+width+'.png'});
   }
   await page.close();
  }
  console.log('PASS: 390/768/1440px, six images, nearby links, local guide anchors, logo and no horizontal overflow');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
