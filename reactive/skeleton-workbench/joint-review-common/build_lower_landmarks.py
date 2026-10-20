"""Reuse native evaluated Z-Anatomy leader endpoints; do not invent or mirror markers."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent.parent
scopes={
'hip':{'Anterior inferior iliac spine':('髂前下棘','Hip bone','Hip','髋骨'),'Superior pubic ramus':('耻骨上支','Hip bone','Hip','髋骨'),'Body of ischium':('坐骨体','Hip bone','Hip','髋骨'),'Acetabular margin':('髋臼缘','Hip bone','Hip','髋骨'),'Acetabular notch':('髋臼切迹','Hip bone','Hip','髋骨'),'Acetabular fossa':('髋臼窝','Hip bone','Hip','髋骨'),'Intertrochanteric line':('转子间线','Femur','Femur','股骨'),'Greater trochanter':('大转子','Femur','Femur','股骨'),'Fovea for ligament of head of femur':('股骨头凹','Femur','Femur','股骨')},
'knee':{'Medial epicondyle of femur':('股骨内上髁','Femur','Femur','股骨'),'Lateral epicondyle of femur':('股骨外上髁','Femur','Femur','股骨'),'Intercondylar fossa':('股骨髁间窝','Femur','Femur','股骨'),'Anterior intercondylar area':('胫骨前髁间区','Tibia','Tibia','胫骨'),'Posterior intercondylar area':('胫骨后髁间区','Tibia','Tibia','胫骨'),'Medial condyle of tibia':('胫骨内侧髁','Tibia','Tibia','胫骨'),'Lateral condyle of tibia':('胫骨外侧髁','Tibia','Tibia','胫骨'),'Head of fibula':('腓骨头','Fibula','Fibula','腓骨')}}
for scope,terms in scopes.items():
 P=W/(scope+'-review');bpy.ops.wm.read_factory_settings(use_empty=True)
 names=[t+'.'+s for t in terms for s in ['t','s','j','i']]+[b+'.'+s for b in {v[1] for v in terms.values()} for s in ['r','l']]
 with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=[n for n in names if n in src.objects]
 for o in d.objects:
  if o:bpy.context.scene.collection.objects.link(o);o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();result=[];missing=[]
 for term,(zh,bone,short,bone_zh) in terms.items():
  for suffix,side in [('j','R'),('i','L')]:
   o=bpy.data.objects.get(term+'.'+suffix)
   if not o:missing.append(term+'.'+suffix);continue
   b=bpy.data.objects[bone+'.'+side.lower()];tree=BVHTree.FromPolygons([b.matrix_world@v.co for v in b.data.vertices],[list(p.vertices) for p in b.data.polygons])
   e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices]
   if not points:missing.append(o.name);continue
   ds=[tree.find_nearest(v)[3] for v in points];i=min(range(len(ds)),key=ds.__getitem__)
   if ds[i]>.0005:missing.append({'label':o.name,'distance_mm':round(ds[i]*1000,3)});continue
   p=tree.find_nearest(points[i])[0]
   result.append({'name':zh,'term':term,'side':side,'bone':'bone_'+short+'_'+side.lower(),'bone_name_zh':bone_zh,'position':[p.x,p.z,-p.y],'source_object':o.name,'source_kind':'native_leader_endpoint_projected_to_own_bone_within_0_5mm','source_leader_offset_mm':round(ds[i]*1000,3),'review':'source_landmark_location_not_ligament_footprint'})
 (P/'landmarks.json').write_text(json.dumps({'source':'Z-Anatomy evaluated native label leaders','landmarks':result,'missing':missing},ensure_ascii=False,indent=2)+'\n');print(scope,len(result),'missing',missing,flush=True)
