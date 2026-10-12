"""Build editable right elbow with named meshes, anchors and flexion shape keys.
Run: blender -b --python blender/build_elbow.py
"""
import bpy, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/structures.json').read_text()); S={s['id']:s for s in D['structures']}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.collections):
 if block.name!='Collection':bpy.data.collections.remove(block)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.fps=30;scene.frame_start=1;scene.frame_end=121
base=bpy.data.collections.get('Collection');base.name='ELBOW_R'
def collection(name):
 c=bpy.data.collections.new(name);base.children.link(c);return c
cols={k:collection(k) for k in ['01_Bones','02_Muscles_superficial','03_Muscles_deep','04_Tendons','05_Fascia','06_Attachment_markers','07_Rig']}
def put(obj,c):
 for old in list(obj.users_collection):old.objects.unlink(obj)
 cols[c].objects.link(obj)
def mat(name,color,rough=.44,alpha=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,alpha);p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha
 if alpha<1:m.surface_render_method='DITHERED'
 return m
mats={'bone':mat('Bone | warm ivory',(.78,.69,.52)), 'flexor':mat('Muscle | flexor',(.51,.10,.065)), 'extensor':mat('Muscle | extensor',(.38,.12,.10)), 'deep':mat('Muscle | deep',(.58,.24,.12)), 'tendon':mat('Tendon | collagen',(.87,.81,.66)), 'fascia':mat('Fascia | schematic',(.3,.65,.56),alpha=.17)}
def empty(name,pos,parent=None,c='07_Rig'):
 o=bpy.data.objects.new(name,None);cols[c].objects.link(o);o.location=pos;o.empty_display_type='SPHERE';o.empty_display_size=.0025;o.parent=parent;return o
root=empty('rig_upper_R',(0,0,0));forearm=empty('joint_elbow_R',(0,0,0),root)
forearm['axis_note']='Approximate mediolateral hinge axis. Supinated forearm, no carrying angle.'
for frame,angle in [(1,0),(121,120)]:
 forearm.rotation_euler[0]=math.radians(angle);forearm.keyframe_insert('rotation_euler',frame=frame)
def linear(obj):
 if not obj.animation_data or not obj.animation_data.action:return
 act=obj.animation_data.action
 for layer in act.layers:
  for strip in layer.strips:
   for slot in act.slots:
    bag=strip.channelbag(slot)
    if bag:
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:kp.interpolation='LINEAR'
linear(forearm)
def mesh(name,verts,faces):
 me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);base.objects.link(o)
 for p in me.polygons:p.use_smooth=True
 return o
def ellipsoid(name,p,scale):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=p);o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return o
# Polyline sampling and centripetal-free Catmull-Rom with consistent topology.
def curve(points,n=32):
 ps=[Vector(p) for p in points];out=[]
 for j in range(n+1):
  q=j/n*(len(ps)-1);k=min(int(q),len(ps)-2);t=q-k
  p0=ps[max(0,k-1)];p1=ps[k];p2=ps[k+1];p3=ps[min(len(ps)-1,k+2)]
  out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 return out
def tube_vertices(points,radii,n=32,sides=16,flat=1,bulge=1):
 path=curve(points,n);verts=[]
 for j,p in enumerate(path):
  t=j/n;k=min(int(t*(len(radii)-1)),len(radii)-2);f=t*(len(radii)-1)-k;r=(radii[k]*(1-f)+radii[k+1]*f)*bulge
  tangent=(path[min(j+1,n)]-path[max(j-1,0)]).normalized()
  u=(Vector((1,0,0))-tangent*tangent.x).normalized();v=tangent.cross(u).normalized()
  for a in range(sides):
   theta=2*math.pi*a/sides;verts.append(p+r*(math.cos(theta)*u+math.sin(theta)*v*flat))
 faces=[]
 for j in range(n):
  for a in range(sides):faces.append((j*sides+a,j*sides+(a+1)%sides,(j+1)*sides+(a+1)%sides,(j+1)*sides+a))
 faces += [tuple(reversed(range(sides))),tuple(n*sides+a for a in range(sides))]
 return verts,faces

