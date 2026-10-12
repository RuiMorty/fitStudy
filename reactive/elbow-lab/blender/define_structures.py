"""Anatomical manifest. Run before geometry generation; no external assets."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
refs=[{'id':'TMA-ARM','title':'TeachMeAnatomy — Muscles of the Upper Arm','url':'https://teachmeanatomy.info/upper-limb/muscles/upper-arm/','checked':'2026-10-10','verified':['肱二头肌两头起点、桡骨粗隆及腱膜止点','肱肌在二头肌深层，肱骨干起、尺骨粗隆止','三头肌三头起点、鹰嘴共同止点、内侧头深层']}, {'id':'TMA-ELBOW','title':'TeachMeAnatomy — The Elbow Joint','url':'https://teachmeanatomy.info/upper-limb/joints/elbow-joint/','checked':'2026-10-10','verified':['肱尺、肱桡关节的骨性配对','肘关节铰链式屈伸；旋前旋后属于不同自由度']}]
refs.append({'id': 'KH-BRACHIALIS', 'title': 'Kenhub — Brachialis muscle', 'url': 'https://www.kenhub.com/en/library/anatomy/brachialis-muscle', 'checked': '2026-10-10', 'verified': ['肱骨前面远侧半起点', '尺骨粗隆与冠突止点文字；具体附着分区几何未审核']})
items=[]
def add(id,name,en,kind,layer,group,bones,origin,insertion,offset,refs_,note,**kwargs):
 items.append(dict(id=id,name=name,english=en,type=kind,layer=layer,parent=group,side='right',bones=bones,origin=origin,insertion=insertion,explode=offset,references=refs_,geometryStatus='schematic',reviewStatus='pending-anatomist',note=note,**kwargs))
for id,name,en,binding,offset,description in [
 ('bone_scapula_R','肩胛骨','Scapula','upper',[-.075,0,.025],'肩胛体、肩胛冈、肩峰、喙突、盂上与盂下区域的程序化示意；无扫描数据。'),
 ('bone_humerus_R','肱骨','Humerus','upper',[0,0,0],'肱骨头、骨干、滑车与小头轮廓示意；双髁中心定义近似屈伸轴。'),
 ('bone_ulna_R','尺骨','Ulna','forearm',[-.042,0,-.012],'鹰嘴、滑车切迹、尺骨粗隆与尺骨干示意；尺骨远端不含腕关节。'),
 ('bone_radius_R','桡骨','Radius','forearm',[.045,0,-.012],'桡骨头、桡骨颈、桡骨粗隆与桡骨干示意；固定旋后位。')]:
 add(id,name,en,'bone','skeleton','skeleton.'+binding,[id],'不适用','不适用',offset,['TMA-ELBOW'],description,binding=binding,anatomyStatus='骨名与关节配对已核对；骨面几何未审核')
common_b='桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜'
common_t='尺骨鹰嘴（经共同肱三头肌腱）'
specs=[
 ('biceps_long','肱二头肌·长头','Biceps brachii · long head','superficial','flexor',['bone_scapula_R','bone_radius_R'],'肩胛骨盂上结节',common_b,[.037,.095,.025],[-.024,.004,.319],[.016,.013,-.043],.0125),
 ('biceps_short','肱二头肌·短头','Biceps brachii · short head','superficial','flexor',['bone_scapula_R','bone_radius_R'],'肩胛骨喙突',common_b,[-.040,.095,.025],[-.040,.032,.298],[.016,.013,-.043],.0135),
 ('brachialis','肱肌','Brachialis','deep','flexor',['bone_humerus_R','bone_ulna_R'],'肱骨干前面远侧区域（起点广面压缩为标记点）','尺骨粗隆；冠突附着细分待审核',[0,.060,-.006],[0,.017,.157],[-.013,.013,-.030],.022),
 ('triceps_long','肱三头肌·长头','Triceps brachii · long head','superficial','extensor',['bone_scapula_R','bone_ulna_R'],'肩胛骨盂下结节',common_t,[-.055,-.075,.025],[-.034,-.004,.267],[-.012,-.023,.014],.015),
 ('triceps_lateral','肱三头肌·外侧头','Triceps brachii · lateral head','superficial','extensor',['bone_humerus_R','bone_ulna_R'],'肱骨后面，桡神经沟上方',common_t,[.055,-.075,.025],[.015,-.013,.248],[-.012,-.023,.014],.016),
 ('triceps_medial','肱三头肌·内侧头','Triceps brachii · medial head','deep','extensor',['bone_humerus_R','bone_ulna_R'],'肱骨后面，桡神经沟下方',common_t,[0,-.060,-.005],[-.002,-.015,.155],[-.012,-.023,.014],.015)
]
for key,name,en,layer,action,bones,origin,insertion,off,o,i,r in specs:
 add('muscle_'+key+'_R',name,en,'muscle',layer,'muscles.'+action,bones,origin,insertion,off,['TMA-ARM'],'肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。',key=key,action=action,originPoint=o,insertionPoint=i,radius=r,anatomyStatus='起止点文字与浅深层关系已核对；坐标、面积、肌束走向待审核')
tendons=[
 ('biceps_long_prox','肱二头肌长头·近端腱','Biceps long head proximal tendon','superficial','flexor',['bone_scapula_R'],'肩胛骨盂上结节','长头肌腹近端',[.037,.095,.025],'长头肌腱越过肱骨头前上方并进入结节间沟的路径仅为示意，关节囊内部分未分段。'),
 ('biceps_short_prox','肱二头肌短头·近端腱','Biceps short head proximal tendon','superficial','flexor',['bone_scapula_R'],'肩胛骨喙突','短头肌腹近端',[-.040,.095,.025],'喙突共同腱未纳入喙肱肌。'),
 ('biceps_distal','肱二头肌·共同远端腱','Distal biceps tendon','superficial','flexor',['bone_radius_R'],'长头与短头肌腹汇合处','桡骨粗隆',[0,.095,.025],'简化为共同腱；未表示扭转、双头足印差异及肱二头肌腱膜。'),
 ('brachialis_distal','肱肌·远端腱','Brachialis distal tendon','deep','flexor',['bone_ulna_R'],'肱肌肌腹远端','尺骨粗隆',[0,.060,-.006],'附着面积、冠突分支及腱膜结构待审核。'),
 ('triceps_long_prox','肱三头肌长头·近端腱','Triceps long head proximal tendon','superficial','extensor',['bone_scapula_R'],'肩胛骨盂下结节','三头肌长头肌腹近端',[-.055,-.075,.025],'起点宽度与腱膜简化。'),
 ('triceps_distal','肱三头肌·共同远端腱','Distal triceps tendon','superficial','extensor',['bone_ulna_R'],'肱三头肌三头汇合处','尺骨鹰嘴',[0,-.075,.025],'三层腱膜与内侧头独立深部插入细节未区分；绕鹰嘴的滑移为路径示意。')]
for key,name,en,layer,action,bones,o,i,off,note in tendons:
 add('tendon_'+key+'_R',name,en,'tendon',layer,'tendons.'+action,bones,o,i,off,['TMA-ARM'],note,key=key,action=action,anatomyStatus='连接关系已核对；腱形、截面和滑移未审核')
add('fascia_brachial_R','臂筋膜·示意层','Brachial fascia · schematic shell','fascia','fascia','fascia',['bone_humerus_R'],'连续筋膜，不以肌肉起止点描述','本样板覆盖上臂；不含肌间隔与前臂筋膜',[.105,0,.025],['TMA-ARM'],'单层半透明外包络，仅用于交互验证；不是按组织厚度或真实筋膜平面重建。',anatomyStatus='完全示意，未作解剖准确声明')
data={'schemaVersion':1,'title':'ELBOW / 01','side':'right','units':'metres','coordinates':{'blender':'+X 外侧 / +Y 前方 / +Z 近端；肘轴中心原点','gltf':'+X 外侧 / +Y 近端 / -Z 前方（标准 Y-up）','conversion':'[x, y, z] Blender → [x, z, -y] glTF'},'joint':{'id':'joint_elbow_R','axisBlender':[1,0,0],'pivotBlender':[0,0,0],'rangeDegrees':[0,120],'assumptions':'固定肩部、旋后位；简化为单轴铰链，不模拟携带角、瞬时轴迁移和旋前旋后。'},'references':refs,'structures':items,'counts':{'bones':4,'muscleHeads':6,'tendons':6,'fascia':1,'totalSelectable':17},'animation':{'angles':list(range(0,121,5)),'fps':30,'durationSeconds':4,'method':'Rigid forearm rotation + sampled path-driven shape keys. Geometry visualization only.'}}
for item in items:
 if item['id'] in ['muscle_brachialis_R','tendon_brachialis_distal_R']:item['references'].append('KH-BRACHIALIS')
(ROOT/'data/structures.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
lines=['# 结构清单与精度边界','', '建模前清单；右侧，4 骨 + 6 肌头 + 6 腱 + 1 筋膜 = 17 个可选对象。左右侧、肌头和肌腱分别计数。所有网格均为原创程序化示意几何，无外部人体模型。','', '仅下列资料核对过的名称、骨性连接、肌肉起止点文字及浅深层关系可称为「已核对」。没有任何骨面或肌肉表面被标为解剖准确。坐标是设计值，并非测量值。','', '| ID / 名称 | 层级 / 所属骨 | 起点 → 止点 | 依据 / 建模边界 |','|---|---|---|---|']
for s in items: lines.append(f"| `{s['id']}`<br>{s['name']} / {s['english']} | {s['parent']} / {s['layer']}<br>{', '.join(s['bones'])} | {s['origin']} → {s['insertion']} | {', '.join(s['references'])}<br>{s['note']} |")
lines+=['','## 坐标与运动约束','',data['coordinates']['blender'],data['coordinates']['gltf'],'','肱骨长度约 0.32 m，前臂约 0.26 m；是统一单位的成人比例示意，未作个体测量。肘关节轴通过近似滑车/小头中心。肩胛骨与肱骨固定；尺桡骨作为同一前臂运动组绕 X 轴屈伸。','', '每块肌肉保留 `origin__<id>`、`insertion__<id>` 空对象。插入标记跟随前臂旋转。肌腹通过近端腱/共同远端腱与骨性标记保持连通；不把肌腹端点误当骨性起止点。','', '## 参考资料（2026-10-10 实际读取）','']
for r in refs: lines+= [f"- [{r['id']} — {r['title']}]({r['url']})：{'；'.join(r['verified'])}。"]
lines+=['','资料只作为事实核对依据，不复制网页插图、网格或整篇正文。模型几何需要后续解剖专业审核；未表示的结构包括关节软骨、韧带、关节囊、神经、血管、喙肱肌、肘肌及旋后肌。']
(ROOT/'docs/STRUCTURES.md').write_text('\n'.join(lines)+'\n')
print('Manifest written:',len(items),'selectable structures')
