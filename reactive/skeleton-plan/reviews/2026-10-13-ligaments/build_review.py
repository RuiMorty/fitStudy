from pathlib import Path
import json,csv,re,struct,hashlib,collections,html
from anatomy_rules import RULES,complete_names
P=Path(__file__).resolve().parent;ROOT=P.parents[2];W=ROOT/'skeleton-workbench';D=W/'z-anatomy-candidate'
bones={b['id']:b for b in json.loads((D/'structures.json').read_text())['bones']};connections={c['id']:c['name_zh'] for c in json.loads((W/'data/connections.json').read_text())['connections']};source={o['name']:o for o in json.loads((ROOT/'skeleton-plan/layer-plan/research/all-source-objects.json').read_text())['objects']}
inputs=[D/'connections.json',D/'ligament-library.json',D/'structures.json',W/'src/app.js',W/'index.html',D/'assets/connections.glb',D/'assets/ligament-library.glb',W/'research/ossicles/Startup.blend'];hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs}
rows=[];bbox={}
for name in ['connections','ligament-library']:
 data=json.loads((D/(name+'.json')).read_text());rows += [r for r in data['objects'] if r.get('tissue_layer')=='ligament'];raw=(W/data['file']).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n])
 for node in g['nodes']:
  if 'mesh' not in node:continue
  if any(k in node for k in ['matrix','rotation','scale']):raise ValueError('Need full world transform audit for '+node.get('name',''))
  acc=g['accessors'][g['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION']];t=node.get('translation',[0,0,0]);bbox[node['name']]={'min':[a+b for a,b in zip(acc['min'],t)],'max':[a+b for a,b in zip(acc['max'],t)]}
complete_names({re.sub(r'\.[rl]$','',r['source_structure_id']) for r in rows});out=[]
def bone_name(i):return bones.get(i,{}).get('name_zh',i)
for row in rows:
 name=row['source_structure_id'];stem=re.sub(r'\.[rl]$','',name);rule=RULES[stem];side=row['side'];issues=[];priority='P3';src=source.get(name);bounds=bbox.get(row['id']);evidence=[]
 source_ok=bool(src and src['type']=='MESH' and src.get('faces',0));asset_ok=bounds is not None
 if not source_ok or not asset_ok:issues.append('源对象或导出对象未匹配');priority='P1'
 expected_side=name[-1].upper() if re.search(r'\.[rl]$',name) else None
 if expected_side and expected_side!=side:issues.append('源名侧别与记录不一致');priority='P1'
 if side in ['L','R'] and bounds:
  x=(bounds['min'][0]+bounds['max'][0])/2
  if (side=='L' and x<-.003) or (side=='R' and x>.003):issues.append('左右名称与位置相反：源文件及导出均已复核，与同名侧颞骨位于相反半身；请二核是否交换左右名称');priority='P1'
 if side=='unknown':issues.append('源名无左右后缀；源坐标及导出坐标均在右侧（x约-0.242m），建议按右侧尺豌豆韧带二核');priority='P1'
 invalid=[i for i in row['bone_ids'] if i not in bones]
 if invalid:issues.append('存在无效骨 ID：'+','.join(invalid));priority='P1'
 expected=[]
 for b in rule['bones']:
  if b.endswith('_M'):bid='bone_'+b
  elif b in ['sternum','sphenoid','hyoid','mandible','sacrum','coccyx']:bid='bone_'+b+'_M'
  elif side in ['L','R']:bid='bone_'+b+'_'+side
  else:continue
  if bid in bones:expected.append(bid)
 current=set(row['bone_ids']);missing=sorted(set(expected)-current);extra=sorted(current-set(expected)) if expected else []
 if expected and (missing or extra):
  issues.append('区域关联与初核的附着骨集合不等同；不能把 bone_ids 直接显示为起止点')
  if priority!='P1':priority='P2'
 if missing and '仅名称' not in rule['basis']:
  issues.append('初核涉及的骨未在当前关联中：'+'、'.join(bone_name(x) for x in missing));priority='P1'
 if not expected:
  issues.append('需要节段、双侧或软组织关系，单纯骨列表不足以表达')
  if priority!='P1':priority='P2'
 soft=any(word in rule['description'] for word in ['半月板','肌腱','腘肌腱','半膜肌腱','与桡骨环状韧带融合'])
 if soft:
  issues.append('需新增明确的软组织连接关系；当前只有骨及关节目录')
  if priority!='P1':priority='P2'
 grouped=bool('组' in row['name_zh'] or re.search(r'ligaments|Ligamenta',stem))
 if grouped:issues.append('源名称表示组合结构，尚不能按一个已细分韧带解读')
 seams=row.get('geometry_audit',{}).get('split_branch_edges',0)
 if seams:issues.append(f'曾拆开 {seams} 条分叉共边，组织连续性需另行核对');priority='P1'
 if stem=='Nuchal ligament':issues.append('当前关联遍及胸腰骶尾，超出项韧带部位；应按颈后结构整理目录');priority='P1'
 if row['id']=='z_lig_ulnar_collateral_ligament_R':issues.append('已有三向形态核查：横向延伸至桡骨头附近，三束不清；源模型形态可疑');priority='P1'
 if stem in ['Calcaneonavicular ligament','Calcaneocuboid ligament','Radiate carpal ligament','Intersesamoid ligament','Dorsal ulnocarpal ligament']:
  issues.append('名称范围/分束命名需专门图谱核对，不能与近名结构直接合并')
 if not issues:issues.append('未发现名称/资源/粗骨关联的明显冲突；未核对精确足印与形态')
 tier='C 名称语义初筛' if rule['basis'].startswith('仅名称') else 'D 需专门连接参考' if rule['basis'].startswith('信息结构') else 'A 有章节支持的总体关系' if rule['basis'].startswith('OpenStax') else 'B 解剖关系初核'
 out.append({'id':row['id'],'name_zh':row['name_zh'],'source_object':name,'side':side,'region':row['region'],'priority':priority,'review_depth':tier,'source_object_matches':source_ok,'export_object_matches':asset_ok,'current_bones':[bone_name(i) for i in row['bone_ids']],'current_bone_ids':row['bone_ids'],'current_connections':[connections.get(i,i) for i in row['joint_or_connection_ids']],'expected_relation_for_second_review':rule['description'],'expected_bone_ids_first_pass':expected,'missing_from_current_first_pass':[bone_name(i) for i in missing],'extra_regional_bones_not_direct_attachment':[bone_name(i) for i in extra],'basis':rule['basis'],'findings':issues,'source_group_name':grouped,'split_branch_edges':seams,'bbox_web_m':bounds,'geometry_review':'右尺侧副韧带已有三视图核查，见 qa/ucl-audit' if row['id']=='z_lig_ulnar_collateral_ligament_R' else '已复核源文件及导出左右坐标，未核对形态/足印' if stem=='Lateral temporomandibular ligament' or side=='unknown' else '未逐模型做形态/足印核查','precise_footprints_checked':False,'anatomy_accepted':False,'reviewer_decision':'','reviewer_notes':''})
