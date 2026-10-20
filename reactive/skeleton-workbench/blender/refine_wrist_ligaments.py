"""Surface refinement of source wrist candidates. Does not certify attachment footprints.
Source Startup.blend and original export stay immutable. Run in Blender background.
"""
import bpy,bmesh,json,heapq,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[1];O=W/'z-anatomy-candidate';Q=W/'qa/ligament-fit-v1'
base=json.loads((O/'ligament-library.json').read_text())
rows=[r for r in base['objects'] if r['side'] in ['L','R'] and any(c in r['joint_or_connection_ids'] for c in ['radiocarpal_'+r['side'],'intercarpal_'+r['side'],'distal_radioulnar_'+r['side']])]
source_bones=['Radius','Ulna','Scaphoid bone','Lunate bone','Triquetrum bone','Pisiform bone','Trapezium bone','Trapezoid bone','Capitate bone','Hamate bone']+[x+' metacarpal bone' for x in ['First','Second','Third','Fourth','Fifth']]
names=[n+'.'+s for n in source_bones for s in ['l','r']]+[r['source_structure_id'] for r in rows]
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (s,d):d.objects=[n for n in names if n in s.objects]
source={o.name:o for o in d.objects if o}
for o in source.values():bpy.context.scene.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def worldmesh(o):
 e=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(e);me.transform(e.matrix_world);return me

def tree_from_mesh(me):
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 tree=BVHTree.FromBMesh(bm);bm.free();vs=[v.co for v in me.vertices]
 lo=Vector(tuple(min(v[i] for v in vs) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vs) for i in range(3)))
 return tree,lo,hi
bones={};bone_objects=[]
for name in names:
 if name in source and name.rsplit('.',1)[0] in source_bones:
  me=worldmesh(source[name]);bones[name]=tree_from_mesh(me);ob=bpy.data.objects.new('reference_'+name,me);bpy.context.scene.collection.objects.link(ob);bone_objects.append(ob)

def nearest(v,t):return t[0].find_nearest(v)
def inside(v,t):
 if any(v[i]<t[1][i]-1e-6 or v[i]>t[2][i]+1e-6 for i in range(3)):return False
 p,n,_,d=nearest(v,t)
 if (v-p).dot(n)>=-1e-7:return False
 # A nearest-normal sign alone is unreliable around concavities. Require ray parity.
 votes=0
 for direction in [Vector((.743,.311,.593)).normalized(),Vector((-.217,.893,.394)).normalized(),Vector((.413,-.537,.736)).normalized()]:
  point=v.copy();count=0
  for _ in range(50):
   hit,normal,index,distance=t[0].ray_cast(point,direction)
   if hit is None:break
   count+=1;point=hit+direction*1e-6
  votes+=count%2
 return votes>=2

def project(v,t,clearance,palmar=False,dorsal=False):
 p,n,_,dist=nearest(v,t)
 if palmar or dorsal:
  sign=-1 if palmar else 1;origin=v.copy();origin.y=t[1].y-.02 if palmar else t[2].y+.02
  hit,normal,idx,d=t[0].ray_cast(origin,Vector((0,-sign,0)))
  if hit is not None:return hit+Vector((0,sign*clearance,0))
 return p+n*clearance

route_palmar=False
def resolve(v,obstacles,clearance=.00022,palmar=False,dorsal=False):
 for _ in range(8):
  changed=False
  for name,t in obstacles.items():
   p,n,idx,dist=nearest(v,t)
   if inside(v,t) or (dist<clearance and (v-p).dot(n)>=0):
    v=project(v,t,clearance,route_palmar,False);changed=True
  if not changed:break
 return v

def audit(me,obstacles):
 samples=[v.co.copy() for v in me.vertices]
 # Vertex + triangle-centroid sampling tests the actual solidified surface.
 me.calc_loop_triangles()
 samples += [sum((me.vertices[i].co for i in t.vertices),Vector())/3 for t in me.loop_triangles]
 result={}
 for name,t in obstacles.items():
  ds=[]
  for v in samples:
   if inside(v,t):
    p,n,idx,d=nearest(v,t)
    if d>.00015:ds.append(d*1000)
  if ds:result[name]={'samples':len(ds),'max_depth_mm':round(max(ds),4)}
 return result
