import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'z-anatomy-candidate';P=R.parent/'skeleton-plan/layer-plan/research';src=R/'research/ossicles/Startup.blend'
audit=json.loads((P/'bone-cartilage-materials.json').read_text());chosen=[x for x in audit if x['cartilage_faces']];bones={b['id']:b for b in json.loads((OUT/'structures.json').read_text())['bones']}
with bpy.data.libraries.load(str(src),link=False) as (source,dst):dst.objects=list({x['source_object'] for x in chosen})
source_objects={o.name:o for o in dst.objects if o}
for o in source_objects.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();grouped={}
for part in chosen:
 grouped.setdefault(part['bone_id'],[]).append(part)
new=[];records=[]
for bone_id,parts in grouped.items():
 vs=[];fs=[];labels=[]
 for part in parts:
  source=source_objects[part['source_object']];e=source.evaluated_get(dg);mesh=e.to_mesh();slots={i for i,m in enumerate(mesh.materials) if m and 'cartilage' in m.name.lower()};polys=[list(p.vertices) for p in mesh.polygons if p.material_index in slots];indices=sorted({i for f in polys for i in f});lookup={i:len(vs)+j for j,i in enumerate(indices)};vs.extend([e.matrix_world@mesh.vertices[i].co for i in indices]);fs.extend([[lookup[i] for i in (list(reversed(f)) if e.matrix_world.determinant()<0 else f)] for f in polys]);labels.append(part['source_object']);e.to_mesh_clear()
 if not fs:continue
 center=sum(vs,Vector())/len(vs);id='surface_mark_'+bone_id.removeprefix('bone_');mesh=bpy.data.meshes.new(id);mesh.from_pydata([v-center for v in vs],[],fs);mesh.update();mesh.validate();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(id,mesh);o.location=center;bpy.context.scene.collection.objects.link(o);new.append(o)
 for f in mesh.polygons:f.use_smooth=True
 b=bones[bone_id];records.append({'id':id,'name_zh':b['name_zh']+'软骨标记面','name_en':'Cartilage material region on '+' + '.join(labels),'side':b['side'],'region':b['region'],'available':True,'trial':False,'tissue':True,'tissue_layer':'surface','tissue_type':'source_material_surface_annotation','bone_ids':[bone_id],'joint_or_connection_ids':b['joint_or_connection_ids'],'source_structure_id':' + '.join(labels)+' / Cartilage material faces','source_dataset':'Z-Anatomy 源材质分区','triangles':len(mesh.polygons),'note':'此对象只提取源骨网格中标为 Cartilage 的面，无新增厚度；可能包含多个不连续区域。不是独立软骨实体，也不代表覆盖边界或组织分类已通过解剖审核。','granularity':'per_bone_material_partition_group','anatomy_review':'pending','rest_position_web_m':[center.x,center.z,-center.y]})
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'assets/surface-marks.glb'),export_format='GLB',use_selection=True,export_extras=True)
scene=bpy.data.scenes.new('Z-Anatomy material surface marks');scene.unit_settings.system='METRIC'
for o in new:scene.collection.objects.link(o)
bpy.context.window.scene=scene
for o in list(bpy.data.objects):
 if o not in new:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assets/z-surface-marks.blend'),compress=True)
(OUT/'surface-marks.json').write_text(json.dumps({'status':'source_surface_annotations_not_volumetric_cartilage','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'file':'z-anatomy-candidate/assets/surface-marks.glb','objects':records,'count':len(records)},ensure_ascii=False,indent=2)+'\n');print('EXPORTED_SURFACE_GROUPS',len(records))
