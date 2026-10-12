import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT.parent/'skeleton-plan'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
mapping=json.loads((PLAN/'source-audit/mapping.json').read_text())
bones=json.loads((PLAN/'data/bones-206.json').read_text())['bones']
mat=bpy.data.materials.new('Bone | ivory'); mat.diffuse_color=(0.73,0.66,0.53,1); mat.use_nodes=True
bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) or mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled'); out=next((n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or mat.node_tree.nodes.new('ShaderNodeOutputMaterial'); mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']); bs.inputs['Base Color'].default_value=(0.73,0.66,0.53,1); bs.inputs['Roughness'].default_value=.66
regions={}; rows=[]
for b,m in zip(bones,mapping['core']):
 assert b['id']==m['id']
 row=dict(b); row['available']=m.get('file_status')=='all_required_binary_stl_downloaded_and_validated'
 row['asset_region']=b['region']; rows.append(row)
 if not row['available']: continue
 region=b['region']
 if region not in regions:
  c=bpy.data.collections.new(region); bpy.context.scene.collection.children.link(c); regions[region]=c
 parts=[]
 for f in m['files']:
  path=PLAN/'source-audit/raw'/f['filename']; assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']
  bpy.ops.wm.stl_import(filepath=str(path)); obj=bpy.context.object
  for v in obj.data.vertices: v.co *= .001
  parts.append(obj)
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0]
 if len(parts)>1:bpy.ops.object.join()
 obj=bpy.context.object; obj.name=b['id']; obj.data.name=b['id']+'_surface'
 for c in list(obj.users_collection):c.objects.unlink(obj)
 regions[region].objects.link(obj)
 # Center pivots without changing assembled world geometry; these are NOT joint centers.
 center=sum((Vector(v) for v in obj.bound_box),Vector())/8
 for v in obj.data.vertices:v.co-=center
 obj.location=center
 for p in obj.data.polygons:p.use_smooth=True
 obj.data.materials.clear(); obj.data.materials.append(mat)
 obj['structure_id']=b['id']; obj['name_zh']=b['name_zh']; obj['region']=region
 obj['anatomy_review']='pending'; obj['source_ids']=','.join(m['primitive_ids'])
 obj['rest_position_blender_m']=list(center); obj['pivot_type']='bbox_center_not_joint'
 row['rest_position_web_m']=[center.x,center.z,-center.y]
 row['triangles']=len(obj.data.polygons)
 row['note']='骶骨源网格可能包含尾骨，分界未审核' if 'sacrum' in b['id'] else '来源几何保留；解剖及关节配合待审核'
 print('IMPORTED',b['id'],flush=True)
manifest={'title':'全身骨架 · 来源审查版','status':'candidate_not_anatomically_validated','core_target':206,'available_count':sum(r['available'] for r in rows),'source':'BodyParts3D 3.0 / DBCLS','commit':mapping['commit'],'license':'CC BY-SA 2.1 Japan','source_to_blender':'[x,y,z] mm -> [x,y,z] m (uniform 0.001)','source_to_web':'[x,y,z] mm -> [x,z,-y] m (glTF Y-up)','operations':['uniform mm-to-m conversion','bbox object pivots with preserved world coordinates','sternum source components joined as one semantic bone','smooth shading; no surface subdivision or shape repair'],'bones':rows,'regions':[]}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/skeleton-review.blend'))
for i,(name,col) in enumerate(regions.items()):
 bpy.ops.object.select_all(action='DESELECT')
 for obj in col.objects:obj.select_set(True)
 filename=f'region-{i}.glb'
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets'/filename),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
 manifest['regions'].append({'name':name,'file':'assets/'+filename,'bytes':(ROOT/'assets'/filename).stat().st_size})
(ROOT/'data/structures.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('BUILD COMPLETE',manifest['available_count'],flush=True)
