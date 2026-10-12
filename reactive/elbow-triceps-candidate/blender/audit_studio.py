import bpy,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/elbow-right.blend'));D=json.loads((ROOT/'data/structures.json').read_text());S={s['id']:s for s in D['structures']}
def bvh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]);e.to_mesh_clear();return tree
result={'scope':'Source atlas contacts are retained; adaptation is not a biomechanical contact solver. Distances measure internal attachment consistency, not anatomical validity.','angles':[]}
for angle in [0,30,60,90,120]:
 bpy.context.scene.frame_set(angle+1);trees={id:bvh(bpy.data.objects[id]) for id in S if id!='fascia_brachial_R'};r={'angle':angle,'anchorToBoneMm':{},'distalFootprintToTendonMm':{},'muscleIntersections':{}}
 for s in D['structures']:
  if s['type']!='muscle':continue
  for end,prefix in enumerate(['origin__','insertion__']):
   p=bpy.data.objects[prefix+s['id']].matrix_world.translation;r['anchorToBoneMm'][prefix+s['id']]=round(trees[s['bones'][end]].find_nearest(p)[3]*1000,4)
 for m,t in [('biceps_long','biceps'),('brachialis','brachialis'),('triceps_long','triceps')]:
  p=bpy.data.objects['insertion__muscle_'+m+'_R'].matrix_world.translation;r['distalFootprintToTendonMm'][t]=round(trees['tendon_'+t+'_distal_R'].find_nearest(p)[3]*1000,3)
 ms=[s['id'] for s in D['structures'] if s['type']=='muscle']
 for i,id in enumerate(ms):
  for other in ms[i+1:]:
   hits=trees[id].overlap(trees[other])
   if hits:r['muscleIntersections'][id+' / '+other]=len(hits)
 result['angles'].append(r)
(ROOT/'qa/geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
