import bpy,json,bmesh,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/next(r['file'] for r in json.loads((P/'z-anatomy-candidate/structures.json').read_text())['regions'] if r['name']=='上肢')))
data=json.loads((P/'motion/elbow-axis.json').read_text());results=[]
def blender(p):return Vector((p[0],-p[2],p[1]))
def tree(o,q=None,pivot=None):
 verts=[o.matrix_world@v.co for v in o.data.vertices]
 if q:verts=[q@(v-pivot)+pivot for v in verts]
 return BVHTree.FromPolygons(verts,[list(f.vertices) for f in o.data.polygons])
for side in ['R','L']:
 spec=data['sides'][side];pivot=blender(spec['pivot']);axis=blender(spec['axis']);h=bpy.data.objects['bone_humerus_'+side];ht=tree(h)
 for angle in range(0,121,5):
  q=Quaternion(axis,math.radians(angle));counts={}
  for bone in ['radius','ulna']:
   o=bpy.data.objects['bone_'+bone+'_'+side];counts[bone]=len(ht.overlap(tree(o,q,pivot)))
  results.append({'side':side,'angle_increment':angle,'triangle_intersection_pairs':counts})
(P/'motion/geometry-sampling.json').write_text(json.dumps({'scope':'Triangle surface intersections only, not cartilage contact or clinical acceptance. Baseline may already intersect.','samples':results},indent=2)+'\n');print('Samples',len(results),'intersection_pairs',sum(sum(r['triangle_intersection_pairs'].values()) for r in results))
