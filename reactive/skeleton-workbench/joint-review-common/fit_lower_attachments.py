"""Local display attachment fitting to explicitly assigned bones, not footprint validation.
Source display meshes are retained in *-unified.blend. Only terminal zones may move.
"""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent.parent
TARGETS={
 'Transverse part of iliofemoral ligament':('Hip','Femur'),
 'Descending part of iliofemoral ligament':('Hip','Femur'),
 'Pubofemoral ligament':('Hip','Femur'),
 'Ischiofemoral ligament':('Hip','Femur'),
 'Transverse acetabular ligament':('Hip','Hip'),
 'Anterior cruciate ligament':('Femur','Tibia'),
 'Posterior cruciate ligament':('Femur','Tibia'),
 'Superficial part of tibial collateral ligament':('Femur','Tibia'),
 'Deep part of tibial collateral ligament':('Femur','Tibia'),
 'Fibular collateral ligament':('Femur','Fibula'),
}
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def tree(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 tr=BVHTree.FromBMesh(bm);bm.free();return tr
for scope in ['hip','knee']:
 P=W/(scope+'-review');bpy.ops.wm.open_mainfile(filepath=str(P/(scope+'-review-unified.blend')));scene=bpy.context.scene
 cat=json.loads((P/'catalog.json').read_text());aud=json.loads((P/'geometry-audit-unified.json').read_text());results=[]
 for r in cat['structures']:
  base=r['name_en'].rsplit('.',1)[0];ob=scene.objects[r['id']+'__refined']
  if base not in TARGETS:
   results.append({'id':r['id'],'status':'unchanged','reason':'关节囊/软骨不是两端骨附着韧带，或连接软组织/源端区未确认；不自动贴向最近骨面。'});continue
  named=['bone_'+x+'_'+r['side'].lower() for x in TARGETS[base]];trs={n:tree(scene.objects[n]) for n in named}
  xyz=np.array([v.co[:] for v in ob.data.vertices]);center=xyz.mean(axis=0);_,_,vh=np.linalg.svd(xyz-center,full_matrices=False);axis=Vector(vh[0]);lo=min(Vector(v).dot(axis) for v in xyz);hi=max(Vector(v).dot(axis) for v in xyz);length=hi-lo
  u0=(xyz@vh[0]-lo)/length
  endpoints=[xyz[u0<.12],xyz[u0>.88]]
  pairs=[named,named[::-1]];cost=lambda ns:sum(float(np.median([trs[n].find_nearest(Vector(p))[3] for p in ps])) for n,ps in zip(ns,endpoints))
  assigned=min(pairs,key=cost)
  if any(np.median([trs[n].find_nearest(Vector(p))[3] for p in ps])>.004 for n,ps in zip(assigned,endpoints)):
   results.append({'id':r['id'],'status':'unchanged','reason':'候选端区距离过大，不做自动修复。'});continue
  me=ob.data.copy();bm=bmesh.new();bm.from_mesh(me)
  if len(bm.faces)<18000:bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
  bm.verts.ensure_lookup_table();old=[v.co.copy() for v in bm.verts];coords=[];weights=[];clipped=0;terminal=[[],[]]
  for i,v in enumerate(bm.verts):
   u=(v.co.dot(axis)-lo)/length;end=0 if u<.5 else 1;dend=u if end==0 else 1-u
   w=1-smooth((dend-.10)/.15);weights.append(w)
   if w<=0:coords.append(v.co.copy());continue
   tr=trs[assigned[end]];q,n,_,d=tr.find_nearest(v.co)
   # A far-away source point must be reviewed, never dragged over another feature.
   if d>.006:clipped+=1;weights[-1]=0;coords.append(v.co.copy());continue
   w*=1-smooth((d-.003)/.003);weights[-1]=w
   signed=(v.co-q).dot(n)
   # Preserve a thin distinct front/back layer; bury the terminal rim by 0.18–0.32 mm.
   offset=-.00025+max(-.00007,min(.00007,signed*.08))
   target=q+n*offset;p=v.co.lerp(target,w)
   # Transition remains outside the support, except the intentional shallow embed zone.
   if .05<w<.65:
    qq,nn,_,dd=tr.find_nearest(p)
    if (p-qq).dot(nn)<-.0004 and (v.co-qq).dot(nn)>=-.0004:p=qq+nn*.00002
   coords.append(p)
   if w>.999:terminal[end].append(i)
  for v,p in zip(bm.verts,coords):v.co=p
  # Smooth only the transition, anchoring terminal rows and all central vertices.
  for _ in range(3):
   updates={}
   for v in bm.verts:
    w=weights[v.index]
    if not .05<w<.95:continue
    ns=[e.other_vert(v) for e in v.link_edges]
    if ns:updates[v]=v.co.lerp(sum((n.co for n in ns),Vector())/len(ns),.12*w*(1-w))
   for v,p in updates.items():v.co=p
  delta=[(v.co-old[i]).length for i,v in enumerate(bm.verts)];middle=[i for i,w in enumerate(weights) if w==0]
  assert max((delta[i] for i in middle),default=0)<1e-9
  metrics=[]
  for end,indices in enumerate(terminal):
   tr=trs[assigned[end]];before=[];after=[];signed=[]
   for i in indices:
    before.append(tr.find_nearest(old[i])[3]*1000);q,n,_,d=tr.find_nearest(bm.verts[i].co);after.append(d*1000);signed.append((bm.verts[i].co-q).dot(n)*1000)
   metrics.append({'bone':assigned[end],'vertices':len(indices),'before_median_surface_distance_mm':round(float(np.median(before)),4) if before else None,'after_max_surface_distance_mm':round(max(after,default=0),4),'signed_depth_min_mm':round(min(signed,default=0),4),'signed_depth_max_mm':round(max(signed,default=0),4)})
  bm.to_mesh(me);bm.free();ob.data=me
  for f in me.polygons:f.use_smooth=True
  ob['attachment_display']='local shallow embedding, not measured enthesis';ob['source_base']=scope+'-review-unified.blend'
  result={'id':r['id'],'status':'fitted','assigned_bones':assigned,'terminal_metrics':metrics,'source_longitudinal_terminal_zone_fraction':.25,'terminal_embed_nominal_mm':.25,'max_vertex_displacement_mm':round(max(delta)*1000,4),'central_region_max_displacement_mm':0,'source_points_over_6mm_not_moved':clipped,'footprint_review':'pending; source endpoint regions, not certified anatomical footprints'};results.append(result)
  note='仅源端部区域顺应指定骨面，末端约 0.18–0.32 mm 浅嵌入并渐变衔接，中间段位置不变。嵌入为显示处理，不是组织学深度；具体足印仍待核准。'
  a=next(x for x in aud if x['id']==r['id']);a.update(contact_display_note=note,surface_displacement_max_mm=result['max_vertex_displacement_mm'],boundary_preserved=False,end_candidates=[],contact_metrics=metrics,audit_scope='attachment_fit_terminal_distances_only',suspected_penetration_nearest_normal_only={})
  r['comparison']=note;r['geometry_revision']='local-attachment-display-v1'
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(P/(scope+'-review-contact.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/(scope+'-review-contact.blend')),compress=True)
 for filename,data in [('attachment-contact-report.json',results),('geometry-audit-contact.json',aud),('catalog.json',cat)]: (P/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 cfg=json.loads((P/'review-config.json').read_text());cfg.update(model=scope+'-review-contact.glb',audit='geometry-audit-contact.json',loadedLabel='端部贴合显示版 · 足印待核准');(P/'review-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
 print(scope,'fitted',sum(x['status']=='fitted' for x in results),'unchanged',sum(x['status']=='unchanged' for x in results),flush=True)
 print(json.dumps([x for x in results if x['status']=='fitted'],ensure_ascii=False),flush=True)
