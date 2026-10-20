"""Build a reviewable whole-body joint-layer inventory from local evidence only."""
from pathlib import Path
import json,csv,re,hashlib,collections
R=Path(__file__).resolve().parent
P=R.parent
W=P.parent/'skeleton-workbench'
base=json.loads((P/'data/joint-connections.json').read_text())['connections']
bones={b['id']:b for b in json.loads((W/'data/structures.json').read_text())['bones']}
z=json.loads((R/'research/z-joint-objects.json').read_text())
zmap={x['name']:x for x in z['objects']}
original_index_names=set(zmap)
all_source_path=R/'research/all-source-objects.json'
if all_source_path.exists():
 for x in json.loads(all_source_path.read_text())['objects']:
  if x['type']=='MESH' and x['faces']:zmap.setdefault(x['name'],{'name':x['name'],'type':x['type'],'vertices':x['vertices'],'polygons':x['faces']})

quality_path=R/'research/joint-geometry-quality.json'
quality={x['object']:x for x in json.loads(quality_path.read_text())['objects']} if quality_path.exists() else {}
parts=[]
for line in (P/'source-audit/upstream/parts_list_e.txt').read_text().splitlines()[1:]:
 if '\t' in line:
  id,name=line.split('\t',1);parts.append({'id':id.strip('"'),'name':name.strip('"')})
rows=[];coverage=[]
def add(id,name,region,tissue,connections=(),bone_ids=(),source_names=(),note='',granularity='individual',stage=1):
 evidence=[]
 for name_en in source_names:
  if name_en in zmap:
   obj=zmap[name_en]
   evidence.append({'source':'Z-Anatomy local Startup.blend','object':name_en,'evidence_file':'research/z-joint-objects.json' if name_en in original_index_names else 'research/all-source-objects.json','type':obj['type'],'vertices':obj['vertices'],'polygons':obj['polygons'],'local_mesh':obj['type']=='MESH' and bool(obj['polygons']),'evaluated_geometry':quality.get(name_en),'quality_review':'pending','registration':'not_registered_to_current_skeleton','license':'per_object_review_pending'})
  # Exact labels only: ontology labels do not establish mesh existence.
  for p in parts:
   if p['name'].lower()==name_en.lower(): evidence.append({'source':'BodyParts3D 3.0 parts_list_e.txt','source_id':p['id'],'label':p['name'],'local_mesh':False,'evidence_kind':'catalog_label_only'})
 status='local_candidate_mesh' if any(x.get('local_mesh') for x in evidence) else 'catalog_label_only' if evidence else 'no_candidate_matched_in_checked_sources' if source_names else 'no_exact_mesh_mapping' if all_source_path.exists() else 'pending_targeted_source_search'
 rows.append({'id':id,'name_zh':name,'region':region,'tissue_type':tissue,'production_stage':stage,'display_layer':'关节内部组织' if stage==1 else '连接组织','connection_ids':list(connections),'bone_ids':list(bone_ids),'granularity':granularity,'candidate_search_terms':list(source_names),'resource_status':status,'source_evidence':evidence,'accepted_asset':None,'coverage_boundary':None,'anatomy_review':'pending','assembly_review':'pending','motion_review':'pending','note':note})
def area(c):
 id=c['id']
 if id.startswith('spine_'):
  return '颈椎' if 'vertebra_C' in id else '胸椎' if 'vertebra_T' in id else '腰椎'
 if id.startswith(('cranial','tmj','incudo','stapes','hyoid')):return '头颈与听骨'
 if id.startswith('atlanto'):return '颅颈交界'
 if id.startswith(('costo','sterno','costal')):return '肩带' if 'clavicular' in id else '胸廓'
 if id.startswith(('acromio','scapulo','gleno')):return '肩带'
 if id.startswith(('humero','proximal_radio','forearm')):return '肘与前臂'
 if id.startswith(('distal_radio','radiocarpal','intercarpal','cmc','mcp','hand_','intermetacarpal')):return '腕手'
 if id.startswith(('sacro','pubic','hip')):return '骨盆与髋'
 if id.startswith(('tibiofemoral','patellofemoral','proximal_tibio')):return '膝'
 return '踝足'
def surf(c,b,suffix='',label='',note=''):
 add('surface_'+c['id']+'_'+b.removeprefix('bone_')+suffix,(label or bones[b]['name_zh'])+' · '+c['name_zh']+'覆盖区',area(c),'articular_surface_covering',[c['id']],[b],note=note or '待核对覆盖边界、组织类型与连续性；不以整骨套壳代替。按面登记不等于独立软骨块。')
