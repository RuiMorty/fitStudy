import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parents[2]/'skeleton-workbench'
names=['Lateral temporomandibular ligament.r','Lateral temporomandibular ligament.l','Temporal bone.r','Temporal bone.l','Ulnopisiform ligament','Ulnopisiform ligament.l','Ulna.r','Ulna.l']
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (s,d):d.objects=[n for n in names if n in s.objects]
for o in d.objects:
 if o:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rows=[]
for obj in d.objects:
 if not obj:continue
 e=obj.evaluated_get(dg);m=e.to_mesh();xs=[(e.matrix_world@v.co).x for v in m.vertices];rows.append({'source_name':obj.name,'source_world_min_x':min(xs),'source_world_max_x':max(xs),'source_world_center_x':(min(xs)+max(xs))/2});e.to_mesh_clear()
(P/'源侧别复核.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
