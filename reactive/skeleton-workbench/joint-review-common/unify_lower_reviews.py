"""Apply shared review UI and landmark associations without replacing source evidence."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent.parent
terms={'iliofemoral':['髂前下棘','转子间线'],'Pubofemoral':['耻骨上支','转子间线'],'Ischiofemoral':['坐骨体','大转子'],'head of femur':['髋臼切迹','髋臼窝','股骨头凹'],'Transverse acetabular':['髋臼切迹'],'Acetabular labrum':['髋臼缘'],'capsule of hip':['髋臼缘','转子间线'],'Anterior cruciate':['胫骨前髁间区','股骨髁间窝'],'Posterior cruciate':['胫骨后髁间区','股骨髁间窝'],'tibial collateral':['股骨内上髁','胫骨内侧髁'],'Fibular collateral':['股骨外上髁','腓骨头'],'fibular head':['腓骨头','胫骨外侧髁'],'poplite':['股骨外上髁','腓骨头'],'meniscotibial':['胫骨前髁间区','胫骨后髁间区'],'Medial meniscus':['胫骨内侧髁'],'Lateral meniscus':['胫骨外侧髁'],'Transverse ligament of knee':['胫骨前髁间区']}
for scope in ['hip','knee']:
 P=W/(scope+'-review');cat=json.loads((P/'catalog.json').read_text())
 for r in cat['structures']:
  r['landmark_names']=list(dict.fromkeys(v for key,values in terms.items() if key.lower() in r['name_en'].lower() for v in values))
  if 'Posterior meniscotibial' in r['name_en']:r['landmark_names']=['胫骨后髁间区']
  if 'Anterior meniscotibial' in r['name_en']:r['landmark_names']=['胫骨前髁间区']
  r['limitations']=r['limitations'].replace(' 骨性标志及柔边色块只帮助定位，不是完整韧带附着区。','')+' 骨性标志及柔边色块只帮助定位，不是完整韧带附着区。'
 cat['gaps']=[g for g in cat['gaps'] if '骨性标志和颜色范围尚未建立' not in g]
 cat['gaps'].append('已接入原生骨性标志与颜色定位范围；未收录的标志不会自动用邻近点代替。精确足印仍需逐项核准。')
 (P/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
 html=(P/'index.html').read_text().replace('<div hidden><label><input id="bone-landmarks"','<label><input id="bone-landmarks"').replace('</div><p class="muted">骨性标志范围待补齐；目前可点击骨骼识别名称。</p>','')
 html=html.replace('Z-Anatomy 原配模型 · 附着与穿插待审核','Z-Anatomy 派生模型 · 骨面色块为定位范围，非精确足印')
 (P/'index.html').write_text(html)
 # Keep the unification reproducible after rebuilding the base catalog.
 (P/'README.md').write_text((P/'README.md').read_text()+'\n审查统一：运行 build_lower_landmarks.py 和 REVIEW_SCOPES=hip,knee 的 build_regions.py，最后运行 unify_lower_reviews.py。原生定位标志并不代表完整足印。\n')
