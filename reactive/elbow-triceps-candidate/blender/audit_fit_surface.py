"""Check fitted flexor contact independently on saved, evaluated triangle centroids."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/elbow-right.blend'))
def evaluated(id):
 o=bpy.data.objects[id].evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();v=[o.matrix_world@x.co for x in m.vertices];f=[list(x.vertices) for x in m.polygons];o.to_mesh_clear();return v,f
rows=[]
for a in [0,30,60,90,120]:
 bpy.context.scene.frame_set(a+1);v,f=evaluated('muscle_brachialis_R');tree=BVHTree.FromPolygons(v,f)
 for id in ['muscle_biceps_long_R','muscle_biceps_short_R']:
  v,f=evaluated(id);ds=[]
  for poly in f:
   p=sum((v[i] for i in poly),Vector())/len(poly)
   if not .055<p.z<.173:continue
   h=tree.ray_cast(Vector((p.x,.25,p.z)),Vector((0,-1,0)),.4)[0]
   if h is not None:ds.append(max(0,(h.y-p.y)*1000))
  rows.append({'angle':a,'muscle':id,'testedCentroids':len(ds),'maxAnteriorEnvelopeIntrusionMm':max(ds,default=0),'over1mm':sum(d>1 for d in ds),'over2mm':sum(d>2 for d in ds)})
report={'scope':'Triangle-centroid sagittal envelope intrusion within z=55–173mm. A directional geometric diagnostic, not a complete collision or anatomy validation.','rows':rows}
report['checks']={'enough_surface_samples':all(r['testedCentroids']>500 for r in rows),'no_sampled_centroid_intrusion_above_2mm':all(r['over2mm']==0 for r in rows)}
report['status']='passed' if all(report['checks'].values()) else 'failed'
(ROOT/'qa/fit-surface-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))

assert report['status']=='passed', 'Fitted layer surface check failed'
