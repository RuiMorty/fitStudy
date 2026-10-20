"""Same-source elbow supplements. New footprints/widths are review candidates, not measurements.
Run with Blender. Does not overwrite the previous source blend or motion assets.
"""
import bpy,bmesh,json,math,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;W=P.parent
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.open_mainfile(filepath=str(P/'elbow-review-assembly.blend'))
scene=bpy.context.scene
read=lambda p:json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def web(p):return Vector((p.x,p.z,-p.y))
def native(p):return Vector((p.x,-p.z,p.y))
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def tree(o):
 bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world)
 for v in bm.verts:v.co=web(v.co)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.normal_update();tr=BVHTree.FromBMesh(bm);bm.free();return tr
bones={(b,s):scene.objects['bone_'+b+'_'+s.lower()] for b in ['Humerus','Ulna','Radius'] for s in ['R','L']}
trees={k:tree(o) for k,o in bones.items()}
landmarks=read(P/'landmarks.json')['landmarks']+read(P/'supplement-landmark-candidates.json')
def landmark(term,side):return Vector(next(r['position'] for r in landmarks if r['term']==term and r['side']==side))
def snap(p,tr,inset=0):q,n,_,_=tr.find_nearest(p);return q+n*inset
mat=bpy.data.materials.new('Supplement ligament ivory');mat.use_nodes=True
next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(.68,.65,.58,1)
next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Roughness'].default_value=.65
fiber_material=runpy.run_path(str(P/'build_fiber_material.py'))['FIBER_MATERIAL']
axisdata=read(W/'motion/elbow-axis.json');newobjects=[];records=[];binding={};metrics=[]
REF_U={'title':'Cinque et al. 2020｜肘内侧尺侧副韧带复合体综述','url':'https://europepmc.org/articles/PMC7083993','quote':'The medial elbow collateral ligament complex is composed of three bundles, the anterior bundle, posterior bundle, and oblique bundle.','retrieved':'2026-10-14'}
REF_L={'title':'Applied anatomy of the elbow｜外侧复合体与斜索','url':'https://clinicalgate.com/2015/03/10/anatomy-of-the-elbow/','quote':'posteriorly via the lateral ulnar collateral ligament which inserts at the supinator crest of the ulna','retrieved':'2026-10-14'}

def record(key,side,zh,origin,insertion,shape,bone_names,landmark_names,kind):
 ident='elbow_'+key+'_'+side
 r={'id':ident,'name_zh':('右' if side=='R' else '左')+zh,'name_en':key.replace('_',' ')+' '+side,'side':side,'region':'上肢','available':True,'trial':False,'tissue':True,'tissue_layer':'ligament','tissue_type':'ligament','bone_ids':['bone_'+b.lower()+'_'+side for b in bone_names],'joint_or_connection_ids':['humeroulnar_'+side,'proximal_radioulnar_'+side],'source_structure_id':('Oblique cord.'+side.lower() if kind=='source' else 'literature_guided_'+key),'source_dataset':'Z-Anatomy 同源斜索' if kind=='source' else '文献关系 + Z-Anatomy 原配骨面候选重建','granularity':'individual_source_object' if kind=='source' else 'independent_candidate_bundle','anatomy_review':'pending','assembly_review':'pending','group':'medial' if key.startswith('ucl') else 'lateral','context_bones':bone_names,'landmark_names':landmark_names,'origin':origin,'insertion':insertion,'shape':shape,'comparison':'沿用同源斜索控制网格，增加显示细分。' if kind=='source' else '独立重建候选；骨性标志只作定位，不等于韧带足印。','limitations':'附着边界、厚度、宽度与材料性质未通过解剖验收；纯屈伸显示变形，不代表真实受力。','evidence_status':'reference_checked_geometry_pending','references':[REF_U] if key.startswith('ucl') else [REF_L],'geometry_revision':'elbow-supplement-v1','motion_kind':'rigid_forearm' if key in ['ucl_transverse','oblique_cord'] else 'deform'}
 if key=='ucl_anterior':r['limitations']+=' 前束远端沿尺骨嵴延伸范围存在个体差异，当前足印为定位候选，未复制文献平均尺寸为本人的测量。'
 if key in ['ucl_posterior','ucl_transverse']:r['references']=[REF_U,dict(REF_L,quote='a posterior part, directed towards the olecranon. All three parts are reinforced by an oblique band (ligament of Cooper) distally on the ulna.')]
 if key=='oblique_cord':r['references']=[dict(REF_L,quote='The oblique cord extends inferolaterally from the lateral border of the tuberosity of the ulna to the radius, just below its tuberosity.')]
 records.append(r);return ident

