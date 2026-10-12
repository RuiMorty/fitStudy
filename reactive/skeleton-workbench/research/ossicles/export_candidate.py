import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;OUT=R.parents[1]/'ear-candidate'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=[f'{n}.{s}' for n in ['Malleus','Incus','Stapes','Temporal bone'] for s in ['r','l']]
with bpy.data.libraries.load(str(R/'Startup.blend'),link=False) as (src,dst):dst.objects=list(names)
for o in dst.objects:
 if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
mat=bpy.data.materials.new('Candidate neutral bone');mat.use_nodes=True
node=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) or mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');output=next((n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(node.outputs['BSDF'],output.inputs['Surface']);node.inputs['Base Color'].default_value=(.6,.54,.42,1);node.inputs['Roughness'].default_value=.8
new=[];rows=[]
for source in dst.objects:
 name=source.name;kind,side=name.rsplit('.',1);prefix={'Malleus':('malleus','锤骨'),'Incus':('incus','砧骨'),'Stapes':('stapes','镫骨'),'Temporal bone':('temporal','颞骨')}[kind]
 id=f'bone_{prefix[0]}_{side.upper()}';verts=[source.matrix_world@v.co for v in source.data.vertices];center=sum(verts,Vector())/len(verts)
 mesh=bpy.data.meshes.new(id+'_surface');mesh.from_pydata([v-center for v in verts],[],[list(p.vertices) for p in source.data.polygons]);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 obj=bpy.data.objects.new(id,mesh);bpy.context.scene.collection.objects.link(obj);obj.location=center;mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=True
 obj['structure_id']=id;obj['source_object']=name;obj['review_status']='candidate_not_registered_to_main';obj['upstream_reflection']=source.matrix_world.determinant()<0
 new.append(obj)
 rows.append({'id':id,'name':('右' if side=='r' else '左')+prefix[1],'side':side,'kind':'temporal' if kind=='Temporal bone' else 'ossicle','source_object':name,'upstream_reflection':source.matrix_world.determinant()<0,'triangles':len(mesh.polygons),'bounds_source':[[min(v[i] for v in verts) for i in range(3)],[max(v[i] for v in verts) for i in range(3)]],'rest_web':[center.x,center.z,-center.y]})
for obj in list(bpy.data.objects):
 if obj not in new:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.object.select_all(action='SELECT');bpy.context.scene.unit_settings.system='METRIC'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assets/ear-candidate.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'assets/ear-candidate.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
data={'source':'Z-Anatomy / Models-of-human-anatomy','commit':'2b6cf98a8ca012571ecb252e5c077b42a21b3b61','archive_sha256':hashlib.sha256((R/'Z-Anatomy.zip').read_bytes()).hexdigest(),'status':'candidate_only_not_registered_to_current_BodyParts3D_3_0','license_review':'Z-Anatomy declares CC BY-SA 4.0; ear reference/inclusion lists Dundee CC BY-NC-SA 4.0; per-ossicle provenance not resolved. Research candidate, not approved redistribution/commercial asset.','units':'source world coordinates retained; adopted as meters for viewer, anatomical size review pending','operations':['bake source world transform including upstream mirrored left side','center object pivot without changing assembled surfaces','recalculate normals and triangulate','replace display material'],'structures':rows}
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('EXPORTED',len(rows),'objects',flush=True)
