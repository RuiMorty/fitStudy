"""Right capitohamate local assembly candidate. Source footprint not certified.
Rebuild the original four-corner sheet between named bones, preserve other objects.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'wrist-review.blend'))
scene=bpy.context.scene;id='z_lig_capitohamate_interosseous_ligament_R';ob=scene.objects[id+'__refined']
def tree(bone):
 bm=bmesh.new();bm.from_mesh(scene.objects['bone_'+bone+'_r'].data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 t=BVHTree.FromBMesh(bm);bm.free();return t
trees={n:tree(n) for n in ['Capitate','Hamate']}
raw=[Vector(p) for p in [[-.2599950432777405,-.015967559069395065,.8423984050750732],[-.25803953409194946,-.016751926392316818,.8422890305519104],[-.25958824157714844,-.012175648473203182,.8424201607704163],[-.2576327323913574,-.012960013933479786,.8423107862472534]]]
# Assign only between the two known source-side rails; no arbitrary nearest bone search.
rails=[[raw[0],raw[2]],[raw[1],raw[3]]]
options=[['Capitate','Hamate'],['Hamate','Capitate']]
assignment=min(options,key=lambda ns:sum(trees[n].find_nearest(p)[3] for n,rail in zip(ns,rails) for p in rail))
N=32;M=32;verts=[];faces=[];weights=[];ends=[[],[]]
for i in range(N+1):
 t=i/N
 for j in range(M+1):
  v=j/M;a=rails[0][0].lerp(rails[0][1],v);b=rails[1][0].lerp(rails[1][1],v)
  pa,na,_,da=trees[assignment[0]].find_nearest(a);pb,nb,_,db=trees[assignment[1]].find_nearest(b)
  a=pa+na*.000035;b=pb+nb*.000035;p=a.lerp(b,t)
  if i==0:ends[0].append(p.copy())
  if i==N:ends[1].append(p.copy())
  # Resolve only local surface incursions, never pull the whole sheet onto a bone.
  if i not in [0,N]:
   for _ in range(4):
    for tr in trees.values():
     q,n,_,d=tr.find_nearest(p)
     if (p-q).dot(n)<0 and d<.002:p=q+n*.000035
  verts.append(p);weights.append(.15+.85*math.sin(math.pi*t))
for i in range(N):
 for j in range(M):
  a=i*(M+1)+j;faces.append((a,a+M+1,a+M+2,a+1))
me=bpy.data.meshes.new('Capitohamate right source-rail fit');me.from_pydata(verts,[],faces);me.update()
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
uv=me.uv_layers.new(name='Illustrative longitudinal')
for l in me.loops:
 i,j=divmod(l.vertex_index,M+1);uv.data[l.index].uv=(j/M*2,i/N)
work=bpy.data.objects.new('Right capitohamate editable fitted surface',me);scene.collection.objects.link(work)
vg=work.vertex_groups.new(name='Thin contact taper')
for i,w in enumerate(weights):vg.add([i],w,'REPLACE')
mod=work.modifiers.new('Display thickness 0.06mm','SOLIDIFY');mod.thickness=.00006;mod.offset=0;mod.vertex_group=vg.name;mod.thickness_vertex_group=0
bpy.context.view_layer.update();final=bpy.data.meshes.new_from_object(work.evaluated_get(bpy.context.evaluated_depsgraph_get()))
for m in ob.data.materials:final.materials.append(m)
for f in final.polygons:f.use_smooth=True
ob.data=final
scene.collection.objects.unlink(work);next(s for s in bpy.data.scenes if s!=scene).collection.objects.link(work)
metrics={n:{'terminal_vertices':len(ps),'max_surface_distance_mm':round(max(trees[n].find_nearest(p)[3] for p in ps)*1000,4)} for n,ps in zip(assignment,ends)}
flags={}
for n,tr in trees.items():
 ds=[]
 final.calc_loop_triangles();samples=[v.co for v in final.vertices]+[sum((final.vertices[k].co for k in f.vertices),Vector())/3 for f in final.loop_triangles]
 for p in samples:
  q,no,_,d=tr.find_nearest(p)
  if (p-q).dot(no)<0 and d>.0001:ds.append(d*1000)
 if ds:flags[n]={'samples':len(ds),'max_depth_mm':round(max(ds),4)}
report=json.loads((P/'geometry-audit.json').read_text());a=next(x for x in report if x['id']==id)
a.update(contact_display_note='仅此右侧对象按源四角边界重新拟合：两端分别贴向头状骨与钩骨，减薄端缘；端区仍是源位置候选，不代表精确解剖足印已核准。',surface_displacement_max_mm=0,end_candidates=[],suspected_penetration_nearest_normal_only=flags,audit_scope='local_vertex_and_triangle_centroid_nearest_normal_screen',contact_metrics=metrics)
# Do not invent displacement correspondence after rebuilding topology.
a['contact_display_note']+=' 本次重建拓扑，不提供无对应关系的逐顶点位移值。';a['surface_displacement_max_mm']=None
for o in scene.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'wrist-review-contact.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'wrist-review-contact.blend'),compress=True)
(P/'geometry-audit-contact.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(P/'capitohamate-contact-check.json').write_text(json.dumps({'source_rails':[[list(p) for p in r] for r in rails],'rail_assignment':assignment,'contacts':metrics,'screening':flags,'scope':'right_only; source-based assembly candidate, footprint unverified'},ensure_ascii=False,indent=2)+'\n')
print('CONTACT_CHECK',json.dumps({'assignment':assignment,'contacts':metrics,'screening':flags}),flush=True)
