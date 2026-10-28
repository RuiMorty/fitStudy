"""Elbow ligaments: inflate the current thin shells into fibrous bodies (elbow-fiber-v1).
Topology, attachment rows and _motion_weight are preserved; every flexion morph is
re-inflated with the rest-pose pairing, so src/elbow-motion.js works unchanged.
Previous GLBs are kept. Run: blender -b --python elbow-review/build_fiber_ligaments.py
"""
import bpy,bmesh,json,sys,runpy,math
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;O=W/'z-anatomy-candidate'
F=runpy.run_path(str(W/'joint-review-common/fiber_shell.py'))
# Peak mid-substance thickness for display, mm.
DISPLAY_THICKNESS_MM={'ucl_anterior':2.6,'ucl_posterior':1.8,'ucl_transverse':1.4,'lucl':1.8,'radial_collateral':1.8,'annular':1.6,'quadrate':1.0,'oblique_cord':1.4}
REVISION='elbow-fiber-v1'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def thickness(id_):return DISPLAY_THICKNESS_MM[next(k for k in DISPLAY_THICKNESS_MM if k in id_)]/1000
def fresh():
 bpy.ops.wm.read_factory_settings(use_empty=True)
def load(path):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));return {o.name:o for o in set(bpy.data.objects)-before}
# Bone BVHs in Blender world space, outward normals.
fresh();review=load(P/'elbow-review-supplement.glb');rest_trees={}
for name,o in review.items():
 if not name.startswith('bone_'):continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.normal_update();rest_trees[name]=BVHTree.FromBMesh(bm);bm.free()
axis=read(W/'motion/elbow-axis.json')['sides']
native=lambda p:Vector((p[0],-p[2],p[1]))
class Posed:
 """Forearm bone rotated about the candidate hinge; queries map into the rest frame."""
 def __init__(self,tree,q,pivot):self.tree,self.q,self.qi,self.pivot=tree,q,q.inverted(),pivot
 def find_nearest(self,p):
  r=self.tree.find_nearest(self.qi@(p-self.pivot)+self.pivot)
  if r[0] is None:return r
  return (self.q@(r[0]-self.pivot)+self.pivot,self.q@r[1],r[2],r[3])
def trees_for(side,angle=0):
 s=side.lower();out={}
 for name,tr in rest_trees.items():
  if not name.endswith('_'+s):continue
  if angle and not name.startswith('bone_Humerus'):
   spec=axis[side];out[name]=Posed(tr,Quaternion(native(spec['axis']).normalized(),math.radians(angle)),native(spec['pivot']))
  else:out[name]=tr
 return out
