import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[2]/'skeleton-workbench';OUT=W/'joint-candidates';(OUT/'assets').mkdir(parents=True,exist_ok=True)
manifest=json.loads((R.parent/'全身关节层台账.json').read_text())
names=sorted({e['object'] for x in manifest['objects'] for e in x['source_evidence'] if e.get('local_mesh')})
configs=[{'id':'knee','name':'右膝半月板','source_bones':['Femur.r','Tibia.r'],'target_bones':['bone_femur_R','bone_tibia_R'],'tissues':['Medial meniscus.r','Lateral meniscus.r']},{'id':'shoulder','name':'右肩关节盂唇','source_bones':['Scapula.r','Humerus.r'],'target_bones':['bone_scapula_R','bone_humerus_R'],'tissues':['Glenoid labrum.r']},{'id':'lumbar','name':'L4—L5 椎间盘','source_bones':['Vertebra L4','Vertebra L5'],'target_bones':['bone_vertebra_L4_M','bone_vertebra_L5_M'],'tissues':['Intervertebral disc L4-L5','Nucleus pulposus L4-L5']}]
p=W/'research/ossicles/Startup.blend'
with bpy.data.libraries.load(str(p),link=False) as (src,dst):
 available=list(src.objects)
 # Resolve actual source vertebral naming from the source library, not guessed geometry.
 lumbar=[n for n in available if ('lumbar vertebra' in n.lower() or 'vertebra l4' in n.lower() or 'vertebra l5' in n.lower())]
 (R/'lumbar-source-names.json').write_text(json.dumps(lumbar,indent=2))
 requested=names+list({n for c in configs for n in c['source_bones'] if n in available})
 dst.objects=requested
source={o.name:o for o in dst.objects if o}
for o in source.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def geom(o):
 e=o.evaluated_get(dg);mesh=e.to_mesh();verts=[e.matrix_world@v.co for v in mesh.vertices];faces=[list(f.vertices) for f in mesh.polygons];e.to_mesh_clear();return verts,faces
quality=[]
for name in names:
 o=source[name];vs,fs=geom(o)
 bm=bmesh.new();v=[bm.verts.new(x) for x in vs];bm.verts.ensure_lookup_table()
 for f in fs:
  try:bm.faces.new([v[i] for i in f])
  except ValueError:pass
 boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);loose=sum(not e.link_faces for e in bm.verts)
 size=[max(x[i] for x in vs)-min(x[i] for x in vs) for i in range(3)]
 quality.append({'object':name,'raw_vertices':len(o.data.vertices),'evaluated_vertices':len(vs),'evaluated_faces':len(fs),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'loose_vertices':loose,'bounds_extent_source_units':size,'mirrored_world_transform':o.matrix_world.determinant()<0,'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport} for m in o.modifiers],'triage':'surface_or_open_mesh_review' if boundary else 'coarse_geometry_review' if len(vs)<150 else 'geometry_review_required','anatomy_review':'pending'})
 bm.free()
(R/'joint-geometry-quality.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'units':'source world units assumed meters; compare bone size, not independently certified','objects':quality},ensure_ascii=False,indent=2)+'\n')
# Keep imported source objects under separate dictionary before appending main bones.
with bpy.data.libraries.load(str(W/'assets/skeleton-review-with-coccyx.blend'),link=False) as (src,dst):dst.objects=list({n for c in configs for n in c['target_bones']})
target={o.name:o for o in dst.objects if o}
for o in target.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def arr(o):return np.array([tuple(x) for x in geom(o)[0]])
def sample(a,n=1800):return a[np.linspace(0,len(a)-1,min(n,len(a)),dtype=int)]
def rigid(a,b):
 ac=a.mean(0);bc=b.mean(0);u,s,vt=np.linalg.svd((a-ac).T@(b-bc));rot=vt.T@u.T
 if np.linalg.det(rot)<0:vt[-1]*=-1;rot=vt.T@u.T
 return rot,bc-rot@ac
reports=[]
for c in configs:
 if any(n not in source for n in c['source_bones']):
  c['status']='source_bone_name_unresolved';c['available_lumbar_names']=lumbar;reports.append(c);continue
 sets=[(sample(arr(source[a])),sample(arr(target[b]),6000)) for a,b in zip(c['source_bones'],c['target_bones'])]
 trees=[]
 for a,b in sets:
  tree=KDTree(len(b))
  for i,v in enumerate(b):tree.insert(Vector(v),i)
  tree.balance();trees.append(tree)
 rot=np.eye(3);trans=np.concatenate([b for a,b in sets]).mean(0)-np.concatenate([a for a,b in sets]).mean(0)
 for iteration in range(35):
  aa=[];bb=[]
  for (a,b),tree in zip(sets,trees):
   moved=a@rot.T+trans;matches=[tree.find(Vector(x)) for x in moved];dist=np.array([m[2] for m in matches]);keep=dist<=np.quantile(dist,.85)
   aa.extend(moved[keep]);bb.extend(np.array([tuple(m[0]) for m in matches])[keep])
  rr,tt=rigid(np.array(aa),np.array(bb));rot=rr@rot;trans=rr@trans+tt
 metrics=[]
 for (a,b),tree,srcname,dstname in zip(sets,trees,c['source_bones'],c['target_bones']):
  ds=np.array([tree.find(Vector(x))[2] for x in a@rot.T+trans])*1000
  metrics.append({'source_bone':srcname,'target_bone':dstname,'sampled_source_to_target_mm_median':float(np.median(ds)),'p95_mm':float(np.quantile(ds,.95)),'source_target_bbox_diagonal_ratio':float(np.linalg.norm(np.ptp(a,axis=0))/np.linalg.norm(np.ptp(b,axis=0)))})
 mat=np.eye(4);mat[:3,:3]=rot;mat[:3,3]=trans
 c.update(status='rigid_fit_candidate_not_anatomically_accepted',registration_matrix=mat.tolist(),bone_fit=metrics,fit_method='35-iteration per-bone nearest-surface trimmed rigid ICP, no scale; median/p95 are directional sampled bone distances, NOT tissue accuracy')
 created=[]
 def mesh_obj(name,source_obj,group,transform=False):
  vs,fs=geom(source_obj)
  if transform:vs=[Vector(rot@np.array(v)+trans) for v in vs]
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);o['group']=group;o['source_object']=source_obj.name
  material=bpy.data.materials.new(name+'_display');material.diffuse_color= {'target':(.65,.63,.58,1),'source':(.22,.43,.65,1),'tissue':(.65,.25,.22,1)}[group];mesh.materials.append(material)
  for f in mesh.polygons:f.use_smooth=True
  created.append(o)
 for n in c['target_bones']:mesh_obj('target_'+n,target[n],'target')
 for n in c['source_bones']:mesh_obj('source_'+n,source[n],'source',True)
 for n in c['tissues']:mesh_obj('tissue_'+n,source[n],'tissue',True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in created:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/'assets'/ (c['id']+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
 for o in created:o.hide_set(True)
 reports.append(c)
(OUT/'data.json').write_text(json.dumps({'status':'candidate_comparison_only','source':'Z-Anatomy Startup.blend versus existing BodyParts3D 3.0 skeleton','license':'Local research preview; per-object license review pending; no deployment','candidates':reports},ensure_ascii=False,indent=2)+'\n')
print('QUALITY',len(quality),'CASES',[(c['id'],c['status']) for c in reports])