out.sort(key=lambda r:(r['priority'],r['region'],r['source_object']))
summary={'date':'2026-10-13','objects':len(out),'source_name_types':len(RULES),'priority_counts':dict(collections.Counter(r['priority'] for r in out)),'depth_counts':dict(collections.Counter(r['review_depth'] for r in out)),'all_sources_and_exports_match':all(r['source_object_matches'] and r['export_object_matches'] for r in out),'unknown_side':sum(r['side']=='unknown' for r in out),'source_group_names':sum(r['source_group_name'] for r in out),'split_seam_candidates':sum(r['split_branch_edges']>0 for r in out),'missing_expected_bone_first_pass':sum(bool(r['missing_from_current_first_pass']) for r in out),'anatomically_accepted':0,'scope':'All loaded ligament/membrane information audited; not all anatomy/geometry validated. Regional association is not the same as attachment. Priority is review urgency, not confirmed error count.'}
assert len(out)==290 and len({r['id'] for r in out})==290
(P/'完整核对结果.json').write_text(json.dumps({'summary':summary,'objects':out,'input_sha256':hashes},ensure_ascii=False,indent=2)+'\n')
cols=[('id','对象 ID'),('name_zh','当前中文名'),('source_object','源英文名'),('side','侧别'),('region','区域'),('priority','复核优先级'),('review_depth','核对深度'),('current_bones','当前关联骨'),('current_connections','当前关联关节'),('expected_relation_for_second_review','建议二核的解剖关系'),('findings','发现与疑点'),('missing_from_current_first_pass','初核涉及但当前未关联的骨'),('extra_regional_bones_not_direct_attachment','区域关联中不能直接当起止点的骨'),('basis','依据及限度'),('geometry_review','模型形态核查状态'),('reviewer_decision','你的二核结论'),('reviewer_notes','你的备注与更改建议')]
with (P/'逐项二次核对表.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow([title for _,title in cols])
 for r in out:writer.writerow(['；'.join(r[k]) if isinstance(r[k],list) else r[k] for k,_ in cols])
# No production inputs may change during this audit.
assert hashes=={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs}
(P/'保护检查.json').write_text(json.dumps({'production_inputs_unchanged':True,'files':hashes},indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
