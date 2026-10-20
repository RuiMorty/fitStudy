"""Explicit source-supported attachment descriptions; no inference from regional bone_ids."""
import json
from pathlib import Path
P=Path(__file__).parent;W=P.parents[1];refs={}
for f in (P/'references').glob('index*.json'):
 for r in json.loads(f.read_text()):
  if r.get('status')==200:refs[r['id']]=r
D={}
def add(name,origin,insertion,course,source,section,quote,limit='',level='reference_checked'):
 r=refs[source];text=(P/'references'/(source+'.txt')).read_text()
 assert quote in text,(name,quote)
 D[name]={'origin':origin,'insertion':insertion,'course':course,'evidence_status':level,'limitations':limit or '文献描述已核对；个体附着区大小和当前三维足印仍待复核。','references':[{'title':section,'url':r['final'],'section':section,'quote':quote,'retrieved':'2026-10-13','page_sha256':r['sha256']}],'model_footprint_status':'not_anatomically_calibrated'}
add('Radiate carpal ligament','头状骨掌侧，为主要放射中心。','主要向舟骨、月骨和三角骨掌侧分散附着。','这是掌侧的一组放射状纤维带，不宜当作一条独立的直线韧带，也不能把区域目录中所有腕骨都当成它的止点。','gray-wrist','Radiate carpal ligament｜百科定义（证据待补强）','The majority of the bands radiate from the capitate to the scaphoid , lunate , and triquetral bones .','当前可直接读取的词条缺少明确原始引文；该关系仅作有出处的待复核描述，尚不能标为解剖准确。分束命名须与现代腕关节图谱对应。','secondary_reference_pending')
# This source describes a shared proximal complex; do not assert all three origins for each division.
for n,distal in [('Ulnocapitate ligament','头状骨'),('Ulnolunate ligament','月骨'),('Ulnotriquetral ligament','三角骨')]:
 add(n,'所属掌侧尺腕韧带复合体的近端区域：TFCC 前缘、掌侧桡尺韧带和尺骨茎突。单独这一束的精确起点尚需专项文献确认。',distal+'；向远端斜行至该骨。','属于掌侧尺腕韧带复合体的一部分；不能把邻近经过的骨当作附着骨。','kenhub-wrist','Kenhub｜Radiocarpal joint / Palmar ulnocarpal ligament','The palmar ulnocarpal ligament arises from the anterior margin of the triangular fibrocartilage complex, the palmar radioulnar ligament and ulnar styloid process .','此出处支持复合体近端及分束止点，未单独界定本束的全部骨性足印，不能据此声称本束同时直接起自三处。','group_origin_only')
add('Lateral temporomandibular ligament','颞骨关节结节起始部附近。','下颌骨髁突颈。','属于关节囊外侧的增厚结构，与关节囊连续，不能当作悬空的独立硬片。','teachme-tmj','TeachMeAnatomy｜TMJ / Ligaments','Lateral ligament – runs from the beginning of the articular tubule to the mandibular neck.','本出处支持整体附着关系；没有提供外斜部、内水平部各自的精确足印，面板不将分束细节写成已核准。')
for n,a,b,quote in [
 ('Scaphotrapeziotrapezoidal ligament','舟骨远端极。','大多角骨和小多角骨。','The scaphotrapeziotrapezoidal ligament, which connects the distal pole of the scaphoid bone to the trapezium and trapezoid bones'),
 ('Scaphocapitate ligament','舟骨。','头状骨。','The scaphocapitate ligament, that courses from the scaphoid to the capitate bone'),
 ('Triquetrocapitate ligament','三角骨远端缘。','头状骨骨体。','The triquetrocapitate ligament, attaching between the distal margin of triquetrum and body of capitate bone.'),
 ('Triquetrohamate ligament','三角骨。','钩骨。','The triquetrohamate ligament,connecting the triquetrum and hamate bones')]:
 add(n,a,b,'位于掌侧腕中关节韧带群。','kenhub-intercarpal','Kenhub｜Intercarpal joints / Palmar intercarpal ligaments',quote)
add('Dorsal scaphotriquetral ligament','三角骨背侧区域。','舟骨背侧区域。','腕背侧骨间韧带的近端增厚部分；整体腕背侧骨间韧带还可有其他纤维，不能据此将整组都视为舟三角韧带。','kenhub-intercarpal','Kenhub｜Intercarpal joints / Dorsal intercarpal ligament','The thickened proximal part of the dorsal intercarpal ligament ligament, extending between the dorsal aspects of the scaphoid and triquetrum bones, is sometimes specifically referred to as the dorsal scaphotriquetral ligament .')
add('Dorsal intercarpal ligaments','三角骨背侧结节。','舟骨背侧沟；可另有纤维至小多角骨和头状骨。','大体横向走行；源对象为组合网格，其各支束尚未与文献逐一对应。','kenhub-intercarpal','Kenhub｜Intercarpal joints / Dorsal intercarpal ligament','The dorsal intercarpal ligament is a horizontal strap that arises from the dorsal tubercle of the triquetrum bone to the dorsal groove of the scaphoid bone, and may pass additional fibres to the trapezoid and capitate bones.')
for n,a,b in [('Scapholunate interosseous ligament','舟骨朝向月骨的相邻面。','月骨朝向舟骨的相邻面。'),('Lunotriquetral interosseous ligament','月骨朝向三角骨的相邻面。','三角骨朝向月骨的相邻面。')]:
 add(n,a,b,'近排腕骨之间的囊内骨间韧带。','kenhub-intercarpal','Kenhub｜Intercarpal joints / Interosseous intercarpal ligaments','These structures span between the adjacent sides of the relevant carpal bones, thus separating the joint spaces of the midcarpal and radiocarpal joints.','本出处未细分掌侧、背侧与膜部，当前薄片不能据此认定代表全部分束。')
