const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN,args:['--no-sandbox']});
for(const width of [390,1440]){
 const page=await browser.newPage({viewport:{width,height:900}});await page.goto('file://'+path.resolve('touring-gallery/test.html'));
 await page.locator('[data-photo]').first().click();await page.locator('dialog[open]').waitFor();
 const img=page.locator('.viewer-image');await img.evaluate(el=>el.decode());
 if(await page.locator('.viewer-count').textContent()!=='1 / 10')throw Error('Wrong image count');
 await page.locator('[data-next]').click();if(await page.locator('.viewer-count').textContent()!=='2 / 10')throw Error('Next failed');
 await page.keyboard.press('ArrowLeft');if(await page.locator('.viewer-count').textContent()!=='1 / 10')throw Error('Previous failed');
 const fit=await img.evaluate(el=>{const r=el.getBoundingClientRect();return el.naturalWidth>1000&&r.width<=innerWidth&&r.height<=innerHeight});if(!fit)throw Error('Photo does not fit viewport or source too small');
 await page.keyboard.press('Escape');if(await page.locator('dialog').isVisible())throw Error('Escape failed');
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Page overflows');
 await page.locator('[data-view-all]').click();await page.locator('.viewer-thumbnails button').last().click();if(await page.locator('.viewer-count').textContent()!=='10 / 10')throw Error('Thumbnail failed');
 await page.screenshot({path:`gallery-check-${width}.png`});console.log('PASS viewer next/previous, keyboard, close, thumbnails and image fit:',width);await page.close();}
await browser.close()})().catch(e=>{console.error(e);process.exit(1)});
