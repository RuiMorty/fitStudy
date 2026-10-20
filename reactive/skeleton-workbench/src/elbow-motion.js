import * as THREE from 'three';
// Rest-pose based bone chain plus display-only, anchored ligament deformation.
export function createElbowMotion({groups,rows,scene,axisData,side,ligamentTemplate=null}){
 const spec=axisData.sides[side],pivot=new THREE.Vector3().fromArray(spec.pivot),axis=new THREE.Vector3().fromArray(spec.axis).normalize();
 const bones=[...groups].filter(([id])=>{const r=rows.get(id);return r&&!r.tissue&&r.side===side&&r.region==='上肢';});
 const moving=bones.filter(([id])=>!/^bone_(scapula|clavicle|humerus)_/.test(id));
 if(!moving.some(([id])=>id==='bone_radius_'+side)||!moving.some(([id])=>id==='bone_ulna_'+side))throw Error('前臂骨链未完整加载');
 const movingIds=new Set(moving.map(([id])=>id));
 const elbowLigaments=new Set(['z_lig_ulnar_collateral_ligament_','z_lig_radial_collateral_ligament_','z_lig_quadrate_ligament_','ligament_annular_radius_'].map(p=>p+side));
 for(const [id,row] of rows)if(row.side===side&&row.motion_kind)elbowLigaments.add(id);
 const rigidIds=new Set(movingIds),safeTissues=new Set();
 for(const [id,o] of groups){const r=rows.get(id);if(!r?.tissue)continue;
  const anchors=r.bone_ids||[],allMoving=anchors.length>0&&anchors.every(b=>movingIds.has(b));
  const explicitRigid=id==='z_lig_quadrate_ligament_'+side||id==='ligament_annular_radius_'+side;
  if(allMoving||explicitRigid)rigidIds.add(id);
  const crosses=anchors.some(b=>movingIds.has(b))&&!allMoving;
  if(anchors.length&&(!crosses||elbowLigaments.has(id)))safeTissues.add(id);
 }
 const poses=[...rigidIds].map(id=>{const o=groups.get(id);return {id,o,position:o.position.clone(),quaternion:o.quaternion.clone(),scale:o.scale.clone()};});
 const deforms=[];
 if(ligamentTemplate){
  ligamentTemplate.updateMatrixWorld(true);
  const sources=[];ligamentTemplate.traverse(o=>{if(o.isMesh&&o.name.endsWith('_'+side))sources.push(o);});
  const expected=[...elbowLigaments].filter(id=>rows.has(id)&&(rows.get(id)?.motion_kind==='deform'||id.startsWith('z_lig_radial_collateral_ligament_')||id.startsWith('z_lig_ulnar_collateral_ligament_')));
  if(sources.length!==expected.length||expected.some(id=>!sources.some(s=>s.name===id)))throw Error('肘部变形资源数量或名称不正确');
  // Validate before modifying scene membership, so failed entry leaves no partial replacements.
  for(const source of sources)if(!groups.has(source.name)||!source.geometry.getAttribute('_motion_weight')||source.geometry.morphAttributes.position?.length!==24)throw Error('韧带变形数据不完整');
  for(const source of sources){
   const id=source.name,original=groups.get(id),sourceGeometry=source.geometry,base=sourceGeometry.getAttribute('position'),weights=sourceGeometry.getAttribute('_motion_weight'),morphs=sourceGeometry.morphAttributes.position;
   const rest=new Float32Array(base.count*3),targets=[];const v=new THREE.Vector3();
   for(let i=0;i<base.count;i++){v.fromBufferAttribute(base,i).applyMatrix4(source.matrixWorld);v.toArray(rest,i*3);}
   for(const morph of morphs){const values=new Float32Array(rest.length);for(let i=0;i<base.count;i++){v.fromBufferAttribute(morph,i);if(sourceGeometry.morphTargetsRelative)v.add(new THREE.Vector3().fromBufferAttribute(base,i));v.applyMatrix4(source.matrixWorld).toArray(values,i*3);}targets.push(values);}
   const geometry=sourceGeometry.clone();geometry.morphAttributes={};geometry.setAttribute('position',new THREE.BufferAttribute(rest.slice(),3).setUsage(THREE.DynamicDrawUsage));
   let material;original.traverse(m=>{if(m.isMesh&&!material)material=m.material.clone();});
   const object=new THREE.Mesh(geometry,material);object.name=id;object.userData.rest=new THREE.Vector3();object.userData.offset=new THREE.Vector3();object.userData.line=original.userData.line;
   original.visible=false;scene.add(object);groups.set(id,object);
   deforms.push({id,original,object,rest,targets,weights});
  }
 }
 const localBones=new Set([...movingIds,'bone_humerus_'+side]);let view='whole',showLigaments=true,ids=new Set(),layerFilter=r=>!r?.tissue||r.tissue_layer==='ligament';
 function rebuildVisible(){
  ids=new Set([...(view==='whole'?[...groups.keys()].filter(id=>!rows.get(id)?.tissue):localBones)].filter(id=>layerFilter(rows.get(id))));
  for(const id of safeTissues){const row=rows.get(id);
   const local=elbowLigaments.has(id)||(row.joint_or_connection_ids||[]).some(c=>['humeroulnar_'+side,'humeroradial_'+side,'proximal_radioulnar_'+side].includes(c));
   if((view==='whole'||local)&&layerFilter(row)&&(row.tissue_layer!=='ligament'||showLigaments))ids.add(id);
  }
 }
 rebuildVisible();
 const guide=new THREE.Line(new THREE.BufferGeometry().setFromPoints([pivot.clone().addScaledVector(axis,-.055),pivot.clone().addScaledVector(axis,.055)]),new THREE.LineBasicMaterial({color:0x75aca7,depthTest:true}));scene.add(guide);
 let angle=0;const vertex=new THREE.Vector3();
 function setAngle(value){
  angle=THREE.MathUtils.clamp(value,...spec.range_degrees);const q=new THREE.Quaternion().setFromAxisAngle(axis,THREE.MathUtils.degToRad(angle));
  for(const pose of poses){pose.o.position.copy(pose.position).sub(pivot).applyQuaternion(q).add(pivot);pose.o.quaternion.copy(q).multiply(pose.quaternion);pose.o.scale.copy(pose.scale);pose.o.updateMatrixWorld(true);}
  const lower=Math.floor(angle/5),upper=Math.min(24,lower+1),t=angle/5-lower;
  for(const d of deforms){const a=lower===0?d.rest:d.targets[lower-1],b=upper===0?d.rest:d.targets[upper-1],out=d.object.geometry.getAttribute('position');
   for(let i=0;i<out.count;i++){const w=d.weights.getX(i);vertex.fromArray(d.rest,i*3);
    if(w>1-1e-6)vertex.sub(pivot).applyQuaternion(q).add(pivot);
    else if(w>=1e-6)vertex.set(a[i*3]*(1-t)+b[i*3]*t,a[i*3+1]*(1-t)+b[i*3+1]*t,a[i*3+2]*(1-t)+b[i*3+2]*t);
    out.setXYZ(i,vertex.x,vertex.y,vertex.z);
   }
   out.needsUpdate=true;d.object.geometry.computeVertexNormals();d.object.geometry.computeBoundingBox();d.object.geometry.computeBoundingSphere();
  }
 }
 function bounds(){const saved=angle,box=new THREE.Box3();for(const deg of [0,30,60,90,120]){setAngle(deg);for(const id of ids)box.expandByObject(groups.get(id));}setAngle(saved);return box;}
 function dispose(){
  for(const pose of poses){pose.o.position.copy(pose.position);pose.o.quaternion.copy(pose.quaternion);pose.o.scale.copy(pose.scale);pose.o.updateMatrixWorld(true);}
  for(const d of deforms){groups.set(d.id,d.original);scene.remove(d.object);d.object.geometry.dispose();d.object.material.dispose();}
  scene.remove(guide);guide.geometry.dispose();guide.material.dispose();
 }
 return {get ids(){return ids;},setLayerFilter:filter=>{layerFilter=filter;rebuildVisible();},get view(){return view;},setView:value=>{view=value==='local'?'local':'whole';rebuildVisible();},setLigaments:value=>{showLigaments=value;rebuildVisible();},setAngle,bounds,dispose,setAxisVisible:value=>guide.visible=value,get angle(){return angle;}};
}
