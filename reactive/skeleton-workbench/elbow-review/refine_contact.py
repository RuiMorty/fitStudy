"""Local RCL display-contact derivative. No changes to UCL or source assets.
End zones are display controls on this source mesh, NOT validated footprints.
"""
import bpy,bmesh,json,math,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/(os.environ.get('ELBOW_BASE','elbow-review')+'.blend')))
scene=bpy.data.scenes['Elbow review'];bpy.context.window.scene=scene
report=json.loads((P/(os.environ.get('ELBOW_AUDIT_BASE','geometry-audit')+'.json')).read_text())
def tree_for(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 tree=BVHTree.FromBMesh(bm);bm.free();return tree
def ring_outer(side):
 obj=bpy.data.objects['construction_ligament_annular_radius_'+side]
 bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bm.normal_update()
 center=sum((v.co for v in bm.verts),Vector())/len(bm.verts)
 orient=sum(v.normal.dot(Vector((v.co.x-center.x,v.co.y-center.y,0))) for v in bm.verts)
 if orient<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 for v in bm.verts:
  weight=obj.vertex_groups[0].weight(v.index)
  v.co+=v.normal*(.000225*weight)
 bm.normal_update();tr=BVHTree.FromBMesh(bm);bm.free();return tr

def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
metrics=[]
for side in ['R','L']:
 id='z_lig_radial_collateral_ligament_'+side
 ob=bpy.data.objects[id+'__refined'];construct=bpy.data.objects['construction_'+id]
 me=construct.data.copy();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 hum=tree_for(bpy.data.objects['bone_Humerus_'+side.lower()])
 ring=ring_outer(side)
 old={v:v.co.copy() for v in bm.verts}
 weights={v:(smooth((v.co.z-1.1035)/.007),smooth((1.098-v.co.z)/.007)) for v in bm.verts}
 # Land on the named connecting structure, never on nearest of all bones.
 for v in bm.verts:
  wh,wr=weights[v]
  target=hum if wh>wr else ring;w=max(wh,wr)
  if not w:continue
  p,n,_,d=target.find_nearest(v.co if wh>wr else v.co-Vector((0,0,.0015)))
  # A tiny surface offset avoids coplanar flicker without a visible air gap.
  v.co=v.co.lerp(p+n*.000035,w)
 # Smooth local curvature without shortening the anchored terminal rows.
 for _ in range(45):
  coords={}
  for v in bm.verts:
   w=max(weights[v]); neighbours=[e.other_vert(v) for e in v.link_edges]
   if not neighbours or w==0:continue
   coords[v]=v.co.lerp(sum((n.co for n in neighbours),Vector())/len(neighbours),.45*w)
  for v,c in coords.items():
   v.co=c
   wh,wr=weights[v]
   if max(wh,wr)>.98:
    tr=hum if wh>wr else ring;p,n,_,d=tr.find_nearest(v.co);v.co=p+n*.000035
 # Keep the transition on the outside of its assigned support surface.
 for v in bm.verts:
  wh,wr=weights[v]
  if not max(wh,wr):continue
  tr=hum if wh>wr else ring
  p,n,_,d=tr.find_nearest(v.co)
  if wh>wr and d<.001 and (v.co-p).dot(n)<.000035:v.co=p+n*.000035
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();bm.to_mesh(me)
 work=bpy.data.objects.new('RCL contact construction '+side,me);scene.collection.objects.link(work)
 vg=work.vertex_groups.new(name='Contact thickness taper')
 for v in bm.verts:
  # Retain body volume and taper smoothly into both connecting surfaces.
  w=max(weights[v]);boundary=v.is_boundary
  vg.add([v.index],max(.05,(1-.95*w)*(.3 if boundary else 1)),'REPLACE')
 displacement=max((v.co-old[v]).length for v in bm.verts)*1000
 end_metrics={}
 for label,idx,tr in [('humerus',0,hum),('annular',1,ring)]:
  vs=[v for v in bm.verts if weights[v][idx]>.999]
  end_metrics[label]={'terminal_vertices':len(vs),'max_surface_distance_mm':round(max(tr.find_nearest(v.co)[3] for v in vs)*1000,4)}
 bm.free();mod=work.modifiers.new('Thin contact ends','SOLIDIFY');mod.thickness=.00045;mod.offset=0;mod.vertex_group=vg.name;mod.thickness_vertex_group=0
 bpy.context.view_layer.update();ev=work.evaluated_get(bpy.context.evaluated_depsgraph_get());final=bpy.data.meshes.new_from_object(ev)
 final.materials.clear()
 for mat in ob.data.materials:final.materials.append(mat)
 for poly in final.polygons:poly.use_smooth=True
 ob.data=final
 # Keep construction editable but outside the export scene.
 scene.collection.objects.unlink(work)
 next(s for s in bpy.data.scenes if s != scene).collection.objects.link(work)
 a=next(x for x in report if x['id']==id)
 a['boundary_preserved']=False;a['surface_displacement_max_mm']=round(displacement,3)
 a['contact_display_note']='仅桡侧副韧带连接端修形：上端贴向肱骨、下端贴向环状韧带，厚度渐薄；约 0.035 mm 贴面间隔用于避免共面闪烁，是显示处理，不是解剖足印测量。'
 a['contact_metrics']=end_metrics
 # Existing PCA endpoints describe the baseline and must not masquerade as new measurements.
 a['end_candidates']=[]
 flags={}
 for name in ['Humerus','Ulna','Radius']:
  tr=tree_for(bpy.data.objects['bone_'+name+'_'+side.lower()]);depth=[]
  for v in final.vertices:
   p,n,_,d=tr.find_nearest(v.co)
   if (v.co-p).dot(n)<0 and d>.0005:depth.append(d*1000)
  if depth:flags[name+'.'+side.lower()]={'samples':len(depth),'max_depth_mm':round(max(depth),2)}
 a['suspected_penetration_nearest_normal_only']=flags
 metrics.append({'id':id,'max_displacement_mm':round(displacement,3),'contacts':end_metrics,'flags':flags})
for o in scene.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/(os.environ.get('ELBOW_OUTPUT','elbow-review-contact')+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/(os.environ.get('ELBOW_OUTPUT','elbow-review-contact')+'.blend')),compress=True)
(P/(os.environ.get('ELBOW_AUDIT_OUTPUT','geometry-audit-contact')+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('CONTACT_RESULT',json.dumps(metrics),flush=True)
