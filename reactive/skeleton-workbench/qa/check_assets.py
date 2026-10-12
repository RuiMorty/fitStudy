from pathlib import Path
import json,struct,hashlib
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'data/structures.json').read_text());names=[];triangles=0
for r in m['regions']:
 p=root/r['file'];d=p.read_bytes();magic,version,length=struct.unpack_from('<4sII',d);assert magic==b'glTF' and version==2 and length==len(d)
 n,t=struct.unpack_from('<II',d,12);g=json.loads(d[20:20+n]);names += [x['name'] for x in g['nodes'] if x.get('name','').startswith('bone_')]
 for mesh in g['meshes']:
  for primitive in mesh['primitives']:triangles+=g['accessors'][primitive['indices']]['count']//3
expected=[b['id'] for b in m['bones'] if b['available']];assert len(names)==len(set(names))==m['available_count'] and set(names)==set(expected)
assert triangles==sum(b.get('triangles',0) for b in m['bones'])
for b in m['bones']:
 if b['available']:
  for f in b['source_files']:assert hashlib.sha256((root.parent/'skeleton-plan/source-audit/raw'/f['filename']).read_bytes()).hexdigest()==f['sha256']
report={'semantic_objects':len(names),'triangles':triangles,'glb_bytes':sum(r['bytes'] for r in m['regions']),'raw_hashes_unchanged':True,'blend_bytes':(root/m.get('editable_master','assets/skeleton-review.blend')).stat().st_size,'status':'file_integrity_and_mapping_only_not_anatomical_validation'}
(root/'qa/asset-report.json').write_text(json.dumps(report,indent=2));print(report)