# Expand each existing connection rather than silently treating all joints as hinges.
for c in base:
 id=c['id'];kind=c['kind'];bs=c['bone_ids'];reg=area(c);start=len(rows)
 disposition='listed'
 if id.startswith('spine_'):
  seg=re.findall(r'vertebra_([CTL]\d+)',id)
  if len(seg)==1:seg.append('S1')
  segment='-'.join(seg)
  add('disc_'+segment,'椎间盘 '+segment,reg,'intervertebral_disc',[id],bs,['Intervertebral disc '+segment],note='整体候选不等于纤维环、髓核和终板已分别完成。')
  add('nucleus_'+segment,'髓核 '+segment,reg,'nucleus_pulposus',[id],bs,['Nucleus pulposus '+segment])
  add('annulus_'+segment,'纤维环 '+segment,reg,'annulus_fibrosus',[id],bs,['Annulus fibrosus '+segment],note='与整体椎间盘为父子分解关系，不能同时叠加重复实体。')
  for face,b in zip(['上','下'],bs):add('endplate_'+segment+'_'+face,segment+'椎间盘'+face+'软骨终板',reg,'cartilaginous_endplate',[id],[b])
  for side in ['L','R']:
   for b in bs:surf(c,b,'_'+side,('左' if side=='L' else '右')+bones[b]['name_zh']+'关节突',note='上下相邻椎骨的对应关节突关节覆盖面；按侧及节段校准。')
 elif id=='atlanto_occipital':
  for side in ['L','R']:
   for b in bs:surf(c,b,'_'+side,('左' if side=='L' else '右')+bones[b]['name_zh'])
 elif id=='atlanto_axial':
  for side in ['L','R']:
   for b in bs:surf(c,b,'_lateral_'+side,('左' if side=='L' else '右')+bones[b]['name_zh']+'外侧寰枢关节面')
  for key,name,b in [('anterior_atlas','寰椎前弓后侧齿突关节面',bs[0]),('anterior_dens','齿突前关节面',bs[1]),('posterior_dens','齿突后关节面',bs[1])]:surf(c,b,'_'+key,name)
  add('atlas_transverse_contact','寰椎横韧带前侧与齿突接触区',reg,'fibrocartilaginous_contact',[id],bs,note='属于韧带侧接触组织，需与横韧带共同制作，不虚构第三块骨。')
 elif kind=='motion_segment':raise ValueError(id)
 elif id.startswith('costovertebral'):
  n=int(id.split('_')[1]);rib=next(b for b in bs if 'rib_' in b)
  for b in bs:surf(c,b,'_head',note='肋头关节覆盖区域；肋头分面及对应上下椎体按模板核对，勿按关联骨个数推定。')
  if n<=10:
   for b in [rib,next(b for b in bs if b==f'bone_vertebra_T{n}_M')]:surf(c,b,'_tubercle',note='肋结节—同序胸椎横突关节面；第11、12肋不生成此项。')
 elif id.startswith(('sternocostal','costal_arch')):
  n=int(id.split('_')[-2]);side=id[-1];suf='.'+side.lower();label=('左' if side=='L' else '右')+f'第{n}肋软骨'
  ordinal=['','first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth'][n]
  add('costal_cartilage_'+str(n)+'_'+side,label,reg,'costal_cartilage',[id],bs,['Costal cartilage of '+ordinal+' rib'+suf,('left' if side=='L' else 'right')+' '+ordinal+' costal cartilage'],note='肋软骨本体；肋软骨连接与胸肋/软骨间连接分别登记；第1胸肋为软骨结合。')
  add('junction_'+id,c['name_zh']+'界面',reg,'joint_interface_review',[id],bs,note='第1胸肋不套用普通滑膜关节；第8—10肋软骨弓连接及变异需分别核对。',granularity='interface_to_review')
 elif kind in ['synovial','synovial_group','paired_synovial','mixed_joint_complex']:
  for b in bs:surf(c,b)
 elif kind=='joint_group':
  side=id[-1]
  if id.startswith('intercarpal'):
   pairs=[('scaphoid','lunate'),('lunate','triquetrum'),('triquetrum','pisiform'),('trapezium','trapezoid'),('trapezoid','capitate'),('capitate','hamate'),('scaphoid','trapezium'),('scaphoid','trapezoid'),('scaphoid','capitate'),('lunate','capitate'),('lunate','hamate'),('triquetrum','hamate')]
  elif id.startswith('distal_intertarsal'):
   pairs=[('navicular','medial_cuneiform'),('navicular','intermediate_cuneiform'),('navicular','lateral_cuneiform'),('medial_cuneiform','intermediate_cuneiform'),('intermediate_cuneiform','lateral_cuneiform'),('lateral_cuneiform','cuboid'),('navicular','cuboid')]
  else:
   prefix='metacarpal' if id.startswith('intermetacarpal') else 'metatarsal'
   pairs=[(f'{prefix}_{n}',f'{prefix}_{n+1}') for n in range(2,5)]
  for left,right in pairs:
   a,b=f'bone_{left}_{side}',f'bone_{right}_{side}'
   for owner,neighbor in [(a,b),(b,a)]:
    surf(c,owner,'_to_'+neighbor.removeprefix('bone_'),note='对应骨：'+bones[neighbor]['name_zh']+'；逐骨对覆盖区域待核对。舟骰界面及其他变异不得默认存在滑膜关节。' if 'navicular' in (left,right) and 'cuboid' in (left,right) else '对应骨：'+bones[neighbor]['name_zh']+'；需按源模型核对骨对关节面与连续性。')
 elif id=='pubic_symphysis':
  add('pubic_interpubic_disc','耻骨间盘',reg,'fibrocartilaginous_disc',[id],bs,['Interpubic disc'])
  for b in bs:surf(c,b,note='耻骨联合的骨侧软骨覆盖，不按滑膜关节制作。')
 elif id=='sacrococcygeal':
  add('sacrococcygeal_disc','骶尾连接纤维软骨候选',reg,'variant_fibrocartilage',[id],bs,note='是否存在及融合状态按模板核对；当前尾骨试拆边界尚未审核。')
 elif kind in ['syndesmosis','fibrous_connection','suture_group']:
  add('fibrous_'+id,c['name_zh']+'纤维连接',reg,'fibrous_connection',[id],bs,note=c['required_soft_tissues']+'；不是关节软骨层。',granularity='group_requires_subdivision' if kind=='suture_group' else 'individual',stage=2)
 else:
  disposition='not_articular_cartilage_layer'
 coverage.append({'id':id,'name_zh':c['name_zh'],'region':reg,'status':disposition,'layer_record_ids':[r['id'] for r in rows[start:]],'notes':c['notes'],'bone_ids':bs})
