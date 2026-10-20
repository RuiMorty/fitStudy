import * as THREE from 'three';
import {explosionOffsets} from './explode.js';
import {OrbitControls} from 'three/addons/OrbitControls.js';
import {GLTFLoader} from 'three/addons/GLTFLoader.js';
// 网页骨骼外观：底色、曝光、灯光和粗糙度统一在这里调整。
const BONE_STYLE = {
  color: 0xc9bfa5, // 低饱和象牙色，接近参考图的骨色
  exposure: 0.90,
  roughness: 0.88,
  hemisphere: 0.85,
  key: 2.0,
  fill: 0.45,
};
const $=id=>document.getElementById(id), host=$('viewer');
const scene=new THREE.Scene();scene.background=new THREE.Color('#292929');
const camera=new THREE.PerspectiveCamera(35,1,.005,30);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(host.clientWidth,host.clientHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=BONE_STYLE.exposure;host.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.zoomToCursor=true;controls.enablePan=true;controls.screenSpacePanning=true;controls.minDistance=.03;controls.maxDistance=8;
const hemisphere=new THREE.HemisphereLight(0xffffff,0x746b5c,BONE_STYLE.hemisphere);scene.add(hemisphere);const key=new THREE.DirectionalLight(0xffffff,BONE_STYLE.key);scene.add(key);scene.add(key.target);
const fill=new THREE.DirectionalLight(0xffffff,BONE_STYLE.fill);fill.position.set(-2,2,-2);scene.add(fill);
const groups=new Map(),hidden=new Set(),rows=new Map();let trialEnabled=true,earSide=null;let currentSource='z',sourceSwitchBusy=false;const sourceCache=new Map();let connectionNames={};let connectionRecords=[];let manifest,selected=null,isolated=null,region='all',explode=0,loadDone=false;
let capsulesEnabled=false,ligamentsEnabled=false,surfacesEnabled=false;
let jointsEnabled=true,bonesEnabled=true,jointsLoading=false,jointError="";
function tissueLayer(b){return b.tissue_layer||'joint';}
function layerEnabled(b){return !b.tissue?(currentSource!=='z'||bonesEnabled):currentSource==='z'&&(tissueLayer(b)==='surface'?surfacesEnabled:tissueLayer(b)==='capsule'?capsulesEnabled:tissueLayer(b)==='ligament'?ligamentsEnabled:jointsEnabled);}
function materialBase(id){const b=rows.get(id);return b?.tissue?(tissueLayer(b)==='surface'?0x71a5a6:tissueLayer(b)==='capsule'?0xb4aca0:tissueLayer(b)==='ligament'?0xc7b799:0x94a8b3):BONE_STYLE.color;}
function activateSelectionLayer(b){if(!b)return;if(b.tissue){const type=tissueLayer(b);if(type==='surface'){surfacesEnabled=true;$('layer-surfaces').checked=true;}else if(type==='capsule'){capsulesEnabled=true;$('layer-capsules').checked=true;}else if(type==='ligament'){ligamentsEnabled=true;$('layer-ligaments').checked=true;}else{jointsEnabled=true;$('layer-joints').checked=true;}}else if(currentSource==='z'){bonesEnabled=true;$('layer-bones').checked=true;}}

const defaultStyle={...BONE_STYLE};
const styleStorageKey='skeleton-workbench-appearance-v1';
let showHighlight=true;
const styleFields=['exposure','roughness','hemisphere','key','fill'];
function applyAppearance(){
  renderer.toneMappingExposure=BONE_STYLE.exposure;
  hemisphere.intensity=BONE_STYLE.hemisphere;key.intensity=BONE_STYLE.key;fill.intensity=BONE_STYLE.fill;
  for(const [id,g] of groups)g.traverse(m=>{if(m.isMesh){const highlight=id===selected&&showHighlight;m.material.color.set(highlight?0xb6c891:materialBase(id));m.material.emissive.set(highlight?0x16220d:0);m.material.roughness=BONE_STYLE.roughness;if(rows.get(id)?.tissue){const capsule=tissueLayer(rows.get(id))==='capsule';m.material.transparent=capsule;m.material.opacity=capsule?.28:1;m.material.depthWrite=!capsule;const surface=tissueLayer(rows.get(id))==='surface';m.material.polygonOffset=surface;m.material.polygonOffsetFactor=surface?-2:0;m.material.polygonOffsetUnits=surface?-2:0;m.material.side=surface?THREE.DoubleSide:THREE.FrontSide;m.renderOrder=surface?1:0;}}});
  $('bone-color').value='#'+BONE_STYLE.color.toString(16).padStart(6,'0');
  $('bone-color-value').textContent=$('bone-color').value.toUpperCase();
  for(const field of styleFields){$('style-'+field).value=BONE_STYLE[field];$('value-'+field).textContent=BONE_STYLE[field].toFixed(2);}
}
function saveAppearance(){try{localStorage.setItem(styleStorageKey,JSON.stringify(BONE_STYLE));$('style-save-status').textContent='已保存在当前浏览器，刷新后保留。';}catch{$('style-save-status').textContent='当前浏览器无法保存，调整仅本次有效。';}}
try{const saved=JSON.parse(localStorage.getItem(styleStorageKey)||'null');if(saved){if(Number.isInteger(saved.color)&&saved.color>=0&&saved.color<=0xffffff)BONE_STYLE.color=saved.color;for(const f of styleFields){const input=$('style-'+f),v=saved[f];if(typeof v==='number'&&Number.isFinite(v)&&v>=Number(input.min)&&v<=Number(input.max))BONE_STYLE[f]=v;}}}catch{}
$('bone-color').oninput=e=>{BONE_STYLE.color=parseInt(e.target.value.slice(1),16);applyAppearance();saveAppearance();};
for(const f of styleFields)$('style-'+f).oninput=e=>{BONE_STYLE[f]=Number(e.target.value);applyAppearance();saveAppearance();};
$('style-highlight').onchange=e=>{showHighlight=e.target.checked;applyAppearance();};
$('style-reset').onclick=()=>{Object.assign(BONE_STYLE,defaultStyle);applyAppearance();saveAppearance();};
applyAppearance();
const lineMat=new THREE.LineBasicMaterial({color:0x94a28b,transparent:true,opacity:.28,depthWrite:false});
const status=t=>$('status').textContent=t;
function active(id){const b=rows.get(id);return layerEnabled(b)&&(!b.trial||trialEnabled)&&(!earSide||(b.region==='听小骨'&&b.side===earSide)||id==='bone_temporal_'+earSide)&&!hidden.has(id)&&(!isolated||isolated===id)&&(region==='all'||rows.get(id).region===region)}
function visibility(){updateEarMaterials();$('count').textContent=currentSource==='z'?`206 骨 · ${[...rows.values()].filter(b=>b.tissue&&tissueLayer(b)!=='surface').length} 关节组织`:(trialEnabled?'200 + 6 试装':'200 / 206');for(const [id,g]of groups){g.visible=active(id);g.userData.line.visible=g.visible&&explode>0&&g.userData.offset.lengthSq()>1e-12;}status(`${currentSource==='z'?'Z-Anatomy 候选 · ':''}${[...groups.keys()].filter(active).length} 个结构可见${loadDone?'':' · 加载中'}`);renderList()}
function renderList(){const q=$('search').value.trim().toLowerCase();$('list').replaceChildren();for(const b of rows.values()){if(!layerEnabled(b))continue;if(region!=='all'&&b.region!==region)continue;if(q&&!`${b.name_zh} ${b.name_en} ${b.id}`.toLowerCase().includes(q))continue;const el=document.createElement('button');el.dataset.id=b.id;el.className=selected===b.id?'selected':'';const name=document.createElement('span');name.textContent=b.name_zh;const state=document.createElement('small');state.textContent=b.tissue?(hidden.has(b.id)?'已隐藏':'候选'):b.trial?(trialEnabled?'试装':'已关闭'):b.available?(hidden.has(b.id)?'已隐藏':''):'待补';el.append(name,state);el.onclick=()=>select(b.id);$('list').appendChild(el)}}
function select(id){selected=id;const b=rows.get(id);activateSelectionLayer(b);if(b.trial&&!trialEnabled){trialEnabled=true;$('ear-trial-enabled').checked=true;visibility();}$('name').textContent=b.name_zh;$('info').replaceChildren();for(const t of [b.available?`${b.region} · ${b.triangles.toLocaleString()} 三角面`:'此结构暂无独立可用网格',b.note||'源文件缺失或待确认分界。',`连接登记：${b.joint_or_connection_ids.map(id=>connectionNames[id]||id).join('、')}`,b.available?`源结构：${b.source_structure_id} · ${b.source_dataset||'BodyParts3D 3.0'}`:'', '解剖审核：待确认；运动轴：未校准']){const p=document.createElement('p');p.textContent=t;$('info').appendChild(p)}for(const [key,g]of groups)g.traverse(o=>{if(o.isMesh){o.material.color.set(key===id&&showHighlight?0xb6c891:materialBase(key));o.material.emissive.set(key===id&&showHighlight?0x16220d:0)}});for(const a of ['focus','isolate','hide'])$(a).disabled=!groups.has(id);setExplode(explode);renderList()}
const modeDescriptions={radial:'各区域围绕各自中心散开，保留原版方便比较。',layers:'按原始前后位置拉开。建议切到侧面观察；这是几何分层，不是组织学分层。',parts:'头部、胸廓、脊柱、左右上肢、骨盆与左右下肢整组分离，组内间距保持不变。',chain:'依据已有连接登记逐段增加间距，是展示路径，不代表真实关节轴或运动。',local:'先选一块骨，只展开它和连接登记中的相邻骨；颅缝等连接组可能包含多块骨。',single:'先选一块骨，仅将它移到旁边，其余骨保持原位。',outward:'全身共用中心，骨间距成比例增加，相机保持固定。'};
function setExplode(value){explode=value;
const mode=$('explode-mode').value;
$('explode-description').textContent=modeDescriptions[mode]+(['local','single'].includes(mode)?(groups.has(selected)?' 当前：'+rows.get(selected).name_zh:' 尚未选中可用骨骼。'):'');
const bones=[...groups].map(([id,g])=>({id,region:rows.get(id).region,side:rows.get(id).side,position:g.userData.rest.toArray()}));
const offsets=explosionOffsets(mode,bones,connectionRecords,selected);
const anchorSelected=rows.get(selected)?.tissue?rows.get(selected).bone_ids[0]:selected;
const boneOffsets=explosionOffsets(mode,bones.filter(b=>!rows.get(b.id).tissue),connectionRecords,anchorSelected);
for(const [id,g] of groups)g.userData.offset.fromArray((rows.get(id).tissue?offsets:boneOffsets).get(id));
for(const [id,g] of groups){const b=rows.get(id);if(!b.tissue||mode==='single'&&selected===id)continue;const anchors=b.bone_ids.map(id=>groups.get(id)).filter(Boolean);if(anchors.length){g.userData.offset.set(0,0,0);for(const bone of anchors)g.userData.offset.add(bone.userData.offset);g.userData.offset.divideScalar(anchors.length);}}

$('spacing').value=String(value*100);$('spacingValue').textContent=`${Math.round(value*100)}%`;for(const g of groups.values()){g.position.copy(g.userData.rest).addScaledVector(g.userData.offset,value);const a=g.userData.line.geometry.attributes.position;a.setXYZ(0,...g.userData.rest.toArray());a.setXYZ(1,...g.position.toArray());a.needsUpdate=true;g.userData.line.geometry.computeBoundingSphere();g.userData.line.visible=g.visible&&value>0&&g.userData.offset.lengthSq()>1e-12}}
function fit(id=null,direction=null){const box=new THREE.Box3();for(const [bid,g]of groups)if((id?bid===id:g.visible&&(!earSide||rows.get(bid).region==='听小骨')))box.expandByObject(g);if(box.isEmpty())return;const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());const aspect=host.clientWidth/host.clientHeight;const dist=Math.max(size.y,size.x/aspect,size.z)*.62/Math.tan(THREE.MathUtils.degToRad(camera.fov/2))+(earSide?.005:.05);let dir=direction||camera.position.clone().sub(controls.target).normalize();if(!dir.lengthSq())dir=new THREE.Vector3(0,0,1);controls.target.copy(center);camera.position.copy(center).addScaledVector(dir,dist);controls.update()}
$('search').oninput=renderList;$('region').onchange=e=>{region=e.target.value;earSide=null;isolated=null;$('search').value='';if(selected&&region!=='all'&&rows.get(selected).region!==region){selected=null;$('name').textContent='选择一个结构';$('info').textContent='在模型或清单中选择，查看来源及连接关系。';for(const a of ['focus','isolate','hide'])$(a).disabled=true;for(const g of groups.values())g.traverse(o=>{if(o.isMesh){o.material.color.set(materialBase(g.name));o.material.emissive.set(0)}});}setExplode(explode);visibility();fit()};$('explode-mode').onchange=()=>setExplode(explode);$('spacing').oninput=e=>setExplode(Number(e.target.value)/100);$('assemble').onclick=()=>setExplode(0);$('focus').onclick=()=>{activateSelectionLayer(rows.get(selected));hidden.delete(selected);visibility();fit(selected)};$('isolate').onclick=()=>{activateSelectionLayer(rows.get(selected));isolated=selected;hidden.delete(selected);visibility();fit(selected)};$('hide').onclick=()=>{hidden.add(selected);visibility()};$('show').onclick=()=>{earSide=null;hidden.clear();isolated=null;region='all';$('region').value='all';visibility();fit()};$('fit').onclick=()=>fit();$('front').onclick=()=>fit(null,new THREE.Vector3(0,0,1));$('back').onclick=()=>fit(null,new THREE.Vector3(0,0,-1));$('side').onclick=()=>fit(null,new THREE.Vector3(1,0,0));
function updateEarMaterials(){for(const side of ['R','L']){const g=groups.get('bone_temporal_'+side);if(!g)continue;const transparent=earSide===side&&$('ear-transparent').checked;g.traverse(o=>{if(o.isMesh){o.material.transparent=transparent;o.material.opacity=transparent?.16:1;o.material.depthWrite=!transparent;o.renderOrder=transparent?2:0;}});}}
function viewEar(side){if(!loadDone)return;bonesEnabled=true;$('layer-bones').checked=true;trialEnabled=true;$('ear-trial-enabled').checked=true;earSide=side;isolated=null;region='all';$('region').value='all';hidden.clear();$('search').value='';setExplode(0);visibility();select('bone_malleus_'+side);fit(null,new THREE.Vector3(0,0,1));}
$('ear-right').onclick=()=>viewEar('R');$('ear-left').onclick=()=>viewEar('L');$('ear-transparent').onchange=()=>visibility();$('ear-whole').onclick=()=>$('show').click();
$('ear-trial-enabled').onchange=e=>{if(currentSource==='z')return;trialEnabled=e.target.checked;if(!trialEnabled&&earSide){earSide=null;region='all';$('region').value='all';isolated=null;visibility();fit();}else visibility();};
let panMode=false;
$('pan-mode').onclick=()=>{panMode=!panMode;controls.mouseButtons.LEFT=panMode?THREE.MOUSE.PAN:THREE.MOUSE.ROTATE;controls.touches.ONE=panMode?THREE.TOUCH.PAN:THREE.TOUCH.ROTATE;$('pan-mode').setAttribute('aria-pressed',String(panMode));$('pan-mode').textContent=panMode?'平移中':'平移';renderer.domElement.style.cursor=panMode?'move':'grab';};
function pickStructure(e){const rect=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);const hits=ray.intersectObjects([...groups.values()].filter(g=>g.visible&&!(earSide&&g.name==='bone_temporal_'+earSide&&$('ear-transparent').checked)),true);if(!hits.length)return null;let o=hits[0].object;while(o&&!rows.has(o.name))o=o.parent;return o?.name||null;}
let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(e.button!==0||panMode||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const id=pickStructure(e);if(id)select(id);});
renderer.domElement.addEventListener('dblclick',e=>{if(panMode||e.button!==0)return;const id=pickStructure(e);if(id){select(id);fit(id);}});
new ResizeObserver(()=>{camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight)}).observe(host);
let frames=0;function frame(){requestAnimationFrame(frame);controls.update();key.position.copy(camera.position).add(new THREE.Vector3(.65,.8,0).applyQuaternion(camera.quaternion));key.target.position.copy(controls.target);renderer.render(scene,camera);frames++}frame();
try{const connections=await fetch('data/connections.json').then(r=>r.json());connectionRecords=connections.connections;connectionNames=Object.fromEntries(connections.connections.map(c=>[c.id,c.name_zh]));manifest=await fetch('z-anatomy-candidate/structures.json').then(r=>{if(!r.ok)throw Error('结构数据读取失败');return r.json()});manifest.bones.forEach(b=>rows.set(b.id,b));$('count').textContent=`${manifest.available_count} / 206 可选`;manifest.regions.forEach(r=>{const o=document.createElement('option');o.value=o.textContent=r.name;$('region').appendChild(o)});renderList();const loader=new GLTFLoader();for(const r of manifest.regions){status(`正在加载${r.name}…`);const gltf=await loader.loadAsync(r.file);gltf.scene.updateMatrixWorld(true);const found=[];gltf.scene.traverse(o=>{if(rows.has(o.name))found.push(o)});for(const o of found){scene.attach(o);const center=new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());o.userData.rest=o.position.clone();o.userData.offset=new THREE.Vector3();o.traverse(m=>{if(m.isMesh){m.material=m.material.clone();m.material.color.set(BONE_STYLE.color);m.material.roughness=BONE_STYLE.roughness;m.material.metalness=0}});const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([o.position.clone(),o.position.clone()]),lineMat);line.visible=false;scene.add(line);o.userData.line=line;groups.set(o.name,o)}setExplode(explode);visibility();if(!isolated)fit(null,new THREE.Vector3(0,0,1))}setExplode(explode);loadDone=true;$('ear-right').disabled=false;$('ear-left').disabled=false;$('ear-trial-state').textContent='200 个基础对象 + 6 个候选试装；5 块与现用颞骨相交。';visibility();fit(null,new THREE.Vector3(0,0,1));}catch(e){status(`加载失败：${e.message}。请通过本地服务器打开并刷新。`);console.error(e)}
syncSourceUI();

