"""Sagittal projection gap sampling: visible background between biceps and deeper tissue.
Measures model spacing, not anatomical truth. No fascia or annotation meshes included.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
tag=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'after'
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+2] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+2 else str(ROOT/'assets/elbow-right.blend'))
D=json.loads((ROOT/'data/structures.json').read_text());ids=[s['id'] for s in D['structures'] if s['type']!='fascia'];results=[]
for angle in [0,30,60,90,120]:
 bpy.context.scene.frame_set(angle+1);trees={}
 for id in ids:
  o=bpy.data.objects[id].evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();trees[id]=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]);o.to_mesh_clear()
 rows=[]
 for zi in range(60):
  z=.055+zi*.002;y0=-.045;step=.0005;row=[]
  for yi in range(250):
   hits=[]
   for id,t in trees.items():
    p,n,i,d=t.ray_cast(Vector((.13,y0+yi*step,z)),Vector((-1,0,0)),.28)
    if p is not None:hits.append((d,id))
   row.append(min(hits)[1] if hits else None)
  gaps=[];start=None
  for i,v in enumerate(row):
   if v is None and start is None:start=i
   if v is not None and start is not None:
    if start>0 and ((row[start-1] in ['bone_humerus_R','muscle_brachialis_R'] and v in ['muscle_biceps_long_R','muscle_biceps_short_R']) or (row[start-1]=='bone_humerus_R' and v=='muscle_brachialis_R')):
     gaps.append({'kind':'deep' if v=='muscle_brachialis_R' else 'superficial','widthMm':(i-start)*step*1000,'yStart':y0+start*step,'yEnd':y0+i*step})
    start=None
  rows.append({'z':z,'gaps':gaps})
 widths=[g['widthMm'] for r in rows for g in r['gaps']]
 results.append({'angle':angle,'maxGapMm':max(widths,default=0),'maxSuperficialGapMm':max((g['widthMm'] for row in rows for g in row['gaps'] if g['kind']=='superficial'),default=0),'maxDeepGapMm':max((g['widthMm'] for row in rows for g in row['gaps'] if g['kind']=='deep'),default=0),'meanAcrossSlicesMm':sum(sum(g['widthMm'] for g in r['gaps']) for r in rows)/len(rows),'slicesWithGap':sum(bool(r['gaps']) for r in rows),'rows':rows})
report={'scope':'Sagittal projected background gap between humerus/brachialis and biceps; z=55–173mm, 2mm slices, y=0.5mm sampling. Not a measured human clearance.','tag':tag,'angles':results}
(ROOT/'qa'/('layer-gaps-'+tag+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['angle','maxGapMm','maxSuperficialGapMm','maxDeepGapMm','meanAcrossSlicesMm','slicesWithGap']} for r in results],indent=2))
