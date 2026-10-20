import json,struct
from pathlib import Path
P=Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
def nodes(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);return [x['name'] for x in j['nodes'] if 'mesh' in x]
m=read(P/'z-anatomy-candidate/latest-reviewed-tissues.json');ids=[x['id'] for x in m['objects']];names=nodes(P/m['file'])
assert len(ids)==len(set(ids))==m['count']==len(names)
assert set(names)==set(ids)
assert not any('__original' in n or 'stored_' in n for n in names)
for r in m['objects']:
 assert r['available'] and r['tissue'] and isinstance(r['bone_ids'],list) and isinstance(r['joint_or_connection_ids'],list)
 assert r.get('anatomy_review')!='accepted'
allrows=[]
for name in ['joints','connections','surface-marks','major-joint-surfaces','ligament-library','repaired-disc','nuclei']:
 d=read(P/f'z-anatomy-candidate/{name}.json')
 allrows.extend(r for r in d['objects'] if r['id'] not in ids and (name!='surface-marks' or r['id'] not in read(P/'z-anatomy-candidate/major-joint-surfaces.json')['replaces_ids']))
allrows+=m['objects'];assert len(allrows)==len(set(r['id'] for r in allrows))
c=read(P/'wrist-review/review-config.json');assert len(nodes(P/'wrist-review'/c['model']))==c['meshCount']
report={'latest_objects':len(ids),'final_tissue_and_surface_ids':len(allrows),'duplicate_ids':0,'original_comparison_meshes':0,'wrist_review_meshes':c['meshCount'],'metadata_contract':'passed','anatomical_acceptance':False,'full_collision_acceptance':False}
(P/'qa/latest-tissues-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
