import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
texts={k:(P/'references'/f'{k}.txt').read_text() for k in ['elbow','proximal']}
def ref(k,start,end):
 s=texts[k];i=s.index(start);j=s.index(end,i)+len(end);return {'title':'Kenhub｜'+('肘关节韧带' if k=='elbow' else '近侧桡尺关节韧带'),'url':'https://www.kenhub.com/en/library/anatomy/'+('elbow-joint' if k=='elbow' else 'proximal-radioulnar-joint'),'quote':s[i:j],'retrieved':'2026-10-13'}
D={
'Ulnar collateral ligament':{'group':'medial','context_bones':['Humerus','Ulna'],'landmark_names':['肱骨内上髁','尺骨冠突','鹰嘴','尺骨崇高结节'],'origin':'肱骨内上髁；这是肱尺连接束的概括性起侧描述。','insertion':'当前资料概括为尺骨冠突区域；不能用这一处代替后束、横束的全部附着。','shape':'三角形复合体，资料区分前、后及下方束。需分束核对。','comparison':'源数据每侧 1 个对象；尚未独立拆分各束，不能据一张连续表面认定复合体已完整。','limitations':'本条资料仅支持总体连接与分束存在。各束精确足印、后束和横束附着仍待专项补齐；不把模型端点或颜色范围作为证据。','evidence_status':'limited','references':[ref('elbow','The ulnar collateral ligament extends','an inferior band .')]},
'Radial collateral ligament':{'group':'lateral','context_bones':['Humerus','Radius','Ulna'],'landmark_names':['肱骨外上髁','桡骨头','桡切迹'],'origin':'肱骨外上髁。','insertion':'远端纤维与桡骨环状韧带融合，并与邻近旋后肌、桡侧腕短伸肌纤维相连。','shape':'外侧纤维束向环状韧带连续过渡；不应简单画成肱骨直接连到桡骨头的一条带。','comparison':'源对象存在；与环状韧带的融合边界仍待核对，不能当作整个外侧副韧带复合体。','limitations':'外侧尺副韧带（LUCL）不等同于此对象，本轮未检出独立同名源模型。','evidence_status':'reference_checked','references':[ref('elbow','The radial collateral ligament has','extensor carpi radialis brevis muscles.')]},
'Annular ligament of radius':{'group':'lateral','context_bones':['Radius','Ulna'],'landmark_names':['桡骨头','桡切迹','桡骨颈'],'origin':'尺骨桡切迹前缘。','insertion':'尺骨桡切迹后缘；主体环绕桡骨头。','shape':'与尺骨共同形成容纳桡骨头旋转的环。环绕接触不等于整圈固定附着在桡骨头。','comparison':'已有独立环状源对象，取自 connections 清单；需核对环内间隙及与桡侧副韧带的连续关系。','limitations':'几何主轴端点对环状结构没有起止意义；A/B 几何候选只能辅助观察，不用于标定附着。','evidence_status':'reference_checked','references':[ref('proximal','The annular ligament extends','radial head can rotate.')]},
'Quadrate ligament':{'group':'lateral','context_bones':['Radius','Ulna'],'landmark_names':['桡切迹','桡骨颈'],'origin':'尺骨旋后肌窝上部、桡切迹下方邻近区域。','insertion':'桡骨颈，位于桡骨粗隆近侧。','shape':'短纤维带，连接近侧桡尺骨；不能用来替代环状韧带。','comparison':'已有源对象，局部较小，需要与桡切迹及桡骨颈配合核对，不能把整个着色范围视为附着。','limitations':'概括性附着有资料支持；足印宽度与实际厚度未标定。','evidence_status':'reference_checked','references':[ref('proximal','The quadrate ligament is a short','radial tuberosity .')]}}
rows=[]
for r in json.loads((P/'source-inventory.json').read_text()):rows.append({**r,**D[re.sub(r'\.[lr]$','',r['source_structure_id'])],'anatomy_review':'pending'})
for r in rows:
 if r['id'].startswith('z_lig_radial_collateral_ligament_'):r['context_tissues']=['ligament_annular_radius_'+r['side']]
if (P/'assembly-notes.json').exists():
 notes=json.loads((P/'assembly-notes.json').read_text())
 for r in rows:r.update(notes.get(r['id'],{}))
gaps=['尺侧副韧带：前、后及横/下方束尚未独立划分，精确附着未验收。','桡侧副韧带不等同于外侧尺副韧带（LUCL）；源名称清单未检出独立 LUCL 对象。','环状韧带与桡侧副韧带的融合、关节囊及完整外侧复合体尚未共同校准。','颜色仅是沿骨面扩展的定位范围示意，不是经过文献描边的骨性边界，也不是韧带足印。','当前不提供关节动画，避免把未核准附着带入屈伸或旋前旋后。']
(P/'catalog.json').write_text(json.dumps({'scope':'elbow_ligaments','type_count':4,'source_object_count':8,'structures':rows,'gaps':gaps},ensure_ascii=False,indent=2)+'\n')
p=P.parent/'data/ligament-attachments.json';a=json.loads(p.read_text())
for k,d in D.items():a['structures'][k]={'origin':d['origin'],'insertion':d['insertion'],'course':d['shape'],'evidence_status':d['evidence_status'],'limitations':d['limitations'],'references':d['references'],'model_footprint_status':'not_anatomically_calibrated'}
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
