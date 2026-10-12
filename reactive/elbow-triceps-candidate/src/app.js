import * as THREE from 'three';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {GLTFLoader} from '../vendor/GLTFLoader.js';
const $=s=>document.querySelector(s);
const state={angle:30,explode:0,playing:false,direction:1,selected:'muscle_biceps_long_R',hidden:new Set(),filter:'all',search:'',isolate:false,superficial:true,fascia:false,anchors:true,attachmentView:false,ready:false};
const host=$('#canvas-host');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.18;renderer.shadowMap.enabled=false;host.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','肘部三维模型：拖动旋转，双指或滚轮缩放，点击结构查看详情');
const scene=new THREE.Scene();const camera=new THREE.PerspectiveCamera(36,1,.005,10);camera.position.set(-.015,.065,-1.03);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(-.015,.065,-.015);controls.enableDamping=true;controls.dampingFactor=.1;controls.enablePan=true;controls.minDistance=.35;controls.maxDistance=1.65;
// Camera-relative inspection lighting: front-facing structures stay readable as the view rotates.
// Keep normal-based shape shading without projected shadow maps or delayed shadow updates.
scene.add(camera);
scene.add(new THREE.HemisphereLight(0xe8edf0,0x67605a,1.1));
const viewLight=new THREE.DirectionalLight(0xfff8ef,2.8);
viewLight.name='inspection_key';viewLight.position.set(0,0,0);viewLight.target.position.set(0,0,-1);
camera.add(viewLight,viewLight.target);
const fillLight=new THREE.DirectionalLight(0xe6efff,.7);
fillLight.name='inspection_fill';fillLight.position.set(-.5,.35,0);fillLight.target.position.set(0,0,-1);
camera.add(fillLight,fillLight.target);
const data=await fetch('data/structures.json?v=034candidate').then(r=>{if(!r.ok)throw Error('结构清单加载失败');return r.json()});
const stats=await fetch('data/geometry-stats.json?v=034candidate').then(r=>r.json());
const byId=new Map(data.structures.map(s=>[s.id,s]));const meshes=new Map();const basePositions=new Map();const baseColors=new Map();const morphBanks=new Map();let gltf,mixer,clip,action;const v3=p=>new THREE.Vector3(p[0],p[2],-p[1]);
const regionMeshes=new Map();let beforeAttachmentView=null;
const guideGroup=new THREE.Group();scene.add(guideGroup);const guides=new Map();const dotGeo=new THREE.SphereGeometry(.0014,16,10);
const dotMats=[new THREE.MeshBasicMaterial({color:0xb5633d,depthTest:true}),new THREE.MeshBasicMaterial({color:0x557867,depthTest:true})];
const dots=dotMats.map(m=>{const d=new THREE.Mesh(dotGeo,m);d.renderOrder=10;guideGroup.add(d);return d;});
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let pointerStart=null,lastDetailAngle=-1,lastPhase='';const frameTimes=[];
function originSpec(){return data.attachmentCalibration?.muscles[state.selected];}
function visible(s){const spec=originSpec();if(state.attachmentView&&spec)return [state.selected,spec.bone,spec.tissue].includes(s.id);return !state.hidden.has(s.id)&&(!state.isolate||s.id===state.selected)&&(s.type!=='fascia'||state.fascia)&&(state.superficial||s.layer!=='superficial');}
function list(){
 const root=$('#structure-list');root.replaceChildren();const groups=[['bone','骨骼'],['muscle','肌肉'],['tendon','肌腱'],['fascia','筋膜']];
 for(const [kind,title] of groups){const items=data.structures.filter(s=>s.type===kind&&(state.filter==='all'||s.type===state.filter)&&(!state.search||(s.name+s.english).toLowerCase().includes(state.search)));
  if(!items.length)continue;const heading=document.createElement('div');heading.className='group-title';heading.innerHTML=`${title}<span>${String(items.length).padStart(2,'0')}</span>`;root.append(heading);
  for(const s of items){const row=document.createElement('div');row.className=`structure-row ${s.id===state.selected?'selected':''} ${visible(s)?'':'is-hidden'}`;row.dataset.id=s.id;const button=document.createElement('button');button.className='select-structure';button.innerHTML=`<i class="layer-dot ${s.layer==='deep'?'deep':''} ${s.type==='bone'?'bone':''}"></i><span>${s.name}</span>`;button.setAttribute('aria-pressed',String(state.selected===s.id));button.addEventListener('click',()=>select(s.id,true));row.append(button);const eye=document.createElement('button');eye.className='eye';eye.textContent=visible(s)?'◉':'○';eye.title=`${visible(s)?'隐藏':'显示'}${s.name}`;eye.setAttribute('aria-label',eye.title);eye.onclick=()=>{if(state.attachmentView)exitOriginView();if(visible(s))state.hidden.add(s.id);else{state.hidden.delete(s.id);if(s.layer==='superficial')state.superficial=true;if(s.type==='fascia')state.fascia=true;if(state.isolate&&s.id!==state.selected)state.isolate=false;}sync();};row.append(eye);root.append(row);}
 }
 if(!root.children.length)root.innerHTML='<p class="no-results">没有匹配的结构</p>';
}
function role(s){if(s.type==='bone')return '骨性参照 · 随所属运动组运动';if(s.type==='fascia')return '组织包络示意 · 不参与力学计算';if(!state.playing)return s.action==='flexor'?'屈肘参与结构 · 静止观察':'伸肘参与结构 · 静止观察';const active=(state.direction===1)===(s.action==='flexor');return active?'主动参与 · 缩短示意':'被动拉长示意';}
function detail(){
 const s=byId.get(state.selected),i=data.structures.indexOf(s)+1;$('#selection-number').textContent=`${String(i).padStart(2,'0')} / 17`;
 const kind={bone:'骨骼',muscle:'肌肉',tendon:'肌腱',fascia:'筋膜'}[s.type];
 $('#detail-content').innerHTML=`<span class="structure-kind">${kind}</span><h3>${s.name}</h3><details class="term"><summary>英文名称</summary><p class="english">${s.english}</p></details><div class="chips"><span class="chip">右侧</span><span class="chip">${{skeleton:'骨骼层',superficial:'浅层',deep:'深层',fascia:'示意包络'}[s.layer]}</span><span class="chip warm">${s.type==='fascia'?'筋膜示意':s.type==='tendon'?'腱区分离':'数据库形态'}</span></div><dl><div class="attachment"><span class="point">起</span><div><dt>${s.type==='bone'?'所属运动组':'起点'}</dt><dd>${s.type==='bone'?(s.binding==='forearm'?'尺桡骨共同绕肘轴运动':'固定上臂参照'):s.origin}</dd></div></div><div class="attachment"><span class="point insert">止</span><div><dt>${s.type==='bone'?'结构说明':'止点'}</dt><dd>${s.type==='bone'?s.note:s.insertion}</dd></div></div></dl><div class="role-card"><span>当前运动角色</span><b id="role-label">${role(s)}</b><small id="length-label"></small></div>`;
 $('#inspect-origin').hidden=s.type!=='muscle';$('#inspect-origin').textContent=state.attachmentView?'返回整体观察':'查看起点';$('#inspect-origin').classList.toggle('active',state.attachmentView);
 if(s.attachmentReview){const note=document.createElement('div');note.className='attachment-note';const title=document.createElement('b');title.textContent='附着候选区 · 待解剖审核';const body=document.createElement('p');body.textContent=s.attachmentReview.note;note.append(title,body);$('#detail-content').append(note);}
 $('#isolate').textContent=state.isolate?'退出隔离':'单块隔离';$('#isolate').classList.toggle('active',state.isolate);updateRole();
}
function updateRole(){const s=byId.get(state.selected);$('#role-label').textContent=role(s);const st=stats[s.id];if(st){const p=state.angle/5,k=Math.min(23,Math.floor(p)),f=p-k,L=THREE.MathUtils.lerp(st.pathLengthsMetres[k],st.pathLengthsMetres[k+1],f);$('#length-label').textContent=`模型路径 ${Math.round(L*1000)} mm · 相对伸展位 ${((L/st.restLength-1)*100).toFixed(1)}%（非人体测量）`;}else $('#length-label').textContent='BodyParts3D 形态 · 运动与分区待专业审核';}
function select(id,reveal=false){if(!byId.has(id))return;state.selected=id;if(state.attachmentView){if(originSpec())focusOrigin();else exitOriginView();}if(reveal){const s=byId.get(id);state.hidden.delete(id);if(s.layer==='superficial')state.superficial=true;if(s.type==='fascia')state.fascia=true;}sync();}
function focusOrigin(){const spec=originSpec();if(!spec)return;controls.minDistance=.12;controls.target.copy(v3(spec.viewTarget));camera.position.copy(controls.target).add(v3(spec.viewOffset));controls.update();$('#view-label').textContent='起点检查 · 遮挡结构暂隐';}
function exitOriginView(){state.attachmentView=false;controls.minDistance=.35;if(beforeAttachmentView){camera.position.copy(beforeAttachmentView.position);controls.target.copy(beforeAttachmentView.target);state.explode=beforeAttachmentView.explode;controls.update();beforeAttachmentView=null;}$('#view-label').textContent='整体观察';}
function sync(){
 $('#superficial').checked=state.superficial;$('#fascia').checked=state.fascia;$('#anchors').checked=state.anchors;$('#explode').value=state.explode*100;$('#explode-value').textContent=`${Math.round(state.explode*100)}% · 展开`;
 for(const s of data.structures){const m=meshes.get(s.id);if(m)m.visible=visible(s);}list();detail();pose();
}
function boneAnchor(s,end){const node=gltf.scene.getObjectByName((end?'insertion__':'origin__')+s.id);if(!node)return new THREE.Vector3();const p=node.getWorldPosition(new THREE.Vector3());const bone=s.bones[end?1:0];if(byId.has(bone))p.add(v3(byId.get(bone).explode).multiplyScalar(state.explode));return p;}
function ringCenter(m,last){const marker=gltf.scene.getObjectByName((last?'belly_insertion__':'belly_origin__')+(m.userData.structure_id||m.name));if(marker)return marker.getWorldPosition(new THREE.Vector3()).add(v3(byId.get(m.userData.structure_id||m.name).explode).multiplyScalar(state.explode));const count=m.geometry.attributes.position.count,sides=16;const center=new THREE.Vector3(),v=new THREE.Vector3();for(let j=0;j<sides;j++){m.getVertexPosition((last?count-sides:0)+j,v);center.add(v);}return m.localToWorld(center.multiplyScalar(1/sides));}
function updateGuides(){
 if(!state.ready)return;gltf.scene.updateMatrixWorld(true);const s=byId.get(state.selected);
 for(const [id,m] of regionMeshes){const owner=byId.get(id),spec=data.attachmentCalibration.muscles[id];m.visible=state.anchors&&id===state.selected&&visible(owner);m.position.copy(v3(byId.get(spec.bone).explode).multiplyScalar(state.explode));}
 dots.forEach((dot,end)=>{dot.visible=state.anchors&&s.type==='muscle'&&visible(s)&&(!state.attachmentView||end===0);if(dot.visible)dot.position.copy(boneAnchor(s,end));});
 for(const [id,lines] of guides){const item=byId.get(id),m=meshes.get(id);for(let end=0;end<2;end++){const line=lines[end];line.visible=state.explode>.001&&visible(item);if(!line.visible)continue;const a=ringCenter(m,end),b=boneAnchor(item,end);line.geometry.attributes.position.setXYZ(0,a.x,a.y,a.z);line.geometry.attributes.position.setXYZ(1,b.x,b.y,b.z);line.geometry.attributes.position.needsUpdate=true;line.computeLineDistances();line.material.opacity=id===state.selected?.85:.25;}}
}
function pose(){
 if(!state.ready)return;
 action.time=Math.min(clip.duration-1e-7,1/30+state.angle/30);
 mixer.update(0);
 // Send only the two neighboring exported morph targets to the GPU (not all 24).
 for(const [id,bank] of morphBanks){
  const k=Math.min(23,Math.floor(state.angle/5)),f=(state.angle-k*5)/5,m=meshes.get(id);
  if(!bank.geometries[k]){
   const g=new THREE.BufferGeometry();g.setIndex(bank.source.index);
   for(const [name,attribute] of Object.entries(bank.source.attributes))g.setAttribute(name,attribute);
   g.morphTargetsRelative=true;
   g.morphAttributes.position=k===0?[bank.targets[0],bank.targets[0]]:[bank.targets[k-1],bank.targets[k]];
   if(bank.normals)g.morphAttributes.normal=k===0?[bank.normals[0],bank.normals[0]]:[bank.normals[k-1],bank.normals[k]];
   bank.geometries[k]=g;
  }
  m.geometry=bank.geometries[k];m.morphTargetInfluences=k===0?[f,0]:[1-f,f];
 }
 gltf.scene.updateMatrixWorld(true);
 for(const [id,m] of meshes){const offset=v3(byId.get(id).explode).multiplyScalar(state.explode),q=m.parent.getWorldQuaternion(new THREE.Quaternion()).invert();m.position.copy(basePositions.get(id)).add(offset.applyQuaternion(q));
  const s=byId.get(id);const ghost=state.attachmentView&&s.type!=='bone';const transparent=ghost||s.type==='fascia';if(m.material.transparent!==transparent){m.material.transparent=transparent;m.material.needsUpdate=true;}m.material.opacity=ghost?(s.type==='tendon'?.32:.18):(s.type==='fascia'?.11:1);m.material.depthWrite=!ghost&&s.type!=='fascia';m.castShadow=!ghost&&s.type!=='fascia';m.renderOrder=ghost?3:0;m.material.color.copy(baseColors.get(id));m.material.emissive.set(0x000000);
  if(id===state.selected){m.material.emissive.set(0x3c2113);m.material.emissiveIntensity=.26;}
 }
 updateGuides();$('#angle').value=state.angle;$('#angle-value').textContent=`${Math.round(state.angle)}°`;const phase=state.playing?(state.direction===1?'屈曲 · 屈肌主动参与':'伸展 · 伸肌主动参与'):'静止观察';$('#phase').textContent=phase;
 if(Math.abs(lastDetailAngle-state.angle)>1||lastPhase!==phase){updateRole();lastDetailAngle=state.angle;lastPhase=phase;}
}
function view(name){if(state.attachmentView){exitOriginView();sync();}const t=controls.target;const positions={front:[-.015,.065,-1.03],side:[1.00,.07,0],back:[0,.09,1.02],reset:[-.015,.065,-1.03],close:[.32,.12,-.4]};camera.position.set(...positions[name]);t.set(-.015,name==='close'?.055:.065,-.015);controls.update();$('#view-label').textContent={front:'前面观',side:'右外侧观',back:'后面观',reset:'前面观',close:'肘部特写'}[name];}
function togglePlay(value=!state.playing){state.playing=value;if(value&&state.angle>=120)state.direction=-1;if(value&&state.angle<=0)state.direction=1;$('#play').textContent=value?'Ⅱ':'▶';$('#play').setAttribute('aria-label',value?'暂停屈伸':'播放屈伸');pose();}
$('#inspect-origin').onclick=()=>{if(state.attachmentView)exitOriginView();else{beforeAttachmentView={position:camera.position.clone(),target:controls.target.clone(),explode:state.explode};state.attachmentView=true;state.explode=0;focusOrigin();}sync();if(matchMedia('(max-width:900px)').matches)host.scrollIntoView({behavior:'smooth',block:'center'});};
$('#play').onclick=()=>togglePlay();$('#angle').oninput=e=>{const nextAngle=+e.target.value;togglePlay(false);state.angle=nextAngle;pose();};$('#explode').oninput=e=>{state.explode=+e.target.value/100;$('#explode-value').textContent=`${e.target.value}% · 展开`;pose();};$('#fit').onclick=()=>{state.explode=0;$('#explode').value=0;$('#explode-value').textContent='0% · 展开';pose();};
for(const key of ['superficial','fascia','anchors'])$('#'+key).onchange=e=>{if(state.attachmentView&&key!=='anchors')exitOriginView();state[key]=e.target.checked;sync();};
$('#reveal').onclick=()=>{state.superficial=false;state.fascia=false;state.isolate=false;state.hidden.delete('muscle_brachialis_R');state.hidden.delete('tendon_brachialis_distal_R');state.selected='muscle_brachialis_R';view('front');sync();};
$('#isolate').onclick=()=>{if(state.attachmentView)exitOriginView();state.isolate=!state.isolate;const s=byId.get(state.selected);state.hidden.delete(s.id);if(s.type==='fascia')state.fascia=true;if(s.layer==='superficial')state.superficial=true;sync();};$('#hide-selected').onclick=()=>{if(state.attachmentView)exitOriginView();state.hidden.add(state.selected);sync();};$('#restore').onclick=()=>{if(state.attachmentView)exitOriginView();state.hidden.clear();state.superficial=true;state.fascia=false;state.isolate=false;sync();};
for(const name of ['front','side','back','reset','close'])$('#view-'+name).onclick=()=>view(name);
$('#search').oninput=e=>{state.search=e.target.value.toLowerCase().trim();list();};for(const b of document.querySelectorAll('[data-filter]'))b.onclick=()=>{state.filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));list();};
function rayAt(x,y){const r=renderer.domElement.getBoundingClientRect();pointer.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects([...meshes.values(),...regionMeshes.values()].filter(m=>m.visible),false)[0];}
renderer.domElement.addEventListener('pointerdown',e=>{pointerStart={x:e.clientX,y:e.clientY,id:e.pointerId,time:performance.now()};});renderer.domElement.addEventListener('pointerup',e=>{if(pointerStart&&pointerStart.id===e.pointerId&&Math.hypot(e.clientX-pointerStart.x,e.clientY-pointerStart.y)<6&&performance.now()-pointerStart.time<700){const hit=rayAt(e.clientX,e.clientY);if(hit)select(hit.object.userData.annotationOwner||hit.object.userData.structure_id||hit.object.name);}pointerStart=null;});renderer.domElement.addEventListener('pointercancel',()=>pointerStart=null);
new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}).observe(host);
try{
 gltf=await new GLTFLoader().loadAsync('assets/elbow-right.glb?v=034candidate');scene.add(gltf.scene);
 gltf.scene.traverse(o=>{if(o.isMesh&&o.userData.annotationOwner){regionMeshes.set(o.userData.annotationOwner,o);o.material=o.material.clone();o.material.transparent=true;o.material.opacity=.80;o.material.depthWrite=false;o.material.side=THREE.DoubleSide;o.renderOrder=2;o.visible=false;}if(o.isMesh&&byId.has(o.userData.structure_id||o.name)){const id=o.userData.structure_id||o.name;o.material=o.material.clone();o.material.metalness=0;o.castShadow=true;o.receiveShadow=true;meshes.set(id,o);basePositions.set(id,o.position.clone());baseColors.set(id,o.material.color.clone());o.frustumCulled=false;if(byId.get(id).type==='fascia'){o.material.transparent=true;o.material.opacity=.11;o.castShadow=false;o.material.depthWrite=false;o.material.side=THREE.DoubleSide;}else o.material.side=byId.get(id).type==='bone'?THREE.DoubleSide:THREE.FrontSide;}});
 for(const [id,m] of meshes){if(m.geometry.morphAttributes.position?.length)morphBanks.set(id,{source:m.geometry,targets:m.geometry.morphAttributes.position,normals:m.geometry.morphAttributes.normal,geometries:[]});}
 if(meshes.size!==17)throw Error(`模型结构缺失：${meshes.size}/17`);
 // Blender emits one scene action per object; merge their tracks to sample them together.
 clip=new THREE.AnimationClip('Elbow flexion 0–120',-1,gltf.animations.flatMap(a=>a.tracks).filter(t=>!t.name.endsWith('.morphTargetInfluences')));mixer=new THREE.AnimationMixer(gltf.scene);action=mixer.clipAction(clip);action.play();action.paused=true;
 for(const s of data.structures.filter(s=>s.type==='muscle')){const lines=[0,1].map(()=>{const geo=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]);const line=new THREE.Line(geo,new THREE.LineDashedMaterial({color:0x6c806b,dashSize:.005,gapSize:.003,transparent:true,opacity:.5,depthTest:false}));line.frustumCulled=false;line.renderOrder=4;guideGroup.add(line);return line;});guides.set(s.id,lines);}
 state.ready=true;sync();$('#loading').remove();$('#load-status').textContent='已加载 · 17 个结构';
}catch(error){$('#loading').innerHTML='<b>模型加载失败</b><small>请按使用说明启动本地服务后打开。</small>';$('#load-status').textContent='加载失败';console.error(error);}
let last=performance.now();function animate(now){const dt=Math.min((now-last)/1000,.05);frameTimes.push(now-last);if(frameTimes.length>240)frameTimes.shift();last=now;if(state.ready&&state.playing&&!document.hidden){state.angle+=dt*26*state.direction;if(state.angle>=120){state.angle=120;state.direction=-1;}if(state.angle<=0){state.angle=0;state.direction=1;}pose();}controls.update();if(state.ready){const s=byId.get(state.selected),label=$('#floating-label'),m=meshes.get(state.selected);label.hidden=!m.visible;if(m.visible){const p=state.attachmentView?boneAnchor(s,0):s.type==='muscle'?ringCenter(m,0):new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());p.project(camera);label.textContent=state.attachmentView?'起点候选区 · 待审核':s.name;label.style.left=`${THREE.MathUtils.clamp((p.x+1)/2*host.clientWidth,65,host.clientWidth-65)}px`;label.style.top=`${THREE.MathUtils.clamp((1-p.y)/2*host.clientHeight-(state.attachmentView?38:0),135,host.clientHeight-40)}px`;}}renderer.render(scene,camera);requestAnimationFrame(animate);}requestAnimationFrame(animate);
// Local QA interface: returns actual mesh positions, ray hits and draw performance.
window.__lab={resetTiming:()=>{frameTimes.length=0},state,data,meshes,regionMeshes,camera,controls,renderer,gltf,stats,select,pose,view,togglePlay,rayAt,sync,
 visible:()=>data.structures.filter(visible).map(s=>s.id),
 snapshot:()=>({angle:state.angle,explode:state.explode,selected:state.selected,visible:data.structures.filter(visible).map(s=>s.id),positions:Object.fromEntries([...meshes].map(([id,m])=>[id,m.position.toArray()])),fps:1000/(frameTimes.slice(-120).reduce((a,b)=>a+b,0)/Math.min(frameTimes.length,120)),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles}),
 meshPoint:(id,index=0)=>{const m=meshes.get(id),p=new THREE.Vector3();m.getVertexPosition(index,p);return m.localToWorld(p).toArray();},
 project:(id)=>{const m=meshes.get(id),p=new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3()).project(camera),r=renderer.domElement.getBoundingClientRect();return {x:r.left+(p.x+1)/2*r.width,y:r.top+(1-p.y)/2*r.height};},
 anchor:(id,end)=>boneAnchor(byId.get(id),end).toArray()
};
