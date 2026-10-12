"""BodyParts3D-derived elbow studio. CC BY-SA 2.1 Japan geometry.
Retains anatomical surfaces; separates tendon regions; adds editable sampled cage deformation.
"""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];P=json.loads((ROOT/'sources/provenance.json').read_text());D=json.loads((ROOT/'data/structures.json').read_text());S={s['id']:s for s in D['structures']}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30;scene.frame_start=1;scene.frame_end=121
bpy.context.preferences.filepaths.save_version=0
rootcol=bpy.context.collection;rootcol.name='ELBOW_STUDIO_R'
cols={}
for name in ['01_Bones','02_Superficial_muscles','03_Deep_muscles','04_Tendons','05_Fascia','06_Attachments','07_Rig']:
 c=bpy.data.collections.new(name);rootcol.children.link(c);cols[name]=c
def put(o,col):
 for c in list(o.users_collection):c.objects.unlink(o)
 cols[col].objects.link(o)
def empty(name,pos,parent=None,col='07_Rig'):
 o=bpy.data.objects.new(name,None);cols[col].objects.link(o);o.location=pos;o.parent=parent;o.empty_display_type='SPHERE';o.empty_display_size=.0018;return o
upper=empty('rig_upper_R',(0,0,0));forearm=empty('joint_elbow_R',(0,0,0),upper)
forearm.rotation_mode='XYZ'
for a in range(0,121,5):forearm.rotation_euler.x=math.radians(a);forearm.keyframe_insert('rotation_euler',frame=a+1)
# Work in rest space until animation is complete.
scene.frame_set(1)
transform=Matrix.Rotation(.215,3,'Y');pivot=Vector((-215,-67,1055))
objects={};full={};profiles={}
for id,entry in P['structures'].items():
 bpy.ops.wm.stl_import(filepath=str(ROOT/'sources'/entry['file']));o=bpy.context.object;o.name=id
 for v in o.data.vertices:
  q=(v.co-pivot)*.001;v.co=transform@Vector((-q.x,-q.y,q.z))
 # STL carries per-face discontinuities; recompute smooth shared normals.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for poly in o.data.polygons:poly.use_smooth=True
 # Conservative relaxation removes digitization ripple without replacing anatomy by primitives.
 bpy.context.view_layer.objects.active=o
 sm=o.modifiers.new('Scan surface relaxation','SMOOTH');sm.factor=.45;sm.iterations=3 if id.startswith('muscle') else 2;bpy.ops.object.modifier_apply(modifier=sm.name)
 de=o.modifiers.new('Web anatomical LOD','DECIMATE');de.ratio=.26 if id.startswith('muscle') else (.24 if 'scapula' in id else .72);bpy.ops.object.modifier_apply(modifier=de.name)
 for poly in o.data.polygons:poly.use_smooth=True
 objects[id]=o
 if id.startswith('muscle'):
  full[id]=np.array([v.co[:] for v in o.data.vertices]);arr=full[id];zlo,zhi=arr[:,2].min(),arr[:,2].max();zs=np.linspace(zlo,zhi,60);centers=[]
  for z in zs:
   near=arr[np.abs(arr[:,2]-z)<.006]
   if not len(near):near=arr[np.argsort(np.abs(arr[:,2]-z))[:12]]
   centers.append(near.mean(0))
  profiles[id]=(zs,np.array(centers))
# Bone surfaces define visible anchor points; these are design regions, not measured footprints.
def nearest(bone,p):
 o=objects[bone];tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]);return tree.find_nearest(Vector(p))[0]
ATT={}
for id,arr in full.items():
 s=S[id];top=arr[arr[:,2]>np.quantile(arr[:,2],.995)].mean(0);bottom=arr[arr[:,2]<np.quantile(arr[:,2],.005)].mean(0)
 origin=nearest(s['bones'][0],top);insertion=nearest(s['bones'][1],bottom)
 # Both biceps heads share the radial attachment; the short head does not terminate on humerus.
 ATT[id]=[np.array(origin),np.array(insertion)]
