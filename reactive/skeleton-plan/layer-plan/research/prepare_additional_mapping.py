from pathlib import Path
import json
R=Path(__file__).resolve().parent;W=R.parents[2]/'skeleton-workbench'
cs=json.loads((W/'data/connections.json').read_text())['connections'];lookup={c['id']:c for c in cs};rows=[]
specs=[('temporomandibular','颞下颌关节囊',['tmj']),('superior tibiofibular','近侧胫腓关节囊',['proximal_tibiofibular']),('sternoclavicular','胸锁关节囊',['sternoclavicular']),('radiocarpal','桡腕关节囊',['radiocarpal']),('knee','膝关节囊',['tibiofemoral','patellofemoral']),('hip','髋关节囊',['hip']),('glenohumeral','盂肱关节囊',['glenohumeral']),('elbow','肘关节囊',['humeroulnar','humeroradial','proximal_radioulnar']),('acromioclavicular','肩锁关节囊',['acromioclavicular']),('interphalangeal joint of great toe','拇趾趾间关节囊',['foot_ip_1_proximal_distal'])]
for side,zh in [('L','左'),('R','右')]:
 def add(id,name,source,connections,kind='capsule',group=False):
  bones=list(dict.fromkeys(b for c in connections for b in lookup[c]['bone_ids']))
  rows.append({'id':id+'_'+side,'name_zh':zh+name,'source_object':source+'.'+side.lower(),'side':side,'layer':kind,'bone_ids':bones,'connection_ids':connections,'granularity':'source_group_unsegmented' if group else 'individual','status':'mapping_draft_pending_geometry_anatomy_review'})
 for en,zhname,ids in specs:
  source='Articular capsule of '+en+('' if en.startswith('interphalangeal') else ' joint')
  add('capsule_'+ids[0],zhname,source,[id+'_'+side for id in ids])
 for part,cn,suffix in [('hand','指',''),('foot','趾',' of foot')]:
  for level,cnlevel,end in [('proximal','近侧','proximal_middle'),('distal','远侧','middle_distal')]:
   add('capsules_'+part+'_'+level,cnlevel+cn+'间关节囊组','Articular capsules of '+level+' interphalangeal joints'+suffix,[f'{part}_ip_{n}_{end}_{side}' for n in range(2,6)],group=True)
  prefix='mcp' if part=='hand' else 'mtp';en='metacarpophalangeal' if part=='hand' else 'metatarsophalangeal'
  add('capsules_'+prefix,('掌指' if part=='hand' else '跖趾')+'关节囊组','Articular capsules of '+en+' joints',[f'{prefix}_{n}_{side}' for n in range(1,6)],group=True)
 add('ligament_annular_radius','桡骨环状韧带','Annular ligament of radius',['proximal_radioulnar_'+side],kind='ligament')
rows.append({'id':'pubic_interpubic_disc','name_zh':'耻骨间盘','source_object':'Interpubic disc','side':'M','layer':'joint','bone_ids':lookup['pubic_symphysis']['bone_ids'],'connection_ids':['pubic_symphysis'],'granularity':'individual','status':'mapping_draft_pending_geometry_anatomy_review'})
names=set(json.loads((W/'research/ossicles/z-all-object-names.json').read_text()));assert all(r['source_object'] in names for r in rows);assert len(rows)==35
(R/'additional-mapping.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(len(rows),'exact source names found')