function syncSourceUI(){
 for(const [id,enabled] of [['capsules',capsulesEnabled],['ligaments',ligamentsEnabled],['surfaces',surfacesEnabled]]){$('layer-'+id).checked=currentSource==='z'&&enabled;$('layer-'+id).disabled=currentSource!=='z'||jointsLoading;}
 $('layer-bones').checked=currentSource==='bp'||bonesEnabled;$('layer-bones').disabled=currentSource!=='z';$('layer-joints').disabled=currentSource!=='z'||jointsLoading;$('joints-only').disabled=currentSource!=='z'||jointsLoading;$('layer-joints').checked=currentSource==='z'&&jointsEnabled;updateJointStatus();
 $('bp-credit').hidden=currentSource==='z';$('z-credit').hidden=currentSource!=='z';$('source-review-note').textContent=currentSource==='z'?'当前为 Z-Anatomy 原配骨架候选，206 个名称对应对象已导出，但未通过解剖、装配或逐对象许可审核。下列历史问题记录针对现用骨架，不自动适用于此候选。':'以下装配问题记录针对现用骨架。';
 for(const id of ['bp','z']){$('source-'+id).setAttribute('aria-pressed',String(currentSource===id));$('source-'+id).disabled=sourceSwitchBusy||jointsLoading||!loadDone;}
 $('ear-trial-enabled').disabled=currentSource==='z';
 $('ear-trial-state').textContent=currentSource==='z'?'当前听小骨沿用 Z-Anatomy 原配位置；原骨架试装开关仅适用于现用骨架。解剖与许可待审核。':'200 个基础对象 + 6 个候选试装；5 块与现用颞骨相交。';
}
async function switchSource(next){
 if(next===currentSource||sourceSwitchBusy||jointsLoading||!loadDone)return;
 sourceSwitchBusy=true;syncSourceUI();
 try{
  if(!sourceCache.has(currentSource))sourceCache.set(currentSource,{groups:new Map(groups),rows:new Map(rows),manifest});
  if(!sourceCache.has(next)){
   const response=await fetch(next==='z'?'z-anatomy-candidate/structures.json':'data/structures.json');if(!response.ok)throw Error('骨架清单未读取');const nextManifest=await response.json();
   if(next==='bp'){const response=await fetch('data/ossicles-trial.json');if(!response.ok)throw Error('听小骨清单未读取');const trial=await response.json();const overrides=new Map(trial.bones.map(b=>[b.id,b]));nextManifest.bones=nextManifest.bones.map(b=>overrides.get(b.id)||b);nextManifest.regions.push({name:'听小骨',file:trial.file});nextManifest.available_count=206;}

   const nextRows=new Map(nextManifest.bones.map(b=>[b.id,b]));const nextGroups=new Map();const loader=new GLTFLoader();
   for(const regionAsset of nextManifest.regions){
    status(`正在加载${next==='z'?' Z-Anatomy':'原骨架'} · ${regionAsset.name}…`);
    const gltf=await loader.loadAsync(regionAsset.file);gltf.scene.updateMatrixWorld(true);const found=[];gltf.scene.traverse(o=>{if(nextRows.has(o.name))found.push(o);});
    for(const o of found){
     // Detach with world pose preserved, so cached models never overlap on screen.
     const world=o.matrixWorld.clone();o.removeFromParent();world.decompose(o.position,o.quaternion,o.scale);
     o.userData.rest=o.position.clone();o.userData.offset=new THREE.Vector3();
     o.traverse(m=>{if(m.isMesh){m.material=m.material.clone();m.material.color.set(BONE_STYLE.color);m.material.roughness=BONE_STYLE.roughness;m.material.metalness=0;}});
     const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([o.position.clone(),o.position.clone()]),lineMat);line.visible=false;o.userData.line=line;nextGroups.set(o.name,o);
    }
   }
   if(nextGroups.size!==nextManifest.available_count)throw Error('候选对象数量与清单不一致');
   sourceCache.set(next,{groups:nextGroups,rows:nextRows,manifest:nextManifest});
  }
  const data=sourceCache.get(next);
  for(const g of groups.values()){scene.remove(g);scene.remove(g.userData.line);}
  groups.clear();rows.clear();for(const [id,b] of data.rows)rows.set(id,b);for(const [id,g]of data.groups){groups.set(id,g);scene.add(g);scene.add(g.userData.line);}
  manifest=data.manifest;currentSource=next;
  if(isolated&&!groups.has(isolated))isolated=null;
  if(selected&&!groups.has(selected)){selected=null;$('name').textContent='选择一个结构';$('info').textContent='此版本尚未提供此前选中的结构。';for(const id of ['focus','isolate','hide'])$(id).disabled=true;}
  setExplode(explode);applyAppearance();visibility();if(selected)select(selected);
  // Deliberately retain camera and orbit target; compare original dimensions without rescaling.
 }catch(e){status('骨架切换失败：'+e.message+'；保留当前模型。');console.error(e);}
 finally{sourceSwitchBusy=false;syncSourceUI();}
}
$('source-bp').onclick=()=>switchSource('bp');$('source-z').onclick=()=>switchSource('z');


