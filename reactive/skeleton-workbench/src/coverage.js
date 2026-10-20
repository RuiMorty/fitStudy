// This inventory describes production status, never anatomical acceptance.
export async function setupCoverage(onView) {
 const root=document.getElementById('coverage');
 try {
  const res=await fetch('z-anatomy-candidate/coverage.json');
  if(!res.ok)throw Error('清单读取失败');
  const data=await res.json();
  const labels={extracted_split_seam_candidate:'拆缝候选待审核',segmented_surface_candidate:'已拆分表面候选',extracted_candidate:'已有候选模型',bone_material_partition_candidate:'仅有骨表面线索',repair_geometry_first:'待修整',excluded_duplicate_component:'暂不重复叠加',inspect_component_inside_disc:'待核对盘内组成',labels_or_guides_only:'仅有标注',reference_and_boundary_work_required:'待补建依据',additional_named_mesh_candidate:'源模型待核对'};
  const note=document.createElement('p');note.textContent=`${data.records.length} 条制作记录，均未通过解剖验收。表面线索不等于独立软骨模型；本清单针对 Z-Anatomy。`;
  const input=document.createElement('input');input.type='search';input.placeholder='查部位或结构，如：肘、膝';input.setAttribute('aria-label','查找制作进度');input.id='coverage-search';
  const filters=document.createElement('div');filters.className='coverage-filters';let state='all',limit=30;
  for(const [key,label] of [['all','全部'],...Object.entries(labels)]){const n=key==='all'?data.records.length:data.records.filter(r=>r.decision===key).length;if(!n)continue;const b=document.createElement('button');b.textContent=`${label} ${n}`;b.dataset.state=key;b.setAttribute('aria-pressed',String(key==='all'));b.onclick=()=>{state=key;limit=30;for(const el of filters.children)el.setAttribute('aria-pressed',String(el===b));render();};filters.append(b);}
  const count=document.createElement('p');count.setAttribute('role','status');const list=document.createElement('div');list.className='coverage-list';const more=document.createElement('button');more.textContent='再显示 30 条';more.onclick=()=>{limit+=30;render();};
  function render(){const q=input.value.trim();const rows=data.records.filter(r=>(state==='all'||r.decision===state)&&(!q||(r.name_zh+' '+r.region).includes(q)));count.textContent=`符合 ${rows.length} 条 · 显示 ${Math.min(limit,rows.length)} 条`;list.replaceChildren();for(const r of rows.slice(0,limit)){const item=document.createElement('article'),title=document.createElement('strong'),status=document.createElement('small'),reason=document.createElement('p');title.textContent=r.name_zh;status.textContent=`${r.region} · ${labels[r.decision]}`;reason.textContent=r.reason;item.append(title,status,reason);if(r.decision==='extracted_split_seam_candidate'||r.decision==='extracted_candidate'||r.decision==='segmented_surface_candidate'){const b=document.createElement('button');b.textContent='查看模型';b.onclick=async()=>{b.disabled=true;try{await onView(r.model_ids?.[0]||r.id);}finally{b.disabled=false;}};item.append(b);}list.append(item);}more.hidden=rows.length<=limit;}
  input.oninput=()=>{limit=30;render();};root.append(note,input,filters,count,list,more);render();
 }catch(e){const p=document.createElement('p');p.textContent='制作进度暂不可用：'+e.message;root.append(p);}
}
