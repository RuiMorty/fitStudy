import bpy,json,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent;W=P.parents[1]
rows=json.loads((W/'z-anatomy-candidate/ligament-library.json').read_text())['objects']
rows=[r for r in rows if any(c in r['joint_or_connection_ids'] for c in ['radiocarpal_L','intercarpal_L','distal_radioulnar_L'])]
bones=['Radius.l','Ulna.l','Scaphoid bone.l','Lunate bone.l','Triquetrum bone.l','Pisiform bone.l','Trapezium bone.l','Trapezoid bone.l','Capitate bone.l','Hamate bone.l']
with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (s,d):d.objects=[n for n in bones+[r['source_structure_id'] for r in rows] if n in s.objects]
objs={o.name:o for o in d.objects if o}
for o in objs.values():
 bpy.context.scene.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees={};report={}
for name in bones:
 if name not in objs:continue
 o=objs[name];e=o.evaluated_get(dg);m=e.to_mesh();bm=bmesh.new();bm.from_mesh(m);bm.transform(e.matrix_world);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();print('VOLUME',name,bm.calc_volume(signed=True),flush=True);
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
 trees[name]=BVHTree.FromBMesh(bm);bm.free();e.to_mesh_clear()
for r in rows:
 o=objs[r['source_structure_id']];e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@v.co for v in m.vertices];hits={}
 for name,tree in trees.items():
  distances=[]
  for x in v:
   pt,no,idx,dist=tree.find_nearest(x)
   if (x-pt).dot(no)<-0.00015:distances.append(dist*1000)
  if distances:hits[name]={'vertices_inside':len(distances),'max_depth_mm':max(distances)}
 report[r['id']]={'source':o.name,'modifiers':[{'type':q.type,'thickness':getattr(q,'thickness',None),'levels':getattr(q,'levels',None)} for q in o.modifiers],'raw_vertices':len(o.data.vertices),'evaluated_vertices':len(v),'penetration_candidates':hits};e.to_mesh_clear()
(P/'before-audit.json').write_text(json.dumps(report,indent=2));print('Audit complete',flush=True)
# Independent diagnosis scene, no source changes.
for ob in list(bpy.context.scene.objects):
 if ob.name not in objs:ob.hide_render=True
mat=bpy.data.materials.new('bone');mat.diffuse_color=(.62,.59,.52,1)
lig=bpy.data.materials.new('ligament');lig.diffuse_color=(.88,.84,.73,1)
sel=bpy.data.materials.new('ulnocapitate');sel.diffuse_color=(.40,.62,.28,1)
for n,o in objs.items():o.data.materials.clear();o.data.materials.append(mat if n in bones else sel if 'Ulnocapitate' in n else lig)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.background_type='WORLD';sc.world.color=(.10,.10,.10);sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
center=Vector((.265,-.025,.845));camera=bpy.data.objects.new('AuditCamera',bpy.data.cameras.new('AuditCamera'));sc.collection.objects.link(camera);sc.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.13
for name,offset in [('palmar',(0,-.4,.02)),('oblique',(.22,-.4,.10)),('dorsal',(0,.4,.02))]:
 camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/('before-'+name+'.png'));bpy.ops.render.render(write_still=True)
