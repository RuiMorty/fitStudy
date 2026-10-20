"""Reuse only evaluated native label leaders; missing labels are reported, not mirrored."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;W=P.parent
terms={'Radial styloid process':('桡骨茎突','Radius','Radius','桡骨'),'Ulnar styloid process':('尺骨茎突','Ulna','Ulna','尺骨'),'Ulnar notch':('尺切迹','Radius','Radius','桡骨'),'Tubercle of scaphoid bone':('舟骨结节','Scaphoid bone','Scaphoid','舟骨'),'Tubercle of trapezium bone':('大多角骨结节','Trapezium bone','Trapezium','大多角骨'),'Hook of hamate bone':('钩骨钩','Hamate bone','Hamate','钩骨')}
bpy.ops.wm.read_factory_settings(use_empty=True)
names=[t+'.'+s for t in terms for s in ['t','s','j','i']]+[b+'.'+s for b in {v[1] for v in terms.values()} for s in ['r','l']]
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=[n for n in names if n in src.objects]
for o in d.objects:
 if o:bpy.context.scene.collection.objects.link(o);o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();result=[];missing=[]
for term,(zh,bone,short,bone_zh) in terms.items():
 for suffix,side in [('j','R'),('i','L')]:
  o=bpy.data.objects.get(term+'.'+suffix)
  if not o:missing.append(term+'.'+suffix);continue
  b=bpy.data.objects[bone+'.'+side.lower()];coords=[b.matrix_world@v.co for v in b.data.vertices];tree=BVHTree.FromPolygons(coords,[list(p.vertices) for p in b.data.polygons])
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];ds=[tree.find_nearest(v)[3] for v in points];i=min(range(len(ds)),key=ds.__getitem__);p=points[i]
  if ds[i]>.0005:missing.append({'label':o.name,'distance_mm':ds[i]*1000});continue
  p=tree.find_nearest(p)[0]
  result.append({'name':zh,'term':term,'side':side,'bone':'bone_'+short+'_'+side.lower(),'bone_name_zh':bone_zh,'position':[p.x,p.z,-p.y],'source_object':o.name,'source_kind':'native_leader_endpoint_projected_to_own_bone_within_0_5mm','source_leader_offset_mm':round(ds[i]*1000,3),'bone_surface_distance_mm':0,'review':'source_landmark_location_not_ligament_footprint'})
(P/'landmarks.json').write_text(json.dumps({'source':'Z-Anatomy evaluated native label leaders','landmarks':result,'missing':missing},ensure_ascii=False,indent=2)+'\n');print('LANDMARKS',len(result),'MISSING',missing,flush=True)