for n,b in [('Pisohamate ligament','钩骨钩。'),('Pisometacarpal ligament','第 5 掌骨。')]:
 add(n,'豌豆骨。',b,'豌豆骨向远端的韧带连接。','kenhub-intercarpal','Kenhub｜Intercarpal joints / Articular surfaces','The pisiform bone is also connected to the hook of hamate bone and fifth metacarpal bones via pisohamate and pisometacarpal ligaments, respectively.')
add('Radioscaphocapitate ligament','桡骨茎突。','舟骨远端；少量纤维继续至头状骨近端。','属于掌侧桡腕韧带群，构成关节囊外侧部分。','kenhub-wrist','Kenhub｜Radiocarpal joint / Palmar radiocarpal ligaments','extends from the styloid process of radius to the distal aspect of scaphoid bone , with a small number of fibres continuing and proximal aspect of the capitate bone.')
add('Dorsal radiocarpal ligament','桡骨背侧结节两侧的桡骨远端。','较宽浅部至三角骨背侧；较窄深部至月三角骨间韧带。','背侧斜向走行；既包含骨性连接，也涉及软组织连接。','kenhub-wrist','Kenhub｜Radiocarpal joint / Dorsal radiocarpal ligament','The narrower deep part arises medial to dorsal tubercle attaches to the lunotriquetral interosseous ligament.')
# Direct peer-reviewed open-access wrist anatomy/ultrasound source, sections 3–7.
paper='wrist-ultrasound-review';title='Wang 等，2021｜腕韧带解剖与超声综述'
add('Ulnocapitate ligament','尺骨远端掌侧的尺腕韧带起始区域。','头状骨掌侧。','由尺骨远端经过月骨掌侧，斜向头状骨；文献所说“跨过月骨”不能写成“以月骨为止点”。',paper,title+' §3.1 / 图7','The ulnocapitate ligament spans over the distal ulna, lunate, and capitate','论文支持尺骨远端—头状骨的走行关系；未提供本模型对应的毫米级足印，具体茎突/TFCC 边界仍须二核。')
add('Ulnolunate ligament','尺骨远端的尺腕韧带起始区域。','月骨。','尺腕掌侧韧带之一。',paper,title+' §3.2 / 图9','The ulnolunate ligament is seen bridging the ulna and lunate','论文支持连接骨关系；不能把整组尺腕韧带的所有起始结构套用到这一束。')
add('Ulnotriquetral ligament','尺骨远端的尺腕韧带起始区域。','三角骨。','构成 TFCC 掌侧壁的一部分。',paper,title+' §3.3 / 图10','the ulnotriquetral ligament is seen bridging the distal ulna and triquetrum')
add('Palmar scaphotriquetral ligament','舟骨结节，附着呈扇形。','三角骨，位于豌豆骨深面。','经头状骨和钩骨掌侧；经过这些骨不等于以这些骨为起止。',paper,title+' §4 / 图13','The ligament can be seen connecting the scaphoid tubercle and triquetrum (underneath the shadow of the pisiform), coursing over the capitate and hamate')
add('Palmar lunotriquetral ligament','月骨掌侧相邻面。','三角骨掌侧相邻面。','近排腕骨间的短掌侧韧带；不要以此代表月三角骨间韧带的全部分束。',paper,title+' §4 / 图11','the volar scapholunate ( Figure 11 A) and lunotriquetral ligaments ( Figure 11 B).')
for n,a,b,quote in [('Radial collateral ligament of wrist joint','桡骨远端桡侧。','舟骨。','The radial collateral ligament connects the distal radius and scaphoid.'),('Ulnar collateral ligament of wrist joint','尺骨远端尺侧。','三角骨。','The ulnar collateral ligament connects the distal ulna and triquetrum.')]:
 add(n,a,b,'腕侧方的关节稳定结构。',paper,title+' §7 / 图19',quote,'此处采用该综述及其引用的侧副韧带研究；不同文献对与尺腕韧带的分界存在差异，未将豌豆骨等附加纤维写成确定止点。')
add('Dorsal ulnocarpal ligament','尺骨远端背侧区域。','三角骨背侧区域。','对照背侧尺三角韧带；超声中表现为关节囊增厚，未必是一条完全独立的带状结构。',paper,title+' §5 / 图16','Under US imaging, the dorsal ulnotriquetral ligament appears as a thickened portion of the capsule instead of a separate ligament','源对象名为 Dorsal ulnocarpal ligament；是否仅代表文献中的背侧尺三角部分仍需结合网格二核。','source_group_mapping_pending')
for item in D.values():
 for ref in item['references']:
  if 'PMC8534780' in ref['url']:
   ref['retrieval_url']=ref['url'];ref['url']='https://doi.org/10.3390/diagnostics11101834'
out={'schema_version':1,'review_date':'2026-10-13','scope':'逐项来源支持的信息；不从区域关联推断附着点。','structures':D}
(W/'data/ligament-attachments.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Attachment descriptions:',len(D))
