"""Inflate thin ligament shells into fibrous display bodies without changing topology.
Each vertex is paired with the opposite layer (ray along its normal); the pair's
midpoint is kept and the half-thickness is rebuilt with an elliptical rim, fascicle
relief and thinner entheses. Because topology is untouched, morph frames can be
re-inflated with the same pairing. Thickness values are display parameters only.
"""
import heapq,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def smoothstep(a,b,x):x=min(max((x-a)/(b-a),0),1);return x*x*(3-2*x)

def triangles(faces):return [(f[0],f[i],f[i+1]) for f in faces for i in range(1,len(f)-1)]

def vertex_normals(verts,tris):
 normals=[Vector() for _ in verts]
 for a,b,c in tris:
  n=(verts[b]-verts[a]).cross(verts[c]-verts[a])
  for i in (a,b,c):normals[i]+=n
 volume=sum(verts[a].dot(verts[b].cross(verts[c])) for a,b,c in tris)
 return [n.normalized()*(1 if volume>=0 else -1) for n in normals]

def inside(trees,p):
 # Nearest-normal test on closed bone meshes; a screening heuristic, not CSG.
 for tr in trees:
  q,n,_,_=tr.find_nearest(p)
  if q is not None and (p-q).dot(n)<0:return True
 return False

def plan(verts,faces,peak,ring=False,rim_radius=.0014,bones=None,enthesis_length=.25,flare=1.,seam_gap=.0015):
 """bones: {name: rest BVH}; ends within 2.5 mm of a bone are blended into it."""
 tris=triangles(faces);normals=vertex_normals(verts,tris);bvh=BVHTree.FromPolygons(verts,tris)
 hits=[]
 for p,n in zip(verts,normals):
  best=None
  for d in (-n,n):
   h=bvh.ray_cast(p+d*1e-5,d,.004)
   if h[0] is not None and (best is None or h[3]<best[3]):best=h
  hits.append(best)
 found=[h[3] for h in hits if h];limit=2.5*float(np.median(found)) if found else 0
 partners=[]
 for p,h in zip(verts,hits):
  if not h or h[3]>limit:partners.append(None);continue
  a,b,c=tris[h[2]];w=_barycentric(h[0],verts[a],verts[b],verts[c]);partners.append(((a,b,c),w))
 # Rim: unpaired vertices (folded edges, flanks of lofted tubes) and open boundaries.
 edges={}
 for f in faces:
  for i in range(len(f)):e=tuple(sorted((f[i],f[(i+1)%len(f)])));edges[e]=edges.get(e,0)+1
 neighbours=[set() for _ in verts]
 for a,b in edges:neighbours[a].add(b);neighbours[b].add(a)
 median=float(np.median(found)) if found else 0
 seeds={i for i,pt in enumerate(partners) if pt is None}|{v for e,c in edges.items() if c==1 for v in e}
 # Separate source pieces of one ligament: edges touching another piece are seams, not rims.
 island=[-1]*len(verts);count=0
 for start in range(len(verts)):
  if island[start]>=0:continue
  stack=[start];island[start]=count
  while stack:
   i=stack.pop()
   for j in neighbours[i]:
    if island[j]<0:island[j]=count;stack.append(j)
  count+=1
 island_tris={k:[t for t in tris if island[t[0]]==k] for k in range(count)}
 seam={}
 if count>1:
  others={k:BVHTree.FromPolygons(verts,island_tris[k]) for k in range(count)}
  for i in list(seeds):
   for k,tr in others.items():
    if k!=island[i] and tr.find_nearest(verts[i],seam_gap)[0] is not None:seam[i]=k;seeds.discard(i);break
 rim=[math.inf]*len(verts);queue=[(0.,i) for i in seeds]
 for i in seeds:rim[i]=0.
 heapq.heapify(queue)
 while queue:
  d,i=heapq.heappop(queue)
  if d!=rim[i]:continue
  for j in neighbours[i]:
   dd=d+(verts[i]-verts[j]).length
   if dd<rim[j]:rim[j]=dd;heapq.heappush(queue,(dd,j))
 finite=[r for r in rim if math.isfinite(r)] or [rim_radius];radius=min(rim_radius,.8*max(finite))
 xyz=np.array([v[:] for v in verts]);center=xyz.mean(axis=0);_,_,vh=np.linalg.svd(xyz-center,full_matrices=False);rel=xyz-center
 if ring:
  # Annular fibres run circumferentially around the smallest principal axis.
  a,b=rel@vh[0],rel@vh[1];radius_mm=float(np.median(np.hypot(a,b)))*1000
  along=np.unwrap(np.arctan2(b,a))*radius_mm/1000;across=rel@vh[2]
 else:along=rel@vh[0];across=rel@vh[1]
 t=(along-along.min())/max(along.max()-along.min(),1e-9);length=float(along.max()-along.min());width=float(across.max()-across.min())
 s=(across-across.min())/max(width,1e-9);fascicles=max(2,round(width*1000/2.4))
 half=[];colors=[];uvs=[]
 for i in range(len(verts)):
  x=min(rim[i]/radius,1) if math.isfinite(rim[i]) else 1;e=min(t[i],1-t[i])
  ellipse=math.sqrt(max(0,1-(1-x)**2));enthesis=1 if ring else .4+.6*smoothstep(0,.22,e)
  ridge=1+.13*x*math.cos(2*math.pi*fascicles*s[i])
  half.append(max(.00003,peak*ellipse*enthesis*ridge/2))
  base=Vector((.78,.77,.75)).lerp(Vector((.93,.90,.84)),x**.6)
  if not ring:base=Vector((.84,.76,.62)).lerp(base,smoothstep(0,.12,e))
  colors.append(base);uvs.append((float(s[i]*width*1000/8),float(t[i]*length*1000/8)))
 # Attachment ends: flare across the footprint and fuse into the nearest bone surface.
 entheses={};end_bones=[None,None];flares=[Vector()]*len(verts)
 if bones and not ring:
  # Station centroids give the local width direction even on curved bands.
  bins=24;sums=[Vector() for _ in range(bins)];cnt=[0]*bins
  for i in range(len(verts)):b=min(int(t[i]*bins),bins-1);sums[b]+=verts[i];cnt[b]+=1
  centre=[sums[b]/cnt[b] if cnt[b] else None for b in range(bins)]
  for b in range(bins):
   if centre[b] is None:centre[b]=next(centre[k] for k in sorted(range(bins),key=lambda k:abs(k-b)) if centre[k] is not None)
  a0=Vector(vh[0])
  for end,sel in ((0,lambda x:x<.03),(1,lambda x:x>.97)):
   tip=[verts[i] for i in range(len(verts)) if sel(t[i])]
   if not tip:continue
   c=sum(tip,Vector())/len(tip);d={n:tr.find_nearest(c)[3] for n,tr in bones.items()};name=min(d,key=d.get)
   if d[name]<.0025:end_bones[end]=name
  offs=[None]*len(verts);reach=[1e-6]*bins
  for i in range(len(verts)):
   b=min(int(t[i]*bins),bins-1);off=verts[i]-centre[b];off-=a0*off.dot(a0);offs[i]=off;reach[b]=max(reach[b],off.length)
  for i in range(len(verts)):
   for end,e in ((0,t[i]),(1,1-t[i])):
    if end_bones[end] and e<enthesis_length:
     w=smoothstep(enthesis_length,0,e);b=min(int(t[i]*bins),bins-1);r=min(offs[i].length/reach[b],1)
     # Rounded, tongue-shaped footprint: lateral fibres stop short of the central ones.
     back=a0*((1 if end==0 else -1)*enthesis_length*length*.3*w*r*r)
     entheses[i]=(end_bones[end],w);flares[i]=offs[i]*(flare*w*w)+back
 # Bony attachments fade to the viewer's bone ivory (#c9bfa5) at the very tip.
 for i,(name,w) in entheses.items():colors[i]=colors[i].lerp(Vector((.79,.75,.65)),smoothstep(.75,1,w))
 # Design values are sRGB; glTF vertex colours are linear.
 colors=[(*(c**2.2 for c in col),1) for col in colors]
 return {'island':island,'island_tris':island_tris,'seam':seam,'entheses':entheses,'flares':flares,'end_bones':end_bones,'t':[float(x) for x in t],
  'neighbours':[sorted(n) for n in neighbours],'partners':partners,'half':half,'colors':colors,'uvs':uvs,'fascicles':fascicles,'length_mm':length*1000,'width_mm':width*1000,'rim_radius_mm':radius*1000,'paired':sum(p is not None for p in partners)}

