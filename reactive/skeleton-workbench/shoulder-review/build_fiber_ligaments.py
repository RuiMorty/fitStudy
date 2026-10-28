"""Shoulder ligaments rebuilt as closed fibrous bodies instead of solidified tape.
The Z-Anatomy source sheet is kept as the mid-surface: boundary and attachment
positions are unchanged. Thickness, cross-section and fascicle relief are display
values (DISPLAY_THICKNESS_MM), not histological measurements.
Run: blender -b --python shoulder-review/build_fiber_ligaments.py
"""
import bpy,bmesh,json,heapq,math
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;O=W/'z-anatomy-candidate'
# Peak mid-substance thickness for display; edges taper elliptically to ~0.
DISPLAY_THICKNESS_MM={'trapezoid':2.6,'conoid':3.2,'acromioclavicular':2.0,'coraco_acromial':2.4,'coracohumeral':2.2,'superior_glenohumeral':1.4,'middle_glenohumeral':1.6,'inferior_glenohumeral':2.2,'transverse_humeral':1.4,'superior_transverse_scapular':1.8,'inferior_transverse_scapular':1.0}
REVISION='shoulder-fiber-v1'
rows=json.loads((P/'source-inventory.json').read_text());names=[r['source_structure_id'] for r in rows]+[b+'.'+s for b in ['Scapula','Humerus','Clavicle'] for s in ['r','l']]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):d.objects=names
src={o.name:o for o in d.objects if o}
for o in src.values():bpy.context.scene.collection.objects.link(o)
def evaluated(o):
 bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=bpy.data.meshes.new_from_object(e);m.transform(e.matrix_world);return m
def thickness_key(id_):return next(k for k in sorted(DISPLAY_THICKNESS_MM,key=len,reverse=True) if '_'+k+'_ligament' in id_)
def smoothstep(a,b,x):x=min(max((x-a)/(b-a),0),1);return x*x*(3-2*x)
def dijkstra(bm,seeds):
 dist={v:math.inf for v in bm.verts};queue=[]
 for v in seeds:dist[v]=0.;queue.append((0.,v.index,v))
 heapq.heapify(queue)
 while queue:
  dis,_,v=heapq.heappop(queue)
  if dis!=dist[v]:continue
  for e in v.link_edges:
   n=e.other_vert(v);dd=dis+e.calc_length()
   if dd<dist[n]:dist[n]=dd;heapq.heappush(queue,(dd,n.index,n))
 return dist
bone_material=bpy.data.materials.new('Bone muted neutral');bone_material.diffuse_color=(.66,.63,.57,1)
lig_material=bpy.data.materials.new('Ligament fibrous');lig_material.use_nodes=True
bsdf=lig_material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.5
attr=lig_material.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';lig_material.node_tree.links.new(attr.outputs['Color'],bsdf.inputs['Base Color'])
out=bpy.data.scenes.new('Shoulder fiber ligaments');out.unit_settings.system='METRIC';bones={};bone_trees={};report=[];ligaments=[]
for name,o in src.items():
 if name.split('.')[0] not in ['Scapula','Humerus','Clavicle']:continue
 me=evaluated(o);ob=bpy.data.objects.new('bone_'+name.replace('.','_'),me);out.collection.objects.link(ob);me.materials.clear();me.materials.append(bone_material);bones[name]=ob
 for f in me.polygons:f.use_smooth=True
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bone_trees[name]=BVHTree.FromBMesh(bm);bm.free()
def inside_samples(mesh,side):
 # Nearest-normal heuristic as in build_models.py; screening only.
 flags={}
 for name,tree in bone_trees.items():
  if not name.endswith('.'+side):continue
  depths=[]
  for v in mesh.vertices:
   p,n,_,dist=tree.find_nearest(v.co)
   if p is not None and (v.co-p).dot(n)<0 and dist>.0005:depths.append(dist*1000)
  if depths:flags[name]={'samples':len(depths),'max_depth_mm':round(max(depths),2)}
 return flags