def cat(points,t):
 u=t*(len(points)-1);i=min(int(u),len(points)-2);f=u-i;a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
 return .5*((2*b)+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)

def make_band(ident,side,centers,widths,width_dir,normal_dir,supports,rigid=False,surface_path=False):
 # Rounded, tapered closed cross-section. Terminal rows are actual surface patches.
 is_ucl=ident.startswith("elbow_ucl_")
 n=64 if is_ucl else 48;m=32 if is_ucl else 16;verts=[];weights=[];params=[]
 for i in range(n+1):
  t=i/n;p=cat(centers,t);w=(1-t)*widths[0]+t*widths[1];w*=.78+.22*abs(2*t-1)
  if surface_path and not is_ucl:p=snap(p,trees['Ulna',side],.0005)
  tangent=(cat(centers,min(1,t+.002))-cat(centers,max(0,t-.002))).normalized()
  across=(tangent.cross(normal_dir) if is_ucl else width_dir-tangent*width_dir.dot(tangent)).normalized();normal=tangent.cross(across).normalized()
  if normal.dot(normal_dir)<0:normal=-normal
  weight=1 if rigid else smooth((t-.12)/.76)
  for j in range(m):
   a=2*math.pi*j/m;thick=.00042*(.25+.75*math.sin(math.pi*t)**.4);v=p+across*(math.cos(a)*w/2)+normal*(math.sin(a)*thick)
   if t<.12:v=v.lerp(snap(v,supports[0],-.00012),1-smooth(t/.12))
   elif t>.88:v=v.lerp(snap(v,supports[1],-.00012),smooth((t-.88)/.12))
   elif not is_ucl:
    for _ in range(3):
     for tr in [trees[b,side] for b in ['Humerus','Ulna','Radius']]:
      q,nn,_,dd=tr.find_nearest(v)
      if dd<.012 and (v-q).dot(nn)<.00015:v=q+nn*.0005
   verts.append(native(v));weights.append(weight);params.append(t)
 if is_ucl:
  # Loft continuous fiber trajectories between smooth attachment curves. No frame flips.
  across=(centers[-1]-centers[0]).normalized().cross(normal_dir).normalized()
  ss=np.linspace(-1,1,33);curves=[]
  for k,tr in enumerate(supports):
   center=centers[0 if k==0 else -1]
   points=[list(snap(center+across*(float(u)*widths[k]/2),tr,-.00012)) for u in ss]
   curves.append(np.polyfit(ss,np.asarray(points),3))
  verts=[]
  for i in range(n+1):
   t=i/n
   for j in range(m):
    a=2*math.pi*j/m;u=math.cos(a);p0=Vector(np.polyval(curves[0],u));p1=Vector(np.polyval(curves[1],u))
    p=p0.lerp(p1,smooth(t))
    p+=normal_dir*(.0012*math.sin(math.pi*t)+math.sin(a)*.00032*(.15+.85*math.sin(math.pi*t)))
    verts.append(native(p))
  # A single smooth clearance field moves the whole sheet, never individual vertices.
  lift=0.
  for p,t in zip(verts,params):
   if .2<t<.8:
    p=web(p);env=math.sin(math.pi*t)
    for tr in [trees[b,side] for b in ['Humerus','Ulna','Radius']]:
     q,nn,_,dd=tr.find_nearest(p);signed=(p-q).dot(nn)
     if dd<.006 and signed<0 and nn.dot(normal_dir)>.2:lift=max(lift,(-signed+.0003)/max(nn.dot(normal_dir)*env,.1))
  lift=min(lift,.003)
  verts=[native(web(p)+normal_dir*(lift*math.sin(math.pi*t))) for p,t in zip(verts,params)]
 faces=[]
 for i in range(n):
  for j in range(m):faces.append((i*m+j,i*m+(j+1)%m,(i+1)*m+(j+1)%m,(i+1)*m+j))
 faces.extend([tuple(reversed(range(m))),tuple(n*m+j for j in range(m))])
 me=bpy.data.meshes.new(ident);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(ident+'__refined',me);scene.collection.objects.link(ob);me.materials.append(fiber_material if is_ucl else mat)
 for f in me.polygons:f.use_smooth=True
 uv=me.uv_layers.new(name='Fiber direction')
 for loop in me.loops:
  i,j=divmod(loop.vertex_index,m);uv.data[loop.index].uv=((.5+.5*math.cos(2*math.pi*j/m),i/n) if is_ucl else (j/m*6,i/n*4))
 attr=me.attributes.new('_motion_weight','FLOAT','POINT');attr.data.foreach_set('value',weights)
 for label,indices in [('Proximal candidate',[i for i,t in enumerate(params) if t==0]),('Distal candidate',[i for i,t in enumerate(params) if t==1])]:ob.vertex_groups.new(name=label).add(indices,1,'REPLACE')
 newobjects.append(ob);binding[ident]={'kind':'rigid_forearm' if rigid else 'deform','side':side,'source':'candidate patches on named bones'}
 records[-1]['attachment_candidates']={'status':'geometric_locator_not_anatomical_footprint','centerline_web_m':[list(p) for p in centers],'terminal_widths_mm':[w*1000 for w in widths],'terminal_inset_mm':.12,'terminal_surface_max_distance_mm':[max(supports[k].find_nearest(web(verts[i]))[3]*1000 for i in (range(m) if k==0 else range(n*m,(n+1)*m))) for k in [0,1]]}
 if not rigid:
  pivot=Vector(axisdata['sides'][side]['pivot']);axis=Vector(axisdata['sides'][side]['axis']);ob.shape_key_add(name='Rest');pose_reports=[]
  for angle in range(5,121,5):
   q=Quaternion(axis,math.radians(angle));qi=q.inverted();positions=[];flag=0;maxpush=0
   for p0,w,t in zip(verts,weights,params):
    p0=web(p0);p=p0.lerp(q@(p0-pivot)+pivot,w);start=p.copy()
    if 0<w<1:
     for _ in range(0 if is_ucl else 4):
      for name,moving in [('Humerus',False),('Ulna',True),('Radius',True)]:
       local=qi@(p-pivot)+pivot if moving else p;q0,nn,_,dd=trees[name,side].find_nearest(local)
       if dd<.015 and (local-q0).dot(nn)<.0001:
        corrected=q0+nn*.0005;p=q@(corrected-pivot)+pivot if moving else corrected
     maxpush=max(maxpush,(p-start).length)
     for name,moving in [('Humerus',False),('Ulna',True),('Radius',True)]:
      local=qi@(p-pivot)+pivot if moving else p;q0,nn,_,dd=trees[name,side].find_nearest(local)
      if .0005<dd<.015 and (local-q0).dot(nn)<0:flag+=1
    positions.append(native(p))
   if is_ucl:
    lift=0.
    for p,t,w in zip(positions,params,weights):
     if .2<t<.8:
      p=web(p)
      for name,moving in [('Humerus',False),('Ulna',True),('Radius',True)]:
       local=qi@(p-pivot)+pivot if moving else p;direction=qi@normal_dir if moving else normal_dir
       q0,nn,_,dd=trees[name,side].find_nearest(local);signed=(local-q0).dot(nn)
       if dd<.006 and signed<0 and nn.dot(direction)>.2:lift=max(lift,(-signed+.0003)/max(nn.dot(direction)*math.sin(math.pi*w),.1))
    lift=min(max(lift,0),.003);positions=[native(web(p)+normal_dir*(lift*math.sin(math.pi*w))) for p,w in zip(positions,weights)]
    flag=0;maxpush=max(maxpush,lift)
    for p,w in zip(positions,weights):
     if 0<w<1:
      p=web(p)
      for name,moving in [('Humerus',False),('Ulna',True),('Radius',True)]:
       local=qi@(p-pivot)+pivot if moving else p;q0,nn,_,dd=trees[name,side].find_nearest(local)
       if .0005<dd<.015 and (local-q0).dot(nn)<0:flag+=1
   key=ob.shape_key_add(name='Flex_'+str(angle));key.data.foreach_set('co',np.asarray(positions,dtype=np.float32).ravel())
   pose_reports.append({'degrees':angle,'free_span_deep_samples':flag,'max_clearance_adjustment_mm':round(maxpush*1000,3)})
  metrics.append({'id':ident,'poses':pose_reports,'scope':'nearest-normal vertex screening only; no full collision acceptance'})
 return ob