def ulnocapitate_sheet(o,local,previous):
 # Follow the two original longitudinal rails, then route continuously on the
 # palmar side. The source rails constrain location; they are not certified footprints.
 raw=[o.matrix_world@v.co for v in o.data.vertices]
 pairs=[(6,7),(10,11),(4,5),(8,9),(1,3),(0,2)]
 rails=[[raw[pair[j]] for pair in pairs] for j in range(2)]
 def catmull(points,t):
  z=t*(len(points)-1);i=min(int(z),len(points)-2);u=z-i
  a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(i+2,len(points)-1)]
  return (2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)*.5
 obstacles=dict(local);obstacles.update({n:t for n,t in previous.items() if n.endswith(o.name[-2:]) and any(x in n for x in ['Palmar scaphotriquetral','Palmar lunotriquetral','Radiate carpal'])})
 length=96;width=12;vertices=[]
 for i in range(length+1):
  t=i/length;a=catmull(rails[0],t);b=catmull(rails[1],t)
  for j in range(width+1):
   v=a.lerp(b,j/width)
   for name,tree in obstacles.items():
    if tree[1].x<=v.x<=tree[2].x and tree[1].z<=v.z<=tree[2].z:
     start=Vector((v.x,tree[1].y-.02,v.z));hit,normal,idx,d=tree[0].ray_cast(start,Vector((0,1,0)))
     if hit is not None:v.y=min(v.y,hit.y-.00032)
   vertices.append(v)
 # Smooth out the envelope by moving only outward; never push back through it.
 for _ in range(18):
  old=[v.copy() for v in vertices]
  for i in range(1,length):
   for j in range(1,width):
    idx=i*(width+1)+j;average=sum(old[k].y for k in [idx-1,idx+1,idx-width-1,idx+width+1])/4
    vertices[idx].y=min(old[idx].y,old[idx].y*.35+average*.65)
 faces=[]
 for i in range(length):
  for j in range(width):
   a=i*(width+1)+j;faces.append((a,a+1,a+width+2,a+width+1))
 me=bpy.data.meshes.new('Continuous palmar ulnocapitate surface');me.from_pydata(vertices,[],faces);me.update();return me

