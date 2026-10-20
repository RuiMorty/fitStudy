import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as THREE from '../vendor/three.module.js';
const source=(await readFile(new URL('../src/elbow-motion.js',import.meta.url),'utf8')).replace("from 'three'",`from '${new URL('../vendor/three.module.js',import.meta.url).href}'`);
const {createElbowMotion}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const axisData=JSON.parse(await readFile(new URL('../motion/elbow-axis.json',import.meta.url),'utf8'));
for(const side of ['R','L']){
 const scene=new THREE.Scene(),groups=new Map(),rows=new Map();
 for(const [name,pos] of [['humerus',[0,1.3,0]],['radius',[.02,.9,0]],['ulna',[-.02,.9,0]],['metacarpal1',[0,.7,0]]]){
  const id='bone_'+name+'_'+side,o=new THREE.Mesh(new THREE.BoxGeometry(.01,.04,.01));o.position.fromArray(pos);scene.add(o);groups.set(id,o);rows.set(id,{region:'上肢',side});
 }
 const before=new Map([...groups].map(([id,o])=>[id,{p:o.position.clone(),q:o.quaternion.clone(),s:o.scale.clone()}]));
 const motion=createElbowMotion({groups,rows,scene,axisData,side});
 for(const angle of [0,30,60,90,120,0,120]){
  motion.setAngle(angle);
  assert.ok(groups.get('bone_humerus_'+side).position.equals(before.get('bone_humerus_'+side).p));
  assert.ok(Math.abs(groups.get('bone_radius_'+side).position.distanceTo(groups.get('bone_ulna_'+side).position)-.04)<1e-10);
  for(const [id,o] of groups)assert.ok(o.scale.equals(before.get(id).s));
 }
 motion.setAngle(0);for(const [id,o] of groups){assert.ok(o.position.distanceTo(before.get(id).p)<1e-12);assert.ok(o.quaternion.equals(before.get(id).q));}
 motion.dispose();assert.equal(scene.children.length,4);
}
console.log('PASS: bilateral rigid chain, fixed humerus, no scaling, exact rest recovery, guide disposal');
