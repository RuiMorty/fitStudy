"""Source-constrained assembly candidates; anatomical footprints remain pending.
Retains original assets. Annular endpoints use source terminal columns. UCL
keeps only the medial humeroulnar strip; uncertain radial extension is excluded.
"""
import bpy,bmesh,json,math,runpy,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'elbow-review.blend'))
scene=bpy.data.scenes['Elbow review'];source_scene=next(s for s in bpy.data.scenes if s!=scene)
bpy.context.window.scene=source_scene;bpy.context.view_layer.update()
raw={}
for side in ['R','L']:
 for name in ['Annular ligament of radius','Ulnar collateral ligament']:
  o=bpy.data.objects[name+'.'+side.lower()];raw[(name,side)]=[o.matrix_world@v.co for v in o.data.vertices]
bpy.context.window.scene=scene
report=json.loads((P/'geometry-audit.json').read_text());checks=[]
def tree(name):
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 t=BVHTree.FromBMesh(bm);bm.free();return t
def cubic(points,u):
 i=min(int(u),len(points)-2);t=u-i;p1=points[i];p2=points[i+1];p0=points[max(0,i-1)];p3=points[min(len(points)-1,i+2)]
 return .5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def make(id,columns,supports,kind):
 nu=(len(columns)-1)*12;nv=16;verts=[];weights=[];baseline=[]
 for i in range(nu+1):
  u=i/nu*(len(columns)-1)
  for j in range(nv+1):
   v=j/nv*(len(columns[0])-1)
   p=cubic([cubic(col,v) for col in columns],u)
   baseline.append(p.copy());w0=smooth(1-u/1.5);w1=smooth(1-(len(columns)-1-u)/1.5)
   w=max(w0,w1);tr=supports[0 if w0>=w1 else 1]
   if w:
    q,n,_,_=tr.find_nearest(p);p=p.lerp(q+n*.00004,w)
   verts.append(p);weights.append((w0,w1))
 faces=[]
 for i in range(nu):
  for j in range(nv):
   a=i*(nv+1)+j;faces.append((a,a+nv+1,a+nv+2,a+1))
 # Restrained smoothing of transition, endpoints remain constrained to their bone.
 for _ in range(12):
  new=list(verts)
  for i in range(1,nu):
   for j in range(1,nv):
    k=i*(nv+1)+j;w=max(weights[k])
    if w:new[k]=verts[k].lerp((verts[k-1]+verts[k+1]+verts[k-nv-1]+verts[k+nv+1])/4,.25*w)
  verts=new
 # Keep source-positioned terminal attachment rows on named support surfaces.
 for i,tr in [(0,supports[0]),(nu,supports[1])]:
  for j in range(nv+1):
   k=i*(nv+1)+j;q,n,_,_=tr.find_nearest(verts[k]);verts[k]=q+n*.00004
 me=bpy.data.meshes.new(id+' assembly surface');me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 uv=me.uv_layers.new(name='Longitudinal illustration')
 for l in me.loops:
  i,j=divmod(l.vertex_index,nv+1);uv.data[l.index].uv=(j/nv*8,i/nu*4)
 work=bpy.data.objects.new('Assembly construction '+id,me);source_scene.collection.objects.link(work)
 vg=work.vertex_groups.new(name='Assembly edge taper')
 for k in range(len(verts)):
  i,j=divmod(k,nv+1);w=max(weights[k]);edge=math.sin(math.pi*j/nv)**.4
  vg.add([k],max(.08,(.25+.75*edge)*(1-.85*w)),'REPLACE')
 mod=work.modifiers.new('Illustrative thickness','SOLIDIFY');mod.thickness=.00045;mod.offset=0;mod.vertex_group=vg.name;mod.thickness_vertex_group=0
 # Ring construction is reused as the support surface by the RCL refinement step.
 if kind=='annular':
  old=bpy.data.objects['construction_'+id];old.data=me.copy()
  for k in range(len(verts)):old.vertex_groups[0].add([k],vg.weight(k),'REPLACE')
 bpy.context.window.scene=source_scene;bpy.context.view_layer.update();ev=work.evaluated_get(bpy.context.evaluated_depsgraph_get());final=bpy.data.meshes.new_from_object(ev);bpy.context.window.scene=scene
 ob=bpy.data.objects[id+'__refined'];final.materials.clear()
 for mat in ob.data.materials:final.materials.append(mat)
 for f in final.polygons:f.use_smooth=True
 ob.data=final
 metrics=[]
 for row,tr in [(0,supports[0]),(nu,supports[1])]:
  points=verts[row*(nv+1):(row+1)*(nv+1)]
  metrics.append({'center_web_m':[sum(p.x for p in points)/len(points),sum(p.z for p in points)/len(points),-sum(p.y for p in points)/len(points)],'max_distance_mm':round(max(tr.find_nearest(p)[3] for p in points)*1000,4)})
 flags={}
 for bone in ['Humerus','Ulna','Radius']:
  tr=tree('bone_'+bone+'_'+id[-1].lower());depth=[]
  for v in final.vertices:
   q,n,_,d=tr.find_nearest(v.co)
   if (v.co-q).dot(n)<0 and d>.0005:depth.append(d*1000)
  if depth:flags[bone]={'samples':len(depth),'max_depth_mm':round(max(depth),2)}
 a=next(x for x in report if x['id']==id);a.update(boundary_preserved=False,end_candidates=[],surface_displacement_max_mm=round(max((p-b).length for p,b in zip(verts,baseline))*1000,3),contact_metrics=metrics,suspected_penetration_nearest_normal_only=flags)
 a['contact_display_note']=('依据源网格两端修整：前、后端分别贴合尺骨；中间保留绕桡骨的走行。附着范围仍为候选，未通过解剖验收。' if kind=='annular' else '仅保留源网格肱尺侧候选带；向桡骨延伸的未确认表面不纳入显示。两端分别贴合肱骨与尺骨，未重建完整前、后、横三束，不能当作完整尺侧副韧带复合体。')
 checks.append({'id':id,'contacts':metrics,'screening':flags})
for side in ['R','L']:
 ulna=tree('bone_Ulna_'+side.lower());hum=tree('bone_Humerus_'+side.lower())
 vs=raw[('Annular ligament of radius',side)]
 indices=[[2,17,3],[4,18,5],[6,19,7],[8,20,9],[24,26,25],[10,21,11],[12,22,13],[27,29,28],[0,16,1],[14,23,15]]
 make('ligament_annular_radius_'+side,[[vs[i] for i in col] for col in indices],[ulna,ulna],'annular')
 vs=raw[('Ulnar collateral ligament',side)]
 make('z_lig_ulnar_collateral_ligament_'+side,[[vs[i] for i in col] for col in [[3,2],[6,7],[0,1],[4,5]]],[hum,ulna],'ucl')
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(P/'elbow-review-assembly-base.blend'),compress=True)
(P/'geometry-audit-assembly-base.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(P/'assembly-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
os.environ['ELBOW_BASE']='elbow-review-assembly-base';os.environ['ELBOW_OUTPUT']='elbow-review-assembly';os.environ['ELBOW_AUDIT_BASE']='geometry-audit-assembly-base';os.environ['ELBOW_AUDIT_OUTPUT']='geometry-audit-assembly'
runpy.run_path(str(P/'refine_contact.py'),run_name='__main__')
print('ASSEMBLY_CHECKS',json.dumps(checks),flush=True)