ATT['muscle_biceps_short_R'][1]=ATT['muscle_biceps_long_R'][1].copy()
# Common triceps insertion is the mean projected footprint on the olecranon.
ulna=objects['bone_ulna_R'];utree=BVHTree.FromPolygons([v.co for v in ulna.data.vertices],[list(p.vertices) for p in ulna.data.polygons]);candidates=np.concatenate([full['muscle_triceps_'+k+'_R'] for k in ['long','lateral','medial']]);candidates=candidates[candidates[:,2]<-.003];contact=min((utree.find_nearest(Vector(p)) for p in candidates),key=lambda hit:hit[3]);common=contact[0]
for k in ['long','lateral','medial']:ATT['muscle_triceps_'+k+'_R'][1]=np.array(common)
# Cut source surfaces into independent tendon regions. A shared cut plane preserves matching seams.
def section(o,name,zmin=None,zmax=None):
 dup=o.copy();dup.data=o.data.copy();rootcol.objects.link(dup);dup.name=name
 bm=bmesh.new();bm.from_mesh(dup.data)
 for z,above in [(zmin,True),(zmax,False)]:
  if z is None:continue
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.0000001,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=above,clear_outer=not above)
 edges=[e for e in bm.edges if e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(dup.data);bm.free()
 for p in dup.data.polygons:p.use_smooth=True
 return dup
cuts={'biceps_long':(.026,.224),'biceps_short':(None,.235),'brachialis':(-.012,None),'triceps_long':(.023,.243),'triceps_lateral':(.023,None),'triceps_medial':(.023,None)}
mapping={};tendonparts={}
for id,src in list(objects.items()):
 if not id.startswith('muscle'):continue
 key=S[id]['key'];lo,hi=cuts[key];body=section(src,id+'_body',lo,hi);bpy.data.objects.remove(src,do_unlink=True);body.name=id;objects[id]=body;mapping[id]=id
 # Source geometry snapshot retained via a temporary reconstruction mesh for cuts.
 entry=P['structures'][id]
 # use pre-cut saved copy from body's original mesh is unavailable; recreate original cleaned topology from stored data cache below.
# Re-import source tendon surfaces and use the same transform/relaxation. Larger coverage at seams avoids holes.
for id,entry in P['structures'].items():
 if not id.startswith('muscle'):continue
 bpy.ops.wm.stl_import(filepath=str(ROOT/'sources'/entry['file']));src=bpy.context.object
 for v in src.data.vertices:
  q=(v.co-pivot)*.001;v.co=transform@Vector((-q.x,-q.y,q.z))
 bm=bmesh.new();bm.from_mesh(src.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015);bm.to_mesh(src.data);bm.free();bpy.context.view_layer.objects.active=src
 sm=src.modifiers.new('Tendon surface relaxation','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
 de=src.modifiers.new('Tendon LOD','DECIMATE');de.ratio=.26;bpy.ops.object.modifier_apply(modifier=de.name)
 key=S[id]['key'];lo,hi=cuts[key]
 if key in ['biceps_long','biceps_short','triceps_long']:
  tid='tendon_'+key+'_prox_R';t=section(src,tid,hi,None);objects[tid]=t;mapping[tid]=id
 if key in ['biceps_long','brachialis']:
  tid='tendon_'+('biceps' if key=='biceps_long' else key)+'_distal_R';t=section(src,tid,None,lo);objects[tid]=t;mapping[tid]=id
 if key.startswith('triceps'):
  t=section(src,'triceps_tendon_part_'+key,None,lo);tendonparts[key]=t
 bpy.data.objects.remove(src,do_unlink=True)
# Combine the anatomical triceps tendon sheets as one selectable, editable object.
bpy.ops.object.select_all(action='DESELECT')
for o in tendonparts.values():o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(tendonparts.values()));bpy.ops.object.join();t=bpy.context.object;t.name='tendon_triceps_distal_R';objects[t.name]=t;mapping[t.name]='muscle_triceps_long_R'
# PBR textures: fine fibre direction in UV space, plus low-frequency variation, no printed imagery.
def make_image(name,arr):
 h,w=arr.shape[:2];im=bpy.data.images.new(name,width=w,height=h,alpha=True);im.pixels.foreach_set(arr.astype('float32').ravel());im.filepath_raw=str(ROOT/'assets'/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
size=1024;y,x=np.mgrid[0:size,0:size]/size
rng=np.random.default_rng(711);noise=rng.random((size,size));phase=x*2*np.pi*100+1.8*np.sin(y*14+x*12)+.7*np.sin(y*41+x*5)
fib=.5+.5*np.sin(phase);fine=.5+.5*np.sin(phase*2.93+y*24);broad=.5+.5*np.sin(x*14+y*5)
height=.62*fib+.22*fine+.10*noise+.06*broad
normal=np.dstack((-np.gradient(height,axis=1)*3.2,-np.gradient(height,axis=0)*3.2,np.ones_like(x)));normal/=np.linalg.norm(normal,axis=2,keepdims=True);rgba=np.dstack((normal*.5+.5,np.ones_like(x)));normalimg=make_image('muscle-fibre-normal',rgba);normalimg.colorspace_settings.name='Non-Color'
# Color follows fibre ridges; desaturated connective tissue at the transition margins.
shade=.68+.19*fib+.10*broad+.03*noise
rgb=np.dstack((.56*shade,.17*shade,.12*shade));
# A narrow irregular collagen transition softens the cut between belly and tendon.
edge=np.clip((.032+.011*np.sin(x*41)+.006*np.sin(x*113)-np.minimum(y,1-y))/.04,0,1);edge=edge*edge*(3-2*edge);rgb=rgb*(1-edge[:,:,None])+np.array([.69,.62,.49])[None,None,:]*edge[:,:,None]
baseimg=make_image('muscle-fibre-color',np.dstack((rgb,np.ones_like(x))))
roughimg=make_image('muscle-fibre-roughness',np.dstack([.45+.15*(1-fib)]*3+[np.ones_like(x)]));roughimg.colorspace_settings.name='Non-Color'
# Tendon collagen uses a finer, lower-contrast normal pattern.
tendonimg=make_image('tendon-collagen-normal',np.dstack((normal*.20+.5,np.ones_like(x))));tendonimg.colorspace_settings.name='Non-Color'
def material(name,color,rough=.5,texture=False,tendon=False,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,alpha);nodes=m.node_tree.nodes;links=m.node_tree.links
 p=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:p=nodes.new('ShaderNodeBsdfPrincipled');out=nodes.new('ShaderNodeOutputMaterial');links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,alpha);p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha
 if 'Subsurface Weight' in p.inputs:p.inputs['Subsurface Weight'].default_value=.09 if texture else .025
 if 'Coat Weight' in p.inputs:p.inputs['Coat Weight'].default_value=.08 if texture or tendon else .015
 if texture:
  im=nodes.new('ShaderNodeTexImage');im.image=baseimg;links.new(im.outputs['Color'],p.inputs['Base Color']);ri=nodes.new('ShaderNodeTexImage');ri.image=roughimg;links.new(ri.outputs['Color'],p.inputs['Roughness'])
 if texture or tendon:
  ni=nodes.new('ShaderNodeTexImage');ni.image=normalimg if texture else tendonimg;nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.35 if texture else .20;links.new(ni.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],p.inputs['Normal'])
 if alpha<1:m.surface_render_method='DITHERED'
 return m
