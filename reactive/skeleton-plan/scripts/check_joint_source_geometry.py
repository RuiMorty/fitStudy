"""Read-only BVH screening of selected bone pairs in unmodified source coordinates."""
import json,struct
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]/'source-audit';m=json.loads((R/'mapping.json').read_text());mapping={b['id']:b['primitive_ids'] for b in m['core']};cache={};dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
def get(k):
 if k in cache:return cache[k]
 alltri=[]
 for sid in mapping[k]:
  b=(R/'raw'/(sid+'.stl')).read_bytes();n=struct.unpack('<I',b[80:84])[0];alltri.append(np.frombuffer(b,dtype=dt,offset=84,count=n)['v'].astype(float))
 tri=np.concatenate(alltri);v,f=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True);f=f.reshape(-1,3);tree=BVHTree.FromPolygons([Vector(p) for p in v],f.tolist(),all_triangles=True);cache[k]=(v,tree);return v,tree
pairs=[('肩','scapula','humerus'),('肱尺','humerus','ulna'),('肱桡','humerus','radius'),('髋','hip','femur'),('胫股','femur','tibia'),('髌股','femur','patella'),('胫距','tibia','talus'),('腓距','fibula','talus')];report=[]
for side in ['L','R']:
 for label,a,b in pairs:
  a='bone_'+a+'_'+side;b='bone_'+b+'_'+side;va,ta=get(a);vb,tb=get(b);overlap=len(ta.overlap(tb));inside=0;closest=float('inf');samples=0
  for vv,tt in [(va,tb),(vb,ta)]:
   for p in vv[::max(1,len(vv)//2500)]:
    q,n,_,d=tt.find_nearest(Vector(p));closest=min(closest,d);samples+=1
    if (Vector(p)-q).dot(n)<0:inside=max(inside,d)
  report.append(dict(name=label,side=side,bones=[a,b],triangle_intersection_pairs=overlap,sampled_max_signed_inside_mm=inside,sampled_nearest_distance_mm=closest,samples=samples))
(R/'joint-source-screening.json').write_text(json.dumps(dict(scope='Unchanged source geometry in documented mm units; triangle-pair intersection and sampled local-normal signed depth. Not a clinical joint fit or motion validation.',results=report),ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
