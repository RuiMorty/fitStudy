import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;W=P.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'z-anatomy-candidate/assets/wrist-ligaments-refined.blend'))
sc=bpy.context.scene
mat=bpy.data.materials.new('Review bone');mat.diffuse_color=(.62,.59,.52,1)
lig=bpy.data.materials.new('Review ligament');lig.diffuse_color=(.88,.84,.73,1)
sel=bpy.data.materials.new('Review ulnocapitate');sel.diffuse_color=(.40,.62,.28,1)
for o in sc.objects:
 o.hide_render=not (o.name.endswith('.l') or o.name.endswith('_L'))
 if o.type=='MESH':o.data.materials.clear();o.data.materials.append(mat if o.name.startswith('reference_') else sel if 'ulnocapitate' in o.name else lig)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Review world');sc.world.color=(.10,.10,.10);sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
center=Vector((.265,-.025,.845));cam=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.13
for name,offset in [('palmar',(0,-.4,.02)),('oblique',(.22,-.4,.10)),('dorsal',(0,.4,.02)),('oblique2',(-.22,-.4,.10))]:
 cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/('after-'+name+'.png'));bpy.ops.render.render(write_still=True)
