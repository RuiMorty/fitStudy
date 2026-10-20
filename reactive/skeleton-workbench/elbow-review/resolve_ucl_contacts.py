"""Display-only bundle clearance. Preserves anchored rows and records unresolved contacts."""
def resolve(ns):
 import math,json
 import numpy as np
 from mathutils import Vector,Quaternion
 from mathutils.bvhtree import BVHTree
 objects=ns['newobjects'];web=ns['web'];native=ns['native'];trees=ns['trees'];axisdata=ns['axisdata'];reports=[]
 for side in ['R','L']:
  obs={k:next(o for o in objects if o.name=='elbow_ucl_'+k+'_'+side+'__refined') for k in ['anterior','posterior','transverse']}
  pivot=Vector(axisdata['sides'][side]['pivot']);axis=Vector(axisdata['sides'][side]['axis']);direction=Vector((1 if side=='R' else -1,0,0))
  rest={k:[web(v.co) for v in ob.data.vertices] for k,ob in obs.items()}
  polys={k:[tuple(p.vertices) for p in ob.data.polygons] for k,ob in obs.items()}
  for angle in range(0,121,5):
   q=Quaternion(axis,math.radians(angle));qi=q.inverted();posed={}
   posed['transverse']=[q@(p-pivot)+pivot for p in rest['transverse']]
   def exposed(p):
    for b,moving in [('Humerus',False),('Ulna',True),('Radius',True)]:
     local=qi@(p-pivot)+pivot if moving else p
     hit,normal,_,dist=trees[b,side].find_nearest(local)
     if dist<.003 and (local-hit).dot(normal)<.00005:return False
    return True
   for k in ['anterior','posterior']:
    ob=obs[k];verts=([p.copy() for p in rest[k]] if angle==0 else [web(v.co) for v in ob.data.shape_keys.key_blocks['Flex_'+str(angle)].data])
    base=[p.copy() for p in verts];weights=[d.value for d in ob.data.attributes['_motion_weight'].data]
    refs=['transverse']+(['anterior'] if k=='posterior' else [])
    ref_trees=[BVHTree.FromPolygons(posed[r],polys[r],all_triangles=False) for r in refs]
    initial=0;remaining=0;max_lift=0
    for iteration in range(16):
     tr=BVHTree.FromPolygons(verts,polys[k],all_triangles=False);hits=set()
     for rt in ref_trees:
      for a,b in tr.overlap(rt):
       face=polys[k][a];center=sum((verts[v] for v in face),Vector())/len(face)
       if exposed(center):hits.add(a)
     if iteration==0:initial=len(hits)
     remaining=len(hits)
     if not hits:break
     rows=set(v//288 for face in hits for v in polys[k][face]);deltas=np.zeros(65)
     for row in rows:
      for i in range(65):deltas[i]=max(deltas[i],.00016*math.exp(-((i-row)/5)**2))
     for i,p in enumerate(verts):
      w=weights[i];delta=float(deltas[i//288])*math.sin(math.pi*w)
      # Move smooth neighborhoods together, never individual intersecting vertices.
      lift=(p-base[i]).dot(direction)
      p+=direction*min(delta,max(0,.0025-lift));max_lift=max(max_lift,(p-base[i]).length)
    posed[k]=verts
    target=ob.data.vertices if angle==0 else ob.data.shape_keys.key_blocks['Flex_'+str(angle)].data
    for v,p in zip(target,verts):v.co=native(p)
    if angle==0:
     for v,p in zip(ob.data.shape_keys.key_blocks[0].data,verts):v.co=native(p)
    reports.append({'side':side,'bundle':k,'degrees':angle,'initial_exposed_face_contacts':initial,'remaining_exposed_face_contacts':remaining,'max_display_clearance_mm':round(max_lift*1000,3)})
 ns['write'](ns['P']/'ucl-interbundle-audit.json',{'scope':'Pairwise BVH face overlap at 5 degree poses, excluding centers within bone; not continuous or full self collision acceptance. Anchored rows preserved.','samples':reports})
 print('UCL CONTACTS',sum(r['initial_exposed_face_contacts'] for r in reports),sum(r['remaining_exposed_face_contacts'] for r in reports),flush=True)
