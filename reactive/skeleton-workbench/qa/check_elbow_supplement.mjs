import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import * as THREE from '../vendor/three.module.js';
const base=new URL('../',import.meta.url),three=new URL('vendor/three.module.js',base).href;
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const utility=url((await readFile(new URL('vendor/BufferGeometryUtils.js',base),'utf8')).replace("from 'three'",`from '${three}'`));
const loaderSource=(await readFile(new URL('vendor/GLTFLoader.js',base),'utf8')).replace("from 'three'",`from '${three}'`).replace("from './BufferGeometryUtils.js'",`from '${utility}'`);
const {GLTFLoader}=await import(url(loaderSource));
const {createElbowMotion}=await import(url((await readFile(new URL('src/elbow-motion.js',base),'utf8')).replace("from 'three'",`from '${three}'`)));
const json=async path=>JSON.parse(await readFile(new URL(path,base),'utf8'));
const load=async path=>{const b=await readFile(new URL(path,base));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;};
const skeleton=await json('z-anatomy-candidate/structures.json'),tissues=await json('z-anatomy-candidate/latest-reviewed-tissues.json');
const supplement=await json('z-anatomy-candidate/elbow-supplement.json');
const axisData=await json('motion/elbow-axis.json'),template=await load('motion/elbow-ligaments-complete.glb');
const scene=new THREE.Scene(),groups=new Map(),rows=new Map([...skeleton.bones,...tissues.objects.filter(r=>!supplement.replaces_ids.includes(r.id)),...supplement.objects].map(r=>[r.id,r]));
for(const path of [skeleton.regions.find(r=>r.name==='上肢').file,tissues.file,supplement.file]){const root=await load(path);root.updateMatrixWorld(true);const found=[];root.traverse(o=>{if(rows.has(o.name))found.push(o);});for(const o of found){scene.attach(o);o.userData.rest=o.position.clone();o.userData.offset=new THREE.Vector3();o.userData.line=new THREE.Line();groups.set(o.name,o);}}
const results=[];
for(const side of ['R','L']){
 const before=new Map([...groups].map(([id,o])=>[id,{o,p:o.position.clone(),q:o.quaternion.clone(),scale:o.scale.clone()}]));
 const controller=createElbowMotion({groups,rows,scene,axisData,side,ligamentTemplate:template});
 assert.ok(controller.ids.has('bone_humerus_'+(side==='R'?'L':'R')),'whole view includes opposite arm');
 controller.setView('local');assert.equal(controller.ids.size,38);controller.setLigaments(false);assert.equal(controller.ids.size,30);controller.setLigaments(true);
 controller.setAngle(60);
 controller.setLayerFilter(r=>r?.tissue_layer==='ligament');assert.equal(controller.ids.size,8,'bone layer can be hidden during motion');
 controller.setLigaments(false);assert.equal(controller.ids.size,0,'both layers off hides all local objects');
 controller.setLayerFilter(r=>!r?.tissue);assert.equal(controller.ids.size,30,'bone layer can be restored independently');
 controller.setLigaments(true);assert.equal(controller.ids.size,30,'ligament checkbox respects layer filter');
 controller.setLayerFilter(r=>!r?.tissue||r.tissue_layer==='ligament');assert.equal(controller.ids.size,38);assert.equal(controller.angle,60,'layer changes preserve angle');
 const pivot=new THREE.Vector3().fromArray(axisData.sides[side].pivot),axis=new THREE.Vector3().fromArray(axisData.sides[side].axis);let maxAnchorError=0,nonRigid=0;
 for(const degrees of [0,2.5,30,62.5,90,117.5,120]){
  controller.setAngle(degrees);const q=new THREE.Quaternion().setFromAxisAngle(axis,THREE.MathUtils.degToRad(degrees));
  for(const prefix of ['elbow_ucl_anterior_','elbow_ucl_posterior_','elbow_lucl_','z_lig_radial_collateral_ligament_']){
   const id=prefix+side,src=template.getObjectByName(id),out=groups.get(id).geometry.getAttribute('position'),original=src.geometry.getAttribute('position'),weights=src.geometry.getAttribute('_motion_weight');
   for(let i=0;i<out.count;i++){const w=weights.getX(i),a=new THREE.Vector3().fromBufferAttribute(original,i),p=new THREE.Vector3().fromBufferAttribute(out,i);if(w<1e-6||w>1-1e-6){if(w>.5)a.sub(pivot).applyQuaternion(q).add(pivot);maxAnchorError=Math.max(maxAnchorError,p.distanceTo(a));}else if(degrees===90){a.sub(pivot).applyQuaternion(q).add(pivot);nonRigid=Math.max(nonRigid,p.distanceTo(a));}}
  }
 }
 assert.ok(maxAnchorError<1e-6);assert.ok(nonRigid>.001,'collaterals actually deform, not rigidly transported');
 const angle=controller.angle;controller.setView('whole');controller.bounds();assert.equal(controller.angle,angle,'changing view preserves motion angle');
 controller.dispose();for(const [id,r]of before){const o=groups.get(id);assert.equal(o,r.o);assert.ok(o.position.distanceTo(r.p)<1e-12);assert.ok(o.quaternion.angleTo(r.q)<1e-7);assert.ok(o.scale.equals(r.scale));}
 results.push({side,max_anchor_error_mm:maxAnchorError*1000,nonrigid_difference_mm:nonRigid*1000,original_objects_and_transforms_restored:true});
}
await writeFile(new URL('qa/elbow-supplement-validation.json',base),JSON.stringify({results,scope:'Actual GLB loading, exact candidate-anchor transport, nonrigid deformation, view toggles and exit restoration; not anatomical acceptance'},null,2)+'\n');console.log(results);