function updateJointStatus(){
 if(jointError&&currentSource==='z'){$('joints-state').textContent=jointError;return;}
 if(currentSource!=='z'){$('joints-state').textContent='原骨架仅用于对照；组织层使用 Z-Anatomy 原配坐标。';return;}
 const tissue=[...rows.values()].filter(b=>b.tissue),counts=Object.fromEntries(['joint','capsule','ligament','surface'].map(type=>[type,tissue.filter(b=>tissueLayer(b)===type).length]));
 $('surfaces-count').textContent=counts.surface+' 骨分区 · 非实体';$('capsules-count').textContent=counts.capsule+' 项候选';$('ligaments-count').textContent=counts.ligament+' 项候选';
 $('joints-state').textContent=jointsLoading?'正在加载原配组织…':`${counts.joint} 项软骨/盘/唇等，${counts.capsule} 项关节囊或囊组，${counts.ligament} 项韧带。未通过解剖验收；拓扑异常项暂未接入，独立髓核不与整体椎间盘重复叠加。`;
}
async function ensureJointLayer(){
 if(currentSource!=='z'||[...rows.values()].some(b=>b.tissue)||jointsLoading)return;
 jointError='';jointsLoading=true;syncSourceUI();
 try{
  const manifests=await Promise.all(['joints','connections','surface-marks'].map(async name=>{const res=await fetch('z-anatomy-candidate/'+name+'.json');if(!res.ok)throw Error(name+' 清单未读取');return res.json();}));
  const allRows=[],allFound=[];
  for(const data of manifests){const gltf=await new GLTFLoader().loadAsync(data.file);gltf.scene.updateMatrixWorld(true);const ids=new Set(data.objects.map(b=>b.id)),found=[];gltf.scene.traverse(o=>{if(ids.has(o.name))found.push(o);});if(found.length!==data.count)throw Error('组织对象数量不一致');allRows.push(...data.objects);allFound.push(...found);}
  if(new Set(allRows.map(b=>b.id)).size!==allRows.length)throw Error('组织 ID 重复');
  for(const b of allRows)rows.set(b.id,b);
  for(const o of allFound){scene.attach(o);o.userData.rest=o.position.clone();o.userData.offset=new THREE.Vector3();o.traverse(m=>{if(m.isMesh){m.material=m.material.clone();m.material.roughness=.8;m.material.metalness=0;}});const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([o.position.clone(),o.position.clone()]),lineMat);line.visible=false;scene.add(line);o.userData.line=line;groups.set(o.name,o);}
  setExplode(explode);applyAppearance();visibility();
 }catch(e){jointsEnabled=false;capsulesEnabled=false;ligamentsEnabled=false;surfacesEnabled=false;$('layer-joints').checked=false;jointError='组织层加载失败：'+e.message+'，重新勾选可重试。';console.error(e);}
 finally{jointsLoading=false;syncSourceUI();}
}
$('layer-surfaces').onchange=async e=>{surfacesEnabled=e.target.checked;if(surfacesEnabled)await ensureJointLayer();applyAppearance();visibility();};
$('layer-capsules').onchange=async e=>{capsulesEnabled=e.target.checked;if(capsulesEnabled)await ensureJointLayer();visibility();};
$('layer-ligaments').onchange=async e=>{ligamentsEnabled=e.target.checked;if(ligamentsEnabled)await ensureJointLayer();visibility();};
$('layer-bones').onchange=e=>{bonesEnabled=e.target.checked;visibility();};
$('layer-joints').onchange=async e=>{jointsEnabled=e.target.checked;if(jointsEnabled)await ensureJointLayer();visibility();};
$('joints-only').onclick=async()=>{jointsEnabled=true;await ensureJointLayer();bonesEnabled=false;earSide=null;isolated=null;hidden.clear();$('layer-bones').checked=false;$('layer-joints').checked=true;visibility();fit();};
await ensureJointLayer();

