"""Build a planning inventory, not anatomy assets or a validated anatomical model."""
import json,csv,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
B=[];J=[]
refs={'颅骨':'AXIAL_SKULL','听小骨':'AXIAL_SKULL','舌骨':'AXIAL_SKULL','脊柱':'AXIAL_SPINE','胸廓':'AXIAL_THORAX','上肢':'APPENDICULAR_UPPER','下肢':'APPENDICULAR_LOWER'}
def bone(key,zh,en,region,side='M',notes=''):
 bid='bone_'+key+'_'+side
 B.append(dict(id=bid,name_zh=({'L':'左','R':'右','M':''}[side])+zh,name_en=en,side=side,region=region,count=1,reference_id=refs[region],source_set='bodyparts3d_3_0_candidate',source_structure_id=None,source_file=None,source_sha256=None,source_status='not_mapped',anatomy_review='pending',assembly_review='pending',rest_transform=None,joint_or_connection_ids=[],landmark_region_ids=[],notes=notes))
 return bid
for key,zh,en in [('frontal','额骨','Frontal bone'),('occipital','枕骨','Occipital bone'),('sphenoid','蝶骨','Sphenoid bone'),('ethmoid','筛骨','Ethmoid bone'),('mandible','下颌骨','Mandible'),('vomer','犁骨','Vomer')]:bone(key,zh,en,'颅骨')
for side in ['L','R']:
 for key,zh,en in [('parietal','顶骨','Parietal bone'),('temporal','颞骨','Temporal bone'),('maxilla','上颌骨','Maxilla'),('zygomatic','颧骨','Zygomatic bone'),('nasal','鼻骨','Nasal bone'),('lacrimal','泪骨','Lacrimal bone'),('palatine','腭骨','Palatine bone'),('inferior_nasal_concha','下鼻甲','Inferior nasal concha')]:bone(key,zh,en,'颅骨',side)
 for key,zh,en in [('malleus','锤骨','Malleus'),('incus','砧骨','Incus'),('stapes','镫骨','Stapes')]:bone(key,zh,en,'听小骨',side)
bone('hyoid','舌骨','Hyoid','舌骨',notes='通过肌肉、韧带悬吊；不建立虚构的骨性铰链。')
for section,n,zh,en in [('C',7,'颈椎','Cervical vertebra'),('T',12,'胸椎','Thoracic vertebra'),('L',5,'腰椎','Lumbar vertebra')]:
 for i in range(1,n+1):bone(f'vertebra_{section}{i}',('寰椎（C1）' if section=='C' and i==1 else '枢椎（C2）' if section=='C' and i==2 else f'第{i}{zh}（{section}{i}）'),f'{en} {section}{i}','脊柱')
