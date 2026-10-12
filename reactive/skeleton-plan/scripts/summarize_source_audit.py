import json,csv,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];A=R/'source-audit';m=json.loads((A/'mapping.json').read_text());g=json.loads((A/'geometry-audit.json').read_text());d=json.loads((A/'mesh-download.json').read_text());j=json.loads((A/'joint-source-screening.json').read_text());ontology={row['Preferred Label'].lower():'FMA'+row['FMAID'] for row in csv.DictReader((A/'upstream/FMA.csv').open())};probes={x['source_id']:x for x in d['files'] if x.get('probe_only')}
for b in m['core']:
 if not b['source_id']:
  sid=ontology.get(b['lookup_label']);b['ontology_id_not_a_model']=sid;b['expected_mesh_http_status']=probes.get(sid,{}).get('http_status')
 if b['id']=='bone_coccyx_M':
  b['mapping_status']='candidate_embedded_in_sacrum_requires_anatomical_segmentation';b['candidate_container_ids']=['FMA16202'];b['note']='No separate coccyx release entry or expected STL. Source sacrum visibly includes a caudal tail-like region; anatomical boundary remains unconfirmed. Do not duplicate the entire sacrum as a coccyx object.'
 for sid in b['primitive_ids']:
  geo=g['source_meshes'][sid]
  if geo['component_count']>1:b.setdefault('geometry_notes',[]).append({'source_id':sid,'component_triangles':[x['triangles'] for x in geo['components']],'status':'small_disconnected_fragments_require_review_not_silent_deletion'})
(A/'mapping.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
coord=dict(units='millimetres',left='positive X',right='negative X',anterior='negative Y',posterior='positive Y',superior='increasing Z',evidence_file='upstream/coordinate_system.png',sha256=hashlib.sha256((A/'upstream/coordinate_system.png').read_bytes()).hexdigest(),note='Fetched from the same fixed commit. Source diagram says all Z positive; measured foot extremity reaches -4.171 mm, recorded rather than shifted.')
(A/'coordinate-evidence.json').write_text(json.dumps(coord,indent=2)+'\n');g['unit_status']='mm confirmed by coordinate-system diagram fetched from same commit; geometry has not been individually repositioned or rescaled';(A/'geometry-audit.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n')
summary=dict(date='2026-10-12',source_commit=m['commit'],decision='partial_source_coverage_not_ready_for_206_bone_production',core_count=206,core_direct_mapping=199,single_mesh_bones=198,composite_bones=1,core_raw_mesh_files=201,candidate_embedded_coccyx=1,unlocated_ear_ossicles=6,extension_foot_group_files=2,extension_foot_connected_components=4,extension_thumb_sesamoids_unlocated=4,raw_files_downloaded=203,raw_bytes=sum(x.get('bytes',0) for x in d['files']),all_downloaded_binary_stl_valid=True,left_right_pairs_checked=83,explicit_all_joint_approval=False,anatomical_approval=False)
(A/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
status={'single_index_match':'单文件已下载核验','composite_index_match':'组合部件已下载，需作为一个结构管理','not_found_in_release_index':'索引及对应文件未找到','candidate_embedded_in_sacrum_requires_anatomical_segmentation':'疑似并入骶骨，待边界审核/拆分'}
with (A/'骨骼资源映射.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['结构ID','中文名','源语义ID','源部件文件','核对结果','关节装配审核','备注'])
 for b in m['core']:w.writerow([b['id'],b['name_zh'],b['source_id'] or '', ';'.join(x+'.stl' for x in b['primitive_ids']),status[b['mapping_status']],'未完成',b.get('note','')])
lines=['# 206块骨骼资源映射结果','', '固定来源：BodyParts3D 3.0，镜像提交 `'+m['commit']+'`。2026-10-12核对。文件可用不代表解剖、关节配合或运动已通过。','', '| 项目ID | 骨骼 | 源ID | 原始部件 | 核对结果 |','|---|---|---|---|---|']
for b in m['core']:lines.append('| '+' | '.join([b['id'],b['name_zh'],b['source_id'] or '—',', '.join(b['primitive_ids']) or '—',status[b['mapping_status']]])+' |')
lines += ['','## 核心206之外的扩展','', '| 结构 | 候选来源 | 结果 |','|---|---|---|']
for b in m['extensions']:lines.append('| '+b['name_zh']+' | '+(b['source_group_id'] or '—')+' | '+('源组有两个连通体；与拇趾及内外侧的对应关系待解剖核对' if b['source_group_id'] else '本版本部件索引未找到')+' |')
(A/'逐骨核对结果.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
