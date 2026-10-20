"""Publish only the user-selected shoulder display derivative to the local viewer."""
import bpy,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;O=W/'z-anatomy-candidate'
bpy.ops.wm.open_mainfile(filepath=str(P/'shoulder-review.blend'));source=bpy.context.scene;scene=bpy.data.scenes.new('Shoulder selected display');rows=json.loads((P/'source-inventory.json').read_text())
for row in rows:
 original=source.objects[row['id']+'__refined'];obj=bpy.data.objects.new(row['id'],original.data.copy());scene.collection.objects.link(obj);obj.matrix_world=original.matrix_world;center=Vector(row['rest_position_web_m']);center=Vector((center.x,-center.z,center.y));obj.data.transform(Matrix.Translation(-center));obj.location=center;row['geometry_revision']='shoulder-display-v1';row['note']='采用肩部审核页的显示优化版；仅显示效果已确认，附着足印、分束和运动尚未验收。';row['triangles']=sum(len(f.vertices)-2 for f in obj.data.polygons);row['anatomy_review']='pending'
bpy.context.window.scene=scene
for o in scene.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'assets/shoulder-ligaments-refined.glb'),export_format='GLB',use_active_scene=True,use_selection=True)
(O/'shoulder-ligaments-refined.json').write_text(json.dumps({'file':'z-anatomy-candidate/assets/shoulder-ligaments-refined.glb','count':len(rows),'objects':rows,'replaces_ids':[r['id'] for r in rows],'status':'display_selected_anatomy_pending'},ensure_ascii=False,indent=2)+'\n')