for side in ['R','L']:
 med=Vector((1 if side=='R' else -1,0,0));lat=-med;ht=trees['Humerus',side];ut=trees['Ulna',side]
 me=landmark('Medial epicondyle of humerus',side);le=landmark('Lateral epicondyle of humerus',side);su=landmark('Sublime tubercle',side);ol=landmark('Olecranon',side);cr=landmark('Supinator crest',side)
 ant=snap(me+Vector((0,-.007,.006)),ht);sublime=snap(su+Vector((0,-.005,0)),ut)
 post=snap(me+Vector((0,-.004,-.003)),ht);ole=snap(ol+med*.009+Vector((0,-.006,0)),ut)
 ident=record('ucl_anterior',side,'肘尺侧副韧带前束','肱骨内上髁前下方区域。','尺骨崇高结节及沿尺骨嵴向远端延伸的附着区。','前内侧束；远端为延长的骨面附着区，并非一个点。',['Humerus','Ulna'],['肱骨内上髁','尺骨崇高结节'],'candidate')
 make_band(ident,side,[ant,(ant+sublime)/2+med*.0015,sublime],(.005,.008),Vector((0,-.6,.8)),med,[ht,ut])
 ident=record('ucl_posterior',side,'肘尺侧副韧带后束','肱骨内上髁后下方区域。','尺骨鹰嘴内侧缘。','后内侧扇形束，尺骨侧附着较展开；不横跨肘后正中填满空隙。',['Humerus','Ulna'],['肱骨内上髁','鹰嘴'],'candidate')
 make_band(ident,side,[post,(post+ole)/2+med*.0015,ole],(.004,.011),Vector((0,.75,.66)),med,[ht,ut])
 ident=record('ucl_transverse',side,'肘尺侧副韧带横束','尺骨冠突内侧邻近区域。','尺骨鹰嘴内侧邻近区域；两端均在尺骨。','横/斜行纤维连接同一块尺骨上的两处区域，不跨肱尺关节。',['Ulna'],['尺骨崇高结节','鹰嘴'],'candidate')
 make_band(ident,side,[su,(su+ole)/2+med*.002,ole],(.0045,.006),Vector((0,1,0)),med,[ut,ut],True,True)
 start=snap(le+Vector((0,-.003,-.001)),ht);end=snap(cr,ut);head=landmark('Head of radius',side)
 via=head+lat*.010+Vector((0,-.002,-.014))
 ident=record('lucl',side,'肘尺侧外侧副韧带','肱骨外上髁外侧韧带复合体起始区域。','尺骨旋后肌嵴。','从外侧起始区绕桡骨头后外侧走向尺骨；不同于终止于环状韧带的桡侧副韧带。',['Humerus','Radius','Ulna'],['肱骨外上髁','桡骨头','旋后肌嵴'],'candidate')
 records[-1]['bone_ids']=['bone_humerus_'+side,'bone_ulna_'+side]
 make_band(ident,side,[start,via,end],(.004,.006),Vector((0,.1,1)),lat,[ht,ut])

