"""Find edge-connected source Cartilage patches. No semantic labels inferred here."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'z-anatomy-candidate';S=R/'research/ossicles/Startup.blend'
bones=[b for b in json.loads((O/'structures.json').read_text())['bones'] if any(b['id'].startswith('bone_'+n+'_') for n in ['scapula','humerus','radius','ulna','hip','femur','patella','tibia'])]
with bpy.data.libraries.load(str(S),link=False) as (src,dst):dst.objects=[b['source_structure_id'] for b in bones]
objects={o.name:o for o in dst.objects if o};result=[]
for o in objects.values():bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
for b in bones:
 o=objects[b['source_structure_id']];m=o.data;slots={i for i,mat in enumerate(m.materials) if mat and 'cartilage' in mat.name.lower()};faces={p.index:p for p in m.polygons if p.material_index in slots};edgefaces={}
 for p in faces.values():
  for edge in p.edge_keys:edgefaces.setdefault(tuple(sorted(edge)),[]).append(p.index)
 neighbors={i:set() for i in faces}
 for group in edgefaces.values():
  for i in group:neighbors[i].update(group)
 pending=set(faces);parts=[]
 while pending:
  first=min(pending);pending.remove(first);queue=[first];component=[]
  while queue:
   i=queue.pop();component.append(i)
   for j in neighbors[i]&pending:pending.remove(j);queue.append(j)
  ids=sorted({i for f in component for i in faces[f].vertices});vs=[o.matrix_world@m.vertices[i].co for i in ids];center=[sum(v[i] for v in vs)/len(vs) for i in range(3)]
  parts.append({'component':len(parts),'source_face_indices':sorted(component),'face_count':len(component),'center_source_m':center,'min_source_m':[min(v[i] for v in vs) for i in range(3)],'max_source_m':[max(v[i] for v in vs) for i in range(3)]})
 result.append({'bone_id':b['id'],'source_object':o.name,'modifiers':[m.type for m in o.modifiers],'components':parts})
(O/'major-joint-surface-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in result:
 if r['bone_id'].endswith('_R'):
  print(r['bone_id'],[(p['component'],p['face_count'],[round(x,3) for x in p['center_source_m']]) for p in r['components']])