bone('sacrum','骶骨','Sacrum','脊柱',notes='成人融合骨按1块计；骶椎分节只作为子区域，不重复计数。')
bone('coccyx','尾骨','Coccyx','脊柱',notes='标准成人清单按1块计；融合与分节存在变异，不能将整体固定概括为完全融合。')
bone('sternum','胸骨','Sternum','胸廓',notes='按1块计，保留胸骨柄/体/剑突子区域及连接状态，勿当作永不变形的整块胸廓。')
for side in ['L','R']:
 for i in range(1,13):bone(f'rib_{i:02}',f'第{i}肋骨',f'Rib {i}','胸廓',side,('真肋，经各自肋软骨连胸骨。' if i<=7 else '假肋，经肋软骨连接肋弓。' if i<=10 else '浮肋，无前方胸骨连接。')+'肋软骨不计入骨数。')
 for key,zh,en in [('clavicle','锁骨','Clavicle'),('scapula','肩胛骨','Scapula'),('humerus','肱骨','Humerus'),('radius','桡骨','Radius'),('ulna','尺骨','Ulna')]:bone(key,zh,en,'上肢',side)
 for key,zh,en in [('scaphoid','手舟骨','Scaphoid'),('lunate','月骨','Lunate'),('triquetrum','三角骨','Triquetrum'),('pisiform','豌豆骨','Pisiform'),('trapezium','大多角骨','Trapezium'),('trapezoid','小多角骨','Trapezoid'),('capitate','头状骨','Capitate'),('hamate','钩骨','Hamate')]:bone(key,zh,en,'上肢',side)
 for i in range(1,6):
  bone(f'metacarpal_{i}',f'第{i}掌骨',f'Metacarpal {i}','上肢',side)
  for seg,cn in [('proximal','近节'),('middle','中节'),('distal','远节')]:
   if i==1 and seg=='middle':continue
   bone(f'hand_phalanx_{i}_{seg}',f'{["拇指","示指","中指","环指","小指"][i-1]}{cn}指骨',f'Hand digit {i} {seg} phalanx','上肢',side)
 for key,zh,en in [('hip','髋骨','Hip bone'),('femur','股骨','Femur'),('patella','髌骨','Patella'),('tibia','胫骨','Tibia'),('fibula','腓骨','Fibula'),('talus','距骨','Talus'),('calcaneus','跟骨','Calcaneus'),('navicular','足舟骨','Navicular'),('cuboid','骰骨','Cuboid'),('medial_cuneiform','内侧楔骨','Medial cuneiform'),('intermediate_cuneiform','中间楔骨','Intermediate cuneiform'),('lateral_cuneiform','外侧楔骨','Lateral cuneiform')]:bone(key,zh,en,'下肢',side,'成人髂骨、坐骨、耻骨融合按1块计；保留三个子区域及髋臼/闭孔等标志。' if key=='hip' else '')
 for i in range(1,6):
  bone(f'metatarsal_{i}',f'第{i}跖骨',f'Metatarsal {i}','下肢',side)
  for seg,cn in [('proximal','近节'),('middle','中节'),('distal','远节')]:
   if i==1 and seg=='middle':continue
   bone(f'foot_phalanx_{i}_{seg}',f'{["拇趾","第二趾","第三趾","第四趾","第五趾"][i-1]}{cn}趾骨',f'Foot digit {i} {seg} phalanx','下肢',side)
lookup={b['id']:b for b in B}
def bid(k,s='M'):return f'bone_{k}_{s}'
def joint(key,name,bones,kind,motion,soft,notes='',priority='P1'):
 for b in bones:assert b in lookup,(key,b)
 j=dict(id=key,name_zh=name,bone_ids=bones,kind=kind,motion_requirements=motion,required_soft_tissues=soft,calibration_status='pending_geometry_and_anatomy_review',joint_frames=None,axis_definition=None,range_of_motion=None,priority=priority,notes=notes)
 J.append(j)
 for b in bones:lookup[b]['joint_or_connection_ids'].append(key)