def tube(name,points,radii,n=32,sides=16,flat=1):
 v,f=tube_vertices(points,radii,n,sides,flat);return mesh(name,v,f)
def join(parts,name):
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name
 # Fuse additive skeletal landmarks into a single watertight, editable mesh.
 mod=o.modifiers.new('Unified bone surface','REMESH');mod.mode='VOXEL';mod.voxel_size=.0015;mod.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
 sm=o.modifiers.new('Surface relaxation','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
 de=o.modifiers.new('Web polygon budget','DECIMATE');de.ratio=.48;bpy.ops.object.modifier_apply(modifier=de.name)
 return o
# Humerus: bowed shaft, medial head, tubercles, distal trochlea and capitulum.
p=[tube('shaft',[(0,0,.028),(.004,-.001,.09),(-.004,-.002,.20),(-.006,0,.285)],[.018,.012,.013,.018],44,24),ellipsoid('head',[-.018,0,.290],[.024,.023,.025]),ellipsoid('greater_tubercle',[.011,-.002,.291],[.012,.016,.019]),ellipsoid('lesser_tubercle',[-.003,.016,.279],[.011,.009,.012]),ellipsoid('distal_flare',[0,0,.026],[.033,.014,.021]),ellipsoid('medial_epicondyle',[-.033,0,.006],[.010,.012,.012]),ellipsoid('capitulum',[.023,0,0],[.012,.013,.013])]
# Trochlea has a spool profile along the mediolateral axis.
p.append(tube('trochlea',[[-.026,0,0],[-.015,0,0],[-.004,0,0],[.006,0,0]],[.013,.0105,.011,.014],18,24))
humerus=join(p,'bone_humerus_R')
# Scapula, with a thin triangular blade and independently editable unified landmarks.
vs=[[-.026,-.005,.292],[-.155,-.021,.315],[-.106,-.024,.133]]
vs=vs+[[x,y-.005,z] for x,y,z in vs]
p=[mesh('blade',vs,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)]),tube('spine',[[-.150,-.026,.29],[-.091,-.037,.286],[-.035,-.029,.313],[.006,-.017,.323]],[.004,.006,.009,.011]),tube('coracoid',[[-.04,-.005,.307],[-.045,.022,.313],[-.039,.035,.299]],[.007,.007,.006]),ellipsoid('glenoid',[-.033,0,.289],[.008,.018,.024]),ellipsoid('supraglenoid_region',[-.030,.001,.311],[.008,.010,.011])]
scapula=join(p,'bone_scapula_R')
# Ulna C-shaped notch: positive Y is anterior, the notch is open anteriorly.
arc=[]
for j in range(25):
 a=math.radians(68+224*j/24);arc.append([-.012,.019*math.cos(a),.019*math.sin(a)])
p=[tube('ulna_shaft',[[-.012,-.006,-.024],[-.016,-.001,-.078],[-.014,.004,-.16],[-.013,.008,-.253]],[.012,.009,.0065,.0075],44,20),tube('trochlear_notch',arc,[.0058,.006,.0058],36,20),ellipsoid('olecranon',[-.012,-.017,.014],[.011,.009,.009]),ellipsoid('coronoid',[-.012,.010,-.018],[.010,.007,.006]),ellipsoid('ulnar_tuberosity',[-.013,.011,-.031],[.008,.005,.010]),ellipsoid('ulna_distal',[-.013,.008,-.252],[.008,.009,.010])]
ulna=join(p,'bone_ulna_R')
p=[tube('radius_shaft',[[.022,0,-.027],[.030,-.001,-.079],[.039,.002,-.167],[.032,.006,-.248]],[.0065,.008,.008,.015],44,20),ellipsoid('radial_head',[.023,0,-.020],[.012,.012,.0055]),ellipsoid('radial_tuberosity',[.017,.009,-.043],[.009,.008,.010]),ellipsoid('radial_distal',[.032,.006,-.25],[.017,.013,.010])]
radius=join(p,'bone_radius_R')
for o in [scapula,humerus,ulna,radius]:
 o.data.materials.clear();o.data.materials.append(mats['bone']);put(o,'01_Bones');o.parent=forearm if o in [ulna,radius] else root

