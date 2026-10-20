import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];rows=[r for r in json.loads((W/'z-anatomy-candidate/ligament-library.json').read_text())['objects'] if any(x in ' '.join(r['joint_or_connection_ids']) for x in ['glenohumeral','acromioclavicular'])]
names=[r['source_structure_id'] for r in rows]+[b+'.'+s for b in ['Scapula','Humerus','Clavicle'] for s in ['r','l']]
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=names
for o in d.objects:
 if o:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
for o in d.objects:
 if o:print(o.name,len(o.data.vertices),[(m.type,getattr(m,'levels',None),getattr(m,'thickness',None)) for m in o.modifiers])
(W/'shoulder-review/source-inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
