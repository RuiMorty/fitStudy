"""Package existing v2 derivatives and same-source reference bones, without reshaping."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
rows=json.loads((P/'source-inventory.json').read_text())
bones={'Radius':'Radius','Ulna':'Ulna',**{x+' bone':x for x in ['Scaphoid','Lunate','Triquetrum','Pisiform','Trapezium','Trapezoid','Capitate','Hamate']},**{x+' metacarpal bone':'Metacarpal'+str(i+1) for i,x in enumerate(['First','Second','Third','Fourth','Fifth'])}}
names=[r['id'] for r in rows]+['reference_'+n+'.'+s for n in bones for s in ['r','l']]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(W/'z-anatomy-candidate/assets/wrist-ligaments-refined-v2.blend'),link=False) as (src,d):
 missing=[n for n in names if n not in src.objects];assert not missing,missing;d.objects=names
material=bpy.data.materials.new('Review neutral');material.diffuse_color=(.65,.63,.59,1)
scene=bpy.context.scene;scene.name='Wrist review';scene.unit_settings.system='METRIC'
source={o.name:o for o in d.objects}
for o in source.values():scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False;o.hide_viewport=False
bpy.context.view_layer.update();assets=[]
for name,o in source.items():
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(e);me.transform(e.matrix_world)
 if name.startswith('reference_'):
  base,side=name[len('reference_'):].rsplit('.',1);new='bone_'+bones[base]+'_'+side
 else:new=name+'__refined'
 me.materials.clear();me.materials.append(material)
 for f in me.polygons:f.material_index=0
 ob=bpy.data.objects.new(new,me);scene.collection.objects.link(ob);assets.append(ob)
 for f in me.polygons:f.use_smooth=True
# Keep loaded source objects in an editable provenance scene, not the web scene.
archive=bpy.data.scenes.new('Preserved v2 package inputs')
for o in source.values():scene.collection.objects.unlink(o);archive.collection.objects.link(o)
for o in scene.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'wrist-review.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'wrist-review.blend'),compress=True)
report=[]
for r in rows:report.append({'id':r['id'],'raw_vertices':None,'end_candidates':[],'contact_display_note':'沿用现有腕部修形 v2；本次仅打包审核，未改形。没有把几何端点当作解剖附着。','surface_displacement_max_mm':0,'suspected_penetration_nearest_normal_only':r.get('geometry_audit',{}).get('static_bone_surface_sampling',{}),'anatomical_status':'pending','audit_scope':'inherited_static_sampling_not_new_collision_verification'})
(P/'geometry-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('WRIST_ASSETS',len(assets),flush=True)
