"""Conservative boundary-locked surface refinement; no invented attachment correction."""
import bpy,bmesh,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
W=Path(__file__).resolve().parent.parent
for scope in ['hip','knee']:
 P=W/(scope+'-review');bpy.ops.wm.open_mainfile(filepath=str(P/(scope+'-review.blend')));scene=bpy.context.scene;rows=json.loads((P/'catalog.json').read_text())['structures'];trees={};report=[]
 for ob in scene.objects:
  if not ob.name.startswith('bone_'):continue
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  trees[ob.name]=BVHTree.FromBMesh(bm);bm.free()
 for r in rows:
  ob=scene.objects[r['id']+'__refined'];me=ob.data.copy();ob.data=me;bm=bmesh.new();bm.from_mesh(me);orig_tree=BVHTree.FromBMesh(bm);raw=len(bm.verts)
  islig=r['id'].startswith('z_lig_');boundary={v for e in bm.edges if e.is_boundary for v in e.verts};open_surface=bool(boundary);changed=False
  if islig and open_surface and len(bm.faces)<10000:
   bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
   boundary={v for e in bm.edges if e.is_boundary for v in e.verts};before={v:v.co.copy() for v in bm.verts}
   for _ in range(3):
    changes={}
    for v in bm.verts:
     if v in boundary:continue
     ns=[e.other_vert(v) for e in v.link_edges]
     if not ns:continue
     p=v.co.lerp(sum((n.co for n in ns),Vector())/len(ns),.12);delta=p-before[v]
     if delta.length>.00015:p=before[v]+delta.normalized()*.00015
     changes[v]=p
    for v,p in changes.items():v.co=p
   changed=True
  max_move=max(((v.co-before[v]).length*1000 for v in bm.verts),default=0) if changed else 0
  distances=[orig_tree.find_nearest(v.co)[3]*1000 for v in bm.verts]
  bm.to_mesh(me);bm.free()
  # Preserve original thickness and footprint. UVs are display detail, not measured fibers.
  if islig:
   vs=[v.co for v in me.vertices];lo=Vector(tuple(min(v[i] for v in vs) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vs) for i in range(3)));axes=sorted(range(3),key=lambda i:hi[i]-lo[i],reverse=True);uv=me.uv_layers.active or me.uv_layers.new(name='Illustrative fiber coordinates')
   for lp in me.loops:
    v=me.vertices[lp.vertex_index].co;uv.data[lp.index].uv=((v[axes[1]]-lo[axes[1]])*180,(v[axes[0]]-lo[axes[0]])*30)
  for f in me.polygons:f.use_smooth=True
  flags={}
  for name,tree in trees.items():
   if not name.endswith('_'+r['side'].lower()):continue
   depth=[]
   for v in list(me.vertices)[::max(1,len(me.vertices)//1500)]:
    p,n,_,d=tree.find_nearest(v.co)
    if d>.0005 and (v.co-p).dot(n)<0:depth.append(d*1000)
   if depth:flags[name]={'flagged_samples':len(depth),'max_depth_mm':round(max(depth),3)}
  note=('对开放韧带表面细分并轻度平顺，原边界锁定、内部顶点调整上限 0.15 mm；保留原厚度。' if changed else '保留该对象的原始几何；封闭网格及关节囊、半月板未套用开放韧带修形。')+' 纤维纹理为显示示意，未移动端部追求贴骨。'
  report.append({'id':r['id'],'raw_vertices':raw,'end_candidates':[],'surface_displacement_max_mm':round(max_move,5),'nearest_source_surface_max_mm':round(max(distances,default=0),5),'boundary_preserved':True,'contact_display_note':note,'suspected_penetration_nearest_normal_only':flags,'audit_scope':'static_nearest_normal_sampling','anatomical_status':'pending','changed':changed})
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(P/(scope+'-review-unified.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/(scope+'-review-unified.blend')),compress=True)
 (P/'geometry-audit-unified.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 cat=json.loads((P/'catalog.json').read_text())
 for r in cat['structures']:
  a=next(x for x in report if x['id']==r['id']);r['comparison']=a['contact_display_note'];r['geometry_review']='static_flags_not_anatomical_acceptance'
 (P/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n');c=json.loads((P/'review-config.json').read_text());c.update(model=scope+'-review-unified.glb',audit='geometry-audit-unified.json',loadedLabel='审查显示版 · 附着待核准');(P/'review-config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
 print(scope,'refined',sum(a['changed'] for a in report),'flagged',sum(bool(a['suspected_penetration_nearest_normal_only']) for a in report),flush=True)
