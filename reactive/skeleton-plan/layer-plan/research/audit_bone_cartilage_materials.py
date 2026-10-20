import bpy,json,collections
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2]/'skeleton-workbench';mapping=json.loads((W/'z-anatomy-candidate/mapping.json').read_text())
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,dst):dst.objects=list({n for row in mapping for n in row['source_objects']})
objects={o.name:o for o in dst.objects if o};report=[]
for row in mapping:
 for name in row['source_objects']:
  o=objects[name];counts=collections.Counter(p.material_index for p in o.data.polygons);materials=[{'slot':i,'name':m.name if m else None,'faces':counts[i]} for i,m in enumerate(o.data.materials)]
  report.append({'bone_id':row['id'],'source_object':name,'materials':materials,'cartilage_faces':sum(v['faces'] for v in materials if v['name'] and 'cartilage' in v['name'].lower()),'all_faces':len(o.data.polygons),'modifiers':[m.type for m in o.modifiers]})
(R/'bone-cartilage-materials.json').write_text(json.dumps(report,indent=2)+'\n');print('BONES_WITH_CARTILAGE_FACES',len({x['bone_id'] for x in report if x['cartilage_faces']}),'FACES',sum(x['cartilage_faces'] for x in report))