// Read-only inspection hooks for geometric round-trip and actual ray-picking QA.
window.skeletonQA={snapshot:()=>({source:currentSource,sourceSwitchBusy,jointsLoading,jointsEnabled,capsulesEnabled,ligamentsEnabled,surfacesEnabled,layerCounts:Object.fromEntries(['joint','capsule','ligament','surface'].map(type=>[type,[...rows.values()].filter(b=>b.tissue&&tissueLayer(b)===type).length])),bonesEnabled,jointObjects:[...rows.values()].filter(b=>b.tissue&&tissueLayer(b)!=='surface').length,trialEnabled,earSide,visibleIds:[...groups.keys()].filter(active),mode:$('explode-mode').value,camera:camera.position.toArray(),target:controls.target.toArray(),transforms:Object.fromEntries([...groups].map(([id,g])=>[id,{scale:g.scale.toArray(),quaternion:g.quaternion.toArray()}])),appearance:{...BONE_STYLE,exposure:renderer.toneMappingExposure,key:key.intensity,hemisphere:hemisphere.intensity,fill:fill.intensity},loaded:loadDone,objects:groups.size,visible:[...groups.keys()].filter(active).length,selected,frames,triangles:renderer.info.render.triangles,restError:Math.max(0,...[...groups.values()].map(g=>g.position.distanceTo(g.userData.rest))),assets:manifest?.regions}),project:(id)=>{const g=groups.get(id);if(!g)return null;const p=new THREE.Box3().setFromObject(g).getCenter(new THREE.Vector3()).project(camera),r=renderer.domElement.getBoundingClientRect();return{x:r.left+(p.x+1)*r.width/2,y:r.top+(1-p.y)*r.height/2}},positions:()=>Object.fromEntries([...groups].map(([id,g])=>[id,g.position.toArray()]))};