mats={'bone':material('Bone | anatomical ivory',(.59,.53,.40),.53),'muscle':material('Muscle | longitudinal fascicles',(.38,.065,.040),texture=True),'tendon':material('Tendon | collagen bundles',(.72,.69,.55),.34,tendon=True),'fascia':material('Fascia | transparent connective sheath',(.45,.59,.52),.7,alpha=.11)}
# Source mesh coordinates → longitudinal UVs; surface variation remains attached while deforming.
def set_uv(o,mid):
 arr=np.array([v.co[:] for v in o.data.vertices]);zs,cs=profiles[mid];cx=np.interp(arr[:,2],zs,cs[:,0]);cy=np.interp(arr[:,2],zs,cs[:,1]);u=np.arctan2(arr[:,1]-cy,arr[:,0]-cx)/(2*np.pi)+.5;v=(arr[:,2]-arr[:,2].min())/max(.001,np.ptp(arr[:,2]));uv=o.data.uv_layers.new(name='FibreUV')
 for poly in o.data.polygons:
  us=[u[o.data.loops[i].vertex_index] for i in poly.loop_indices];wrap=max(us)-min(us)>.5
  for idx in poly.loop_indices:
   j=o.data.loops[idx].vertex_index;uu=u[j]+(1 if wrap and u[j]<.5 else 0);uv.data[idx].uv=(uu,v[j])
