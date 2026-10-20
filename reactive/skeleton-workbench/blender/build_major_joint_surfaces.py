"""Split verified source connected patches; keep ambiguous compound patches intact."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'z-anatomy-candidate';S=R/'research/ossicles/Startup.blend'
audit=json.loads((O/'major-joint-surface-audit.json').read_text());bones={b['id']:b for b in json.loads((O/'structures.json').read_text())['bones']}
# Index assignments inspected using native-world centroids, medial/lateral location, opposing bone and reference anatomy.
spec={
 'scapula':[(1,'关节盂',['glenohumeral'],'肩')],
 'humerus':[(2,'肱骨头',['glenohumeral'],'肩'),(0,'肱骨小头',['humeroradial'],'肘'),(1,'肱骨滑车',['humeroulnar'],'肘')],
 'radius':[(1,'桡骨头复合区',['humeroradial','proximal_radioulnar'],'肘')],
 'ulna':[(0,'尺骨近端复合区',['humeroulnar','proximal_radioulnar'],'肘')],
 'hip':[(1,'髋臼关节区',['hip'],'髋')],
 'femur':[(1,'股骨头',['hip'],'髋'),(0,'股骨膝端复合区',['tibiofemoral','patellofemoral'],'膝')],
 'patella':[(0,'髌骨关节面',['patellofemoral'],'膝')],
 'tibia':[(0,'胫骨内侧平台',['tibiofemoral'],'膝'),(2,'胫骨外侧平台',['tibiofemoral'],'膝')]}
with bpy.data.libraries.load(str(S),link=False) as (src,dst):dst.objects=[r['source_object'] for r in audit]
objects={o.name:o for o in dst.objects if o}
for o in objects.values():bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();new=[];records=[];proof=[]
for r in audit:
 b=bones[r['bone_id']];side=b['side'];stem=r['bone_id'][5:-2];o=objects[r['source_object']];assert not r['modifiers'],'Need evaluated face provenance before exporting modified mesh';source=o.data;used=set();tasks=[]
 # Match the skeleton export's full-mesh normal repair and triangulation before splitting.
 world=[o.matrix_world@v.co for v in source.vertices];bone_center=sum(world,Vector())/len(world)
 full=bpy.data.meshes.new('provenance_'+stem+'_'+side);full.from_pydata([v-bone_center for v in world],[],[list(p.vertices) for p in source.polygons]);full.update();full.validate()
 bm=bmesh.new();bm.from_mesh(full);bm.faces.ensure_lookup_table();tag=bm.faces.layers.int.new('source_face')
 for f in bm.faces:f[tag]=f.index
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.index_update()
 triangles={}
 for f in bm.faces:triangles.setdefault(f[tag],[]).append([v.index for v in f.verts])
 bm.free()
 for index,label,connections,region in spec[stem]:
  c=r['components'][index];used.add(index);tasks.append((str(index),label,connections,region,c['source_face_indices'],False))
 remaining=[c for c in r['components'] if c['component'] not in used]
 if remaining:tasks.append(('remainder',b['name_zh'][1:]+'其他标记组',[],'其他',[i for c in remaining for i in c['source_face_indices']],True))
 covered=[]
 for suffix,label,connections,region,indices,residual in tasks:
  covered+=indices;verts=sorted({v for i in indices for v in source.polygons[i].vertices});lookup={v:j for j,v in enumerate(verts)};vs=[o.matrix_world@source.vertices[v].co for v in verts];center=sum(vs,Vector())/len(vs);faces=[]
  for i in indices:
   for f in triangles[i]:faces.append([lookup[v] for v in f])
  id='surface_patch_'+stem+'_'+side+'_'+suffix;m=bpy.data.meshes.new(id);m.from_pydata([v-center for v in vs],[],faces);m.update();bm=bmesh.new();bm.from_mesh(m);boundary=sum(e.is_boundary for e in bm.edges);junction=sum(not e.is_manifold and not e.is_boundary for e in bm.edges);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();obj=bpy.data.objects.new(id,m);obj.location=center;bpy.context.scene.collection.objects.link(obj);new.append(obj)
  for p in m.polygons:p.use_smooth=True
  note='原骨 Cartilage 材质面原位拆分，无新增厚度，不是实体软骨；边界和组织分类待解剖审核。'
  if '复合' in label:note+='源连通片跨多个关节区域，未强行细分；不能当作各子关节面的精确边界。'
  if residual:note+='本批肩肘髋膝之外的剩余面原样保留。'
  records.append(dict(id=id,name_zh=('左' if side=='L' else '右')+label+'标记面',name_en=r['source_object']+' Cartilage patch '+suffix,side=side,region=b['region'],available=True,trial=False,tissue=True,tissue_layer='surface',tissue_type='source_material_surface_annotation',bone_ids=[b['id']],joint_or_connection_ids=[c+'_'+side for c in connections] if connections else b['joint_or_connection_ids'],source_structure_id=r['source_object']+' / Cartilage patch '+suffix,source_dataset='Z-Anatomy 源材质分区',triangles=len(m.polygons),note=note,granularity='residual_source_group' if residual else 'compound_surface_patch' if '复合' in label else 'connected_surface_patch',anatomy_review='pending',rest_position_web_m=[center.x,center.z,-center.y],source_face_indices=indices,geometry_audit=dict(boundary_edges=boundary,nonmanifold_junction_edges=junction),joint_region=region,reference_ids=[] if residual else ['openstax-ap2-9.6'],semantic_review='reference_supported_candidate_not_boundary_validated'))
 expected=[i for c in r['components'] for i in c['source_face_indices']];assert len(covered)==len(set(covered)) and set(covered)==set(expected)
 proof.append(dict(bone_id=b['id'],source_faces=len(expected),exported_faces=len(covered),no_missing_or_duplicate_faces=True))
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'assets/major-joint-surfaces.glb'),export_format='GLB',use_selection=True)
scene=bpy.data.scenes.new('Shoulder elbow hip knee source surface patches');scene.unit_settings.system='METRIC'
for o in new:scene.collection.objects.link(o)
bpy.context.window.scene=scene
for o in list(bpy.data.objects):
 if o not in new:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'assets/z-major-joint-surfaces.blend'),compress=True)
(O/'major-joint-surfaces.json').write_text(json.dumps(dict(status='segmented_source_surfaces_not_volumetric_cartilage',source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),file='z-anatomy-candidate/assets/major-joint-surfaces.glb',count=len(records),replaces_ids=['surface_mark_'+r['bone_id'][5:] for r in audit],objects=records,face_conservation=proof),ensure_ascii=False,indent=2)+'\n')
print('SURFACE_PATCHES',len(records),'TARGET',sum(r['joint_region']!='其他' for r in records))
