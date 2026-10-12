const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/Users/agiuser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const report={checks:[],errors:[],environment:'Local Chrome headless; not a physical phone'};
try{const page=await browser.newPage({viewport:{width:1440,height:1050}});page.on('pageerror',e=>report.errors.push(e.message));await page.goto('http://127.0.0.1:8768/?v=033light');await page.waitForFunction(()=>window.__lab?.state.ready);
const result=await page.evaluate(()=>{const l=__lab;const key=l.camera.getObjectByName('inspection_key');const positions=l.camera.position.toArray(),target=l.controls.target.toArray();const checks=[];const check=(name,pass)=>checks.push({name,pass});
check('Initial camera faces anatomical front without lateral offset',Math.abs(positions[0]-target[0])<1e-9&&Math.abs(positions[1]-target[1])<1e-9&&positions[2]<target[2]);
check('Camera-relative front light exists',key?.parent===l.camera&&key.position.length()===0);
check('Projected shadow maps disabled',!l.renderer.shadowMap.enabled);
const colors=()=>JSON.stringify([...l.meshes].map(([id,m])=>[id,m.material.color.toArray(),m.material.emissive.toArray()]));const reference=colors(),ratio=l.renderer.getPixelRatio();
for(const direction of [1,-1]){l.state.direction=direction;l.togglePlay(true);check('Playback keeps material colors direction '+direction,colors()===reference);check('Playback keeps pixel ratio direction '+direction,l.renderer.getPixelRatio()===ratio);l.togglePlay(false);}
for(const angle of [0,30,82,120]){l.state.angle=angle;const sample=direction=>{l.state.direction=direction;l.pose();return [...l.meshes.keys()].map(id=>l.meshPoint(id,0))};check('Same-angle geometry is direction independent '+angle,JSON.stringify(sample(1))===JSON.stringify(sample(-1)));}
l.state.angle=30;l.pose();return checks;});
for(const c of result){assert.ok(c.pass,c.name);report.checks.push(c)}
for(const view of ['front','side','back']){await page.evaluate(v=>__lab.view(v),view);await page.waitForTimeout(400);await page.locator('#canvas-host').screenshot({path:path.join(__dirname,'lighting-'+view+'.png')});const aligned=await page.evaluate(()=>{const l=__lab,k=l.camera.getObjectByName('inspection_key');l.camera.updateMatrixWorld(true);return k.getWorldPosition(l.camera.position.clone()).distanceTo(l.camera.position)<1e-9;});assert.ok(aligned);report.checks.push({name:'Front light follows '+view+' view',pass:true});}
assert.equal(report.errors.length,0);report.status='passed';console.log(JSON.stringify(report));
}catch(e){report.status='failed';report.failure=String(e);process.exitCode=1;console.error(e)}finally{fs.writeFileSync(path.join(__dirname,'lighting-verification.json'),JSON.stringify(report,null,2));await browser.close()}})();