# Common deformation field evaluated on the original surface. Tendon seams use identical weights.
def deform(mid,arr,angle):
 a=math.radians(angle);I=ATT[mid][1];O=ATT[mid][0];R=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]]);delta=R@I-I
 z=arr[:,2];isflex='biceps' in mid or 'brachialis' in mid;lower=(-.034 if 'biceps' in mid else -.036) if isflex else .004;upperz=.222 if 'biceps' in mid else (.153 if 'brachialis' in mid else .205)
 t=np.clip((upperz-z)/(upperz-lower),0,1);w=t
 out=arr+delta[None,:]*w[:,None]
 # At the actual distal insertions, continue rigid rotation to keep the footprint on bone.
 end=np.clip((lower+.012-z)/.018,0,1);out=out*(1-end[:,None])+(arr@R.T)*end[:,None]
 zs,cs=profiles[mid];center=np.column_stack((np.interp(z,zs,cs[:,0]),np.interp(z,zs,cs[:,1]),z));bell=np.sin(np.pi*t)**2
 gain=(.19 if isflex else -.10)*math.sin(a/2);out[:,:2]+=(arr-center)[:,:2]*(gain*bell)[:,None]
 # Anterior/posterior routing keeps the moving belly away from the hinge's osseous volume.
 out[:,1]+=(.016 if isflex else -.010)*math.sin(a/2)*bell
 # Small registration offsets separate native atlas overlap while retaining surface shapes.
 if 'biceps' in mid:
  out[:,1]+=.013*bell+.004*max(0,(angle-90)/30)*np.sin(np.pi*t);out[:,0]+=(.005 if 'long' in mid else -.005)*bell
 if 'triceps_long' in mid or 'triceps_lateral' in mid:
  out[:,1]-=.007*bell;out[:,0]+=(.003 if 'lateral' in mid else -.003)*bell
 return out
stats={}
for id,o in objects.items():
 s=S[id];o.data.materials.clear();o.data.materials.append(mats[s['type']]);o.parent=forearm if s.get('binding')=='forearm' else upper
 if s['type']=='bone':put(o,'01_Bones')
 else:
  mid=mapping[id];set_uv(o,mid);put(o,'04_Tendons' if s['type']=='tendon' else ('03_Deep_muscles' if s['layer']=='deep' else '02_Superficial_muscles'))
  arr=np.array([v.co[:] for v in o.data.vertices]);o.data.vertices.foreach_set('co',deform(mid,arr,0).astype(np.float32).ravel());o.shape_key_add(name='Basis');lengths=[];zs,cs=profiles[mid];rpath=cs.copy()
  for angle in range(0,121,5):
   pp=deform(mid,rpath,angle);lengths.append(float(np.linalg.norm(np.diff(pp,axis=0),axis=1).sum()))
   if angle==0:continue
   key=o.shape_key_add(name=f'Flex_{angle:03d}');vs=deform(mid,arr,angle);key.data.foreach_set('co',vs.astype(np.float32).ravel())
   for frame,val in [(1,0),(max(1,angle-4),0),(angle+1,1),(angle+6,0)]:
    if frame>121:continue
    key.value=val;key.keyframe_insert('value',frame=frame)
  stats[id]={'pathLengthsMetres':lengths,'restLength':lengths[0],'vertexCount':len(arr),'measurement':'source centreline cage, not physiological muscle length','sourceId':mid}
 s['geometryStatus']='atlas-derived' if s['type']=='bone' or s['type']=='muscle' else 'atlas-region-separated'
 s['anatomyStatus']='BodyParts3D 数据集形态；本次配准、腱分区与运动尚待专业审核'
 if id in P['structures']:s['sourceFMA']=P['structures'][id]['fma']
 o['structure_id']=id;o['label_zh']=s['name'];o['geometry_status']=s['geometryStatus'];o['source']='BodyParts3D / CC BY-SA 2.1 Japan';o['layer']=s['layer'];o['origin_description']=s['origin'];o['insertion_description']=s['insertion']
 if s['type']=='muscle':
  origin,insert=ATT[id];s['originPoint']=origin.tolist();s['insertionPoint']=insert.tolist()
  empty('origin__'+id,origin,upper,'06_Attachments');empty('insertion__'+id,insert,forearm,'06_Attachments')
  for ending,label in [(False,'belly_origin__'),(True,'belly_insertion__')]:
   threshold=arr[:,2].min()+.002 if ending else arr[:,2].max()-.002
   band=arr[arr[:,2]<=threshold] if ending else arr[arr[:,2]>=threshold]
   pt=band.mean(0);mark=empty(label+id,pt,upper,'06_Attachments')
   for a in range(0,121,5):mark.location=deform(mid,np.array([pt]),a)[0];mark.keyframe_insert('location',frame=a+1)

