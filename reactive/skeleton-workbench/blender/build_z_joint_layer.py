import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'z-anatomy-candidate';P=R.parent/'skeleton-plan/layer-plan';src=R/'research/ossicles/Startup.blend'
items=json.loads((P/'全身关节层台账.json').read_text())['objects'];quality={x['object']:x for x in json.loads((P/'research/joint-geometry-quality.json').read_text())['objects']};bone_rows={b['id']:b for b in json.loads((OUT/'structures.json').read_text())['bones']}
chosen=[];excluded=[]
for row in items:
 es=[e for e in row['source_evidence'] if e.get('local_mesh')]
 if not es:continue
 name=es[0]['object']
 if row['tissue_type']=='nucleus_pulposus':excluded.append({'id':row['id'],'source_object':name,'reason':'whole_disc_already_contains_nucleus_volume'});continue
 if quality[name]['nonmanifold_edges']:excluded.append({'id':row['id'],'source_object':name,'reason':'nonmanifold_geometry_pending_repair'});continue
 chosen.append((row,name))
with bpy.data.libraries.load(str(src),link=False) as (source,dst):dst.objects=[n for row,n in chosen]
objects={o.name:o for o in dst.objects if o}
for o in objects.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();new=[];rows=[]
for row,name in chosen:
 source=objects[name];ev=source.evaluated_get(dg);m=ev.to_mesh();vs=[ev.matrix_world@v.co for v in m.vertices];fs=[list(p.vertices) for p in m.polygons];ev.to_mesh_clear();center=sum(vs,Vector())/len(vs)
 mesh=bpy.data.meshes.new(row['id']);mesh.from_pydata([v-center for v in vs],[],fs);mesh.update();mesh.validate();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(row['id'],mesh);o.location=center;bpy.context.scene.collection.objects.link(o);new.append(o)
 for f in mesh.polygons:f.use_smooth=True
 region=bone_rows[row['bone_ids'][0]]['region'];side='L' if row['id'].endswith('_L') else 'R' if row['id'].endswith('_R') else 'M'
 rows.append({'id':row['id'],'name_zh':row['name_zh'],'name_en':name,'side':side,'region':region,'available':True,'trial':False,'tissue':True,'tissue_type':row['tissue_type'],'bone_ids':row['bone_ids'],'joint_or_connection_ids':row['connection_ids'],'source_structure_id':name,'source_dataset':'Z-Anatomy 原配关节组织候选','triangles':len(mesh.polygons),'note':'保留同一 Z-Anatomy 源库的原配坐标；未校准附着边界和动态关系。关联骨仅用于目录与展开参考，不代表已标定的附着足印。','anatomy_review':'pending','rest_position_web_m':[center.x,center.z,-center.y]})
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'assets/joints.glb'),export_format='GLB',use_selection=True,export_extras=True)
scene=bpy.data.scenes.new('Z-Anatomy joint layer candidate');scene.unit_settings.system='METRIC'
for o in new:scene.collection.objects.link(o)
bpy.context.window.scene=scene
for o in list(bpy.data.objects):
 if o not in new:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assets/z-joints-candidate.blend'),compress=True)
(OUT/'joints.json').write_text(json.dumps({'status':'source_native_candidate_not_validated','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'file':'z-anatomy-candidate/assets/joints.glb','objects':rows,'excluded':excluded,'count':len(rows)},ensure_ascii=False,indent=2)+'\n');print('JOINTS',len(rows),'EXCLUDED',len(excluded))