# Project design anchors onto the corresponding schematic bone surface, in local rest coordinates.
# This enforces visible attachment continuity; it does not validate anatomical footprints.
ATT={}
for item in D['structures']:
 if item['type']!='muscle':continue
 actual=[]
 for end,field in enumerate(['originPoint','insertionPoint']):
  design=item.get('design'+field[0].upper()+field[1:],item[field]);item['design'+field[0].upper()+field[1:]]=design
  bone=bpy.data.objects[item['bones'][end]];tree=BVHTree.FromPolygons([v.co for v in bone.data.vertices],[list(p.vertices) for p in bone.data.polygons]);p,normal,idx,dist=tree.find_nearest(Vector(design));actual.append(p);item[field]=list(p);item[field+'ProjectionMm']=round(dist*1000,3)
 ATT[item['key']]=actual

def rot(p,angle):
 x,y,z=p;a=math.radians(angle);return Vector((x,y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)))

def landmarks(a):
 bi=rot(ATT['biceps_long'][1],a);br=rot(ATT['brachialis'][1],a);tr=rot(ATT['triceps_long'][1],a)
 return bi,br,tr,bi+Vector((-.015,.036,.075)),br+Vector((.008,.012,.047)),Vector((tr.x,min(-.044,tr.y-.022),tr.z+.046))

def path_for(key,a):
 bi,br,tr,bj,bh,tj=landmarks(a)
 paths={
 'biceps_long':[[-.006,.034,.260],[.014,.061,.216],[.017,.067,.144],bj],
 'biceps_short':[[-.034,.038,.256],[-.022,.061,.211],[-.015,.068,.134],bj],
 'brachialis':[ATT['brachialis'][0],[0,.029,.124],[-.001,.032,.077],bh],
 'triceps_long':[[-.035,-.025,.248],[-.026,-.044,.21],[-.024,-.043,.134],tj],
 'triceps_lateral':[ATT['triceps_lateral'][0],[.024,-.040,.203],[.030,-.049,.123],tj],
 'triceps_medial':[ATT['triceps_medial'][0],[-.001,-.028,.12],[-.001,-.029,.076],tj],
 'biceps_long_prox':[ATT['biceps_long'][0],[-.008,.021,.311],[.001,.029,.285],[-.006,.034,.260]],
 'biceps_short_prox':[ATT['biceps_short'][0],[-.037,.036,.278],[-.034,.038,.256]],
 'biceps_distal':[bj,(bj+bi)/2+Vector((0,.004,0)),bi],
 'brachialis_distal':[bh,(bh+br)/2+Vector((0,.004,0)),br],
 'triceps_long_prox':[ATT['triceps_long'][0],[-.036,-.019,.258],[-.035,-.025,.248]],
 'triceps_distal':[tj,Vector((-.012,min(-.028,tr.y-.014),tr.z+.018)),tr]
 }
 pts=[Vector(p) for p in paths[key]]
 if key in ['biceps_long','biceps_short','brachialis','triceps_long','triceps_lateral','triceps_medial']:
  # Distribute insertion displacement through distal muscle, keeping proximal origin fixed.
  if a:
   delta=pts[-1]-Vector(path_for(key,0)[-1]);pts[1]+=delta*.12;pts[2]+=delta*.52
   if key in ['biceps_long','biceps_short']:
    pts[1].y+=.004*math.sin(math.radians(a/2));pts[2].y+=.008*math.sin(math.radians(a/2))
 return pts

def path_length(points):
 p=curve(points,80);return sum((b-a).length for a,b in zip(p,p[1:]))
