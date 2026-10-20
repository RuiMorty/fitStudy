import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[2]
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (s,d):d.objects=['Ulnocapitate ligament.l','Ulnocapitate ligament.r']
for o in d.objects:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
for o in d.objects:print(o.name,json.dumps({'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons]}),flush=True)
