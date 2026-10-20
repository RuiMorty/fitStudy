"""Non-destructive shoulder appearance candidates, not calibrated footprints.
Original evaluated meshes and derivative meshes coexist in one review scene.
"""
import bpy,bmesh,json,heapq,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
rows=json.loads((P/'source-inventory.json').read_text());names=[r['source_structure_id'] for r in rows]+[b+'.'+s for b in ['Scapula','Humerus','Clavicle'] for s in ['r','l']]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=names
src={o.name:o for o in d.objects if o}
for o in src.values():bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
def evaluated(o):
 bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=bpy.data.meshes.new_from_object(e);m.transform(e.matrix_world);return m
bone_material=bpy.data.materials.new('Bone muted neutral');bone_material.diffuse_color=(.66,.63,.57,1)
lig_material=bpy.data.materials.new('Ligament ivory');lig_material.diffuse_color=(.73,.70,.63,1);lig_material.use_nodes=True
bsdf=lig_material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.73,.70,.63,1);bsdf.inputs['Roughness'].default_value=.63
out=bpy.data.scenes.new('Shoulder review');out.unit_settings.system='METRIC';report=[];assets=[];bone_trees={}
for name,o in src.items():
 if name.split('.')[0] not in ['Scapula','Humerus','Clavicle']:continue
 me=evaluated(o);ob=bpy.data.objects.new('bone_'+name.replace('.','_'),me);out.collection.objects.link(ob);me.materials.clear();me.materials.append(bone_material)
 for f in me.polygons:f.use_smooth=True
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 bone_trees[name]=BVHTree.FromBMesh(bm);bm.free();assets.append(ob)
for row in rows:
 o=src[row['source_structure_id']];orig=evaluated(o);original=bpy.data.objects.new(row['id']+'__original',orig);out.collection.objects.link(original);assets.append(original);orig.materials.clear();orig.materials.append(lig_material)
 for mod in o.modifiers:
  if mod.type=='SOLIDIFY':mod.show_viewport=False;mod.show_render=False
 me=evaluated(o);bm=bmesh.new();bm.from_mesh(me)
 # Add surface resolution without increasing Catmull-Clark boundary shrinkage.
 for _ in range(3):bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
 bm.verts.ensure_lookup_table();boundary={v for e in bm.edges if e.is_boundary for v in e.verts};before={v:v.co.copy() for v in bm.verts}
 for _ in range(5):
  next_coords={}
  for v in bm.verts:
   if v in boundary:continue
   neighbours=[e.other_vert(v) for e in v.link_edges]
   if neighbours:next_coords[v]=v.co.lerp(sum((n.co for n in neighbours),Vector())/len(neighbours),.18)
  for v,c in next_coords.items():v.co=c
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me)
 # Surface UVs use principal axes for subtle illustrative longitudinal detail.
 # Preserve the open boundary exactly; taper only the illustrative thickness.
 distances={v:0. if v in boundary else math.inf for v in bm.verts};queue=[(0.,v.index,v) for v in boundary];heapq.heapify(queue)
 while queue:
  dis,_,v=heapq.heappop(queue)
  if dis!=distances[v]:continue
  for edge in v.link_edges:
   n=edge.other_vert(v);d=dis+edge.calc_length()
   if d<distances[n]:distances[n]=d;heapq.heappush(queue,(d,n.index,n))
 # A restrained convex cross-section avoids a perfectly planar tape surface.
 # It is a display proposal, not a measured ligament thickness or strain.
 bm.normal_update()
 for v in bm.verts:
  d=distances[v]
  if d>0:v.co+=v.normal*(.00055*(1-math.exp(-d/.002)))
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me)
 xyz=np.array([v.co[:] for v in me.vertices]);center=xyz.mean(axis=0);_,_,vh=np.linalg.svd(xyz-center,full_matrices=False);long=vh[0];cross=vh[1];coords=(xyz-center)@np.stack([cross,long],axis=1);uv=me.uv_layers.new(name='Longitudinal illustration')
 for loop in me.loops:uv.data[loop.index].uv=(float(coords[loop.vertex_index,0]*800),float(coords[loop.vertex_index,1]*100))
 derivative=bpy.data.objects.new(row['id']+'__refined',me);bpy.context.scene.collection.objects.link(derivative)
 vg=derivative.vertex_groups.new(name='Illustrative edge taper')
 for v in bm.verts:vg.add([v.index],.18+.82*min(distances[v]/.002,1),'REPLACE')
 displacement=max((v.co-before[v]).length for v in bm.verts)*1000
 # End candidates are PCA boundary extremes, deliberately NOT labeled true origins.
 bv=[v.co.copy() for v in boundary];axis=Vector(long);ordered=sorted(bv,key=lambda v:v.dot(axis));k=max(2,len(ordered)//12)
 ends=[sum(p,Vector())/len(p) for p in [ordered[:k],ordered[-k:]]]
 endpoints=[]
 for point in ends:
  ds={name:round(tree.find_nearest(point)[3]*1000,3) for name,tree in bone_trees.items() if name.endswith('.'+row['side'].lower())}
  endpoints.append({'position':[point.x,point.z,-point.y],'nearest_bone':min(ds,key=ds.get),'distance_mm':min(ds.values()),'distances_mm':ds,'status':'geometric_edge_candidate_not_anatomical_footprint'})
 bm.free();mod=derivative.modifiers.new('Display thickness only, not histology','SOLIDIFY');mod.thickness=.00045;mod.offset=0;mod.vertex_group=vg.name;mod.thickness_vertex_group=0
 final=evaluated(derivative);ob=bpy.data.objects.new(row['id']+'__refined',final);# avoid duplicate name in export
 derivative.name='construction_'+row['id'];ob.name=row['id']+'__refined';out.collection.objects.link(ob);assets.append(ob);final.materials.clear();final.materials.append(lig_material)
 for f in final.polygons:f.use_smooth=True
 # Heuristic penetration flags, not watertight collision acceptance.
 flags={}
 for name,tree in bone_trees.items():
  if not name.endswith('.'+row['side'].lower()):continue
  depths=[]
  for v in final.vertices:
   p,n,_,dist=tree.find_nearest(v.co)
   if (v.co-p).dot(n)<0 and dist>.0005:depths.append(dist*1000)
  if depths:flags[name]={'samples':len(depths),'max_depth_mm':round(max(depths),2)}
 report.append({'id':row['id'],'raw_vertices':len(o.data.vertices),'original_triangles':sum(len(f.vertices)-2 for f in orig.polygons),'refined_triangles':sum(len(f.vertices)-2 for f in final.polygons),'boundary_preserved':True,'cross_section_display_relief_max_mm':0.55,'surface_displacement_max_mm':round(displacement,3),'end_candidates':endpoints,'suspected_penetration_nearest_normal_only':flags,'anatomical_status':'pending'})
bpy.context.window.scene=out
for o in out.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'shoulder-review.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'shoulder-review.blend'),compress=True)
(P/'geometry-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('DONE',len(assets),len(report),flush=True)
