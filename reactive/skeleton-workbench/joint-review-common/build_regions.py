"""Surface-following colored locator regions; deliberately NOT anatomical segmentations.
Distance is measured along bone mesh edges, never an unbounded floating sphere.
"""
import bpy,json,heapq,math,os
from mathutils import Vector
from pathlib import Path
W=Path(__file__).resolve().parents[1]
radii={'喙突':.026,'肩峰':.024,'大结节':.014,'小结节':.009,'盂上结节':.006,'关节盂':.021,'锥状结节':.009,'斜方线':.013,'盂切迹':.012,'肱骨内上髁':.013,'肱骨外上髁':.012,'尺骨崇高结节':.007,'桡切迹':.011,'鹰嘴':.022,'尺骨冠突':.015,'桡骨头':.018,'桡骨颈':.013}
radii['旋后肌嵴']=.014
radii.update({'桡骨茎突':.008,'尺骨茎突':.006,'尺切迹':.008,'舟骨结节':.006,'大多角骨结节':.006,'钩骨钩':.007})
radii.update({'髂前下棘':.016,'耻骨上支':.025,'坐骨体':.023,'髋臼缘':.020,'髋臼切迹':.018,'髋臼窝':.022,'转子间线':.024,'大转子':.027,'股骨头凹':.012,'股骨内上髁':.017,'股骨外上髁':.017,'股骨髁间窝':.021,'胫骨前髁间区':.018,'胫骨后髁间区':.018,'胫骨内侧髁':.023,'胫骨外侧髁':.023,'腓骨头':.016})
for scope in os.environ.get('REVIEW_SCOPES','shoulder,elbow').split(','):
 P=W/(scope+'-review');bpy.ops.wm.open_mainfile(filepath=str(P/(scope+'-review.blend')));scene=bpy.context.scene;data=json.loads((P/'landmarks.json').read_text());out=[]
 for row in data['landmarks']:
  row['name']=row['name'].replace('尺骨 sublime 结节','尺骨崇高结节');ob=scene.objects[row['bone']];vs=[ob.matrix_world@v.co for v in ob.data.vertices];adj=[[] for _ in vs]
  # Imported bones can contain duplicated seam vertices; weld adjacency only.
  buckets={}
  for i,v in enumerate(vs):buckets.setdefault(tuple(round(float(x),6) for x in v),[]).append(i)
  for bucket in buckets.values():
   for i in bucket[1:]:adj[bucket[0]].append((i,0));adj[i].append((bucket[0],0))
  for f in ob.data.polygons:
   ids=list(f.vertices)
   for a,b in zip(ids,ids[1:]+ids[:1]):
    d=(vs[a]-vs[b]).length;adj[a].append((b,d));adj[b].append((a,d))
  p=Vector((row['position'][0],-row['position'][2],row['position'][1]));seed=min((i for i in range(len(vs)) if adj[i]),key=lambda i:(vs[i]-p).length_squared);radius=radii[row['name']];dist=[math.inf]*len(vs);dist[seed]=0;queue=[(0,seed)]
  while queue:
   d,i=heapq.heappop(queue)
   if d!=dist[i] or d>radius:continue
   for j,w in adj[i]:
    v=d+w
    if v<dist[j] and v<radius*1.15:dist[j]=v;heapq.heappush(queue,(v,j))
  ob.data.calc_loop_triangles();faces=[list(t.vertices) for t in ob.data.loop_triangles if max(dist[i] for i in t.vertices)<radius];ids=sorted({i for f in faces for i in f});mapping={i:n for n,i in enumerate(ids)}
  assert len(faces)>0,(scope,row['name'],len(vs),len(ob.data.polygons),seed,list(vs[seed]),list(p),len(adj[seed]),sum(d<radius for d in dist))
  pts=[];alpha=[]
  for i in ids:
   v=vs[i];pts.extend([round(v.x,7),round(v.z,7),round(-v.y,7)]);t=max(0,min(1,(dist[i]/radius-.65)/.35));alpha.append(round(.68*(1-t*t*(3-2*t)),3))
  out.append({'name':row['name'],'side':row['side'],'bone':row['bone'],'positions':pts,'alpha':alpha,'indices':[mapping[i] for f in faces for i in f],'geodesic_radius_mm':radius*1000,'status':'illustrative_locator_extent_not_anatomical_boundary'})
 data['region_status']='approximate_locator_only';(P/'landmarks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');(P/'landmark-regions.json').write_text(json.dumps({'status':'illustrative_surface_locator_not_attachment_footprint','regions':out},ensure_ascii=False,separators=(',',':'))+'\n');print(scope,'regions',len(out),'triangles',sum(len(r['indices'])//3 for r in out),flush=True)