new=[];report=[];outrows=[]
# Intercarpal source surfaces precede the superficial ulnocapitate crossing.
rows.sort(key=lambda r:('Ulnocapitate' in r['source_structure_id'],r['id']))
ligtrees={}
for row in rows:
 name=row['source_structure_id'];route_palmar=name.startswith('Ulnocapitate');o=source[name];side=name[-1];local={n:t for n,t in bones.items() if n.endswith('.'+side)}
 before=worldmesh(o);before_audit=audit(before,local)
 for mod in o.modifiers:
  if mod.type=='SOLIDIFY':mod.show_viewport=False;mod.show_render=False
  if mod.type=='SUBSURF':mod.levels=3;mod.render_levels=3
 if not any(m.type=='SUBSURF' for m in o.modifiers):
  m=o.modifiers.new('Surface resolution','SUBSURF');m.subdivision_type='SIMPLE';m.levels=3;m.render_levels=3
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();me=ulnocapitate_sheet(o,local,ligtrees) if route_palmar else worldmesh(o)
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table()
 # Slightly round densely sampled source borders, without collapsing the whole strip.
 boundary=[v for v in bm.verts if v.is_boundary]
 for _ in range(2):
  positions={v:(v.co*.8+sum((e.other_vert(v).co for e in v.link_edges),Vector())*(.2/len(v.link_edges))) for v in boundary}
  for v,p in positions.items():v.co=p
 bm.to_mesh(me);bm.free()
 # Geodesic distance from border controls visual thickness taper, not tissue measurement.
 adjacency=[[] for _ in me.vertices];boundary_count={}
 for f in me.polygons:
  for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):boundary_count[tuple(sorted((a,b)))]=boundary_count.get(tuple(sorted((a,b))),0)+1
 for e in me.edges:
  a,b=e.vertices;d=(me.vertices[a].co-me.vertices[b].co).length;adjacency[a].append((b,d));adjacency[b].append((a,d))
 dist=[float('inf')]*len(me.vertices);queue=[]
 for (a,b),count in boundary_count.items():
  if count==1:
   for i in (a,b):dist[i]=0;heapq.heappush(queue,(0,i))
 while queue:
  d,i=heapq.heappop(queue)
  if d!=dist[i]:continue
  for j,w in adjacency[i]:
   if d+w<dist[j]:dist[j]=d+w;heapq.heappush(queue,(d+w,j))
 palmar=any(x in name for x in ['Palmar','Ulnocapitate','Radiate carpal','Scaphocapitate','Triquetrocapitate','Triquetrohamate','Radioscaphocapitate','Radiocapitate','Scaphotrapeziotrapezoidal'])
 dorsal='Dorsal' in name
 # Known crossing: ulnocapitate travels superficial to the proximal carpal row.
 obstacles=dict(local)
 if 'Ulnocapitate' in name:
  obstacles.update({n:t for n,t in ligtrees.items() if n.endswith('.'+side) and any(x in n for x in ['Palmar scaphotriquetral','Palmar lunotriquetral','Radiate carpal'])})
 seed_positions=[v.co.copy() for v in me.vertices];contact=[]
 for i,v in enumerate(me.vertices):
  p=v.co.copy()
  if dist[i]<.0008 and not route_palmar:
   candidates=[(nearest(p,t)[3],n,t) for n,t in local.items()];d,n,t=min(candidates,key=lambda x:x[0])
   if d<.0015:
    target=project(p,t,.00010,False,False);w=(1-min(dist[i]/.0008,1))*.85;p=p.lerp(target,w);contact.append(i)
  v.co=resolve(p,obstacles,.00024,palmar,dorsal)
 # Relax the displaced sheet and reproject; no blanket shrinkwrap to unrelated bones.
 for _ in range(3):
  coords=[v.co.copy() for v in me.vertices]
  for i,v in enumerate(me.vertices):
   if dist[i]>.0003 and adjacency[i]:v.co=coords[i].lerp(sum((coords[j] for j,w in adjacency[i]),Vector())/len(adjacency[i]),.25)
   v.co=resolve(v.co,obstacles,.00024,palmar,dorsal)
 center=Vector(row['rest_position_web_m']);center=Vector((center.x,-center.z,center.y))
 me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 obj=bpy.data.objects.new(row['id'],me);bpy.context.scene.collection.objects.link(obj)
 vg=obj.vertex_groups.new(name='visual_thickness_taper')
 for i,d in enumerate(dist):vg.add([i],.18+.82*min(d/.0012,1),'REPLACE')
 contact_group=obj.vertex_groups.new(name='source_border_contact_candidates_not_anatomical_footprints')
 if contact:contact_group.add(contact,1,'REPLACE')
 mod=obj.modifiers.new('Tapered schematic thickness 0.22 mm','SOLIDIFY');mod.thickness=.00022;mod.offset=0;mod.vertex_group=vg.name;mod.thickness_vertex_group=0;mod.use_even_offset=False
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();final=worldmesh(obj)
 # Final collision correction on the closed mesh, including rim vertices.
 for v in final.vertices:v.co=resolve(v.co,obstacles,.000065,palmar,dorsal)
 final.update();bm=bmesh.new();bm.from_mesh(final)
 bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
 bm.to_mesh(final);bm.free()
 for v in final.vertices:v.co=resolve(v.co,obstacles,.00009,False,False)
 # Refine only remaining chords whose midpoint/centroid cuts through a bone.
 for iteration in range(3):
  bm=bmesh.new();bm.from_mesh(final);bad=set()
  for f in bm.faces:
   c=f.calc_center_median()
   if any(inside(c,t) and nearest(c,t)[3]>.00008 for t in local.values()):bad.update(f.edges)
  if not bad:bm.free();break
  bmesh.ops.subdivide_edges(bm,edges=list(bad),cuts=1,use_grid_fill=True);bm.to_mesh(final);bm.free()
  for v in final.vertices:v.co=resolve(v.co,obstacles,.00012,False,False)
 final.update();bm=bmesh.new();bm.from_mesh(final);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(final);bm.free()
 obj.modifiers.clear();obj.data=final
 ligtrees[name]=tree_from_mesh(final)
 after=audit(final,local)
 moved=[(me.vertices[i].co-seed_positions[i]).length*1000 for i in range(len(me.vertices))]
 obj['source_object']=name;obj['geometry_review']='surface fit candidate; anatomical footprint not certified';obj['visual_thickness_m']=.00022
 for f in final.polygons:f.use_smooth=True
 final.transform(__import__('mathutils').Matrix.Translation(-center));obj.location=center;new.append(obj)
 result={'id':row['id'],'source':name,'before':before_audit,'after':after,'max_surface_displacement_mm':round(max(moved),3),'vertices':len(final.vertices),'contact_candidate_vertices':len(contact)};report.append(result)
 rr=dict(row);rr['triangles']=sum(len(f.vertices)-2 for f in final.polygons);rr['geometry_revision']='wrist-surface-fit-v1';rr['note']='已对源网格细分、边缘渐薄并校正静态骨面穿插；贴骨区域依据源边界修整，不等于已核准解剖足印。厚度为显示参数，非测量值。';rr['geometry_audit']={'static_bone_surface_sampling':after,'source_vertex_positions_preserved':False,'source_file_preserved':True};outrows.append(rr)
 print('REFINED',name,'before',len(before_audit),'after',len(after),flush=True)
# Hide imported references, retain explicit bone copies in editable scene.
for o in source.values():o.hide_render=True;o.hide_set(True)
for ob in list(bpy.context.scene.objects):
 if ob not in new and ob not in bone_objects:ob.hide_render=True
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'assets/wrist-ligaments-refined.glb'),export_format='GLB',use_selection=True,export_extras=True)
# Keep only the intended reference and editable objects in the saved review scene.
scene=bpy.data.scenes.new('Wrist ligament surface revision');scene.unit_settings.system='METRIC'
for o in new+bone_objects:scene.collection.objects.link(o)
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(O/'assets/wrist-ligaments-refined.blend'),compress=True)
(O/'wrist-ligaments-refined.json').write_text(json.dumps({'file':'z-anatomy-candidate/assets/wrist-ligaments-refined.glb','count':len(outrows),'objects':outrows,'replaces_ids':[x['id'] for x in outrows],'status':'surface_fit_candidate_not_anatomy_accepted'},ensure_ascii=False,indent=2)+'\n')
(Q/'refinement-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('DONE',len(new),flush=True)