# Solid fascicle experiment is not part of the restored active model.

# Reuse the original oblique-cord control mesh at its evaluated world coordinates.
source_scene=bpy.data.scenes.new('Source oblique cords');bpy.context.window.scene=source_scene
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (a,b):b.objects=['Oblique cord.r','Oblique cord.l']
for o in b.objects:source_scene.collection.objects.link(o);o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
for side in ['R','L']:
 src=next(o for o in b.objects if o.name.startswith('Oblique cord.'+side.lower()));ev=src.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev);me.transform(ev.matrix_world)
 ident=record('oblique_cord',side,'前臂斜索','尺骨粗隆外侧缘邻近区域。','桡骨粗隆下方。','向远端、外侧斜行的近端前臂纤维束；不等同于尺侧副韧带横束。',['Ulna','Radius'],['桡骨颈'],'source')
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=5,use_grid_fill=True);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(ident+'__refined',me);scene.collection.objects.link(ob);me.materials.clear();me.materials.append(mat)
 for f in me.polygons:f.use_smooth=True
 newobjects.append(ob);binding[ident]={'kind':'rigid_forearm','side':side,'source':'Z-Anatomy Oblique cord'}
bpy.context.window.scene=scene
# Carry over the previous RCL deformation without regenerating/altering other joints.
with bpy.data.libraries.load(str(W/'motion/elbow-ligaments-motion.blend'),link=False) as (a,b):b.objects=['z_lig_radial_collateral_ligament_R','z_lig_radial_collateral_ligament_L']
rcls=[]
for o in b.objects:scene.collection.objects.link(o);o.animation_data_clear();rcls.append(o)
for o in rcls:
 if o.data.shape_keys:o.data.shape_keys.animation_data_clear()