# Special internal structures, bilateral and explicit.
for side,zh in [('L','左'),('R','右')]:
 for key,label,en,conn,tissue,note in [
 ('tmj_disc','颞下颌关节盘','Articular disc of temporomandibular joint','tmj','articular_disc','盘与上下腔关系需核对；覆盖组织不能一律标透明软骨。'),
 ('sc_disc','胸锁关节盘','Articular disc of sternoclavicular joint','sternoclavicular','articular_disc','先检查厚度与实体性，低面数候选不可直接验收。'),
 ('ac_disc','肩锁关节盘候选','Articular disc of acromioclavicular joint','acromioclavicular','variant_articular_disc','完整性、退变和个体差异待核对，不默认人人均有完整盘。'),
 ('glenoid_labrum','肩关节盂唇','Glenoid labrum','glenohumeral','labrum','保留与囊和二头肌长头附着的关系。'),
 ('tfcc_disc','腕三角纤维软骨复合体—关节盘','Articular disc of distal radio-ulnar joint','distal_radioulnar','articular_disc','仅关节盘，不等同整个 TFCC；韧带、半月板同系物等后续另列。'),
 ('acetabular_labrum','髋臼唇','Acetabular labrum','hip','labrum','髋臼切迹及横韧带关系后续核对。'),
 ('medial_meniscus','膝内侧半月板','Medial meniscus','tibiofemoral','meniscus','前后根及囊附着属于后续连接层。'),
 ('lateral_meniscus','膝外侧半月板','Lateral meniscus','tibiofemoral','meniscus','腘肌腱裂孔等局部关系待核对。')]:
  c=next(c for c in base if c['id']==conn+'_'+side)
  add(key+'_'+side,zh+label,area(c),tissue,[c['id']],c['bone_ids'],[en+'.'+side.lower()],note=note)
 # Floating ribs still have cartilage although they do not reach sternum.
 for n in [11,12]:
  b=f'bone_rib_{n:02d}_{side}'
  if b not in bones:b=f'bone_rib_{n}_{side}'
  add(f'costal_cartilage_{n}_{side}',zh+f'第{n}肋软骨','胸廓','costal_cartilage',bone_ids=[b],note='浮肋前端软骨；未在原有胸肋连接登记中出现，需补入全身层。')
# Explicit omissions of first connection registry.
add('manubriosternal_interface','胸骨柄体连接','胸廓','symphysis_or_fusion',bone_ids=['bone_sternum_M'],note='原模型胸骨已合为单骨语义对象；需要定位内部柄体边界，不能从关节登记缺项推定无结构。')
add('xiphisternal_interface','剑胸连接','胸廓','synchondrosis_or_fusion',bone_ids=['bone_sternum_M'],note='年龄相关融合状态待核对。')
for side,zh in [('L','左'),('R','右')]:
 for n in range(3,8):
  add(f'uncovertebral_C{n-1}_C{n}_{side}',zh+f'C{n-1}—C{n}钩椎区域','颈椎','variant_joint_interface',note='是否独立滑膜腔及年龄相关形态需文献核对；独立列项，不复制关节突表面。',granularity='interface_to_review')