def side_of(name):return name.removesuffix('__refined')[-1]
def process(o,report=None):
 """Inflate object o in place (mesh + any shape keys)."""
 id_=o.name.removesuffix('__refined');me=o.data;mw=o.matrix_world;mi=mw.inverted();side=side_of(o.name)
 if not me.shape_keys and len(me.vertices)<600:
  # Coarse static meshes gain resolution first; never applied to morphing meshes.
  bm=bmesh.new();bm.from_mesh(me)
  for _ in range(2):bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
  bm.to_mesh(me);bm.free()
 faces=[tuple(p.vertices) for p in me.polygons]
 rest=[mw@v.co for v in me.vertices]
 ring='annular' in id_;pl=F['plan'](rest,faces,thickness(id_),ring=ring,bones=None if ring else trees_for(side))
 bonelist=list(trees_for(side).values());inside_before=sum(F['inside'](bonelist,p) for p in rest)
 def tip_gap(points):
  out=[]
  for end in (0,1):
   name=pl['end_bones'][end]
   if not name:out.append(None);continue
   tip=[p for p,t in zip(points,pl['t']) if (t<.03 if end==0 else t>.97)];ds=sorted(rest_trees[name].find_nearest(p)[3]*1000 for p in tip);out.append({'bone':name,'median_gap_mm':round(ds[len(ds)//2],3)})
  return out
 gap_before=tip_gap(rest)
 new,shrunk=F['inflate'](pl,rest,trees_for(side))
 frames=[]
 if me.shape_keys:
  keys=me.shape_keys.key_blocks
  for k in keys[1:]:
   angle=int(k.name.split('_')[1]);posed=[mw@v.co for v in k.data]
   out,_=F['inflate'](pl,posed,trees_for(side,angle));frames.append((k,out))
  for v,p in zip(keys[0].data,new):v.co=mi@p
  for k,out in frames:
   for v,p in zip(k.data,out):v.co=mi@p
 for v,p in zip(me.vertices,new):v.co=mi@p
 for uv in list(me.uv_layers):me.uv_layers.remove(uv)
 for a in [a for a in me.color_attributes]:me.color_attributes.remove(a)
 col=me.color_attributes.new('Col','FLOAT_COLOR','POINT');uv=me.uv_layers.new(name='Fiber')
 for i,c in enumerate(pl['colors']):col.data[i].color=c
 for loop in me.loops:uv.data[loop.index].uv=pl['uvs'][loop.vertex_index]
 for f in me.polygons:f.use_smooth=True
 me.update()
 inside_after=sum(F['inside'](bonelist,mw@v.co) for v in me.vertices)
 if report is not None:report.append({'id':id_,'revision':REVISION,'vertices':len(me.vertices),'display_peak_thickness_mm':thickness(id_)*1000,'paired_vertices':pl['paired'],'rim_radius_mm':round(pl['rim_radius_mm'],2),'fascicle_relief_count':pl['fascicles'],'rest_vertices_shrunk_for_bone_clearance':shrunk,'rest_vertices_inside_bone_before':inside_before,'rest_vertices_inside_bone_after':inside_after,'morph_frames_reinflated':len(frames),'seam_vertices':len(pl['seam']),'enthesis_tips_before':gap_before,'enthesis_tips_after':tip_gap([mw@v.co for v in me.vertices]),'topology_preserved':True,'anatomical_status':'pending'})
def export(path,objs,morph=False):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_attributes=True,export_vertex_color='ACTIVE',export_morph=morph,export_animations=False,export_extras=True)
# 1) Review page: bones + 16 refined ligaments.
report=[];ligs=[o for n,o in review.items() if n.endswith('__refined')]
for o in ligs:process(o,report)
export(P/'elbow-review-fiber.glb',[o for n,o in review.items() if n.startswith('bone_')]+ligs)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'elbow-fiber-ligaments.blend'),compress=True)
write(P/'geometry-audit-fiber.json',report)
# 2) Main page static objects, taken from their current published GLBs with transforms intact.
supp=read(O/'elbow-supplement.json');latest=read(O/'latest-reviewed-tissues.json')
latest_rows=[r for r in latest['objects'] if r.get('display_source','').startswith('elbow-review') and r['id'] not in supp['replaces_ids']]
rows=supp['objects']+latest_rows;ids={r['id'] for r in rows}
fresh();objs={**load(O/'assets/elbow-supplement.glb')};lat=load(O/'assets/latest-reviewed-tissues.glb');objs.update({n:o for n,o in lat.items() if n in ids})
main=[objs[r['id']] for r in rows]
for o in main:process(o)
export(O/'assets/elbow-ligaments-fiber.glb',main)
published=[]
for r,o in zip(rows,main):
 r=dict(r);r.update(geometry_revision=REVISION,display_source='z-anatomy-candidate/assets/elbow-ligaments-fiber.glb',triangles=sum(len(f.vertices)-2 for f in o.data.polygons),fiber_note='由现有薄壳按配对中面重建厚度：椭圆收边、端部渐薄、纤维束起伏均为显示参数，非组织学测量；拓扑与运动权重保持不变，附着足印仍待验收。')
 published.append(r)
write(O/'elbow-ligaments-fiber.json',{'file':'z-anatomy-candidate/assets/elbow-ligaments-fiber.glb','count':len(published),'objects':published,'replaces_ids':[r['id'] for r in published],'status':'display_candidate_anatomy_pending'})
# 3) Motion template: same inflation applied to rest and all 24 flexion morphs.
fresh();motion=load(W/'motion/elbow-ligaments-complete.glb');movers=[o for o in motion.values() if o.type=='MESH']
for o in movers:process(o)
export(W/'motion/elbow-ligaments-fiber.glb',movers,morph=True)
print('DONE review',len(ligs),'main',len(main),'motion',len(movers),flush=True)
