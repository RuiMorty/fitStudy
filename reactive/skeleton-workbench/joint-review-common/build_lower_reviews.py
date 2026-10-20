"""Build source-based hip/knee review catalogs; mesh packaging uses Blender companion."""
import json,re
from pathlib import Path
W=Path(__file__).resolve().parent.parent
allrows=[]
for f in ['ligament-library.json','connections.json','joints.json']:
 allrows+=json.loads((W/'z-anatomy-candidate'/f).read_text())['objects']
names=set(json.loads((W/'research/ossicles/z-all-object-names.json').read_text()))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
# These are regional descriptions from the linked text, not validated model footprints.
evidence={
 'iliofemoral':('髂前下棘区域（整条髂股韧带的文献概述；本源对象单束足印待核对）','股骨转子间线区域；横部、降部各自范围不能用整条描述代替。','整体呈 Y 形、分叉；源模型拆为横部和降部。','arises from the anterior inferior iliac spine and then bifurcates before inserting into the intertrochanteric line of the femur.'),
 'Pubofemoral':('耻骨上支区域。','股骨转子间线区域，与前下方关节囊融合；精确纤维终止范围待核对。','三角形，强化关节囊前下方。','spans between the superior pubic rami and the intertrochanteric line of the femur, reinforcing the capsule anteriorly and inferiorly.'),
 'Ischiofemoral':('坐骨体区域。','股骨大转子区域；具体足印及与囊融合边界待核对。','后侧螺旋走行。','spans between the body of the ischium and the greater trochanter of the femur, reinforcing the capsule posteriorly.'),
 'Ligament of head of femur':('髋臼窝区域（资料的区域概述，髋臼切迹及横韧带相关附着需进一步细分核对）。','股骨头凹。','囊内结构，不能只用一条骨到骨直线概括。','It is a relatively small structure, which runs from the acetabular fossa to the fovea of the femur.'),
 'Articular capsule of hip':('髋臼边缘。','前方至转子间线，后方至股骨颈。','包绕关节的囊状结构；不应表示成两端韧带。','The capsule of the hip joint attaches to the edge of the acetabulum proximally. Distally, it attaches to the intertrochanteric line anteriorly and the femoral neck posteriorly.'),
 'Fibular collateral':('股骨外上髁。','腓骨头外侧面凹陷。','比胫侧副韧带更细、较圆索状。','It attaches proximally to the lateral epicondyle of the femur and distally to a depression on the lateral surface of the fibular head.'),
 'Posterior cruciate':('胫骨后髁间区。','向前上方至股骨内侧髁区域；资料概述为 anteromedial femoral condyle，精确股骨足印待专门文献复核。','与前交叉韧带交叉；本页不把源模型视为已校准运动束。','attaches at the posterior intercondylar region of the tibia and ascends anteriorly to attach to the anteromedial femoral condyle.'),
 'Anterior cruciate':('胫骨前髁间区。','向后上方至股骨髁间窝区域；该概述未细分外侧髁内侧面的足印范围，仍待专门文献复核。','交叉走行；分束和足印范围待核对。','It ascends posteriorly to attach to the femur in the intercondylar fossa.'),
}
for scope,label,bones in [('hip','髋部',{'Hip bone':'Hip','Femur':'Femur'}),('knee','膝部',{'Femur':'Femur','Tibia':'Tibia','Fibula':'Fibula','Patella':'Patella'})]:
 P=W/(scope+'-review');P.mkdir(exist_ok=True)
 groups=({'capsular':'囊外韧带','intra':'囊内 / 髋臼缘','capsule':'关节囊'} if scope=='hip' else {'cruciate':'交叉韧带','collateral':'侧副韧带','posterior':'后侧稳定结构','meniscal':'半月板及连接','patellar':'髌骨支持结构','tibfib':'近侧胫腓','capsule':'膝关节囊'})
 rows=[]
 for r in allrows:
  jointids=r.get('joint_or_connection_ids',[])
  targets=['hip_R','hip_L'] if scope=='hip' else [j+'_'+s for j in ['tibiofemoral','patellofemoral','proximal_tibiofibular'] for s in ['R','L']]
  if not set(jointids).intersection(targets):continue
  name=r.get('source_structure_id','')
  if name not in names or 'Interosseous membrane' in name:continue
  if any(x['source_structure_id']==name for x in rows):continue
  rows.append(dict(r))
 extras=([('Acetabular labrum','髋臼盂唇','intra')] if scope=='hip' else [('Medial meniscus','内侧半月板','meniscal'),('Lateral meniscus','外侧半月板','meniscal'),('Medial patellar retinaculum','髌内侧支持带','patellar'),('Lateral patellar retinaculum','髌外侧支持带','patellar')])
 for en,zh,g in extras:
  for s in ['R','L']:
   name=en+'.'+s.lower()
   if name in names and not any(r['source_structure_id']==name for r in rows):rows.append({'id':'z_review_'+re.sub('[^a-z0-9]+','_',en.lower())+'_'+s,'source_structure_id':name,'name_zh':('右' if s=='R' else '左')+zh,'side':s,'group':g})
 for r in rows:
  n=r['source_structure_id'];s=r['side'];r['name_en']=n
  if scope=='hip':g='capsule' if 'capsule' in n else 'intra' if any(x in n for x in ['head of femur','acetabular','labrum']) else 'capsular'
  else:g='tibfib' if 'fibular head' in n or 'superior tibiofibular' in n else 'capsule' if 'capsule' in n else 'cruciate' if 'cruciate' in n else 'collateral' if 'collateral' in n else 'posterior' if 'poplite' in n else 'patellar' if 'retinaculum' in n else 'meniscal'
  r['group']=r.get('group',g);r['context_bones']=list(bones.values());r['landmark_names']=[];r['references']=[]
  r.update(origin='该源对象的精确附着区域尚未关联已核对文献。',insertion='待核对，不使用最近骨面或对象名称自动填充。',shape='保留 Z-Anatomy 原模型及原始配准；形状、厚度与分束待审核。',comparison='本次接入原配网格，未移动附着边界、未添加自动贴骨或平滑修形。',limitations='源模型可供比较，不代表解剖准确；足印、穿插和动态长度尚未验收。',evidence_status='missing',anatomy_review='pending',assembly_review='pending',source_dataset='Z-Anatomy',tissue_type=r.get('tissue_type','source_tissue'))
  for key,vals in evidence.items():
   if key in n:
    r['origin'],r['insertion'],r['shape'],quote=vals;r['evidence_status']='reference_checked';r['references']=[{'title':'TeachMeAnatomy · '+('The Hip Joint' if scope=='hip' else 'The Knee Joint')+'（区域概述，非模型足印验收）','url':'https://teachmeanatomy.info/lower-limb/joints/'+scope+'-joint/','quote':quote}];break
 # Meniscal connections must display their real soft-tissue context, even across groups.
 for r in rows:
  n=r['name_en'];s=r['side'];r['context_tissues']=[]
  if scope=='knee' and r['group'] in ['cruciate','collateral','posterior','meniscal','tibfib']:r['context_bones']=['Femur','Tibia','Fibula']
  if any(x in n.lower() for x in ['menisco','transverse ligament of knee','deep part of tibial']):
   r['context_tissues']=[x['id'] for x in rows if x['side']==s and x['source_structure_id'].split('.')[0] in ['Medial meniscus','Lateral meniscus']]
 gaps=['所有源模型仍待逐项核对附着足印、侧别、厚度和穿插；本版无关节运动。','骨性标志和颜色范围尚未建立；不会用骨中心或随意点位代替。','未关联文献的条目在详情中标为待补齐，不据名称编写附着。']
 if scope=='knee':gaps+=['髌韧带在源库中有 .or/.ol/.er/.el 特殊后缀网格；其对象含义尚未确认，暂未接入。髌韧带实体、半月股骨韧带及腘肌腱需后续单独确认。','后外侧复合体尚非完整装配；腘腓韧带等软组织连接的上下文仍需补齐。']
 initial=next(r['id'] for r in rows if ('Descending part' if scope=='hip' else 'Anterior cruciate') in r['name_en'] and r['side']=='R')
 save(P/'catalog.json',{'scope':scope,'structures':rows,'gaps':gaps});save(P/'source-inventory.json',rows)
 save(P/'review-config.json',{'title':label+'结构','bones':list(bones.values()),'model':scope+'-review.glb','meshCount':len(rows)+len(bones)*2,'initialId':initial,'target':[0,1,0],'camera':[0,1,.5],'storageKey':scope+'-review-v1','allowOriginal':False,'loadedLabel':'原配模型 · 待审核','boneOpacityControl':True,'minFitDistance':.26 if scope=='hip' else .22})
 save(P/'bone-map.json',bones);save(P/'landmarks.json',{'landmarks':[]});save(P/'landmark-regions.json',{'regions':[]})
 save(P/'geometry-audit.json',[{'id':r['id'],'end_candidates':[],'suspected_penetration_nearest_normal_only':{},'surface_displacement_max_mm':None,'contact_display_note':'保留源网格；本轮未进行自动贴骨或碰撞验收。','audit_scope':'not_performed'} for r in rows])
 html=(W/'wrist-review/index.html').read_text();html=html.replace('腕部韧带',label+'结构').replace('右腕','右'+label[0]).replace('左腕','左'+label[0]).replace('腕部模型',label+'模型').replace('腕部三维',label+'三维').replace('31 类 · 61 个现有对象',str(len(rows)//2)+' 类 · '+str(len(rows))+' 个现有对象')
 html=re.sub(r'<select id="group">.*?</select>','<select id="group"><option value="all">全部结构</option>'+''.join('<option value="'+k+'">'+v+'</option>' for k,v in groups.items())+'</select>',html)
 html=html.replace('右头状钩骨间韧带已局部修整 · 精确附着仍待核准','Z-Anatomy 原配模型 · 附着与穿插待审核').replace('选择韧带','选择结构').replace('点击韧带','点击结构').replace('单条 + 连接结构','单项 + 连接结构').replace('选中韧带显示','选中结构显示')
 html=html.replace('<a href="../elbow-review/">← 肘部审核</a>','<a href="../hip-review/">髋部审核</a><a href="../knee-review/">膝部审核</a>')
 # Do not offer empty landmark controls as if annotations existed.
 html=html.replace('<label><input id="bone-landmarks"','<div hidden><label><input id="bone-landmarks"').replace('<label style="display:none"><input id="markers"','</div><p class="muted">骨性标志范围待补齐；目前可点击骨骼识别名称。</p><label style="display:none"><input id="markers"')
 (P/'index.html').write_text(html);(P/'app.js').write_text("import '../joint-review-common/app.js?v=lower-review1';\n");(P/'style.css').write_text("@import '../shoulder-review/style.css?v=bone-pick1';\n")
 (P/'README.md').write_text('# '+label+'审核候选\n\n从父目录本机 HTTP 服务打开 '+scope+'-review/。保留 Z-Anatomy 同源原配坐标；.blend 含源对象场景及网页网格场景。\n\n'+ '\n'.join('- '+g for g in gaps)+'\n\n公开参考： https://teachmeanatomy.info/lower-limb/joints/'+scope+'-joint/ （2026-10-13 读取；只支持标明的区域概述。）\n\n复建：先运行 joint-review-common/build_lower_reviews.py，再用 Blender 执行 package_lower_reviews.py。\n')
 print(scope,len(rows),'tissues',len(rows)+2*len(bones),'total')
