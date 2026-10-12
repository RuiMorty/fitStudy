import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/skeleton-review-with-coccyx.blend'))
base=json.loads((ROOT/'data/structures.json').read_text());candidate=json.loads((ROOT/'ear-candidate/data.json').read_text())
names=[r['id'] for r in candidate['structures']]
with bpy.data.libraries.load(str(ROOT/'ear-candidate/assets/ear-candidate.blend'),link=False) as(src,dst):dst.objects=list(names)
loaded={row['id']:obj for row,obj in zip(candidate['structures'],dst.objects)}
# Libraries are requested in row order, preserve that relation despite Blender name suffixes.
for obj in dst.objects:
 if not obj.users_collection:bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.update()
def points(o):return np.array([list(o.matrix_world@v.co) for v in o.data.vertices])
def rigid(a,b):
 ac=a.mean(0);bc=b.mean(0);u,s,vt=np.linalg.svd((a-ac).T@(b-bc));r=vt.T@u.T
 if np.linalg.det(r)<0:vt[-1]*=-1;r=vt.T@u.T
 return r,bc-r@ac
report={'method':'per-side trimmed rigid temporal-surface ICP, no scale; visualization trial only','anatomy_review':'not_validated','warning':'Global temporal surface fit does not validate tympanic cavity, oval window or tympanic membrane attachment.','sides':[]};added=[];source_rows=[]
for side in ['R','L']:
 target=bpy.data.objects['bone_temporal_'+side];source=loaded['bone_temporal_'+side]
 a=points(source);b=points(target);tree=KDTree(len(b))
 for i,p in enumerate(b):tree.insert(Vector(p),i)
 tree.balance();r=np.eye(3);t=b.mean(0)-a.mean(0)
 for iteration in range(100):
  moved=a@r.T+t;nearest=[tree.find(Vector(p)) for p in moved];dist=np.array([v[2] for v in nearest]);mask=dist<=np.quantile(dist,.8)
  delta,shift=rigid(moved[mask],b[[nearest[i][1] for i in np.flatnonzero(mask)]]);r=delta@r;t=delta@t+shift
  if np.linalg.norm(shift)<1e-8 and np.linalg.norm(delta-np.eye(3))<1e-7:break
 moved=a@r.T+t;dist=np.array([tree.find(Vector(p))[2] for p in moved]);matrix=np.eye(4);matrix[:3,:3]=r;matrix[:3,3]=t
 target_bvh=BVHTree.FromPolygons([target.matrix_world@v.co for v in target.data.vertices],[list(p.vertices) for p in target.data.polygons])
 side_report={'side':side,'matrix_source_to_main':matrix.tolist(),'scale':1,'iterations':iteration+1,'temporal_vertex_nearest_mm':{'median':float(np.median(dist)*1000),'p95':float(np.quantile(dist,.95)*1000),'max':float(dist.max()*1000)},'ossicles':[]}
 for row in candidate['structures']:
  if row['side'].upper()!=side or row['kind']!='ossicle':continue
  obj=loaded[row['id']];original=points(obj);world=original@r.T+t;center=world.mean(0)
  for v,p in zip(obj.data.vertices,world):v.co=Vector(p-center)
  obj.matrix_world=Matrix.Translation(Vector(center));obj.name=row['id'];obj['trial_layer']=True;obj['source_dataset']='Z-Anatomy';obj['review_status']='rigid_fit_trial_not_anatomically_validated'
  bvh=BVHTree.FromPolygons([Vector(p) for p in world],[list(p.vertices) for p in obj.data.polygons]);overlap=len(bvh.overlap(target_bvh));d=[target_bvh.find_nearest(Vector(p))[3] for p in world]
  side_report['ossicles'].append({'id':row['id'],'temporal_intersecting_triangle_pairs':overlap,'nearest_temporal_surface_mm':float(min(d)*1000),'max_pairwise_distance_change_mm':float(np.max(np.abs(np.linalg.norm(original-original[0],axis=1)-np.linalg.norm(world-world[0],axis=1)))*1000)})
  out=dict(next(x for x in base['bones'] if x['id']==row['id']));out.update(available=True,trial=True,source_structure_id=row['source_object'],source_dataset='Z-Anatomy 候选',source_status='external_source_rigid_fit_trial',source_file='ear-candidate/assets/ear-candidate.blend',source_files=[],source_sha256=None,source_set='z_anatomy_2b6cf98_candidate',triangles=row['triangles'],rest_position_web_m=[float(center[0]),float(center[2]),float(-center[1])],anatomy_review='pending',assembly_review='rigid_surface_fit_only',note='整侧听骨链随颞骨表面刚性拟合试装；未核对鼓室与前庭窗。'+('上游左侧为镜像。' if side=='L' else '')+'具体耳部素材许可待确认。',upstream_reflection=row['upstream_reflection'],registration=matrix.tolist());source_rows.append(out);added.append(obj)
 report['sides'].append(side_report)
# Drop candidate temporal references, retain only the original main skeleton plus trial ossicles.
for side in ['R','L']:bpy.data.objects.remove(loaded['bone_temporal_'+side],do_unlink=True)
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/skeleton-with-ossicle-trial.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in added:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/ossicles-trial.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
(ROOT/'data/ossicles-trial.json').write_text(json.dumps({'status':'trial_not_anatomically_validated','source':candidate['source'],'license_review':candidate['license_review'],'file':'assets/ossicles-trial.glb','bones':source_rows,'registration_report':'data/ossicles-registration.json'},ensure_ascii=False,indent=2))
(ROOT/'data/ossicles-registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
