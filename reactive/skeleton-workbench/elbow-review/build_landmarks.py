"""Read original Z-Anatomy label leaders; do not infer from ligament endpoints."""
import bpy,json
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
terms={'Medial epicondyle of humerus':('肱骨内上髁','Humerus'),'Lateral epicondyle of humerus':('肱骨外上髁','Humerus'),'Sublime tubercle':('尺骨崇高结节','Ulna'),'Radial notch':('桡切迹','Ulna'),'Olecranon':('鹰嘴','Ulna'),'Coronoid process of ulna':('尺骨冠突','Ulna'),'Head of radius':('桡骨头','Radius'),'Neck of radius':('桡骨颈','Radius')}
terms['Supinator crest']=('旋后肌嵴','Ulna')
names=[t+'.'+s for t in terms for s in ['t','s','j','i']]+[t+'.'+s for t in ['Humerus','Ulna','Radius'] for s in ['r','l']]
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=names
for o in d.objects:
 if o:
  bpy.context.scene.collection.objects.link(o);o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();result=[]
for term,(zh,bone) in terms.items():
 for suffix,side in [('j','R'),('i','L')]:
  o=bpy.data.objects[term+'.'+suffix];b=bpy.data.objects[bone+'.'+side.lower()]
  coords=[b.matrix_world@v.co for v in b.data.vertices];tree=BVHTree.FromPolygons(coords,[list(p.vertices) for p in b.data.polygons])
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();endpoints=[e.matrix_world@v.co for v in me.vertices];ds=[tree.find_nearest(v)[3] for v in endpoints];i=min(range(len(ds)),key=ds.__getitem__);p=endpoints[i]
  assert abs(p.x)>.03 and p.z>1,str((o.name,list(p),[(c.type,c.name) for c in o.constraints]))
  assert ds[i]<.0001, str((o.name,ds[i]))
  result.append({'name':zh,'term':term,'side':side,'bone':'bone_'+bone+'_'+side.lower(),'position':[p.x,p.z,-p.y],'source_object':o.name,'source_kind':'evaluated_original_label_leader_nearest_endpoint','bone_surface_distance_mm':round(ds[i]*1000,3),'review':'source_landmark_location_not_ligament_footprint'})
(P/'landmarks.json').write_text(json.dumps({'source':'Z-Anatomy Startup.blend original anatomical labels','landmarks':result},ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