# Connection groups are explicit planning groups, not a claim to enumerate every synovial joint.
joint('cranial_sutures','颅骨缝连接组',[b['id'] for b in B if b['region']=='颅骨' and b['id']!=bid('mandible')],'suture_group','日常运动示范保持整体稳定；各骨可独立展开','颅缝纤维组织','包含多条实际颅缝；逐缝结构与边界需后续另列，不能把本组当成一个关节。','P2')
joint('hyoid_suspension','舌骨悬吊',[bid('hyoid')],'soft_tissue_suspension','由周围肌肉与韧带关系控制，不虚构骨性转轴','舌骨上/下肌群、茎突舌骨韧带','其他附着骨关系由软组织连接表描述。','P2')
joint('atlanto_occipital','寰枕关节组',[bid('occipital'),bid('vertebra_C1')],'paired_synovial','点头为主，含小范围其他运动；左右成对约束','关节囊、寰枕膜等','轴由关节面校准。')
joint('atlanto_axial','寰枢关节组',[bid('vertebra_C1'),bid('vertebra_C2')],'coupled_synovial','中央与两侧关节共同约束旋转','寰椎横韧带、翼状韧带、覆膜、关节囊','寰枕和寰枢之间无椎间盘。')
spine=[f'vertebra_C{i}' for i in range(2,8)]+[f'vertebra_T{i}' for i in range(1,13)]+[f'vertebra_L{i}' for i in range(1,6)]+['sacrum']
for a,b in zip(spine,spine[1:]):joint(f'spine_{a}_{b}',f'{a.replace("vertebra_","")}—{b.replace("vertebra_","")}运动节段',[bid(a),bid(b)],'motion_segment','椎间盘与双侧关节突共同约束；屈伸、侧屈、旋转按节段耦合','椎间盘、关节突软骨/关节囊、纵韧带、黄韧带及棘间等韧带','组内各关节及韧带仍须细分；胸腰段不能共享单一轴和角度。')
joint('sacrococcygeal','骶尾连接',[bid('sacrum'),bid('coccyx')],'symphysis_or_fused_variant','按选定成人模板记录活动或融合状态','骶尾韧带、连接组织','保留变异说明。','P2')
for side in ['L','R']:
 label={'L':'左','R':'右'}[side]
 def j(k,n,keys,kind,motion,soft,notes='',priority='P1'):
  joint(k+'_'+side,label+n,[bid(k2,s2) if isinstance(k2,str) else '' for k2,s2 in keys],kind,motion,soft,notes,priority)
 j('tmj','颞下颌关节',[('temporal',side),('mandible','M')],'synovial','两侧共同控制下颌；转动加滑动','关节盘、关节囊、韧带','不能用两个独立动画同时驱动同一下颌骨。','P2')
 j('incudomalleolar','锤砧关节',[('malleus',side),('incus',side)],'synovial','微小传振；运动教学阶段可保持装配','关节囊、听小骨悬吊韧带',priority='P2')
 j('incudostapedial','砧镫关节',[('incus',side),('stapes',side)],'synovial','微小传振','关节囊',priority='P2')
 j('stapes_window','镫骨—前庭窗连接',[('stapes',side),('temporal',side)],'fibrous_connection','镫骨底板微动，非普通大关节','镫骨环韧带',priority='P2')
 for i in range(1,13):
  thor=[(f'vertebra_T{i}','M')]+([(f'vertebra_T{i-1}','M')] if i in range(2,10) else [])
  j(f'costovertebral_{i:02}',f'第{i}肋椎连接组',[(f'rib_{i:02}',side)]+thor,'rib_joint_group','呼吸时肋骨与椎体协同；肋头关节与肋横突关节分别校准','肋头及肋横突关节囊/韧带','第11/12肋无肋横突关节；第10肋关节面及肋头连接存在变异，需按源模板确认。',priority='P2')
  if i<=7:j(f'sternocostal_{i:02}',f'第{i}胸肋连接',[(f'rib_{i:02}',side),('sternum','M')],'cartilage_mediated_connection','通过肋软骨连接；呼吸不能将肋骨和胸骨焊死','肋软骨、胸肋韧带；第1连接类型与其余不同','此条包括肋软骨两端连接；软骨待单独建模。','P2')
  elif i<=10:j(f'costal_arch_{i:02}',f'第{i}肋软骨弓连接',[(f'rib_{i:02}',side),(f'rib_{i-1:02}',side)],'cartilage_mediated_connection','经软骨连接上位肋软骨，不建立肋骨间直接铰链','肋软骨及软骨间连接','骨ID描述间接关系；软骨对象会补入连接图。','P2')
 j('sternoclavicular','胸锁关节',[('sternum','M'),('clavicle',side)],'synovial','锁骨抬降、前后运动和轴向旋转；联动肩胛','关节盘、关节囊、胸锁/肋锁韧带')
 j('acromioclavicular','肩锁关节',[('clavicle',side),('scapula',side)],'synovial','肩胛与锁骨之间小幅多轴运动','肩锁/喙锁韧带、关节囊、关节盘变异')
 j('scapulothoracic','肩胛胸壁功能连接',[('scapula',side)]+[(f'rib_{i:02}',side) for i in range(2,8)],'functional_gliding','肩胛沿胸壁上/下回旋、内外旋、前后倾及位移；与胸锁/肩锁耦合','前锯肌、肩胛下肌及相关筋膜/滑动界面','功能性滑动关系，不是有共同关节腔的骨性关节；比例不预设为固定常数。')
 for k,n,keys,kind,motion,soft in [
 ('glenohumeral','盂肱关节',['scapula','humerus'],'synovial','屈伸、外展内收、内外旋；校准关节中心与伴随平移','盂唇、关节囊、盂肱/喙肱韧带、肩袖'),
 ('humeroulnar','肱尺关节',['humerus','ulna'],'synovial','以屈伸为主；检查提携角和全范围关节面接触','软骨、关节囊、尺侧/外侧副韧带复合体'),
 ('humeroradial','肱桡关节',['humerus','radius'],'synovial','随肘屈伸及前臂旋转共同运动','关节软骨、关节囊'),
 ('proximal_radioulnar','近侧桡尺关节',['radius','ulna'],'synovial','与远侧桡尺共同控制旋前旋后','桡骨环状韧带、方形韧带、关节囊'),
 ('distal_radioulnar','远侧桡尺关节',['radius','ulna'],'synovial','桡骨相对尺骨旋转和平移；不能让前臂两骨锁成一体','三角纤维软骨复合体、关节囊'),
 ('forearm_interosseous','前臂骨间连接',['radius','ulna'],'syndesmosis','与桡尺关节协调，不独立指定重复驱动','前臂骨间膜'),
 ('radiocarpal','桡腕关节组',['radius','scaphoid','lunate','triquetrum'],'synovial_group','屈伸及桡尺偏，与腕中关节分配运动','关节软骨、关节盘、桡腕及腕侧副韧带'),
 ]:
  j(k,n,[(v,side) for v in keys],kind,motion,soft)
 carpal=['scaphoid','lunate','triquetrum','pisiform','trapezium','trapezoid','capitate','hamate']
 j('intercarpal','腕骨间连接组',[(v,side) for v in carpal],'joint_group','腕中和腕骨间协同；豌豆骨与三角骨关系单列校准','腕骨间韧带、关节囊、软骨','后续逐关节面展开；不能将8块腕骨看作一个刚体。')
 for i in range(1,6):
  root={1:['trapezium'],2:['trapezium','trapezoid','capitate'],3:['capitate'],4:['capitate','hamate'],5:['hamate']}[i]
  j(f'cmc_{i}',f'第{i}腕掌连接',[(f'metacarpal_{i}',side)]+[(v,side) for v in root],'synovial_group','拇指鞍状关节需表现对掌；其余腕掌活动差异化','腕掌韧带、关节囊、软骨')
  j(f'mcp_{i}',f'第{i}掌指关节',[(f'metacarpal_{i}',side),(f'hand_phalanx_{i}_proximal',side)],'synovial','屈伸及条件性外展内收，按手指区分','掌板、侧副韧带、关节囊、伸肌腱帽')
  segs=['proximal','distal'] if i==1 else ['proximal','middle','distal']
  for a,b in zip(segs,segs[1:]):j(f'hand_ip_{i}_{a}_{b}',f'第{i}指'+({'proximal':'近节','middle':'中节','distal':'远节'}[a])+'—'+({'proximal':'近节','middle':'中节','distal':'远节'}[b])+'指间关节',[(f'hand_phalanx_{i}_{a}',side),(f'hand_phalanx_{i}_{b}',side)],'synovial','以屈伸为主；与屈伸肌腱路径耦合','掌板、侧副韧带、关节囊、腱鞘/滑车')
 j('intermetacarpal','掌骨间连接组',[(f'metacarpal_{i}',side) for i in range(2,6)],'joint_group','第2—5掌骨基底间的微动','掌骨间韧带、关节囊',priority='P2')
 j('sacroiliac','骶髂关节',[('sacrum','M'),('hip',side)],'mixed_joint_complex','小幅点头/反点头与骨盆环协调','骶髂关节软骨、骨间/前后骶髂韧带、骶结节/骶棘韧带','不能把骶髂关节做成大幅球窝运动。')
 for k,n,keys,kind,motion,soft in [
 ('hip','髋关节',['hip','femur'],'synovial','多轴运动，中心与轴由股骨头和髋臼校准','髋臼唇、软骨、关节囊、髂股/耻股/坐股韧带'),
 ('tibiofemoral','胫股关节组',['femur','tibia'],'synovial_group','屈伸伴随滚动、滑动和轴向旋转；不采用全范围固定单轴','内外侧半月板、交叉/侧副韧带、关节囊、软骨'),
 ('patellofemoral','髌股关节',['femur','patella'],'synovial','髌骨沿滑车滑动并伴倾斜/旋转，随膝角变化','软骨、髌支持带、股四头肌腱、髌韧带'),
 ('proximal_tibiofibular','近侧胫腓关节',['tibia','fibula'],'synovial','小幅滑动，与踝及膝状态协调','关节囊、胫腓头韧带'),
 ('distal_tibiofibular','远侧胫腓连接',['tibia','fibula'],'syndesmosis','踝背屈时允许与踝穴匹配的微动','胫腓前后韧带、骨间韧带与小腿骨间膜'),
 ('talocrural','距小腿关节组',['tibia','fibula','talus'],'synovial_group','背屈跖屈为主，校准踝穴和距骨滑车','软骨、关节囊、三角韧带、外侧韧带复合体'),
 ('subtalar','距下关节',['talus','calcaneus'],'synovial','斜轴耦合运动；与横跗关节共同表现足部内外翻','距跟骨间韧带、颈韧带、关节囊、软骨'),
 ('talocalcaneonavicular','距跟舟关节组',['talus','calcaneus','navicular'],'synovial_group','与距下、跟骰关节共同控制后/中足运动','足底跟舟韧带、关节囊、软骨'),
 ('calcaneocuboid','跟骰关节',['calcaneus','cuboid'],'synovial','与距舟部分共同构成横跗运动关系','长/短足底韧带、分歧韧带、关节囊'),
 ('distal_intertarsal','远侧跗骨间连接组',['navicular','cuboid','medial_cuneiform','intermediate_cuneiform','lateral_cuneiform'],'joint_group','舟楔、楔骨间及楔骰等微动；足弓不能作为僵硬三角架','跗骨间韧带、关节囊、软骨'),
 ]:j(k,n,[(v,side) for v in keys],kind,motion,soft)
 for i in range(1,6):
  root={1:['medial_cuneiform'],2:['medial_cuneiform','intermediate_cuneiform','lateral_cuneiform'],3:['lateral_cuneiform'],4:['cuboid'],5:['cuboid']}[i]
  j(f'tmt_{i}',f'第{i}跗跖连接',[(f'metatarsal_{i}',side)]+[(v,side) for v in root],'synovial_group','按足柱分配活动，保留第2跖骨基底嵌入关系','跗跖韧带、Lisfranc韧带复合体、关节囊')
  j(f'mtp_{i}',f'第{i}跖趾关节',[(f'metatarsal_{i}',side),(f'foot_phalanx_{i}_proximal',side)],'synovial','屈伸及有限外展内收；拇趾背伸关联足底腱膜绞盘效应','跖板、侧副韧带、关节囊；第1跖趾还需成对籽骨')
  segs=['proximal','distal'] if i==1 else ['proximal','middle','distal']
  for a,b in zip(segs,segs[1:]):j(f'foot_ip_{i}_{a}_{b}',f'第{i}趾'+({'proximal':'近节','middle':'中节','distal':'远节'}[a])+'—'+({'proximal':'近节','middle':'中节','distal':'远节'}[b])+'趾间关节',[(f'foot_phalanx_{i}_{a}',side),(f'foot_phalanx_{i}_{b}',side)],'synovial','以屈伸为主','跖板、侧副韧带、关节囊、肌腱')
 j('intermetatarsal','跖骨间连接组',[(f'metatarsal_{i}',side) for i in range(2,6)],'joint_group','第2—5跖骨基底间微动','跖骨间韧带、关节囊',priority='P2')
