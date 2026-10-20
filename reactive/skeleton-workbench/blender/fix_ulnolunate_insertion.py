"""Targeted bilateral distal attachment correction; footprint remains a review candidate.
Reads v1, writes v2, never modifies the source dataset or v1 assets.
"""
import bpy,bmesh,json,ast
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[1];O=W/'z-anatomy-candidate';Q=W/'qa/ligament-fit-v1'
# Reuse the parity-based bone sampling checks without executing the batch builder.
module=ast.parse((W/'blender/refine_wrist_ligaments.py').read_text())
for node in module.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['tree_from_mesh','nearest','inside','audit']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<audit helpers>','exec'))
bpy.ops.wm.open_mainfile(filepath=str(O/'assets/wrist-ligaments-refined.blend'))
sc=bpy.context.scene;report=[]
for side,old,prox in [('L',(.2618985,-.0159537,.8575558),(.2430745,-.02066,.876104)),('R',(-.2624111,-.0203373,.8571093),(-.2433306,-.017023,.875696))]:
 obj=sc.objects['z_lig_ulnolunate_ligament_'+side];matrix=obj.matrix_world.copy();inv=matrix.inverted();bones={}
 for b in sc.objects:
  if b.name.startswith('reference_') and b.name.endswith('.'+side.lower()):
   me=b.data.copy();me.transform(b.matrix_world);bones[b.name]=tree_from_mesh(me)
 lun=bones['reference_Lunate bone.'+side.lower()];old=Vector(old);prox=Vector(prox);axis=old-prox
 # Choose a palmar-surface candidate centrally within this model's lunate,
 # then require the whole distal band to contact that named bone only.
 target=(lun[1]+lun[2])*.5;target.z+=.0015
 def palm(v,t,clearance=.00010):
  origin=Vector((v.x,t[1].y-.02,v.z));hit,n,i,d=t[0].ray_cast(origin,Vector((0,1,0)))
  if hit is None:raise RuntimeError('Distal patch missed lunate palmar surface')
  return hit+Vector((0,-clearance,0))
 target=palm(target,lun);delta=target-old;ends=[]
 # Original source rail coordinates captured before refinement, in world metres.
 source_rails={
 'L':[(.260000855,-.015633464,.857895315),(.263796180,-.016273994,.857216239),(.246584356,-.024550904,.865975380),(.250410795,-.023957949,.870136797),(.241203576,-.020618631,.873648703),(.244945481,-.020701546,.878559589),(.255876362,-.018201154,.859476447),(.259562641,-.018555228,.860869229),(.243379444,-.023340272,.870273054),(.246680677,-.022222111,.875916362)],
 'R':[(-.260618716,-.019586353,.857315004),(-.264203578,-.021088252,.856903613),(-.245846719,-.023686595,.866790533),(-.249781594,-.022934146,.870823085),(-.241464809,-.017168531,.873241127),(-.245196402,-.016877567,.878151894),(-.256097049,-.020882824,.859309494),(-.259664416,-.021626651,.860850453),(-.243010670,-.020945963,.870618463),(-.246557310,-.019258387,.875963390)]}
 rv=list(map(Vector,source_rails[side]))
 pairs=[(4,5),(8,9),(2,3),(6,7),(0,1)]
 rails=[[rv[p[j]].copy() for p in pairs] for j in range(2)]
 across=(rv[1]-rv[0]).normalized()
 for j in range(2):
  rails[j][-1]=target+across*((j-.5)*.0034)
  rails[j][-2]=rails[j][-1].lerp(rails[j][2],.5)
 def curve(points,t):
  z=t*4;i=min(int(z),3);u=z-i;a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(i+2,4)]
  return (2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)*.5
 verts=[];faces=[]
 for i in range(81):
  t=i/80;left=curve(rails[0],t);right=curve(rails[1],t)
  for j in range(13):
   p=left.lerp(right,j/12)
   if t>.72:
    hit=lun[0].ray_cast(Vector((p.x,lun[1].y-.02,p.z)),Vector((0,1,0)))[0]
    if hit is None:
     if t>.9:raise RuntimeError(str((side,t,list(p),list(target),[list(x) for x in rails[0]])))
     hit=p.copy()
    else:hit+=Vector((0,-.0002,0))
    w=min(1,(t-.72)/.18);w=w*w*(3-2*w);p=p.lerp(hit,w)
   for _ in range(4):
    for name,tree in bones.items():
     if inside(p,tree):p=palm(p,tree,.00020)
   verts.append(inv@p)
   if t>.94:ends.append(p.copy())
   if i and j:
    n=i*13+j;faces.append((n-14,n-13,n,n-1))
 mesh=bpy.data.meshes.new('Ulnolunate continuous lunate attachment '+side);mesh.from_pydata(verts,[],faces);mesh.update();obj.data=mesh
 for f in mesh.polygons:f.use_smooth=True
 mod=obj.modifiers.new('Thin ligament sheet','SOLIDIFY');mod.thickness=.00012;mod.offset=0
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();final=bpy.data.meshes.new_from_object(obj.evaluated_get(dg));obj.modifiers.clear();obj.data=final
 obj.data.update();bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 me=obj.data.copy();me.transform(matrix);collisions=audit(me,bones)
 distances={name:{'min_mm':round(min(nearest(p,t)[3] for p in ends)*1000,3),'max_mm':round(max(nearest(p,t)[3] for p in ends)*1000,3)} for name,t in bones.items() if 'Lunate' in name or 'Scaphoid' in name}
 if collisions:raise RuntimeError(str(collisions))
 if distances['reference_Lunate bone.'+side.lower()]['max_mm']>.3:raise RuntimeError('End patch is not attached to lunate')
 obj['geometry_review']='Distal patch rerouted to lunate palmar surface; exact footprint and proximal origin pending review'
 report.append({'id':obj.name,'distal_patch_samples':len(ends),'distances':distances,'bone_penetration_over_0_15mm':collisions,'anatomy_review':'pending'})
bpy.ops.object.select_all(action='DESELECT')
objects=[o for o in sc.objects if o.name.startswith('z_lig_')]
assert len(objects)==61
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'assets/wrist-ligaments-refined-v2.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'assets/wrist-ligaments-refined-v2.blend'),compress=True)
data=json.loads((O/'wrist-ligaments-refined.json').read_text());data['file']='z-anatomy-candidate/assets/wrist-ligaments-refined-v2.glb'
for row in data['objects']:
 if row['id'].startswith('z_lig_ulnolunate_ligament_'):
  row['triangles']=sum(len(f.vertices)-2 for f in sc.objects[row['id']].data.polygons);row['geometry_revision']='ulnolunate-lunate-palmar-v2';row['note']='已将远端从舟骨侧改至月骨掌侧并检查静态骨面穿插；精确附着足印及近端起始区仍待解剖复核。';row['anatomy_review']='pending'
(O/'wrist-ligaments-refined.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(Q/'ulnolunate-insertion-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