for row in rows:
 o=src[row['source_structure_id']];side=row['side'].lower();peak=DISPLAY_THICKNESS_MM[thickness_key(row['id'])]/1000
 for mod in o.modifiers:
  if mod.type=='SOLIDIFY':mod.show_viewport=False;mod.show_render=False
 sheet=evaluated(o);bm=bmesh.new();bm.from_mesh(sheet);bpy.data.meshes.remove(sheet)
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 # Refine until edges are ~0.5 mm so the elliptical rim can actually round.
 for _ in range(5):
  if sum(e.calc_length() for e in bm.edges)/len(bm.edges)<.0005:break
  bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=1,use_grid_fill=True)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update()
 boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
 for _ in range(6):
  nxt={v:v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),.3) for v in bm.verts if v not in boundary}
  for v,c in nxt.items():v.co=c
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 xyz=np.array([v.co[:] for v in bm.verts]);center=xyz.mean(axis=0);_,_,vh=np.linalg.svd(xyz-center,full_matrices=False);long=Vector(vh[0]);cross=Vector(vh[1])
 along=[(v.co-Vector(center)).dot(long) for v in bm.verts];lo,hi=min(along),max(along);length=hi-lo
 t={v:(along[v.index]-lo)/length for v in bm.verts}
 # Boundary near the long-axis extremes is attachment; the rest is free side edge.
 side_edge=[v for v in boundary if .07<t[v]<.93] or list(boundary)
 d_side=dijkstra(bm,side_edge)
 # Per-station extents, smoothed and linearly interpolated so nothing steps between bins.
 bins=24;halfwidth=[0.]*bins;across={};cmin=[math.inf]*bins;cmax=[-math.inf]*bins
 for v in bm.verts:
  b=min(int(t[v]*bins),bins-1);c=v.co.dot(cross);across[v]=c
  halfwidth[b]=max(halfwidth[b],d_side[v]);cmin[b]=min(cmin[b],c);cmax[b]=max(cmax[b],c)
 def fill(a):
  known=[i for i in range(bins) if math.isfinite(a[i]) and a[i]!=0]
  return [a[min(known,key=lambda k:abs(k-i))] if not (math.isfinite(a[i]) and a[i]!=0) else a[i] for i in range(bins)]
 def smooth(a):
  for _ in range(3):a=[(a[max(0,i-1)]+2*a[i]+a[min(bins-1,i+1)])/4 for i in range(bins)]
  return a
 halfwidth,cmin,cmax=smooth(fill(halfwidth)),smooth(fill(cmin)),smooth(fill(cmax))
 def at(a,tt):f=min(max(tt*bins-.5,0),bins-1.001);i=int(f);return a[i]+(a[i+1]-a[i])*(f-i)
 width=max(cmax[b]-cmin[b] for b in range(bins))
 fascicles=max(2,round(width*1000/2.4))
 profile={};s_of={}
 for v in bm.verts:
  x=min(d_side[v]/max(at(halfwidth,t[v]),1e-5),1);lo_c,hi_c=at(cmin,t[v]),at(cmax,t[v]);s=min(max((across[v]-lo_c)/max(hi_c-lo_c,1e-6),0),1);s_of[v]=s
  ellipse=math.sqrt(max(0,1-(1-x)**2));enthesis=.4+.6*smoothstep(0,.22,min(t[v],1-t[v]))
  ridge=1+.13*x*math.cos(2*math.pi*fascicles*s)
  profile[v]=(x,max(.00005,peak*ellipse*enthesis*ridge))
 # Grow away from the nearest bone; centred where the band spans free space.
 trees=[tr for n,tr in bone_trees.items() if n.endswith('.'+side)];below={}
 for v in bm.verts:
  dn=min((tr.ray_cast(v.co,-v.normal,.004)[3] or .004 for tr in trees),default=.004);dp=min((tr.ray_cast(v.co,v.normal,.004)[3] or .004 for tr in trees),default=.004)
  below[v]=(dn,dp,.12 if dn<dp and dn<.003 else .88 if dp<dn and dp<.003 else .5)
 bias={v:below[v][2] for v in bm.verts}
 for _ in range(8):bias={v:.5*bias[v]+.5*sum(bias[e.other_vert(v)] for e in v.link_edges)/len(v.link_edges) for v in bm.verts}
 positions=[];colors=[];uvs=[];n=len(bm.verts)
 for layer in (0,1):
  for v in bm.verts:
   x,th=profile[v];a=bias[v];dn,dp,_=below[v];free=min(t[v],1-t[v])>.08
   down=a*th;up=(1-a)*th
   # Away from attachments keep the deep face just above the bone surface.
   if free and down>dn-.00012:extra=down-max(0,dn-.00012);down-=extra;up+=extra
   if free and up>dp-.00012:extra=up-max(0,dp-.00012);up-=extra;down+=extra
   positions.append(v.co+v.normal*up if layer==0 else v.co-v.normal*down)
   e=min(t[v],1-t[v]);base=Vector((.78,.77,.75)).lerp(Vector((.93,.90,.84)),x**.6);base=Vector((.84,.76,.62)).lerp(base,smoothstep(0,.12,e))
   # Design values are sRGB; glTF vertex colours are linear.
   colors.append((*(c**2.2 for c in base),1));uvs.append((s_of[v]*width*1000/8,t[v]*length*1000/8))
 # Added thickness must not enter bone where the source mid-surface was outside;
 # source-level intersections are left as-is rather than hidden.
 def inside(p):
  for tr in trees:
   q,nn,_,dist=tr.find_nearest(p)
   if q is not None and (p-q).dot(nn)<0:return q,nn
 pushed=0
 for v in bm.verts:
  mid=inside(v.co)
  for i in (v.index,v.index+n):
   hit=inside(positions[i])
   if not hit:continue
   # Mid-surface already in bone: never extend deeper than the source does.
   if mid:
    if (positions[i]-hit[0]).length>(v.co-mid[0]).length:positions[i]=v.co.copy();pushed+=1
   else:positions[i]=hit[0]+hit[1]*.0001;pushed+=1
 faces=[[f.verts[0].index,f.verts[1].index,f.verts[2].index] for f in bm.faces]
 faces+=[[i+n for i in reversed(f)] for f in faces]
 for e in bm.edges:
  if not e.is_boundary:continue
  f=e.link_faces[0];a,b=e.verts[0].index,e.verts[1].index;loop=[l.vert.index for l in f.loops];i=loop.index(a)
  if loop[(i+1)%3]!=b:a,b=b,a
  faces.append([b,a,a+n,b+n])
 # Light relaxation of the finished body removes push-out spikes and residual facets.
 neighbours=[set() for _ in positions]
 for f in faces:
  for i,a in enumerate(f):neighbours[a].update(f[:i]+f[i+1:])
 for _ in range(3):positions=[p.lerp(sum((positions[j] for j in nb),Vector())/len(nb),.35) for p,nb in zip(positions,neighbours)]
 bm.free()
 me=bpy.data.meshes.new(row['id']);me.from_pydata([p[:] for p in positions],[],faces);me.validate()
 col=me.color_attributes.new('Col','FLOAT_COLOR','POINT');uv=me.uv_layers.new(name='Fiber')
 for i,c in enumerate(colors):col.data[i].color=c
 for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));closed=all(e.is_manifold for e in bm.edges);volume=abs(bm.calc_volume());bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 me.materials.append(lig_material)
 rest=Vector(next(r for r in json.loads((O/'latest-reviewed-tissues.json').read_text())['objects'] if r['id']==row['id'])['rest_position_web_m']);rest=Vector((rest.x,-rest.z,rest.y))
 me.transform(Matrix.Translation(-rest));ob=bpy.data.objects.new(row['id'],me);ob.location=rest;out.collection.objects.link(ob);ligaments.append(ob)
 world=me.copy();world.transform(Matrix.Translation(rest))
 report.append({'id':row['id'],'revision':REVISION,'display_peak_thickness_mm':peak*1000,'fascicle_relief_count':fascicles,'thickness_vertices_pushed_out_of_bone':pushed,'length_mm':round(length*1000,1),'width_mm':round(width*1000,1),'triangles':sum(len(f.vertices)-2 for f in me.polygons),'closed_manifold':closed,'volume_mm3':round(volume*1e9,1),'mid_surface_boundary_preserved':True,'suspected_penetration_nearest_normal_only':inside_samples(world,side),'anatomical_status':'pending'})
 bpy.data.meshes.remove(world)