joint('pubic_symphysis','耻骨联合',[bid('hip','L'),bid('hip','R')],'symphysis','骨盆环有限运动，不做大幅独立滑动','耻骨间盘及耻骨韧带')
# Verify only existing local raw source records, without claiming full-source anatomical fit.
source_root=R.parent/'elbow-attachments'/'sources';provenance=json.loads((source_root/'provenance.json').read_text())
for b in B:
 if b['id'] in provenance['structures']:
  e=provenance['structures'][b['id']];f=source_root/e['file'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==e['sha256']
  b.update(source_structure_id=e['fma'],source_file=e['file'],source_sha256=h,source_status='local_raw_file_hash_verified_only')
# Preserve completed resource-audit evidence when regenerating the planning table.
audit_file=R/'source-audit/mapping.json'
if audit_file.exists():
 audit=json.loads(audit_file.read_text())
 for entry in audit['core']:
  b=lookup[entry['id']];b['resource_mapping_status']=entry['mapping_status']
  b['resource_audit']='source-audit/mapping.json'
  if entry.get('files'):
   b['source_structure_id']=entry['source_id'];b['source_files']=entry['files'];b['source_status']='raw_source_files_verified_geometry_and_anatomy_pending'
   if len(entry['files'])==1:b['source_file']=entry['files'][0]['filename'];b['source_sha256']=entry['files'][0]['sha256']
  else:b['source_status']=entry['mapping_status']
counts=dict(Counter(b['region'] for b in B))
assert counts=={'颅骨':22,'听小骨':6,'舌骨':1,'脊柱':26,'胸廓':25,'上肢':64,'下肢':62},counts
assert len(B)==206 and len(lookup)==206
assert len({j['id'] for j in J})==len(J)
assert all(b['joint_or_connection_ids'] for b in B)
assert all(b['side'] in ['L','R','M'] for b in B)
for b in B:
 if b['side']=='L':assert b['id'][:-1]+'R' in lookup
extras=[]
for side in ['L','R']:
 for part,zh in [('medial','内侧'),('lateral','外侧')]:extras.append(dict(id=f'bone_hallux_sesamoid_{part}_{side}',name_zh={'L':'左','R':'右'}[side]+f'第1跖趾关节{zh}籽骨',reason='前足负重、拇趾屈肌腱走行和第1跖趾运动需要；常用206清单未包含。',required_before='前足完整运动与肌腱教学验收',source_status='not_mapped',anatomy_review='pending'))
for side in ['L','R']:
 for part,zh in [('radial','桡侧'),('ulnar','尺侧')]:extras.append(dict(id=f'bone_thumb_sesamoid_{part}_{side}',name_zh={'L':'左','R':'右'}[side]+f'拇指掌指关节{zh}籽骨',reason='拇短屈肌、拇收肌附着及拇指掌指关节/屈肌腱教学需要；常用206清单未包含。',required_before='拇指完整软组织与运动教学验收',source_status='not_mapped',anatomy_review='pending'))
if audit_file.exists():
 for entry in audit['extensions']:
  item=next(x for x in extras if x['id']==entry['id']);item['source_status']=entry['status'];item['source_group_id']=entry['source_group_id'];item['resource_audit']='source-audit/mapping.json'
for item in extras:
 item['planned_connection_id']=('mtp_1_' if 'hallux' in item['id'] else 'mcp_1_')+item['id'][-1]
 assert item['planned_connection_id'] in {j['id'] for j in J}
metadata=dict(title='成人骨架与运动扩展规划',date='2026-10-12',status='planning_not_anatomically_validated',core_count=206,counts=counts,joint_connection_record_count=len(J),joint_inventory_scope='运动连接与连接组首轮登记；组内关节面、全部颅缝和各韧带/关节囊尚需进一步细分。记录数不等于人体关节数。',functional_scope=['结构交互','骨架运动','关节间隙与稳定结构','肌肉肌腱附着及形变'],excluded_scope=['真实肌力与关节受力计算'],source_set_status='partial_coverage_199_verified_remaining_items_and_joint_fit_pending' if audit_file.exists() else 'candidate_pending_full_coverage_and_registration_audit')
(R/'data/bones-206.json').write_text(json.dumps({'metadata':metadata,'bones':B},ensure_ascii=False,indent=2)+'\n')
(R/'data/joint-connections.json').write_text(json.dumps({'scope':metadata['joint_inventory_scope'],'connections':J},ensure_ascii=False,indent=2)+'\n')
(R/'data/extension-bones.json').write_text(json.dumps({'note':'核心206之外的功能性扩展，不混入206计数；不是全部人群变异骨的穷举。','planned':extras},ensure_ascii=False,indent=2)+'\n')
with (R/'data/bones-206.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['结构ID','中文名称','英文名称','侧别','部位','来源状态','源结构ID','关节或连接组','备注'])
 for b in B:w.writerow([b['id'],b['name_zh'],b['name_en'],b['side'],b['region'],b['source_status'],b['source_structure_id'] or '', ';'.join(b['joint_or_connection_ids']),b['notes']])
lines=['# 成人骨骼逐块清单 · 206块','', '这是规划清单，不表示206个模型已获取或已通过解剖核验。L=左，R=右，M=正中/非成对。每个ID对应一个可独立识别结构。','']
for region,n in counts.items():
 lines += [f'## {region} · {n}块','','| 序号 | 结构ID | 中文名称 | 备注 |','|---|---|---|---|']
 for i,b in enumerate(B,1):
  if b['region']==region:lines.append(f'| {i} | `{b["id"]}` | {b["name_zh"]} | {b["notes"]} |')
 lines.append('')
(R/'骨骼清单.md').write_text('\n'.join(lines)+'\n')
lines=['# 关节与运动连接登记','',metadata['joint_inventory_scope'],'','所有局部坐标、运动轴和活动范围均待模型与文献校准，当前不填猜测角度。','', '| ID | 连接 | 类型 | 运动要求 | 软组织依赖 | 注意事项 |','|---|---|---|---|---|---|']
for j in J:lines.append('| '+' | '.join([j['id'],j['name_zh'],j['kind'],j['motion_requirements'],j['required_soft_tissues'],j['notes']])+' |')
(R/'关节与运动清单.md').write_text('\n'.join(lines)+'\n')
(R/'data/validation.json').write_text(json.dumps(dict(metadata=metadata,checks={'206_unique_core_ids':True,'expected_regional_counts':True,'left_right_pairs':True,'all_bones_have_connection_plan':True,'all_connection_bone_references_exist':True,'existing_4_raw_source_hashes_verified':4,'core_bones_with_downloaded_source_mapping':sum(bool(b.get('source_files')) for b in B)},not_verified=['full_source_coverage','same_reference_registration','anatomical_accuracy','joint_axes_and_ranges','geometry_and_motion']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'bones':len(B),'counts':counts,'connection_records':len(J),'core_source_mappings_verified':sum(bool(b.get('source_files')) for b in B),'planned_extra_bones':len(extras)},ensure_ascii=False))
