"""Recess hip capsule locally beneath capsular ligament meshes. Display derivative only.
Do not change ligament attachments or assign arbitrary ordering to unrelated tissues.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent.parent/'hip-review'
bpy.ops.wm.open_mainfile(filepath=str(P/'hip-review-contact.blend'));scene=bpy.context.scene
cat=json.loads((P/'catalog.json').read_text());audit=json.loads((P/'geometry-audit-contact.json').read_text());reports=[]
for side in ['R','L']:
 row=next(r for r in cat['structures'] if r['side']==side and r['id'].startswith('capsule_hip_'))
 ob=scene.objects[row['id']+'__refined'];me=ob.data.copy();bm=bmesh.new();bm.from_mesh(me)
 if len(bm.faces)<25000:bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();bm.verts.ensure_lookup_table()
 center=sum((v.co for v in bm.verts),Vector())/len(bm.verts)
 if sum(v.normal.dot(v.co-center) for v in bm.verts)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 ligs=[r for r in cat['structures'] if r['side']==side and r['group']=='capsular']
 trees={r['id']:BVHTree.FromPolygons([v.co for v in scene.objects[r['id']+'__refined'].data.vertices],[list(f.vertices) for f in scene.objects[r['id']+'__refined'].data.polygons]) for r in ligs}
 original=[v.co.copy() for v in bm.verts];normals=[v.normal.copy() for v in bm.verts];depth=[0.]*len(bm.verts);contacts={k:0 for k in trees}
 for v in bm.verts:
  for key,tr in trees.items():
   q,n,_,d=tr.find_nearest(v.co)
   if d>.002 or abs(n.dot(v.normal))<.35:continue
   signed=(v.co-q).dot(v.normal)
   if signed<-.00045:continue
   # Smooth influence prevents a hard seam at the edge of the overlap neighbourhood.
   t=max(0,min(1,(d-.0007)/.0013));fade=1-t*t*(3-2*t)
   dep=min(.0015,max(0,signed+.00045))*fade
   if dep>depth[v.index]:depth[v.index]=dep
   if dep>.00001:contacts[key]+=1
 # Diffuse the small inset field, never the source capsule tangential coordinates.
 for _ in range(5):
  nxt=depth[:]
  for v in bm.verts:
   neighbours=[e.other_vert(v).index for e in v.link_edges]
   if neighbours:nxt[v.index]=max(depth[v.index],.65*sum(depth[i] for i in neighbours)/len(neighbours))
  depth=nxt
 for v in bm.verts:v.co=original[v.index]-normals[v.index]*depth[v.index]
 bm.to_mesh(me);bm.free();ob.data=me
 for f in me.polygons:f.use_smooth=True
 near_before=sum(any(tr.find_nearest(v)[3]<.00005 for tr in trees.values()) for v in original)
 near_after=sum(any(tr.find_nearest(v.co)[3]<.00005 for tr in trees.values()) for v in me.vertices)
 report={'near_coincident_before':near_before,'near_coincident_after':near_after,'id':row['id'],'changed_vertices':sum(d>1e-7 for d in depth),'vertices':len(depth),'max_inset_mm':round(max(depth)*1000,4),'ligament_meshes_unchanged':True,'overlap_neighbourhood_by_ligament':contacts,'status':'local_display_separation_not_measured_capsular_layers'};reports.append(report)
 note='关节囊仅在囊外韧带重叠邻域局部内退、平滑过渡；韧带网格及其骨面附着未改。显示分层不代表真实组织间隙，实际组织在此融合。'
 row['comparison']=note;row['geometry_revision']='capsule-overlap-v1';a=next(x for x in audit if x['id']==row['id']);a.update(contact_display_note=note,surface_displacement_max_mm=report['max_inset_mm'],audit_scope='capsule_overlap_display_only',end_candidates=[],suspected_penetration_nearest_normal_only={})
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(P/'hip-review-overlap.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'hip-review-overlap.blend'),compress=True)
for name,data in [('overlap-report.json',reports),('geometry-audit-overlap.json',audit),('catalog.json',cat)]: (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
cfg=json.loads((P/'review-config.json').read_text());cfg.update(model='hip-review-overlap.glb',audit='geometry-audit-overlap.json',loadedLabel='重叠交界显示版 · 解剖待核准');(P/'review-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');print(json.dumps(reports,ensure_ascii=False),flush=True)