def export(path,obs,morph=False):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_attributes=True,export_materials='NONE',export_morph=morph,export_animations=False,export_extras=True)
# Static supplemental pack for the main viewer: 10 independently named objects.
for o in newobjects:o.name=o.name.replace('__refined','')
export(W/'z-anatomy-candidate/assets/elbow-supplement.glb',newobjects)
# Deformation pack: RCL plus new anterior/posterior/LUCL; transverse and oblique are rigid.
deforms=[o for o in newobjects if binding[o.name]['kind']=='deform']+rcls
export(W/'motion/elbow-ligaments-complete.glb',deforms,True)
for o in newobjects:o.name+='__refined'
oldcat=read(P/'catalog.json');kept=[r for r in oldcat['structures'] if not r['id'].startswith('z_lig_ulnar_collateral_ligament_') and not r['id'].startswith('elbow_')]
review_obs=[o for o in scene.objects if o.name.startswith('bone_') or any(o.name==r['id']+'__refined' for r in kept)]+newobjects
export(P/'elbow-review-supplement.glb',review_obs)
# Editable source stores original bones and new patches with shape keys. No legacy file removed.
scene.frame_set(1)
for o in deforms:
 if o.data.shape_keys:
  for key in list(o.data.shape_keys.key_blocks)[1:]:
   angle=int(key.name.split('_')[-1]);key.value=0;key.keyframe_insert('value',frame=1);key.keyframe_insert('value',frame=max(1,angle-4));key.value=1;key.keyframe_insert('value',frame=angle+1);key.value=0;key.keyframe_insert('value',frame=angle+6)
# The editable scene animates the matching bones and same-chain tissues too.
from mathutils import Matrix
for side in ['R','L']:
 spec=axisdata['sides'][side];pivot=native(Vector(spec['pivot']));axis=native(Vector(spec['axis']))
 moving=[bones[b,side] for b in ['Ulna','Radius']]+[o for o in newobjects if binding[o.name.replace('__refined','')]['kind']=='rigid_forearm' and o.name.endswith(side+'__refined')]+[scene.objects[p+side+'__refined'] for p in ['ligament_annular_radius_','z_lig_quadrate_ligament_']]
 for ob in moving:
  rest=ob.matrix_world.copy();ob.rotation_mode='QUATERNION'
  for angle in range(0,121,5):
   q=Quaternion(axis,math.radians(angle));ob.matrix_world=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)@rest
   ob.keyframe_insert('location',frame=angle+1);ob.keyframe_insert('rotation_quaternion',frame=angle+1)
visible=set(review_obs)|set(rcls)
visible-={scene.objects[r['id']+'__refined'] for r in kept if r['id'].startswith('z_lig_radial_collateral_ligament_')}
for ob in scene.objects:ob.hide_set(ob not in visible);ob.hide_render=ob not in visible
scene.frame_set(1);scene.frame_start=1;scene.frame_end=121
bpy.ops.wm.save_as_mainfile(filepath=str(P/'elbow-review-supplement.blend'),compress=True)
for r in records:
 r['display_source']='elbow-review/elbow-review-supplement.glb'
 mesh=next(o.data for o in newobjects if o.name==r['id']+'__refined');mesh.calc_loop_triangles();r['triangles']=len(mesh.loop_triangles)
write(W/'z-anatomy-candidate/elbow-supplement.json',{'file':'z-anatomy-candidate/assets/elbow-supplement.glb','count':len(records),'objects':records,'replaces_ids':['z_lig_ulnar_collateral_ligament_R','z_lig_ulnar_collateral_ligament_L']})
write(P/'supplement-catalog.json',{'scope':'elbow_ligaments','type_count':8,'source_object_count':8,'structures':kept+records,'gaps':['新增前、后、横束及 LUCL 为独立候选，不代表精确足印通过验收。','副外侧副韧带存在变异，暂无可靠独立同源对象，本次未添加。','关节囊尚未绑定运动；旋前旋后、真实材料应力尚未实现。']})
write(P/'supplement-motion-bindings.json',binding);write(P/'supplement-deformation-audit.json',metrics)
# Review reader supports per-page catalog override.
cfg=read(P/'review-config.json');cfg.update(revision='ucl-restored9',model='elbow-review-supplement.glb',catalog='supplement-catalog.json',meshCount=len(review_obs),initialId='elbow_ucl_anterior_R',audit='supplement-geometry-audit.json',loadedLabel='分束与缺项补充候选 · 足印待核准');write(P/'review-config.json',cfg)
audit=read(P/'geometry-audit-assembly.json');audit=[a for a in audit if any(r['id']==a['id'] for r in kept)]
for r in records:audit.append({'id':r['id'],'raw_vertices':0,'surface_displacement_max_mm':None,'end_candidates':[],'suspected_penetration_nearest_normal_only':{},'audit_scope':'not_performed','contact_display_note':'独立候选构建；静态端部贴合与形态抽样记录见补充报告。完整相交、足印和宽度尚未验收。'})
write(P/'supplement-geometry-audit.json',audit)
print('SUPPLEMENT',len(records),'review meshes',len(review_obs),'deforms',len(deforms),flush=True)
print([(r['id'],max(p['free_span_deep_samples'] for p in r['poses'])) for r in metrics],flush=True)