# Separate editable fascia: adaptive envelope of this model, explicitly schematic.
verts=[];faces=[];rings=60;sides=64
allmus=np.concatenate([deform(k,full[k],0) for k in full])
for j in range(rings+1):
 z=.015+j/rings*.255;near=allmus[np.abs(allmus[:,2]-z)<.01];cx=(near[:,0].max()+near[:,0].min())/2;cy=(near[:,1].max()+near[:,1].min())/2;rx=np.ptp(near[:,0])/2+.004;ry=np.ptp(near[:,1])/2+.004
 for k in range(sides):
  a=2*math.pi*k/sides;verts.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
for j in range(rings):
 for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
me=bpy.data.meshes.new('FasciaEnvelope');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('fascia_brachial_R',me);cols['05_Fascia'].objects.link(o);o.parent=upper;o.data.materials.append(mats['fascia']);o['structure_id']=o.name;o['geometry_status']='schematic';o['label_zh']='臂筋膜·示意层'
for p in me.polygons:p.use_smooth=True
# All animation curves use linear interpolation between 5-degree source deformations.
for obj in [forearm]+[o for o in cols['06_Attachments'].objects if o.animation_data]+[o.data.shape_keys for o in objects.values() if o.data.shape_keys]:
 if not obj.animation_data or not obj.animation_data.action:continue
 act=obj.animation_data.action
 for layer in act.layers:
  for strip in layer.strips:
   for slot in act.slots:
    bag=strip.channelbag(slot)
    if bag:
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:kp.interpolation='LINEAR'
D['title']='ELBOW / 02 — ATLAS STUDIO';D['source']=P;D['coordinates']['sourceTransform']={'sourcePivotMm':list(pivot),'rotationYRadians':.215,'sourceToLocal':'translate, convert mm to m, flip X/Y, rotate about Y'}
D['joint']['assumptions']='BodyParts3D 单男性体表数据；固定上臂、单轴屈伸，0° 为源模型配准姿态。轴、附着面积、动态碰撞尚待专业审核。'
D['animation']['method']='Atlas surface cage deformation sampled every 5 degrees; NOT biomechanical simulation.'
(ROOT/'data/structures.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n');(ROOT/'data/geometry-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
t=bpy.data.texts.new('SOURCE_AND_LICENSE');t.write(json.dumps(P,ensure_ascii=False,indent=2));t=bpy.data.texts.new('MODEL_NOTES');t.write('Atlas-derived anatomical meshes. Tendon region segmentation and shape-key cage deformation are illustrative adaptations, not validated muscle mechanics. Source STL files are distributed in sources/. CC BY-SA 2.1 Japan applies to derived geometry. All vertices and shape keys remain editable.')
# Studio camera inside the editable source, excluded from web export.
bpy.ops.object.camera_add(location=(.52,.82,.26));camera=bpy.context.object;camera.name='Studio_Camera';direction=Vector((0,0,.07))-camera.location;camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.68;scene.camera=camera
for loc,power,size_ in [((.15,.45,.65),55,.4),((-.35,-.1,.3),40,.3),((.25,-.25,.05),20,.2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size_;l.rotation_euler=(Vector((0,0,.12))-l.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.08,.09,.1);scene.render.engine='CYCLES';scene.cycles.samples=48;scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.frame_set(26)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=.8;area.spaces.active.region_3d.view_location=(0,0,.07);area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/elbow-right.blend'))
scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/elbow-right.glb'),export_format='GLB',export_extras=True,export_yup=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_morph=True,export_morph_normal=True,export_cameras=False,export_lights=False)
print('STUDIO_BUILD_COMPLETE')
