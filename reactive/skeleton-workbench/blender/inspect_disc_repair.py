import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
with bpy.data.libraries.load(str(R/'research/ossicles/Startup.blend'),link=False) as (s,d):d.objects=['Intervertebral disc L1-L2']
o=d.objects[0];bpy.context.scene.collection.objects.link(o);bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
def stats():return {'v':len(bm.verts),'e':len(bm.edges),'f':len(bm.faces),'boundary':sum(e.is_boundary for e in bm.edges),'branch':sum(len(e.link_faces)>2 for e in bm.edges),'wire':sum(e.is_wire for e in bm.edges)}
print('BEFORE',stats());bad=[e for e in bm.edges if not e.is_manifold];print('BAD',[(e.index,[v.index for v in e.verts],[f.index for f in e.link_faces],e.calc_length()) for e in bad]);seen={};dups=[]
for f in bm.faces:
 key=tuple(sorted(v.index for v in f.verts))
 if key in seen:dups.append(f)
 else:seen[key]=f
print('DUPLICATE_FACES',len(dups));bmesh.ops.delete(bm,geom=dups,context='FACES_ONLY');print('AFTER_DEDUP',stats());bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);print('AFTER_WELD',stats())
