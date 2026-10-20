from pathlib import Path
import json,collections,csv
R=Path(__file__).resolve().parent;P=R.parent;W=P.parent.parent/'skeleton-workbench';source=json.loads((R/'all-source-objects.json').read_text());objects={o['name']:o for o in source['objects']};materials=json.loads((R/'bone-cartilage-materials.json').read_text());bybone=collections.defaultdict(list)
for m in materials:
 if m['cartilage_faces']:bybone[m['bone_id']].append(m)
plan=json.loads((P/'全身关节层台账.json').read_text());exported={};excluded={}
for file in ['joints','connections']:
 data=json.loads((W/'z-anatomy-candidate'/ (file+'.json')).read_text())
 for x in data['objects']:exported[x['id']]={'file':'z-anatomy-candidate/'+file+'.json','source_object':x['source_structure_id']}
 for x in data.get('excluded',[]):excluded[x['id']]=x
records=[]
for r in plan['objects']:
 id=r['id'];sources=[];reason=''
 if id in exported:decision='extracted_candidate';sources=[exported[id]];reason='已接入源坐标候选，非解剖验收。'
 elif id in excluded:decision='excluded_duplicate_component' if r['tissue_type']=='nucleus_pulposus' else 'repair_geometry_first';sources=[excluded[id]];reason=excluded[id]['reason']
 elif r['tissue_type']=='annulus_fibrosus':decision='inspect_component_inside_disc';sources=[{'source_object':'Intervertebral disc '+id.removeprefix('annulus_'),'separate_object_found':False}];reason='全对象名、材质和顶点组索引未建立独立纤维环映射；需检查整体盘与髓核边界，不能直接相减生成。'
 elif r['tissue_type'] in ['articular_surface_covering','cartilaginous_endplate'] and any(b in bybone for b in r['bone_ids']):
  decision='bone_material_partition_candidate';sources=[m for b in r['bone_ids'] for m in bybone[b]];reason='相关骨存在 Cartilage 材质面，需按本关节确定覆盖区；骨级分区不是本条逐关节面的准确映射，无独立厚度。'
 else:
  candidates=list(r.get('candidate_search_terms',[]))
  if id.startswith('fibrous_forearm_interosseous_'):candidates+=['Interosseous membrane of forearm.'+id[-1].lower()]
  if id=='sacrococcygeal_disc':candidates+=['Sacrococcygeal symphysis']
  if id.startswith('uncovertebral'):candidates+=['Uncovertebral joints.j','Uncovertebral joints.g']
  found=[objects[n] for n in candidates if n in objects];sources=found
  if any(x['type']=='MESH' and x['faces'] for x in found):decision='additional_named_mesh_candidate';reason='实际源库中存在有面的对象；未完成本条语义映射、网格质量和接入。'
  elif found:decision='labels_or_guides_only';reason='找到的是文字或无面的辅助对象，不是组织实体。'
  else:decision='reference_and_boundary_work_required';reason='本轮本地全对象/材质检查未建立可用映射；先核对图谱边界与命名，再决定其他来源或补建，不宣称资源不存在。'
 records.append({'id':id,'name_zh':r['name_zh'],'region':r['region'],'tissue_type':r['tissue_type'],'decision':decision,'reason':reason,'evidence':sources,'anatomy_review':'pending'})
counts=dict(collections.Counter(r['decision'] for r in records));result={'scope':'local complete object inventory and rule-based resource triage; not anatomical validation or exhaustive external search','source_sha256':source['source_sha256'],'source_objects':len(objects),'plan_records':len(records),'summary':counts,'records':records}
(P/'剩余资源处置台账.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
labels={'extracted_candidate':'已提取候选','excluded_duplicate_component':'避免重复叠加','repair_geometry_first':'先修几何','inspect_component_inside_disc':'核对整体盘内组成','bone_material_partition_candidate':'骨网格材质分区候选','additional_named_mesh_candidate':'新增有面对象待核对','labels_or_guides_only':'只有标注/辅助对象','reference_and_boundary_work_required':'需参考与边界核查'}
with (P/'剩余资源处置台账.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['ID','名称','区域','处置类别','说明'])
 for r in records:writer.writerow([r['id'],r['name_zh'],r['region'],labels[r['decision']],r['reason']])
print(json.dumps(counts,ensure_ascii=False,indent=2))