stats={}
for s in D['structures']:
 if s['type'] not in ['muscle','tendon']:continue
 key=s['key'];ism=s['type']=='muscle';r=s.get('radius',.0035)
 if key=='triceps_distal':r=.008
 if key=='brachialis_distal':r=.005
 radii=[r*.025,r*.83,r,r*.77,r*.10] if ism else [r*.85,r,r,r*.9]
 flat=.64 if key=='brachialis' else (.7 if key in ['triceps_medial','triceps_distal'] else .80)
 n=36 if ism else 22;sides=16 if ism else 12
 p0=path_for(key,0);L0=path_length(p0)
 verts,faces=tube_vertices(p0,radii,n,sides,flat);o=mesh(s['id'],verts,faces);o.parent=root
 o.data.materials.append(mats['deep' if s['layer']=='deep' and ism else (s['action'] if ism else 'tendon')]);put(o,('03_Muscles_deep' if s['layer']=='deep' else '02_Muscles_superficial') if ism else '04_Tendons')
 o.shape_key_add(name='Basis')
 lengths=[]
 for a in range(0,121,5):
  p=path_for(key,a);L=path_length(p);lengths.append(round(L,6))
  if a==0:continue
  b=o.shape_key_add(name=f'Flex_{a:03d}');vs,_=tube_vertices(p,radii,n,sides,flat,math.sqrt(L0/L) if ism else 1)
  for v,co in zip(b.data,vs):v.co=co
  for fr,val in [(1,0),(max(1,a-4),0),(a+1,1),(min(121,a+6),0)]:
   # Last key must remain at one at the terminal frame.
   if a==120 and fr==121 and val==0:continue
   b.value=val;b.keyframe_insert('value',frame=fr)
 linear(o.data.shape_keys)
 stats[s['id']]={'pathLengthsMetres':lengths,'restLength':L0,'vertexCount':len(verts)}
 if ism:
  ori=empty('origin__'+s['id'],s['originPoint'],root,'06_Attachment_markers')
  ins=empty('insertion__'+s['id'],s['insertionPoint'],forearm,'06_Attachment_markers')
  for m in [ori,ins]:m['structure_id']=s['id'];m['coordinate_accuracy']='schematic anatomical region'
# A thin open sleeve, intentionally stylized and independent of muscle geometry.
verts,faces=tube_vertices([[0,.002,.025],[0,.006,.09],[-.001,.007,.19],[-.01,.004,.272]],[.044,.060,.065,.045],36,40,1.02)
fascia=mesh('fascia_brachial_R',verts,faces[:-2]);fascia.data.materials.append(mats['fascia']);fascia.parent=root;put(fascia,'05_Fascia')
for id,s in S.items():
 o=bpy.data.objects[id];o['structure_id']=id;o['label_zh']=s['name'];o['geometry_status']='schematic';o['origin_description']=s['origin'];o['insertion_description']=s['insertion'];o['layer']=s['layer']
# Save information inside Blender too.
t=bpy.data.texts.new('READ_ME');t.write((ROOT/'docs/STRUCTURES.md').read_text());t.write('\n\nTimeline 1–121 = elbow flexion 0–120 degrees. All geometry is schematic. Muscles are shape-key driven, bones are rigid children of joint_elbow_R. Units: metres.')
(ROOT/'data/structures.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
scene.frame_set(31)
# Comfortable editable solid-material viewport.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=.8;area.spaces.active.region_3d.view_location=(0,0,.06)
   area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/elbow-right.blend'))
scene.frame_set(1)
# Bake all actions as a single coherent scene clip; export standard glTF Y-up.
props=bpy.ops.export_scene.gltf.get_rna_type().properties
kwargs=dict(filepath=str(ROOT/'assets/elbow-right.glb'),export_format='GLB',export_extras=True,export_yup=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_morph=True,export_morph_normal=False,export_cameras=False,export_lights=False)
if 'export_animation_mode' in props:kwargs['export_animation_mode']='SCENE'
bpy.ops.export_scene.gltf(**kwargs)
(ROOT/'data/geometry-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print('BUILD_COMPLETE',len(S),'structures;',len(bpy.data.objects),'total objects')
