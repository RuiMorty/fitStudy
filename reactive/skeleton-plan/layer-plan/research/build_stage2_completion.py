from pathlib import Path
import json,collections
P=Path(__file__).resolve().parents[1];W=P.parents[1]/'skeleton-workbench';O=W/'z-anatomy-candidate'
connections=json.loads((W/'data/connections.json').read_text())['connections'];models=[]
for name in ['joints','connections','ligament-library','repaired-disc','nuclei']:
 models+=json.loads((O/(name+'.json')).read_text())['objects']
result=[]
for c in connections:
 candidates=[m for m in models if c['id'] in m['joint_or_connection_ids']]
 synovial='synovial' in c['kind'];mixed=c['kind'] in ['motion_segment','rib_joint_group','joint_group','mixed_joint_complex','cartilage_mediated_connection']
 result.append({'connection_id':c['id'],'name_zh':c['name_zh'],'kind':c['kind'],'required_soft_tissues':c['required_soft_tissues'],'internal_candidates':[m['id'] for m in candidates if m.get('tissue_layer','joint')=='joint'],'capsule_candidates':[m['id'] for m in candidates if m.get('tissue_layer')=='capsule'],'ligament_regional_candidates':[m['id'] for m in candidates if m.get('tissue_layer')=='ligament'],'synovium':'missing_model' if synovial else 'requires_subjoint_classification_and_model' if mixed else 'not_applicable_to_this_connection_type','volumetric_surface_cartilage':'not_completed' if synovial else 'structure_specific_review_required','attachment_review':'pending','assembly_review':'pending','complete':False})
summary={'stage_complete':False,'connections':len(result),'synovial_connections_without_synovium':sum(r['synovium']=='missing_model' for r in result),'synovial_connections_without_capsule_candidate':sum('synovial' in r['kind'] and not r['capsule_candidates'] for r in result),'anatomically_accepted_connections':0,'note':'Candidate association by source parent does not establish complete coverage or anatomical attachment.'}
(P/'第二阶段完成度检查.json').write_text(json.dumps({'summary':summary,'connections':result},ensure_ascii=False,indent=2)+'\n');print(summary)
