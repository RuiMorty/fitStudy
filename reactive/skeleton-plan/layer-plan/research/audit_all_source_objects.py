import bpy,bmesh,json,re,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;W=R.parents[2]/'skeleton-workbench';p=W/'research/ossicles/Startup.blend'
with bpy.data.libraries.load(str(p),link=False) as (src,dst):dst.objects=list(src.objects)
objects=[o for o in dst.objects if o];records=[];candidate_names=[]
for o in objects:
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'faces':len(o.data.polygons) if o.type=='MESH' else None,'vertex_groups':[g.name for g in o.vertex_groups] if o.type=='MESH' else [],'materials':[m.name for m in o.data.materials if m] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type,'enabled':m.show_viewport} for m in o.modifiers]}
 if o.type=='FONT':
  try:row['text']=o.data.body[:250]
  except UnicodeDecodeError:row['text_read_error']='invalid_utf8_in_source_font_data'
 records.append(row)
 if re.search(r'articular capsule|interpubic|annular ligament of radius|articular surface|articular cartilage|annulus|fibrous ring',o.name,re.I):
  candidate_names.append(o.name)
  if not o.users_collection:bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();details=[]
for o in objects:
 if o.name not in candidate_names:continue
 detail={'name':o.name,'type':o.type}
 if o.type=='MESH':
  e=o.evaluated_get(dg);m=e.to_mesh();bm=bmesh.new();bm.from_mesh(m);details.append({**detail,'evaluated_vertices':len(m.vertices),'evaluated_faces':len(m.polygons),'boundary_edges':sum(x.is_boundary for x in bm.edges),'nonmanifold_edges':sum(not x.is_manifold for x in bm.edges),'extent':[max((e.matrix_world@v.co)[i] for v in m.vertices)-min((e.matrix_world@v.co)[i] for v in m.vertices) for i in range(3)] if m.vertices else None});bm.free();e.to_mesh_clear()
 else:details.append(detail)
(R/'all-source-objects.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'count':len(records),'objects':records},ensure_ascii=False,indent=2)+'\n')
(R/'additional-joint-candidates.json').write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n');print('AUDITED',len(records),'DETAIL',len(details))