# Supplementary native capsules and ligaments discovered by full object inspection.
supplement=R/'research/additional-mapping.json'
if supplement.exists():
 for x in json.loads(supplement.read_text()):
  if any(r['id']==x['id'] for r in rows):continue
  connections=x['connection_ids'];c=next(c for c in base if c['id']==connections[0])
  add(x['id'],x['name_zh'],area(c),'fibrous_capsule' if x['layer']=='capsule' else 'ligament',connections,x['bone_ids'],[x['source_object']],note='源库组合对象尚需分段核对；关联骨不是精确附着足印。' if x['granularity']=='source_group_unsegmented' else '源坐标候选，附着边界与装配尚待审核。',granularity=x['granularity'],stage=2)
# Local evidence inventory: nomenclature hits can be non-joint cartilage or landmark objects.
raw=[]
for obj in z['objects']:
 name=obj['name'];low=name.lower()
 if not any(k in low for k in ['cartilage','menisc','labrum','disc','pulposus','fibrosus']):continue
 role='candidate_tissue'
 if any(k in low for k in ['thyroid','cricoid','arytenoid','nasal','alar','corniculate','cartilages of ear']):role='outside_musculoskeletal_joint_layer'
 elif 'ligament' in low:role='later_connection_layer'
 elif name.endswith(('.g','.j','.t','.s','.i')):role='group_or_landmark_requires_review'
 raw.append({**obj,'classification':role})
# Candidate export links do not upgrade anatomy acceptance.
for kind in ['joints','connections']:
 path=W/'z-anatomy-candidate'/(kind+'.json')
 if path.exists():
  exported=json.loads(path.read_text());mapping={x['id']:x for x in exported['objects']}
  for row in rows:
   if row['id'] in mapping:row['candidate_asset']={'manifest':'../skeleton-workbench/z-anatomy-candidate/'+kind+'.json','glb':exported['file'],'status':'source_native_candidate_not_validated'}
# Validate ID references and ensure every original connection is accounted for.
assert len({x['id'] for x in rows})==len(rows)
for row in rows:
 for b in row['bone_ids']:assert b in bones,(row['id'],b)
assert len(coverage)==len(base)
stats={'records':len(rows),'original_connections_accounted_for':len(coverage),'accepted_joint_assets':0,'resource_status':dict(collections.Counter(r['resource_status'] for r in rows)),'regions':dict(collections.Counter(r['region'] for r in rows)),'scope_tasks':sum(r['granularity']=='group_requires_subdivision' for r in rows)}
def dump(name,data):(R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
dump('全身关节层台账.json',{'status':'planning_and_local_candidate_audit_not_anatomical_validation','scope':'全身关节层首版；条目含覆盖区域、内部组织和待拆分任务，条目数不是人体关节数或最终模型数','statistics':stats,'resource_triage_report':'剩余资源处置台账.json','objects':rows})
dump('连接覆盖检查.json',coverage)
dump('research/候选组织分类.json',raw)
with (R/'全身关节层台账.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['ID','名称','区域','组织类型','批次','条目粒度','资源状态','候选对象','关联骨','备注'])
 for x in rows:writer.writerow([x['id'],x['name_zh'],x['region'],x['tissue_type'],x['production_stage'],x['granularity'],x['resource_status'],'; '.join(e.get('object',e.get('label','')) for e in x['source_evidence']),'; '.join(x['bone_ids']),x['note']])
md=['# 全身关节层逐项清单','', '首版范围：覆盖原有全部连接登记，并补入部分此前未登记组织。所有条目尚未通过解剖审核；逐面条目是覆盖区域，不是独立软骨块。', '',f'共 {len(rows)} 条，覆盖 {len(coverage)} 条原有连接登记；含 {stats["scope_tasks"]} 条仍需拆分的任务。条目数不是人体关节数。','', '资源状态：本地候选网格 ≠ 已配准模型；目录名称 ≠ 本地几何；未匹配 ≠ 世界上没有资源。','']
status={'local_candidate_mesh':'本地候选网格，待核对','catalog_label_only':'只有目录名称','no_candidate_matched_in_checked_sources':'指定名称在已查来源未匹配','pending_targeted_source_search':'待逐项检索/覆盖区标定','no_exact_mesh_mapping':'本地已核查，逐面映射待定'}
for reg in stats['regions']:
 md += ['## '+reg,'','| ID | 结构/覆盖区 | 资源 | 备注 |','|---|---|---|---|']
 for x in rows:
  if x['region']==reg:md.append(f'| {x["id"]} | {x["name_zh"]} | {status[x["resource_status"]]} | {x["note"]} |')
 md.append('')
(R/'全身关节层清单.md').write_text('\n'.join(md)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
