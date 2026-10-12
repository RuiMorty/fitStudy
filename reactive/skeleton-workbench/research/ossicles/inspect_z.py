import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
results=[]
for p in r.glob('*.blend'):
 if p.name.startswith('candidate'):continue
 with bpy.data.libraries.load(str(p),link=False) as (src,dst):
  names=list(src.objects)
  matches=[n for n in names if any(s in n.lower() for s in ['malle','incus','stape','ossic','temporal bone','tympan','cochle','vestib','coccy'])]
  dst.objects=list(matches)
 result={'file':p.name,'object_count':len(names),'matches':matches,'objects':[]}
 for o in dst.objects:
  if o is not None and not o.users_collection:bpy.context.scene.collection.objects.link(o)
 bpy.context.view_layer.update()
 for o in dst.objects:
  if o is None:continue
  pts=[o.matrix_world@Vector(v) for v in o.bound_box]
  result['objects'].append({'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'matrix_world':[list(row) for row in o.matrix_world],'properties':{k:str(o[k])[:1800] for k in o.keys() if k!='_RNA_UI'},'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers]})
 results.append(result)
(r/'z-object-index.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps([{'file':x['file'],'count':x['object_count'],'matches':x['matches']} for x in results],ensure_ascii=False,indent=2))