bpy.context.window.scene=out
for s in list(bpy.data.scenes):
 if s!=out:bpy.data.scenes.remove(s)
def export(path,objs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_vertex_color='ACTIVE',export_normals=True)
export(O/'assets/shoulder-ligaments-fiber.glb',ligaments)
# Review page expects bone_* plus <id>__refined objects in one file.
review=[]
for ob in ligaments:c=ob.copy();c.name=ob.name+'__refined';out.collection.objects.link(c);review.append(c)
export(P/'shoulder-review-fiber.glb',list(bones.values())+review)
for c in review:bpy.data.objects.remove(c)
bpy.data.orphans_purge(do_recursive=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'shoulder-fiber-ligaments.blend'),compress=True)
latest={r['id']:r for r in json.loads((O/'latest-reviewed-tissues.json').read_text())['objects']}
published=[]
for r in report:
 row=dict(latest[r['id']]);row.update(geometry_revision=REVISION,display_source='z-anatomy-candidate/assets/shoulder-ligaments-fiber.glb',triangles=r['triangles'],note='源片作中面重建的闭合纤维体：透镜形截面、端部渐薄、纤维束起伏均为显示参数，非组织学测量；附着足印仍待验收。')
 published.append(row)
(O/'shoulder-ligaments-fiber.json').write_text(json.dumps({'file':'z-anatomy-candidate/assets/shoulder-ligaments-fiber.glb','count':len(published),'objects':published,'replaces_ids':[r['id'] for r in published],'status':'display_candidate_anatomy_pending'},ensure_ascii=False,indent=2)+'\n')
(P/'geometry-audit-fiber.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('DONE',len(ligaments),'closed',sum(r['closed_manifold'] for r in report),flush=True)
