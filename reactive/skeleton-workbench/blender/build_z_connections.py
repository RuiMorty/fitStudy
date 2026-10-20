import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'z-anatomy-candidate';P=R.parent/'skeleton-plan/layer-plan/research';src=R/'research/ossicles/Startup.blend'
mapping=json.loads((P/'additional-mapping.json').read_text());bones={b['id']:b for b in json.loads((OUT/'structures.json').read_text())['bones']}
with bpy.data.libraries.load(str(src),link=False) as (source,dst):dst.objects=[r['source_object'] for r in mapping]
objects={o.name:o for o in dst.objects if o}
for o in objects.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();new=[];rows=[];excluded=[]
for row in mapping:
 source=objects[row['source_object']];e=source.evaluated_get(dg);m=e.to_mesh();bm=bmesh.new();bm.from_mesh(m);boundary=sum(x.is_boundary for x in bm.edges);bad=sum(not x.is_manifold for x in bm.edges);bm.free()
 if bad>boundary or not m.polygons:
  excluded.append({**row,'reason':'nonmanifold_junction_or_no_faces','boundary_edges':boundary,'nonmanifold_edges':bad});e.to_mesh_clear();continue
 vs=[e.matrix_world@v.co for v in m.vertices];fs=[list(f.vertices) for f in m.polygons];e.to_mesh_clear();center=sum(vs,Vector())/len(vs)
 mesh=bpy.data.meshes.new(row['id']);mesh.from_pydata([v-center for v in vs],[],fs);mesh.update();mesh.validate();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(row['id'],mesh);o.location=center;bpy.context.scene.collection.objects.link(o);new.append(o)
 for f in mesh.polygons:f.use_smooth=True
 regions=[bones[b]['region'] for b in row['bone_ids']];region=regions[0]
 if '上肢' in regions:region='上肢'
 elif '下肢' in regions:region='下肢'
 record={'id':row['id'],'name_zh':row['name_zh'],'name_en':row['source_object'],'side':row['side'],'region':region,'available':True,'trial':False,'tissue':True,'tissue_layer':row['layer'],'tissue_type':'fibrous_capsule' if row['layer']=='capsule' else 'ligament' if row['layer']=='ligament' else 'fibrocartilaginous_disc','bone_ids':row['bone_ids'],'joint_or_connection_ids':row['connection_ids'],'source_structure_id':row['source_object'],'source_dataset':'Z-Anatomy 原配候选','triangles':len(mesh.polygons),'note':('原始组合网格尚未逐关节拆分；' if row['granularity']=='source_group_unsegmented' else '')+'保留源坐标。关节囊开口、覆盖边界和韧带附着均待审核；关联骨只用于目录与展示。','granularity':row['granularity'],'geometry_audit':{'boundary_edges':boundary,'nonmanifold_edges':bad,'modifiers':[m.type for m in source.modifiers]},'anatomy_review':'pending','rest_position_web_m':[center.x,center.z,-center.y]};rows.append(record)
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'assets/connections.glb'),export_format='GLB',use_selection=True,export_extras=True)
scene=bpy.data.scenes.new('Z-Anatomy connection candidates');scene.unit_settings.system='METRIC'
for o in new:scene.collection.objects.link(o)
bpy.context.window.scene=scene
for o in list(bpy.data.objects):
 if o not in new:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assets/z-connections-candidate.blend'),compress=True)
(OUT/'connections.json').write_text(json.dumps({'status':'source_native_candidate_not_validated','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'file':'z-anatomy-candidate/assets/connections.glb','objects':rows,'excluded':excluded,'count':len(rows)},ensure_ascii=False,indent=2)+'\n');print('EXPORTED',len(rows),'EXCLUDED',[(x['source_object'],x['reason']) for x in excluded])
