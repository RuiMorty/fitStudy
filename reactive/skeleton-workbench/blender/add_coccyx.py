import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
# Keep the 199-object source-review master untouched for comparison.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/skeleton-review.blend'))
data_path=ROOT/'data/structures.json'
data=json.loads(data_path.read_text())
backup=ROOT/'data/supplements/structures-before-coccyx.json'
if not backup.exists():backup.write_text(json.dumps(data,ensure_ascii=False,indent=2))
data=json.loads(backup.read_text())
sac=bpy.data.objects['bone_sacrum_M']; original=sac.data.copy();original_location=sac.location.copy()
cut_z=.824
records=[]
for name,keep_lower in [('bone_sacrum_M',False),('bone_coccyx_M',True)]:
 obj=sac if not keep_lower else bpy.data.objects.new(name,original.copy())
 if keep_lower:
  sac.users_collection[0].objects.link(obj);obj.location=original_location.copy()
 else:obj.data=original.copy()
 bpy.context.view_layer.update()
 bm=bmesh.new();bm.from_mesh(obj.data)
 plane_local=obj.matrix_world.inverted()@Vector((0,0,cut_z))
 result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=plane_local,plane_no=Vector((0,0,1)),clear_outer=keep_lower,clear_inner=not keep_lower)
 boundary=[e for e in bm.edges if e.is_boundary];caps=bmesh.ops.holes_fill(bm,edges=boundary,sides=0).get('faces',[])
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
 # Independent pivots, no translation of the source surface in world space.
 points=[v.co.copy() for v in obj.data.vertices];center=Vector(tuple((min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)))
 for v in obj.data.vertices:v.co-=center
 obj.location+=center
 obj.name=name;obj.data.name=name+'_candidate_surface'
 for face in obj.data.polygons:face.use_smooth=True
 obj['structure_id']=name;obj['name_zh']='尾骨' if keep_lower else '骶骨';obj['region']='脊柱';obj['anatomy_review']='pending_segmentation_boundary';obj['source_ids']='FMA16202';obj['derived_operation']='candidate plane split at source Z=824 mm; planar cut cap, not an articular surface';obj['rest_position_blender_m']=list(obj.location)
 row=next(b for b in data['bones'] if b['id']==name)
 row.update(available=True,asset_region='脊柱',source_status='derived_segmentation_candidate',source_structure_id='FMA16202',anatomy_review='pending_segmentation_boundary',assembly_review='pending',triangles=len(obj.data.polygons),rest_position_web_m=[obj.location.x,obj.location.z,-obj.location.y],note='由同源骶尾合并网格试拆；Z=824毫米平面边界及封口待审核，不代表已确认的骶尾关节面。',derived_from='bone_sacrum_M / FMA16202',derived_operation={'type':'plane_split','source_z_mm':824,'keep':'inferior' if keep_lower else 'superior','cap':'planar_pending_review'})
 source_row=next(b for b in json.loads(backup.read_text())['bones'] if b['id']=='bone_sacrum_M')
 row['source_files']=source_row['source_files'];row['source_file']=source_row['source_file'];row['source_sha256']=source_row['source_sha256'];row['source_set']=source_row['source_set']
 bpy.context.view_layer.update()
 world=[obj.matrix_world@v.co for v in obj.data.vertices]
 records.append({'id':name,'triangles':len(obj.data.polygons),'cap_loop_edges':len(boundary),'bounds_m':[[min(v[i] for v in world) for i in range(3)],[max(v[i] for v in world) for i in range(3)]]})
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/skeleton-review-with-coccyx.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in sac.users_collection[0].objects:obj.select_set(True)
filename='assets/spine-with-coccyx.glb'
bpy.ops.export_scene.gltf(filepath=str(ROOT/filename),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
region=next(r for r in data['regions'] if r['name']=='脊柱');region.update(file=filename,bytes=(ROOT/filename).stat().st_size)
data['available_count']=sum(b['available'] for b in data['bones']);data['operations'].append('candidate coccyx segmented from FMA16202 at original Z=824 mm; split boundary and planar cap not anatomically reviewed')
data['editable_master']='assets/skeleton-review-with-coccyx.blend'
data_path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
(ROOT/'data/supplements/coccyx-report.json').write_text(json.dumps({'status':'candidate_not_anatomically_validated','cut_source_z_mm':824,'preserved_master':'assets/skeleton-review.blend','records':records,'ossicles':'not_added_no_verified_same_template_source'},ensure_ascii=False,indent=2))
print('COCCYX CANDIDATE EXPORTED',data['available_count'],flush=True)
