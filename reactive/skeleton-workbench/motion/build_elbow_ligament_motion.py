"""Display deformation from existing reviewed meshes; no new anatomical footprints claimed."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent.parent
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.open_mainfile(filepath=str(P/'elbow-review/elbow-review-assembly.blend'))
s=bpy.context.scene;axisdata=json.loads((P/'motion/elbow-axis.json').read_text());reports=[];deforms=[]
def cv(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
 bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 tr=BVHTree.FromBMesh(bm);bm.free();return tr
for side in ['R','L']:
 spec=axisdata['sides'][side];pivot=cv(spec['pivot']);axis=cv(spec['axis']);low=side.lower()
 hum=s.objects['bone_Humerus_'+low];ulna=s.objects['bone_Ulna_'+low];radius=s.objects['bone_Radius_'+low];ring=s.objects['ligament_annular_radius_'+side+'__refined'];ht,ut,rt,at=map(tree,[hum,ulna,radius,ring])
 for prefix,distal in [('z_lig_ulnar_collateral_ligament_',ut),('z_lig_radial_collateral_ligament_',at)]:
  ident=prefix+side;src=s.objects[ident+'__refined'];me=src.data.copy();me.transform(src.matrix_world);o=bpy.data.objects.new(ident,me);s.collection.objects.link(o);deforms.append(o)
  xyz=np.array([v.co[:] for v in me.vertices]);dp=np.array([ht.find_nearest(Vector(p))[3] for p in xyz]);dd=np.array([distal.find_nearest(Vector(p))[3] for p in xyz]);prox=(dp<=.0008)&(dp<dd);dist=(dd<=.0008)&(dd<dp)
  if prox.sum()<8 or dist.sum()<8:raise RuntimeError('Insufficient attachment candidates '+ident)
  weights=dp/np.maximum(dp+dd,1e-9);weights[prox]=0;weights[dist]=1
  edges=np.array([tuple(e.vertices) for e in me.edges]);ia=np.concatenate([edges[:,0],edges[:,1]]);ib=np.concatenate([edges[:,1],edges[:,0]]);degree=np.bincount(ia,minlength=len(xyz))
  for _ in range(1200):
   avg=np.bincount(ia,weights=weights[ib],minlength=len(xyz))/np.maximum(degree,1);weights=.3*weights+.7*avg;weights[prox]=0;weights[dist]=1
  # Store actual fixed vertex sets; nearest surfaces identify candidates only.
  attr=me.attributes.new(name='_motion_weight',type='FLOAT',domain='POINT');attr.data.foreach_set('value',weights.astype(np.float32))
  for label,mask in [('Humerus attachment candidate',prox),('Distal attachment candidate',dist)]:
   vg=o.vertex_groups.new(name=label);vg.add(np.flatnonzero(mask).tolist(),1,'REPLACE')
  o.shape_key_add(name='Rest');poses=[];maxpush=0
  for angle in range(5,121,5):
   q=Quaternion(axis,math.radians(angle));qi=q.inverted();positions=[];flags=0
   for i,p0 in enumerate(xyz):
    p=Quaternion(axis,math.radians(angle*weights[i]))@(Vector(p0)-pivot)+pivot
    # Free span only: cap corrective displacement, preserve both attached regions exactly.
    if not prox[i] and not dist[i]:
     start=p.copy()
     for _ in range(3):
      for tr,moving in [(ht,False),(ut,True),(rt,True)]:
       local=qi@(p-pivot)+pivot if moving else p
       near,n,_,d=tr.find_nearest(local)
       if d<.006 and (local-near).dot(n)<-.00012:
        corrected=near+n*.00005
        p=q@(corrected-pivot)+pivot if moving else corrected
     change=p-start
     if change.length>.0025:p=start+change.normalized()*.0025
     maxpush=max(maxpush,(p-start).length)
    positions.append(p)
   key=o.shape_key_add(name='Flex_'+str(angle));key.data.foreach_set('co',np.array(positions,dtype=np.float32).ravel())
   # Editable keyed poses; interpolation is for display, not a material law.
   key.value=0;key.keyframe_insert('value',frame=1);key.keyframe_insert('value',frame=max(1,angle-4));key.value=1;key.keyframe_insert('value',frame=angle+1);key.value=0;key.keyframe_insert('value',frame=angle+6)
   # Count only free-span samples deeper than 0.5mm; normal-sign screen is not full collision proof.
   maxanchor=0
   for i,p in enumerate(positions):
    target=q@(Vector(xyz[i])-pivot)+pivot if dist[i] else Vector(xyz[i])
    if prox[i] or dist[i]:maxanchor=max(maxanchor,(p-target).length)
    else:
     for tr,moving in [(ht,False),(ut,True),(rt,True)]:
      local=qi@(p-pivot)+pivot if moving else p;near,n,_,d=tr.find_nearest(local)
      if .0005<d<.006 and (local-near).dot(n)<0:flags+=1
   poses.append({'degrees':angle,'anchor_error_mm':maxanchor*1000,'free_span_deep_samples_nearest_normal':flags})
  reports.append({'id':ident,'proximal_anchor_vertices':int(prox.sum()),'distal_anchor_vertices':int(dist.sum()),'vertices':len(xyz),'max_free_span_correction_mm':maxpush*1000,'poses':poses,'status':'geometric_attachment_candidates_not_confirmed_anatomical_footprints'})
# Export only 4 deformable derivatives; annular and quadrate use exact rigid transport.
s.frame_set(1)
for o in list(s.objects):o.select_set(False)
for o in deforms:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'motion/elbow-ligaments-motion.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_attributes=True,export_animations=False,export_extras=True)
# Keep a clean editable source scene containing the four meshes and source reference bones.
rigid_references=set()
for side in ['R','L']:
 spec=axisdata['sides'][side];pivot=cv(spec['pivot']);axis=cv(spec['axis'])
 for name in ['bone_Ulna_'+side.lower(),'bone_Radius_'+side.lower(),'ligament_annular_radius_'+side+'__refined','z_lig_quadrate_ligament_'+side+'__refined']:
  ob=s.objects[name];rest=ob.matrix_world.copy();ob.rotation_mode='QUATERNION';rigid_references.add(ob)
  for angle in range(0,121,5):
   q=Quaternion(axis,math.radians(angle));ob.matrix_world=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)@rest
   ob.keyframe_insert('location',frame=angle+1);ob.keyframe_insert('rotation_quaternion',frame=angle+1)
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for slot in action.slots:
    bag=strip.channelbag(slot)
    if bag:
     for curve in bag.fcurves:
      for point in curve.keyframe_points:point.interpolation='LINEAR'
s.frame_set(1)
keep=set(deforms)|rigid_references|{o for o in s.objects if o.name.startswith('bone_')}
for o in list(s.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for other in list(bpy.data.scenes):
 if other!=s:bpy.data.scenes.remove(other)
s.frame_start=1;s.frame_end=121;bpy.data.orphans_purge(do_recursive=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'motion/elbow-ligaments-motion.blend'),compress=True)
(P/'motion/ligament-deformation-audit.json').write_text(json.dumps({'method':'Harmonic weight field between source-contact candidates; weighted rotation; bounded free-span bone clearance correction.','frames_degrees':list(range(0,121,5)),'reports':reports},ensure_ascii=False,indent=2)+'\n')
print([(r['id'],max(p['free_span_deep_samples_nearest_normal'] for p in r['poses']),r['max_free_span_correction_mm']) for r in reports],flush=True)
