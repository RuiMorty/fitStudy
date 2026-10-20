"""Explicit source-name translations and regional inventory, not attachment calibration."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parents[2]/'skeleton-workbench';O=W/'z-anatomy-candidate'
source=json.loads((P/'all-source-objects.json').read_text())['objects'];connections=json.loads((W/'data/connections.json').read_text())['connections'];bones=json.loads((O/'structures.json').read_text())['bones']
translations='''Ulnotriquetral ligament|尺三角韧带
Ulnopisiform ligament|尺豌豆韧带
Ulnolunate ligament|尺月韧带
Ulnocapitate ligament|尺头状韧带
Ulnar collateral ligament|肘尺侧副韧带
Ulnar collateral ligament of wrist joint|腕尺侧副韧带
Triquetrohamate ligament|三角钩骨韧带
Triquetrocapitate ligament|三角头状骨韧带
Trapezoideocapitate interosseous ligament|小多角头状骨间韧带
Trapezoid ligament|斜方韧带
Trapeziotrapezoidal interosseous ligament|大小多角骨间韧带
Transverse tibiofibular ligament|胫腓横韧带
Transverse part of iliofemoral ligament|髂股韧带横部
Transverse ligament of knee|膝横韧带
Transverse humeral ligament|肱骨横韧带
Transverse acetabular ligament|髋臼横韧带
Tibionavicular ligament|胫舟韧带
Tibiocalcaneal ligament|胫跟韧带
Talonavicular ligament|距舟韧带
Talocalcaneal interosseous ligament|距跟骨间韧带
Supraspinous ligament|棘上韧带
Superior transverse scapular ligament|肩胛上横韧带
Superior pubic ligament|耻骨上韧带
Superior glenohumeral ligament|盂肱上韧带
Stylomandibular ligament|茎突下颌韧带
Stylohyoid ligament|茎突舌骨韧带
Scapholunate interosseous ligament|舟月骨间韧带
Radiocapitate ligament|桡头状骨韧带
Radiate ligament of head of rib|肋头辐状韧带组
Posterior tibiotalar ligament|胫距后韧带
Posterior meniscotibial ligament (Medial meniscus)|内侧半月板胫骨后韧带
Posterior meniscotibial ligament (Lateral meniscus)|外侧半月板胫骨后韧带
Plantar cuboideonavicular ligament|足底骰舟韧带
Plantar calcaneonavicular ligament|足底跟舟韧带
Sphenomandibular ligament|蝶下颌韧带
Scaphotrapeziotrapezoidal ligament|舟大小多角骨韧带
Scaphocapitate ligament|舟头状骨韧带
Sacrotuberous ligament|骶结节韧带
Sacrospinous ligament|骶棘韧带
Radioscaphocapitate ligament|桡舟头状骨韧带
Radiate carpal ligament|腕辐状韧带
Radial collateral ligament|肘桡侧副韧带
Radial collateral ligament of wrist joint|腕桡侧副韧带
Quadrate ligament|方形韧带
Pubofemoral ligament|耻股韧带
Pterygospinous ligament|翼棘韧带
Posterior tibiofibular ligament|胫腓后韧带
Posterior talofibular ligament|距腓后韧带
Posterior talocalcaneal ligament|距跟后韧带
Posterior sternoclavicular ligament|胸锁后韧带
Posterior sacro-iliac ligament|骶髂后韧带
Posterior longitudinal ligament|后纵韧带
Posterior ligament of fibular head|腓骨头后韧带
Posterior cruciate ligament|后交叉韧带
Popliteofibular ligament|腘腓韧带
Plantar tarsometatarsal ligaments|跗跖足底韧带组
Plantar metatarsophalangeal ligaments|跖趾足底韧带组
Plantar metatarsal ligaments|跖骨足底韧带组
Plantar interphalangeal ligaments|趾间足底韧带组
Plantar intercuneiform ligaments|楔骨间足底韧带组
Plantar cuneonavicular ligaments|楔舟足底韧带组
Plantar cuneocuboid ligament|楔骰足底韧带
Plantar calcaneocuboid ligament|跟骰足底韧带
Pisotriquetral ligament|豌豆三角骨韧带
Pisometacarpal ligament|豌豆掌骨韧带
Pisohamate ligament|豌豆钩骨韧带
Palmar trapezoideocapitate ligament|掌侧小多角头状骨韧带
Palmar scaphotriquetral ligament|掌侧舟三角骨韧带
Palmar radio-ulnar ligament|掌侧桡尺韧带
Palmar metacarpal ligaments|掌骨掌侧韧带组
Palmar lunotriquetral ligament|掌侧月三角骨韧带
Palmar interphalangeal ligaments|指间掌侧韧带组
Palmar carpometacarpal ligaments|腕掌掌侧韧带组
Palmar capitohamate ligament|掌侧头状钩骨韧带
Oblique popliteal ligament|腘斜韧带
Nuchal ligament|项韧带
Middle glenohumeral ligament|盂肱中韧带
Metatarsal interosseous ligaments|跖骨间韧带组
Meniscopatellar ligament|半月板髌骨韧带
Medial talocalcaneal ligament|距跟内侧韧带
Lunotriquetral interosseous ligament|月三角骨间韧带
Long plantar ligament|足底长韧带
Ligamenta flava|黄韧带组
Ligament of head of femur|股骨头韧带
Lateral temporomandibular ligament|颞下颌外侧韧带
Lateral talocalcaneal ligament|距跟外侧韧带
Ischiofemoral ligament|坐股韧带
Intra-articular ligament of head of rib|肋头关节内韧带组
Interspinous ligaments|棘间韧带组
Intersesamoid ligament|籽骨间韧带
Interosseous sacro-iliac ligament|骶髂骨间韧带
Interosseous metacarpal ligaments|掌骨间韧带组
Interosseous membrane of leg|小腿骨间膜
Intercuneiform interosseous ligaments|楔骨间韧带组
Intercornual ligament|骶尾角间韧带
Interclavicular ligament|锁骨间韧带
Inferior transverse scapular ligament|肩胛下横韧带
Inferior pubic ligament|耻骨下韧带
Inferior glenohumeral ligament|盂肱下韧带
Iliolumbar ligament|髂腰韧带
Fibular collateral ligament|腓侧副韧带
Dorsal ulnocarpal ligament|背侧尺腕韧带
Dorsal tarsometatarsal ligaments|跗跖背侧韧带组
Dorsal scaphotriquetral ligament|背侧舟三角骨韧带
Dorsal radiocarpal ligament|背侧桡腕韧带
Dorsal radio-ulnar ligament|背侧桡尺韧带
Dorsal metatarsal ligaments|跖骨背侧韧带组
Dorsal metacarpal ligaments|掌骨背侧韧带组
Dorsal intercuneiform ligaments|楔骨间背侧韧带组
Dorsal intercarpal ligaments|腕骨间背侧韧带组
Dorsal cuneonavicular ligaments|楔舟背侧韧带组
Dorsal cuneocuboid ligament|楔骰背侧韧带
Dorsal cuboideonavicular ligament|骰舟背侧韧带
Dorsal carpometacarpal ligaments|腕掌背侧韧带组
Dorsal calcaneocuboid ligament|跟骰背侧韧带
Descending part of iliofemoral ligament|髂股韧带降部
Deep transverse metatarsal ligament|跖骨深横韧带
Deep transverse metacarpal ligament|掌骨深横韧带
Deep part of tibial collateral ligament|胫侧副韧带深部
Superficial part of tibial collateral ligament|胫侧副韧带浅部
Cuneometatarsal interosseous ligaments|楔跖骨间韧带组
Cuneocuboid interosseous ligament|楔骰骨间韧带
Costotransverse ligament|肋横突韧带组
Costoclavicular ligament|肋锁韧带
Coracohumeral ligament|喙肱韧带
Coraco-acromial ligament|喙肩韧带
Conoid ligament|锥状韧带
Collateral metatarsophalangeal ligaments|跖趾侧副韧带组
Collateral metacarpophalangeal ligaments|掌指侧副韧带组
Collateral interphalangeal ligaments of hand|指间侧副韧带组
Collateral interphalangeal ligaments of foot|趾间侧副韧带组
Capitohamate interosseous ligament|头状钩骨间韧带
Calcaneonavicular ligament|跟舟韧带
Calcaneofibular ligament|跟腓韧带
Calcaneocuboid ligament|跟骰韧带
Arcuate popliteal ligament|腘弓状韧带
Anterior tibiofibular ligament|胫腓前韧带
Anterior talofibular ligament|距腓前韧带
Anterior talocalcaneal ligament|距跟前韧带
Anterior sternoclavicular ligament|胸锁前韧带
Anterior sacro-iliac ligament|骶髂前韧带
Anterior meniscotibial ligament (Medial meniscus)|内侧半月板胫骨前韧带
Anterior meniscotibial ligament (Lateral meniscus)|外侧半月板胫骨前韧带
Anterior longitudinal ligament|前纵韧带
Anterior ligament of fibular head|腓骨头前韧带
Anterior cruciate ligament|前交叉韧带
Acromioclavicular ligament|肩锁韧带'''
zh=dict(line.split('|') for line in translations.splitlines())
# Parent collections determine regional catalog association, not exact bone footprints.
parent_rules={
 'Radiocarpal joint.g':['radiocarpal','intercarpal','distal_radioulnar'], 'Intercarpal joints.g':['intercarpal','radiocarpal'], 'Elbow joint.g':['humeroulnar','humeroradial','proximal_radioulnar'], 'Acromioclavicular joint.g':['acromioclavicular'], 'Tibiofibular syndesmosis.g':['distal_tibiofibular'], 'Hip joint.g':['hip'], 'Knee joint.g':['tibiofemoral','patellofemoral','proximal_tibiofibular'], 'Glenohumeral joint.g':['glenohumeral'], 'Medial collateral ligament of ankle.g':['talocrural','talocalcaneonavicular'], 'Lateral collateral ligament of ankle.g':['talocrural','subtalar'], 'Intertarsal joints.g':['subtalar','talocalcaneonavicular','calcaneocuboid','distal_intertarsal'], 'Fibrous joints of vertebral column.g':['spine_','atlanto_','sacrococcygeal'], 'Fibrous joints of pectoral girdle.g':['glenohumeral','acromioclavicular'], 'Pubic symphysis':['pubic_symphysis'], 'Cranial syndesmoses.g':['tmj','hyoid_suspension'], 'Joint of head of rib.g':['costovertebral_'], 'Costotransverse joint.g':['costovertebral_'], 'Fibrous joints of pelvic girdle.g':['sacroiliac','spine_vertebra_L5_sacrum'], 'Sacro-iliac joint.g':['sacroiliac'], 'Sternoclavicular joint.g':['sternoclavicular'], 'Superior tibiofibular joint.g':['proximal_tibiofibular'], 'Tarsometatarsal joints.g':['tmt_'], 'Metatarsophalangeal joints.g':['mtp_'], 'Intermetatarsal joints.g':['intermetatarsal','mtp_1'], 'Interphalangeal joints of foot.g':['foot_ip_'], 'Intermetacarpal joints.g':['intermetacarpal'], 'Interphalangeal joints of hand.g':['hand_ip_'], 'Carpometacarpal joints.g':['cmc_'], 'Distal radio-ulnar joint.g':['distal_radioulnar'], 'Fibrous joints of free lower limb.g':['proximal_tibiofibular','distal_tibiofibular'], 'Temporomandibular joint.g':['tmj'], 'Metacarpophalangeal joints.g':['mcp_']}
existing={x['source_structure_id'] for file in ['joints','connections'] for x in json.loads((O/(file+'.json')).read_text())['objects']}
rows=[];excluded=[]
for o in source:
 name=o['name']
 if o['type']!='MESH' or not o.get('faces') or not ('ligament' in name.lower() or 'Interosseous membrane of leg' in name):continue
 if name in existing:continue
 if re.search(r'\.(?:o|e)\d*[rl]$',name):excluded.append({'source_object':name,'reason':'attachment_patch_not_ligament_body'});continue
 base=re.sub(r'\.[rl]$','',name);side=name[-1].upper() if re.search(r'\.[rl]$',name) else 'M'
 if base not in zh:excluded.append({'source_object':name,'reason':'outside_joint_layer_or_unresolved_semantics'});continue
 parent=o['parent']
 if parent.startswith('Dorsal intercarpal ligaments'):parent='Intercarpal joints.g'
 prefixes=parent_rules.get(parent)
 if not prefixes:excluded.append({'source_object':name,'reason':'unmapped_source_parent'});continue
 cs=[c for c in connections if any(c['id'].startswith(pre) for pre in prefixes) and (side=='M' or not c['id'].endswith(('_L','_R')) or c['id'].endswith('_'+side))];bs=sorted({b for c in cs for b in c['bone_ids']})
 if not bs:excluded.append({'source_object':name,'reason':'no_regional_bone_mapping'});continue
 region=next(b['region'] for b in bones if b['id']==bs[0])
 if any(b['id'] in bs and b['region']=='上肢' for b in bones):region='上肢'
 elif any(b['id'] in bs and b['region']=='下肢' for b in bones):region='下肢'
 rows.append({'id':'z_lig_'+re.sub('[^a-z0-9]+','_',base.lower()).strip('_')+'_'+side,'name_zh':('左' if side=='L' else '右' if side=='R' else '')+zh[base],'source_object':name,'source_parent':o['parent'],'side':side,'region':region,'layer':'ligament','bone_ids':bs,'connection_ids':[c['id'] for c in cs],'granularity':'source_object_not_segmented','association_kind':'source_parent_regional_catalog_not_attachment','note':'沿用原配坐标；依据源父级归入区域目录，关联骨不是精确起止点。附着范围、局部穿插及源组合对象的拆分尚待审核。'})
for row in rows:
 # Source side suffixes are reversed relative to the temporal bones. Keep stable
 # mesh IDs/source names for provenance; anatomical side lives in the side field.
 if row['source_object'] in ('Lateral temporomandibular ligament.r','Lateral temporomandibular ligament.l'):
  side='L' if row['source_object'].endswith('.r') else 'R'
  row['side']=side;row['name_zh']=('左' if side=='L' else '右')+'颞下颌外侧韧带'
  row['bone_ids']=['bone_mandible_M','bone_temporal_'+side];row['connection_ids']=['tmj_'+side]
  row['note']='已按颞骨同侧位置纠正源左右标记；源名称及网格 ID 保留用于追溯，不代表解剖侧别。模型位置未改变，附着范围和分束待审核。'
 if row['source_object']=='Ulnopisiform ligament':
  row['side']='unknown';row['name_zh']+='（源未标侧）';row['note']='源名称缺少左右标记，暂不纳入左右局部预设。'+row['note']
(P/'ligament-library-mapping.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(P/'ligament-library-exclusions.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2)+'\n');print('MAPPED',len(rows),'EXCLUDED',len(excluded));print(json.dumps(excluded,ensure_ascii=False))
