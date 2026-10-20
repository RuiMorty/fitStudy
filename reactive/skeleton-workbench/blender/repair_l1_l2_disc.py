"""Bounded repair of small local topology defects, source file untouched."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'z-anatomy-candidate';S=R/'research/ossicles/Startup.blend'
with bpy.data.libraries.load(str(S),link=False) as (s,d):d.objects=['Intervertebral disc L1-L2']
source=d.objects[0];bpy.context.scene.collection.objects.link(source);bpy.context.view_layer.update();m=bpy.data.meshes.new('disc_repair');m.from_pydata([source.matrix_world@v.co for v in source.data.vertices],[],[list(f.vertices) for f in source.data.polygons]);m.update();bm=bmesh.new();bm.from_mesh(m)
def stats():return {'vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'branch_edges':sum(len(e.link_faces)>2 for e in bm.edges),'wire_edges':sum(e.is_wire for e in bm.edges)}
before=stats();bad=[e for e in bm.edges if not e.is_manifold];faces={f for e in bad for f in e.link_faces};area=sum(f.calc_area() for f in faces);assert area<.000005,area
removed=len(faces);bmesh.ops.delete(bm,geom=list(faces),context='FACES_ONLY');loose=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=loose,context='VERTS')
edges={e for e in bm.edges if e.is_boundary};loops=[]
while edges:
 e=edges.pop();group={e};queue=[e]
 while queue:
  edge=queue.pop()
  for v in edge.verts:
   for n in set(v.link_edges)&edges:edges.remove(n);group.add(n);queue.append(n)
 vs={v for e in group for v in e.verts};diam=max((a.co-b.co).length for a in vs for b in vs);assert diam<.003,diam
 filled=bmesh.ops.holes_fill(bm,edges=list(group),sides=0)['faces'];loops.append({'boundary_edges':len(group),'diameter_mm':diam*1000,'filled_faces':len(filled)})
wire=[e for e in bm.edges if e.is_wire];bmesh.ops.delete(bm,geom=wire,context='EDGES');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));after=stats();assert after['boundary_edges']==after['branch_edges']==after['wire_edges']==0,after
bm.to_mesh(m);bm.free();center=sum((v.co for v in m.vertices),Vector())/len(m.vertices)
for v in m.vertices:v.co-=center
for p in m.polygons:p.use_smooth=True
o=bpy.data.objects.new('disc_L1-L2',m);o.location=center;bpy.context.scene.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.ops.export_scene.gltf(filepath=str(O/'assets/repaired-disc.glb'),export_format='GLB',use_selection=True)
scene=bpy.data.scenes.new('L1 L2 localized topology repair');scene.collection.objects.link(o);bpy.context.window.scene=scene
for obj in list(bpy.data.objects):
 if obj!=o:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'assets/z-repaired-disc.blend'),compress=True)
record=dict(id='disc_L1-L2',name_zh='椎间盘 L1–L2（局部修复候选）',name_en='Intervertebral disc L1-L2')
record.update(side='M',region='脊柱',available=True,trial=False,tissue=True,tissue_type='intervertebral_disc',tissue_layer='joint',bone_ids=['bone_vertebra_L1_M','bone_vertebra_L2_M'],joint_or_connection_ids=['spine_vertebra_L1_vertebra_L2'],source_structure_id='Intervertebral disc L1-L2',source_dataset='Z-Anatomy 局部拓扑修复候选',triangles=len(m.polygons),note='仅修复原网格局部非流形缺陷，未调整整体位置和形状。修补边界与组织形态待解剖审核，不表示已完成椎间盘分层。',anatomy_review='pending',rest_position_web_m=[center.x,center.z,-center.y],repair_audit={'before':before,'after':after,'removed_faces':removed,'removed_area_mm2':area*1e6,'patches':loops})
(O/'repaired-disc.json').write_text(json.dumps({'status':'localized_topology_repair_not_anatomically_validated','source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'file':'z-anatomy-candidate/assets/repaired-disc.glb','count':1,'objects':[record]},ensure_ascii=False,indent=2)+'\n');print(record['repair_audit'])
