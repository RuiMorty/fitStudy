"""Geometric proximity evidence only; does not classify penetration or anatomical attachment."""
import bpy,bmesh,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'z-anatomy-candidate';S=R/'research/ossicles/Startup.blend'
bones={b['id']:b for b in json.loads((O/'structures.json').read_text())['bones']}
connections={c+'_'+s for c in ['glenohumeral','humeroulnar','hip','tibiofemoral'] for s in ['L','R']}
tissues=[t for t in json.loads((O/'connections.json').read_text())['objects'] if t['tissue_layer']=='capsule' and set(t['joint_or_connection_ids'])&connections]
names={t['source_structure_id'] for t in tissues}|{bones[b]['source_structure_id'] for t in tissues for b in t['bone_ids']}
with bpy.data.libraries.load(str(S),link=False) as (src,dst):dst.objects=list(names)
objects={o.name:o for o in dst.objects if o}
for o in objects.values():bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees={};results=[]
for b in {b for t in tissues for b in t['bone_ids']}:
 o=objects[bones[b]['source_structure_id']].evaluated_get(dg);m=o.to_mesh();trees[b]=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]);o.to_mesh_clear()
for t in tissues:
 o=objects[t['source_structure_id']].evaluated_get(dg);m=o.to_mesh();bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();rim={v.index for e in bm.edges if e.is_boundary for v in e.verts};bm.free();points=[o.matrix_world@m.vertices[i].co for i in sorted(rim)];distances=[]
 for p in points:distances.append(min(trees[b].find_nearest(p)[3] for b in t['bone_ids']))
 distances.sort();results.append({'id':t['id'],'name_zh':t['name_zh'],'boundary_vertices':len(rim),'rim_to_nearest_related_bone_mm':{k:round(distances[min(len(distances)-1,int(q*(len(distances)-1)))]*1000,3) if distances else None for k,q in [('min',0),('median',.5),('p95',.95),('max',1)]},'interpretation':'Rim-to-bone proximity only. An opening is not automatically damage; distance does not prove attachment or penetration. Requires anatomical footprint review.'});o.to_mesh_clear()
(O/'major-joint-assembly-audit.json').write_text(json.dumps({'status':'geometric_evidence_not_anatomy_acceptance','objects':results},ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False,indent=2))
