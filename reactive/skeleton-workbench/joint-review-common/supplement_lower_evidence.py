"""Only add statements supported by stored, inspected reference excerpts."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent.parent
for scope in ['hip','knee']:
 P=W/(scope+'-review');cat=json.loads((P/'catalog.json').read_text());src=(P/'references/teachmeanatomy-excerpt.txt').read_text()
 for r in cat['structures']:
  n=r['name_en'];quote=None
  if 'Acetabular labrum' in n:
   quote='There is a horseshoe shaped fibrocartilaginous ring around the acetabulum which increases its depth, known as the'
   r.update(origin='沿髋臼周缘分布的纤维软骨环；不是具有两端起止的韧带。',insertion='与髋臼横韧带的连续关系及具体结合边界，仍待专门资料核对。',shape='马蹄形纤维软骨环，加深髋臼。')
  elif n.split('.')[0] in ['Medial meniscus','Lateral meniscus']:
   quote='They are attached at both ends to the intercondylar area of the tibia.'
   r.update(origin='前端附着于胫骨髁间区；该资料仅给区域概述，未提供各根部精确范围。',insertion='后端同样附着于胫骨髁间区；不是附着股骨。各根部相对交叉韧带的位置待核对。',shape='纤维软骨性半月板；内、外侧的轮廓及活动度不同，不把本页概述当精确形态模板。')
  if quote:
   assert quote in ' '.join(src.split()),quote
   r['references']=[{'title':'TeachMeAnatomy · '+('The Hip Joint' if scope=='hip' else 'The Knee Joint')+'（区域概述）','url':'https://teachmeanatomy.info/lower-limb/joints/'+scope+'-joint/','quote':quote}];r['evidence_status']='reference_checked'
 (P/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
 lines=['# '+('髋' if scope=='hip' else '膝')+'部逐项审查清单','', '同侧原配模型；文献概述、骨性标志定位、精确足印、形态与碰撞是不同的核对项。所有精确足印仍待审核。','', '| 对象 | 文献 | 相关标志 | 精确足印 / 形态 |','|---|---|---|---|']
 for r in cat['structures']:
  if r['side']!='R':continue
  lines.append('| '+r['name_zh']+' | '+('已关联区域概述' if r['references'] else '待补专门文献')+' | '+('、'.join(r['landmark_names']) or '未收录对应标志')+' | 待核对 |')
 lines+=['','几何初筛为最近表面法线抽样；并非可靠的实体穿透判定，特别是骨端附着与关节内部结构。不能将初筛数字当作修形目标。','', '显示版仅对可用开放韧带表面进行边界锁定的轻度修整；不自动延伸附着，不替换缺失解剖结构。']
 (P/'AUDIT-CHECKLIST.md').write_text('\n'.join(lines)+'\n')
