// NODE_PATH must include playwright. Run after tests/viewer_fixtures.py.
let chromium;
try { ({chromium}=require('playwright')); }
catch { ({chromium}=require('../frontend/node_modules/playwright')); }
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
(async()=>{
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1280,height:740}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let checks=0;
  for(const name of ['site','thermal','fire','smoke','structure','large']){
    const started=Date.now();
    await page.goto(pathToFileURL(path.resolve(`output_reports/viewer/${name}.html`)).href);
    await page.waitForFunction(()=>window.__epcViewer?.ready,{timeout:30000});
    assert.equal(await page.locator('#error').isVisible(),false);checks++;
    await page.locator('[data-view=top]').click();assert.equal(await page.evaluate(()=>window.__epcViewer.view),'top');checks++;
    await page.locator('[data-view=front]').click();assert.equal(await page.evaluate(()=>window.__epcViewer.view),'front');checks++;
    await page.locator('[data-view=iso]').click();
    const beforeEdge=await page.locator('#edges').getAttribute('class');await page.locator('#edges').click();assert.notEqual(await page.locator('#edges').getAttribute('class'),beforeEdge);checks++;
    await page.locator('[data-layer=equipment]').uncheck();await page.locator('[data-layer=equipment]').check();checks++;
    await page.locator('#section').fill('65');assert.match(await page.locator('#section-value').textContent(),/m/);await page.locator('#section').fill('100');checks++;
    if(name==='site'){
      await page.locator('[data-view=top]').click();
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      async function center(label){const b=await page.locator('.model-label').filter({hasText:new RegExp(`^${label}$`)}).boundingBox();return [b.x+b.width/2,b.y+b.height];}
      const p=await center('ENC-009'),q=await center('ENC-010');
      await page.mouse.click(...p);assert.equal(await page.locator('#selection-name').textContent(),'ENC-009');checks++;
      await page.locator('#measure').click();await page.mouse.click(...p);await page.mouse.click(...q);
      const distance=parseFloat(await page.locator('#measure-result').textContent());
      const expected=await page.evaluate(()=>{const a=window.__epcViewer.geometry.find(x=>x.label==='ENC-009'),b=window.__epcViewer.geometry.find(x=>x.label==='ENC-010');return Math.hypot(a.x-b.x,a.y-b.y);});
      assert.ok(Math.abs(distance-expected)<.02,`${distance} vs ${expected}`);checks++;
      await page.locator('#measure').click();await page.locator('[data-view=iso]').click();
    }
    if(!['site','large'].includes(name)){
      await page.locator('#play').click();await page.waitForFunction(()=>window.__epcViewer.frame>0);
      await page.locator('#play').click();const paused=await page.evaluate(()=>window.__epcViewer.frame);await page.waitForTimeout(450);assert.equal(await page.evaluate(()=>window.__epcViewer.frame),paused);checks++;
      const max=await page.locator('#timeline').getAttribute('max');await page.locator('#timeline').fill(max);assert.equal(await page.evaluate(()=>window.__epcViewer.frame),Number(max));checks++;
      await page.screenshot({path:`output_reports/viewer/${name}-result.png`});
      await page.locator('#reset').click();assert.equal(await page.evaluate(()=>window.__epcViewer.frame),0);checks++;
      if(name==='thermal'){
        assert.equal(await page.evaluate(()=>window.__epcViewer.flowFrame),0);checks++;
        const pauseAtThree=()=>page.evaluate(()=>new Promise(resolve=>{
          function watch(){if(window.__epcViewer.frame>=3){document.getElementById('play').click();resolve();}else requestAnimationFrame(watch);}watch();
        }));
        await page.locator('#play').click();await pauseAtThree();
        assert.equal(await page.evaluate(()=>window.__epcViewer.flowFrame),3);checks++;
        await page.locator('#reset').click();await page.locator('#play').click();await pauseAtThree();
        assert.equal(await page.evaluate(()=>window.__epcViewer.flowFrame),3);checks++;
      }
    }
    await page.screenshot({path:`output_reports/viewer/${name}.png`});
    console.log(`${name}: ready + controls + playback checked in ${Date.now()-started}ms`);
  }
  await page.setViewportSize({width:390,height:740});
  await page.locator('#panels').click();assert.equal(await page.locator('#layers').isVisible(),true);checks++;
  await page.locator('[data-layer=equipment]').uncheck();await page.locator('[data-layer=equipment]').check();checks++;
  await page.locator('#section').fill('50');await page.locator('#section').fill('100');checks++;
  await page.locator('#panels').click();await page.screenshot({path:'output_reports/viewer/mobile.png'});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);checks++;
  assert.deepEqual(errors,[]);checks++;
  console.log(`${checks} browser checks passed; JS exceptions: ${errors.length}`);
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
