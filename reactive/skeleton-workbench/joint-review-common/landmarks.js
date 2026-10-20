import * as THREE from 'three';
export async function setupLandmarks({host,scene,camera,controls,objects,getSide,getSelected,getLandmarkNames,revision}){
 const response=await fetch('landmarks.json'+(revision?'?v='+encodeURIComponent(revision):''),{cache:'no-store'});if(!response.ok)throw Error('骨性标志读取失败');const {landmarks}=await response.json();
 const $=id=>document.getElementById(id),svgNS='http://www.w3.org/2000/svg';
 const svg=document.createElementNS(svgNS,'svg');svg.classList.add('landmark-lines');host.append(svg);
 const entries=landmarks.map(data=>{const label=document.createElement('span');label.className='bone-landmark';label.textContent=data.name;host.append(label);const line=document.createElementNS(svgNS,'line'),circle=document.createElementNS(svgNS,'circle');circle.setAttribute('r','3');svg.append(line,circle);return{data,label,line,circle};});
 const palette=['#cf9954','#5bada2','#7f9fd2','#c9838f','#9ba45b','#a78bc2','#c0845d','#6ea6bc','#b1a06e'];
 const names=[...new Set(landmarks.map(x=>x.name))];
 const regionResponse=await fetch('landmark-regions.json'+(revision?'?v='+encodeURIComponent(revision):''),{cache:'no-store'});if(!regionResponse.ok)throw Error('骨面范围读取失败');
 const regionData=await regionResponse.json();
 for(const e of entries){const color=palette[names.indexOf(e.data.name)%palette.length];e.label.style.setProperty('--landmark-color',color);e.line.style.stroke=color;e.circle.style.fill=color;
  const patch=regionData.regions.find(r=>r.name===e.data.name&&r.side===e.data.side);if(!patch)continue;
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(patch.positions,3));geometry.setIndex(patch.indices);const c=new THREE.Color(color),colors=[];for(const alpha of patch.alpha)colors.push(c.r,c.g,c.b,alpha);geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,4));geometry.computeVertexNormals();
  e.region=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,depthWrite:false,depthTest:true,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1,stencilWrite:true,stencilRef:objects.get(e.data.bone)?.userData.stencilId||255,stencilFunc:THREE.EqualStencilFunc,stencilFail:THREE.KeepStencilOp,stencilZFail:THREE.KeepStencilOp,stencilZPass:THREE.KeepStencilOp}));e.region.renderOrder=2;scene.add(e.region);
 }
 const filter=$('landmark-filter');for(const name of [...new Set(landmarks.map(x=>x.name))]){const o=document.createElement('option');o.value=o.textContent=name;filter.append(o);}
 const related={coraco_acromial:['喙突','肩峰'],coracohumeral:['喙突','大结节','小结节'],conoid:['喙突','锥状结节'],trapezoid:['喙突','斜方线'],acromioclavicular:['肩峰'],transverse_humeral:['大结节','小结节'],superior_glenohumeral:['盂上结节','关节盂','小结节'],middle_glenohumeral:['关节盂','小结节'],inferior_glenohumeral:['关节盂'],superior_transverse_scapular:['喙突'],inferior_transverse_scapular:['盂切迹']};
 function candidates(){const key=getSelected().replace(/^z_lig_/,'').replace(/_ligament_[LR]$/,'');return entries.filter(e=>e.data.side===getSide()&&(filter.value==='all'||filter.value===e.data.name||filter.value==='related'&&(getLandmarkNames?.()||related[key]||['喙突','肩峰']).includes(e.data.name)));}
 function explain(){const named=landmarks.find(x=>x.name===filter.value);$('landmark-description').textContent=named?`${named.name} · ${named.bone_name_zh|| (named.bone.includes('Scapula')?'肩胛骨':named.bone.includes('Humerus')?'肱骨':named.bone.includes('Ulna')?'尺骨':named.bone.includes('Radius')?'桡骨':'锁骨')}。颜色表示该标志附近的骨面定位范围，柔边为示意，不代表完整附着区。`:'显示当前韧带相关的已有骨性标志；未收录的标志不会用邻近点代替。';}
 filter.onchange=()=>{$('bone-landmarks').checked=true;explain();};
 $('locate-landmark').onclick=()=>{const wanted=candidates();if(!wanted.length)return;const center=new THREE.Vector3();for(const e of wanted){center.add(new THREE.Vector3(...e.data.position));const bone=objects.get(e.data.bone);if(bone)bone.visible=true;}center.divideScalar(wanted.length);$('bones').checked=true;$('bone-landmarks').checked=true;const delta=center.clone().sub(controls.target);camera.position.add(delta);controls.target.copy(center);controls.update();};
 explain();
 function frame(){const width=host.clientWidth,height=host.clientHeight;const eligible=new Set(candidates());const shown=[];
 for(const e of entries){const bone=objects.get(e.data.bone);if(e.region){e.region.visible=$('bone-landmarks').checked&&$('landmark-regions').checked&&eligible.has(e)&&!!bone?.visible;if(bone)e.region.position.copy(bone.position).sub(bone.userData.rest);}const p=new THREE.Vector3(...e.data.position);if(bone)p.add(bone.position.clone().sub(bone.userData.rest));p.project(camera);const visible=$('bone-landmarks').checked&&eligible.has(e)&&bone?.visible&&p.z>=-1&&p.z<=1&&Math.abs(p.x)<.98&&Math.abs(p.y)<.98;for(const n of[e.label,e.line,e.circle])n.style.display=visible?'':'none';if(!visible)continue;const x=(p.x+1)*width/2,y=(1-p.y)*height/2;shown.push({e,x,y,left:x<width/2});}
 for(const left of [true,false]){let prev=72;const list=shown.filter(s=>s.left===left).sort((a,b)=>a.y-b.y);for(let i=0;i<list.length;i++){const {e,x,y}=list[i];const labelX=Math.max(8,Math.min(width-96,x+(left?-110:30)));const labelY=Math.min(height-80-(list.length-1-i)*28,Math.max(prev,y-14));prev=labelY+28;e.label.style.left=labelX+'px';e.label.style.top=labelY+'px';e.line.setAttribute('x1',x);e.line.setAttribute('y1',y);e.line.setAttribute('x2',labelX+(left?e.label.offsetWidth:0));e.line.setAttribute('y2',labelY+12);e.circle.setAttribute('cx',x);e.circle.setAttribute('cy',y);}}
 }
 return {frame};
}
