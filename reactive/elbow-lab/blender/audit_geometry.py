import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/elbow-right.blend'))
data=json.loads((ROOT/'data/structures.json').read_text());muscles=[s for s in data['structures'] if s['type']=='muscle'];bones=[s for s in data['structures'] if s['type']=='bone'];result={'note':'Triangle overlaps detect surface intersections, not anatomical contact validity; intended attachment junctions included. All surfaces schematic.','angles':[]}
def bvh(o):
 deps=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(deps);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];f=[list(p.vertices) for p in m.polygons];tree=BVHTree.FromPolygons(v,f);e.to_mesh_clear();return tree
for a in [0,30,60,90,120]:
 bpy.context.scene.frame_set(a+1);trees={s['id']:bvh(bpy.data.objects[s['id']]) for s in muscles+bones};row={'angle':a,'boneMuscleSurfaceIntersections':{},'muscleSurfaceIntersections':{},'anchorSurfaceDistancesMm':{}}
 for s in muscles:
  for bi in bones:
   hits=trees[s['id']].overlap(trees[bi['id']])
   if hits:row['boneMuscleSurfaceIntersections'][s['id']+' / '+bi['id']]=len(hits)
  for end,name in enumerate(['origin__','insertion__']):
   p=bpy.data.objects[name+s['id']].matrix_world.translation;nearest=trees[s['bones'][end]].find_nearest(p);row['anchorSurfaceDistancesMm'][name+s['id']]=round(nearest[3]*1000,3)
 for i,s in enumerate(muscles):
  for other in muscles[i+1:]:
   hits=trees[s['id']].overlap(trees[other['id']])
   if hits:row['muscleSurfaceIntersections'][s['id']+' / '+other['id']]={'pairs':len(hits),'firstMusclePathFraction':[round(min(x[0] for x in hits)/16/36,2),round(max(x[0] for x in hits)/16/36,2)],'secondMusclePathFraction':[round(min(x[1] for x in hits)/16/36,2),round(max(x[1] for x in hits)/16/36,2)]}
 result['angles'].append(row)
(ROOT/'qa/geometry-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
