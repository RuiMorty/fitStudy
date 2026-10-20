"""Build display derivatives and an ID-preserving latest-tissue bundle.
Local symmetric thickness reduction is not an anatomical layer-order correction.
"""
import bpy,bmesh,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent.parent
OUT=P/'z-anatomy-candidate/assets'
bpy.context.preferences.filepaths.save_version=0
reports=[];published={};bundles=[]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
def fresh(name):
 s=bpy.data.scenes.new(name);bpy.context.window.scene=s;return s
def load(p):
 
 for o in bpy.data.objects:
  if not o.name.startswith('stored_'):o['publish_name']=o.name;o.name='stored_'+str(o.as_pointer())
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(p));return [o for o in bpy.context.scene.objects if o not in before and o.type=='MESH']
def select(obs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
def export(p,obs):
 
 for o in bpy.data.objects:
  if o not in obs and not o.name.startswith('stored_'):o['publish_name']=o.name;o.name='stored_'+str(o.as_pointer())
 for o in obs:
  if o.name.startswith('stored_'):o.name=o['publish_name']
 select(obs);bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
def tree(o):
 return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons])
def refine(obs,bones,scope):
 # Near-coincident tissue surfaces only; all distances in metres.
 trees={o.name:tree(o) for o in obs};bt=[tree(o) for o in bones]
 for o in obs:
  bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.normal_update()
  # Only closed surfaces have a defined inward thickness direction.
  if any(not e.is_manifold for e in bm.edges):
   reports.append({'scope':scope,'id':o.name,'status':'open_surface_unchanged'});bm.free();continue
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
  xyz=np.array([tuple(o.matrix_world@v.co) for v in bm.verts]);center=xyz.mean(0);_,_,vh=np.linalg.svd(xyz-center,full_matrices=False);axis=(xyz-center)@vh[0];lo,hi=axis.min(),axis.max()
  original=[v.co.copy() for v in bm.verts];normals=[v.normal.copy() for v in bm.verts];depth=[0.]*len(bm.verts);limits=[0.]*len(bm.verts);protected=0
  own=trees[o.name];others=[t for name,t in trees.items() if name!=o.name and name.split('__')[0].endswith(o.name.split('__')[0][-1])]
  before=0
  for v in bm.verts:
   i=v.index;p=o.matrix_world@v.co;n=(o.matrix_world.to_3x3()@v.normal).normalized();t=(axis[i]-lo)/max(hi-lo,1e-9)
   # Endpoint candidates and bone-near areas are locked; not claimed true footprints.
   if t<.18 or t>.82 or any(tr.find_nearest(p)[3]<.0006 for tr in bt):protected+=1;continue
   hit=own.ray_cast(p-n*.000002,-n,.003)
   if hit[0] is None:continue
   thickness=hit[3]+.000002
   limits[i]=min(.00012,thickness*.18)
   near=min((tr.find_nearest(p)[3] for tr in others),default=1)
   if near<.00005:before+=1
   if near<.0003:
    edge=max(0,min(1,(t-.18)/.12,(.82-t)/.12))
    candidates=[limits[i]*edge*k/4 for k in range(5)]
    clearance=lambda d:min((tr.find_nearest(p-n*d)[3] for tr in others),default=1)
    best=max(candidates,key=clearance)
    if clearance(best)>near+1e-7:depth[i]=best
  for _ in range(3):
   depth=[min(limits[v.index],.5*depth[v.index]+.5*sum(depth[e.other_vert(v).index] for e in v.link_edges)/max(1,len(v.link_edges))) for v in bm.verts]
  for v in bm.verts:
   i=v.index;p=o.matrix_world@original[i];q=o.matrix_world@(original[i]-normals[i]*depth[i])
   d0=min((tr.find_nearest(p)[3] for tr in others),default=1);d1=min((tr.find_nearest(q)[3] for tr in others),default=1)
   if d1<d0:depth[i]=0
   v.co=original[i]-normals[i]*depth[i]
  after=sum(min((tr.find_nearest(o.matrix_world@v.co)[3] for tr in others),default=1)<.00005 for v in bm.verts if limits[v.index]>0)
  bm.to_mesh(o.data);bm.free();o.data.update()
  reports.append({'scope':scope,'id':o.name,'changed_vertices':sum(x>1e-9 for x in depth),'max_inset_mm':max(depth,default=0)*1000,'protected_vertices':protected,'near_005mm_before':before,'near_005mm_after':after,'status':'display_thickness_only_not_collision_acceptance'})
