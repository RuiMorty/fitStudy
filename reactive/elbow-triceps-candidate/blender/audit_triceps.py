"""Independent saved-mesh checks: bone overlap and distributed belly motion.
Nearest-face signed distances are local surface tests, not a full collision/force solver.
"""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/elbow-right.blend'))
ids=['muscle_triceps_'+k+'_R' for k in ['long','lateral','medial']]+['tendon_triceps_distal_R']
def mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([e.matrix_world@p.co for p in m.vertices]);f=np.array([list(p.vertices) for p in m.loop_triangles]);e.to_mesh_clear();return v,f
bpy.context.scene.frame_set(1);rest={mid:mesh(bpy.data.objects[mid])[0] for mid in ids}
maxima={mid:{bone:0 for bone in ['humerus','ulna','radius']} for mid in ids};motion={};rows=[]
for angle in np.arange(0,120.01,2.5):
 bpy.context.scene.frame_set(int(angle)+1,subframe=float(angle)%1);trees={}
 for bone in ['humerus','ulna','radius']:
  v,f=mesh(bpy.data.objects['bone_'+bone+'_R']);trees[bone]=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist())
 for mid in ids:
  v,f=mesh(bpy.data.objects[mid]);pts=np.concatenate([v,v[f].mean(axis=1)])
  for bone,tree in trees.items():
   hits=[tree.find_nearest(Vector(p)) for p in pts];signed=np.array([-h[3] if (Vector(p)-h[0]).dot(h[1])<0 else h[3] for p,h in zip(pts,hits)])
   depth=float(max(0,-signed.min())*1000);maxima[mid][bone]=max(maxima[mid][bone],depth)
   rows.append({'angle':float(angle),'structure':mid,'bone':bone,'maxInsideMm':depth,'samplesInsideOver1mm':int((signed<-.001).sum())})
  if angle==120 and mid.startswith('muscle'):
   rv=rest[mid];o=bpy.data.objects[mid];g=o.vertex_groups.get('Origin_fixed_to_bone');pins={p.index for p in o.data.vertices if g and any(w.group==g.index and w.weight>.999 for w in p.groups)}
   t=(rv[:,2]-rv[:,2].min())/np.ptp(rv[:,2]);belly=(t>.30)&(t<.75)&np.array([i not in pins for i in range(len(rv))]);d=np.linalg.norm(v-rv,axis=1)*1000
   motion[mid]={'middleUpperFreeVertices':int(belly.sum()),'medianDisplacementMm':float(np.median(d[belly])),'fractionMovingOver1mm':float((d[belly]>1).mean())}
checks={'triceps_middle_upper_bellies_participate':all(r['medianDisplacementMm']>1 and r['fractionMovingOver1mm']>.5 for r in motion.values()),'bone_surface_intrusion_under_1mm':all(v<1 for b in maxima.values() for v in b.values())}
r={'scope':'0–120 degrees every 2.5 degrees; all vertices and triangle centres. Local nearest-normal signed surface distances, not volumetric intersection or anatomical validation.','maxInsideMm':maxima,'distributedMotion':motion,'checks':checks,'samples':rows,'status':'passed' if all(checks.values()) else 'failed'}
(R/'qa/triceps-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2))
if not all(checks.values()):raise RuntimeError('Triceps surface or motion check failed')
