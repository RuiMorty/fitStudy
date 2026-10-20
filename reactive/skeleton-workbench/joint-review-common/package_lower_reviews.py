"""Evaluate original Z-Anatomy objects, preserving world coordinates and source scene."""
import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parent.parent
for scope in ['hip','knee']:
 P=W/(scope+'-review');rows=json.loads((P/'source-inventory.json').read_text());bones=json.loads((P/'bone-map.json').read_text())
 mapping={r['source_structure_id']:r['id']+'__refined' for r in rows}
 mapping.update({name+'.'+s:'bone_'+key+'_'+s for name,key in bones.items() for s in ['r','l']})
 bpy.ops.wm.read_factory_settings(use_empty=True)
 with bpy.data.libraries.load(str(W/'research/ossicles/Startup.blend'),link=False) as (src,d):
  assert all(n in src.objects for n in mapping);d.objects=list(mapping)
 scene=bpy.context.scene;scene.name=scope+' review';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 source=list(d.objects)
 for o in source:
  scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False;o.hide_viewport=False
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();mat=bpy.data.materials.new('Review neutral');mat.diffuse_color=(.65,.63,.59,1);report=[]
 for o in source:
  assert o.type=='MESH',(o.name,o.type)
  e=o.evaluated_get(deps);me=bpy.data.meshes.new_from_object(e);me.transform(e.matrix_world)
  assert len(me.polygons)>0,o.name
  me.materials.clear();me.materials.append(mat)
  for f in me.polygons:f.material_index=0;f.use_smooth=True
  ob=bpy.data.objects.new(mapping[o.name],me);scene.collection.objects.link(ob);ob['source_object']=o.name;ob['anatomy_review']='pending'
  report.append({'name':ob.name,'source':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'source_world_coordinates_preserved':True})
 archive=bpy.data.scenes.new('Original source objects')
 for o in source:scene.collection.objects.unlink(o);archive.collection.objects.link(o)
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.gltf(filepath=str(P/(scope+'-review.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/(scope+'-review.blend')),compress=True)
 (P/'mesh-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('PACKAGED',scope,len(report),flush=True)