def _barycentric(p,a,b,c):
 v0,v1,v2=b-a,c-a,p-a;d00,d01,d11,d20,d21=v0.dot(v0),v0.dot(v1),v1.dot(v1),v2.dot(v0),v2.dot(v1);den=d00*d11-d01*d01 or 1e-30
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;return (1-v-w,v,w)

def inflate(plan_,verts,bones=None):
 """Return new positions for one frame. bones: {name: BVH-like} posed for this frame;
 posed wrappers may expose .q (rotation) so rest-pose flare vectors follow the bone."""
 trees=list((bones or {}).values());n=len(verts);mids=[None]*n;dirs=[None]*n;h=list(plan_['half']);shrunk=0
 for i,p in enumerate(verts):
  pt=plan_['partners'][i]
  if pt is None:continue
  (a,b,c),(wa,wb,wc)=pt;q=verts[a]*wa+verts[b]*wb+verts[c]*wc;d=p-q
  if d.length<1e-9:continue
  mids[i]=(p+q)/2;dirs[i]=d.normalized()
  if trees and inside(trees,mids[i]+dirs[i]*h[i]):
   if inside(trees,mids[i]):h[i]=min(h[i],(p-mids[i]).length)  # never deeper than the source
   else:
    lo,hi=0.,h[i]
    for _ in range(7):
     m=(lo+hi)/2
     if inside(trees,mids[i]+dirs[i]*m):hi=m
     else:lo=m
    h[i]=lo
   shrunk+=1
 # Spread clearance reductions so they read as gentle grooves, not dents; only ever thinner.
 nb=plan_['neighbours']
 for _ in range(4):h=[min(h[i],.5*h[i]+.5*sum(h[j] for j in nb[i])/len(nb[i])) if nb[i] else h[i] for i in range(n)]
 out=[mids[i]+dirs[i]*h[i] if mids[i] is not None else p.copy() for i,p in enumerate(verts)]
 # Close seams between source pieces: meet halfway, then relax a two-ring band.
 if plan_['seam']:
  surf={k:BVHTree.FromPolygons(out,tr) for k,tr in plan_['island_tris'].items()}
  moved={i:out[i].lerp(surf[k].find_nearest(out[i])[0],.5) for i,k in plan_['seam'].items()}
  for i,p in moved.items():out[i]=p
  band=set(moved)
  for _ in range(2):band|={j for i in band for j in nb[i]}
  for _ in range(3):
   nxt={i:out[i].lerp(sum((out[j] for j in nb[i]),Vector())/len(nb[i]),.4) for i in band if i not in moved and nb[i]}
   for i,p in nxt.items():out[i]=p
 # Entheses: widen the footprint, lay the deep face on bone and fade the superficial face into it.
 ent={i:(bones[name],w) for i,(name,w) in plan_['entheses'].items() if bones and name in bones}
 def lay(i,p,outer):
  # Superficial face thins to nothing before the tip; the tip then dips just under the
  # bone surface so fibres read as entering bone, with no coplanar film to z-fight.
  tree,w=ent[i];q,nn,_,_=tree.find_nearest(p)
  if q is None:return p
  sink=smoothstep(0,.85,w);lift=2*h[i]*(1-sink)-.00008*sink if outer else -.00008
  return p.lerp(q+nn*lift,w)
 outer={}
 for i,(tree,w) in ent.items():
  rot=getattr(tree,'q',None);flare=rot@plan_['flares'][i] if rot is not None else plan_['flares'][i]
  q,nn,_,_=tree.find_nearest(out[i])
  outer[i]=mids[i] is None or nn is None or (out[i]-mids[i]).dot(nn)>=0
  out[i]=lay(i,out[i]+flare,outer[i])
 # Bone meshes are coarse; relax the footprint, then put the deep face back on bone.
 # Smooth only along the bone normal so bumps go but the flared width is kept.
 for _ in range(6):
  nxt={}
  for i,(tree,w) in ent.items():
   if not nb[i]:continue
   nn=tree.find_nearest(out[i])[1]
   if nn is None:continue
   delta=sum((out[j] for j in nb[i]),Vector())/len(nb[i])-out[i];nxt[i]=out[i]+nn*(delta.dot(nn)*.6*w)
  for i,p in nxt.items():out[i]=p
 # Even out the ragged terminal row in the tangent plane as well.
 tip={i for i,(tree,w) in ent.items() if w>.6 and nb[i]}
 for _ in range(3):
  nxt={i:out[i].lerp(sum((out[j] for j in nb[i]),Vector())/len(nb[i]),.35) for i in tip}
  for i,p in nxt.items():out[i]=p
 for i in ent:out[i]=lay(i,out[i],outer[i]) if i in tip else (lay(i,out[i],False) if not outer[i] else out[i])
 return out,shrunk
