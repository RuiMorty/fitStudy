import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'z-anatomy-candidate';source_file=R/'research/ossicles/Startup.blend'
bones=json.loads((R/'data/structures.json').read_text())['bones'];names=json.loads((R/'research/ossicles/z-all-object-names.json').read_text())
ordinals=['','First','Second','Third','Fourth','Fifth','Sixth','Seventh','Eighth','Ninth','Tenth','Eleventh','Twelfth']
mapping=[]
for bone in bones:
 id=bone['id'];en=bone['name_en'];side='.'+bone['side'].lower() if bone['side']!='M' else '';mapped=[en+side]
 if 'vertebra_' in id:
  seg=id.split('_')[2];mapped=[{'C1':'Atlas (C1)','C2':'Axis (C2)'}.get(seg,'Vertebra '+seg)]
 elif id=='bone_sternum_M':mapped=['Manubrium of sternum','Body of sternum','Xiphoid process']
 elif 'rib_' in id:mapped=[ordinals[int(id.split('_')[2])]+' rib'+side]
 elif 'metacarpal_' in id or 'metatarsal_' in id:mapped=[ordinals[int(id.split('_')[2])]+' '+id.split('_')[1]+' bone'+side]
 elif 'phalanx_' in id:
  bits=id.split('_');mapped=[bits[4].capitalize()+' phalanx of '+ordinals[int(bits[3])].lower()+' finger of '+bits[1]+side]
 elif mapped[0] not in names and en+' bone'+side in names:mapped=[en+' bone'+side]
 missing=[n for n in mapped if n not in names]
 mapping.append({'id':id,'source_objects':mapped,'missing':missing})
(OUT/'mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
missing=[m for m in mapping if m['missing']];print('MISSING',missing,flush=True)
with bpy.data.libraries.load(str(source_file),link=False) as (src,dst):dst.objects=list({n for m in mapping if not m['missing'] for n in m['source_objects']})
imported={o.name:o for o in dst.objects if o}
for o in imported.values():
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();created=[];rows=[]
for bone,m in zip(bones,mapping):
 row={k:bone[k] for k in ['id','name_zh','name_en','side','region','joint_or_connection_ids']};row.update(available=not bool(m['missing']),trial=False,source_dataset='Z-Anatomy 候选',source_structure_id=' + '.join(m['source_objects']),source_objects=m['source_objects'],anatomy_review='pending',assembly_review='pending',note='沿用 Z-Anatomy 原配世界位置与尺寸；未缩放配准至现用骨架。解剖、许可和装配待核对。')
 rows.append(row)
 if not row['available']:continue
 verts=[];faces=[];mirror=[]
 for n in m['source_objects']:
  o=imported[n];e=o.evaluated_get(dg);mesh=e.to_mesh();offset=len(verts);verts.extend([e.matrix_world@v.co for v in mesh.vertices]);faces.extend([[offset+i for i in f.vertices] for f in mesh.polygons]);e.to_mesh_clear();mirror.append(o.matrix_world.determinant()<0)
 center=sum(verts,Vector())/len(verts);mesh=bpy.data.meshes.new(bone['id']+'_z');mesh.from_pydata([v-center for v in verts],[],faces);mesh.update();mesh.validate(verbose=False);bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 obj=bpy.data.objects.new(bone['id'],mesh);obj.location=center;bpy.context.scene.collection.objects.link(obj);obj['source_objects']=' + '.join(m['source_objects']);obj['review_status']='candidate_pending';created.append(obj)
 for f in mesh.polygons:f.use_smooth=True
 row.update(triangles=len(mesh.polygons),upstream_reflection=any(mirror),rest_position_web_m=[center.x,center.z,-center.y])
print('BUILT',len(created),'TRIANGLES',sum(r.get('triangles',0) for r in rows),flush=True)
# Export only derived bones. No source deletion or source-file save.
regions=[]
for region in dict.fromkeys(b['region'] for b in rows):
 bpy.ops.object.select_all(action='DESELECT');ids={b['id'] for b in rows if b['region']==region and b['available']}
 for o in created:o.select_set(o.name in ids)
 file='assets/region-'+str(len(regions))+'.glb';bpy.ops.export_scene.gltf(filepath=str(OUT/file),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
 regions.append({'name':region,'file':'z-anatomy-candidate/'+file,'bytes':(OUT/file).stat().st_size})
# Save editable candidate in a new scene containing only the extracted skeleton.
new_scene=bpy.data.scenes.new('Z-Anatomy skeleton candidate')
new_scene.unit_settings.system='METRIC';new_scene.unit_settings.scale_length=1
for o in created:new_scene.collection.objects.link(o)
bpy.context.window.scene=new_scene
for o in list(bpy.data.objects):
 if o not in created:bpy.data.objects.remove(o,do_unlink=True)
for old_scene in list(bpy.data.scenes):
 if old_scene!=new_scene:bpy.data.scenes.remove(old_scene)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assets/z-skeleton-candidate.blend'),compress=True)
(OUT/'structures.json').write_text(json.dumps({'status':'source_native_candidate_not_anatomically_approved','source':'Z-Anatomy','source_sha256':hashlib.sha256(source_file.read_bytes()).hexdigest(),'source_commit':'2b6cf98a8ca012571ecb252e5c077b42a21b3b61','available_count':len(created),'core_target':206,'units':'source world coordinates adopted as meters; no fit or rescale','license_review':'Z-Anatomy CC BY-SA 4.0; per-object provenance pending, including ear references','bones':rows,'regions':regions},ensure_ascii=False,indent=2)+'\n')
print('EXPORTED',len(created),flush=True)
