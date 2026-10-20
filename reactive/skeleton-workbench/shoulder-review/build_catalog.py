import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
refs={k:re.sub(r'\s+',' ',(P/'references'/f'{k}.txt').read_text()) for k in ['shoulder','cc','ca','stsl','itsl','ac','coracoid-review']}
urls={'shoulder':'https://www.kenhub.com/en/library/anatomy/the-shoulder-joint','cc':'https://www.kenhub.com/en/library/anatomy/coracoclavicular-ligament','ca':'https://www.kenhub.com/en/library/anatomy/coracoacromial-ligament','stsl':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12049851/','itsl':'https://pmc.ncbi.nlm.nih.gov/articles/PMC8802659/','ac':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12415468/','coracoid-review':'https://doi.org/10.1055/s-0041-1741091'}
def quote(k,start,end=None):
 s=refs[k];i=s.lower().index(start.lower());j=s.find(end,i)+len(end) if end else s.find('. ',i)+1;q=s[i:j];assert q and q in s;return {'title':{'shoulder':'Kenhub｜盂肱关节 · 韧带','cc':'Kenhub｜喙锁韧带','ca':'Kenhub｜喙肩韧带','stsl':'Paraskevas 等，2025｜肩胛切迹与上横韧带','itsl':'2022｜肩胛上神经与盂切迹韧带','ac':'2025｜肩锁韧带与后方稳定性','coracoid-review':'Desai 等，2022｜喙突与肩部韧带'}[k],'url':urls[k],'quote':q,'retrieved':'2026-10-13'}
D={}
def add(name,group,bones,a,b,shape,comparison,reference,limit='',status='reference_checked'):
 D[name]={'group':group,'context_bones':bones,'origin':a,'insertion':b,'shape':shape,'comparison':comparison,'references':reference,'limitations':limit or '资料用于核对连接关系和形态类型，不能证明当前网格的精确足印、厚度或运动性能。','evidence_status':status,'anatomy_review':'pending'}
add('Superior glenohumeral ligament','capsule',['Scapula','Humerus'],'本次参考资料描述为肩胛骨盂上结节；与上盂唇的具体附着关系仍需补充核查。','肱骨小结节近端、解剖颈邻近区域。','上方囊韧带，与喙肱韧带共同参与肩袖间隙的稳定。','源数据为独立带状对象；与盂唇、关节囊及肱二头肌腱的关系未一并重建。',[quote('shoulder','The superior glenohumeral ligament extends', 'lesser tubercle of humerus.')], '本次资料给出概括性附着描述，不能直接把盂上结节上的某一点作为唯一标准。需结合盂唇与个体变异进一步核对。','limited')
add('Middle glenohumeral ligament','capsule',['Scapula','Humerus'],'肩胛骨前方关节盂缘，位于上盂肱韧带下方。','肱骨小结节区域。','较宽的囊韧带，位于肩胛下肌腱深面并与其融合；形态存在变异。','已有独立源对象，但尚未表现与关节囊、肩胛下肌腱融合的边界。',[quote('shoulder','The middle glenohumeral ligament attaches','subscapularis muscle.')])
add('Inferior glenohumeral ligament','capsule',['Scapula','Humerus'],'下方盂唇与关节盂缘区域，须按前后束区分。','肱骨颈下内侧区域，具体附着形式有差异。','吊带状复合体：前束、后束以及二者之间的腋隐窝。','每侧仅 1 个源对象，缺少可独立选择的前束、后束和腋隐窝；不能用窄带外观代表整个复合体。',[quote('shoulder','The inferior glenohumeral ligament is','axillary pouch.')])
add('Coracohumeral ligament','capsule',['Scapula','Humerus'],'肩胛骨喙突区域。','肱骨大小结节区域，并与肩袖间隙周边结构连续。','跨肩关节上方；分束和与肌腱融合关系需结合更细致资料核对。','现有单个源网格未明确拆分至大小结节的纤维部分，不把表面平滑视为分束准确。',[quote('shoulder','The coracohumeral ligament extends','superior side.')])
add('Transverse humeral ligament','capsule',['Humerus'],'肱骨大结节侧。','肱骨小结节侧。','横跨结节间沟上方，与肱二头肌长头腱的通道相关。','源对象存在，骨面相交需区分末端埋入与游离段穿骨；不能封住腱通道。',[quote('shoulder','The transverse humeral ligament extends','sulcus.')], '传统独立韧带命名与腱纤维延续的组织学解释存在讨论；本样板保留源命名，不声称独立组织边界已核准。')
add('Coraco-acromial ligament','arch',['Scapula','Humerus'],'喙突外侧缘。','肩峰前外侧下表面。','强韧的三角形／扇形结构，与喙突、肩峰共同构成喙肩弓，跨过肱骨头上方。','源控制网格仅 4 个顶点，难以表达扇形分束和自然边缘；端部存在疑似骨面相交，尚未调整足印。',[quote('ca','The coracoacromial ligament is a strong','of the scapula .'),quote('coracoid-review','The CAL extends','coracoid process')])
add('Conoid ligament','arch',['Scapula','Clavicle'],'喙突基部区域。','锁骨下表面的锥状结节。','喙锁韧带的锥状部分，与斜方部分在喙突侧连续，向锁骨侧分开。','已有独立源对象；需核对锁骨端是否对应锥状结节及与斜方束的连续关系。',[quote('cc','Conoid part:','Trapezoid part:'),quote('coracoid-review','The CCL is a complex','clavicle superiorly')])
add('Trapezoid ligament','arch',['Scapula','Clavicle'],'喙突上表面区域。','锁骨下表面的斜方线。','喙锁韧带的斜方部分，较扁平；与锥状部分共同连接喙突和锁骨。','源控制网格 6 顶点，尚未校准斜方线上的附着范围。',[quote('cc','Trapezoid part:','Function'),quote('coracoid-review','The CCL is a complex','clavicle superiorly')])
add('Acromioclavicular ligament','scapula',['Scapula','Clavicle'],'肩峰的肩锁关节邻近区域（详细边界待补依据）。','锁骨肩峰端邻近区域（详细边界待补依据）。','肩锁关节囊韧带复合体，尤其需要核对上后方部分，不能概括为一根绳。','现有每侧一个对象，未分出不同方向的囊韧带部分。',[quote('ac','80% of horizontal stability','complex')], '本次论文支持上后方囊韧带复合体的重要性，尚不足以精确定位全部附着边界；此条未标为附着资料已核准。','limited')
add('Superior transverse scapular ligament','scapula',['Scapula'],'肩胛上切迹一侧骨缘。','肩胛上切迹另一侧骨缘。','跨越切迹形成纤维骨性孔道；肩胛上神经从下方通过，形态可变。','源网格仅 4 顶点；应保留切迹下方通道，不应整片压贴骨面。',[quote('stsl','the suprascapular notch (SN) of the superior border','above the STSL.')])
add('Inferior transverse scapular ligament','scapula',['Scapula'],'肩胛冈外侧与盂切迹邻近区域，精确附着待补。','肩胛颈后方、盂切迹邻近区域，精确附着待补。','又称盂切迹韧带；与肩胛上神经通过盂切迹的通道相关，存在变异。','源网格仅 4 顶点；跨切迹走行需要从背面核对，当前未校准足印。',[quote('itsl','The nerve continues along','[ 6 ].')], '当前资料支持与盂切迹及神经通道的位置关系，未直接证明两端足印，因此附着描述作为待核对范围。','limited')
rows=json.loads((P/'source-inventory.json').read_text());result=[]
for r in rows:result.append({**r,**D[re.sub(r'\.[rl]$','',r['source_structure_id'])]})
gaps=['盂肱下韧带复合体：源对象存在，但前束、后束和腋隐窝未独立分区；下一步须结合囊、盂唇后再拆分。','喙肱韧带及肩锁囊韧带：现有对象不代表全部分束和融合边界已建好。','喙盂韧带：本次源清单未见独立对象；文献描述存在变异及辨识差异，列为研究候选，不强行补一条标准带。','本轮范围是肩部韧带；胸锁、肋锁连接另成一组，不计入此处 11 类。','视觉修形版只改善网格分辨率、边缘厚度和材质，没有校准所有附着，也不作为运动绑定成品。']
(P/'catalog.json').write_text(json.dumps({'scope':'shoulder_girdle_ligaments','type_count':11,'source_object_count':22,'structures':result,'gaps':gaps},ensure_ascii=False,indent=2)+'\n')
# Add cited shoulder descriptions to the existing main info panel without changing wrist entries.
p=P.parent/'data/ligament-attachments.json';all_data=json.loads(p.read_text())
for name,d in D.items():all_data['structures'][name]={'origin':d['origin'],'insertion':d['insertion'],'course':d['shape'],'evidence_status':d['evidence_status'],'limitations':d['limitations'],'references':d['references'],'model_footprint_status':'not_anatomically_calibrated'}
p.write_text(json.dumps(all_data,ensure_ascii=False,indent=2)+'\n')
print('22 structures, 11 attachment entries; quotes verified in saved source text')