# Reviews are the authoritative versions; import their actual configured GLBs.
for scope in ['shoulder','elbow','wrist','hip','knee']:
 s=fresh(scope);folder=P/(scope+'-review');cfg=read(folder/'review-config.json');cat=read(folder/'catalog.json');obs=load(folder/('wrist-review-contact.glb' if scope=='wrist' else cfg['model']));rows={r['id']:r for r in cat['structures']};tissues=[o for o in obs if o.name.endswith('__refined') and o.name[:-9] in rows];bones=[o for o in obs if o.name.startswith('bone_')]
 if len(tissues)!=len(rows):raise RuntimeError((scope,len(tissues),len(rows)))
 if scope=='wrist':
  refine(tissues,bones,scope);export(folder/'wrist-review-overlap.glb',bones+tissues);bpy.ops.wm.save_as_mainfile(filepath=str(folder/'wrist-review-overlap.blend'),compress=True)
  cfg.update(model='wrist-review-overlap.glb',meshCount=len(bones+tissues),loadedLabel='交界厚度优化版 · 解剖待核准');write(folder/'review-config.json',cfg)
 for o in tissues:
  key=o.name[:-9];o.name=key;o['publish_name']=key;r=dict(rows[key]);r['display_source']=scope+'-review/'+cfg['model'];r['geometry_revision']=scope+'-latest-display';published[key]=r;bundles.append(o)
# Ankle ligaments still live in the source library; select named regional groups.
s=fresh('ankle');lib=read(P/'z-anatomy-candidate/ligament-library.json');arows={r['id']:r for r in lib['objects'] if r.get('source_parent') in ['Medial collateral ligament of ankle.g','Lateral collateral ligament of ankle.g','Tibiofibular syndesmosis.g','Intertarsal joints.g']};allobs=load(P/lib['file']);ankle=[o for o in allobs if o.name in arows]
if len(ankle)!=len(arows):raise RuntimeError('Ankle IDs missing')
# Load matched Z-Anatomy lower limb bones solely to protect attachment vicinity.
sourcebones=load(OUT/'region-5.glb')
for o in ankle:o.name=o['publish_name']
refine(ankle,sourcebones,'ankle')
for o in ankle:
 for face in o.data.polygons:face.use_smooth=True
export(OUT/'ankle-ligaments-overlap.glb',ankle);select(ankle+sourcebones);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ankle-ligaments-overlap.blend'),compress=True)
for o in ankle:
 r=dict(arows[o.name]);r.update(geometry_revision='ankle-overlap-display',display_source='z-anatomy-candidate/assets/ankle-ligaments-overlap.glb');o['publish_name']=o.name;published[o.name]=r;bundles.append(o)
# Export only latest tissues: no original comparison meshes or duplicate bones.
s=fresh('Latest tissues only')
for o in bundles:s.collection.objects.link(o)
select(bundles);bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
export(OUT/'latest-reviewed-tissues.glb',bundles)
for other in list(bpy.data.scenes):
 if other!=s:bpy.data.scenes.remove(other)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'latest-reviewed-tissues.blend'),compress=True)
for r in published.values():
 r.setdefault('available',True);r.setdefault('tissue',True);r.setdefault('region','下肢');r.setdefault('tissue_layer','joint' if r.get('tissue_type') in ['labrum','meniscus'] else 'ligament');r.setdefault('tissue_type','ligament');r.setdefault('joint_or_connection_ids',['patellofemoral_'+r['side']]);r.setdefault('bone_ids',['bone_patella_'+r['side'],'bone_femur_'+r['side']])
write(P/'z-anatomy-candidate/latest-reviewed-tissues.json',{'file':'z-anatomy-candidate/assets/latest-reviewed-tissues.glb','count':len(published),'objects':list(published.values()),'replaces_ids':list(published),'note':'最新显示网格；未完成全部解剖及动态验收'})
write(P/'z-anatomy-candidate/overlap-small-joints-report.json',reports)
print('PUBLISHED',len(published),'CHANGED',sum(r.get('changed_vertices',0)>0 for r in reports),flush=True)
# Synchronize display-only audit labels with the actual exported derivative.
wr=P/'wrist-review';catalog=read(wr/'catalog.json');audit=read(wr/'geometry-audit-contact.json')
changed={r['id'].removesuffix('__refined'):r for r in reports if r['scope']=='wrist' and r.get('changed_vertices',0)>0}
for row in catalog['structures']:
 if row['id'] in changed:
  row['comparison']=row['comparison'].split(' 本轮交界优化：')[0]+' 本轮交界优化：仅局部减薄近重合处，保留端部候选和贴骨邻域；没有按显示结果重新认定附着。'
for a in audit:
 if a['id'] in changed:
  a.update(audit_scope='small_joint_overlap_display_only',contact_display_note='局部厚度内退与平滑过渡，仅用于减轻近重合交界。端部候选及距骨面 0.6 mm 内的顶点锁定；不代表真实足印范围。',surface_displacement_max_mm=round(changed[a['id']]['max_inset_mm'],5))
write(wr/'catalog.json',catalog);write(wr/'geometry-audit-overlap.json',audit)
cfg=read(wr/'review-config.json');cfg['audit']='geometry-audit-overlap.json';write(wr/'review-config.json',cfg)
latest=read(P/'z-anatomy-candidate/latest-reviewed-tissues.json');lookup={r['id']:r for r in catalog['structures']}
for r in latest['objects']:
 if r['id'] in lookup:r['comparison']=lookup[r['id']]['comparison']
write(P/'z-anatomy-candidate/latest-reviewed-tissues.json',latest)
