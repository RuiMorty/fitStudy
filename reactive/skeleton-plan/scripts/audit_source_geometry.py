import json,struct,hashlib,math
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];A=R/'source-audit';m=json.loads((A/'mapping.json').read_text());files=json.loads((A/'mesh-download.json').read_text())['files'];fm={x['source_id']:x for x in files}
dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')]);arrays={};geos={}
for sid,entry in fm.items():
 p=A/'raw'/(sid+'.stl')
 if not p.exists() or entry['status'] not in ['downloaded','cached_previous_download']:continue
 raw=p.read_bytes();n=struct.unpack('<I',raw[80:84])[0];assert len(raw)==84+50*n
 tri=np.frombuffer(raw,dtype=dtype,offset=84,count=n)['vertices'].astype(np.float64);assert np.isfinite(tri).all();arrays[sid]=tri
 v,f=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True);f=f.reshape(-1,3);parent=np.arange(len(v))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for face in f:
  a=root(face[0]);b=root(face[1]);c=root(face[2]);parent[b]=a;parent[c]=a
 roots=np.array([root(i) for i in range(len(v))]);ids,counts=np.unique(roots[f[:,0]],return_counts=True)
 components=[]
 for rid,count in zip(ids,counts):
  sub=v[roots==rid];components.append(dict(triangles=int(count),min=sub.min(0).tolist(),max=sub.max(0).tolist()))
 components.sort(key=lambda x:x['triangles'],reverse=True)
 edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,ec=np.unique(edges,axis=0,return_counts=True)
 area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 geos[sid]=dict(triangles=n,unique_vertices=len(v),min=v.min(0).tolist(),max=v.max(0).tolist(),center=((v.min(0)+v.max(0))/2).tolist(),extent=np.ptp(v,axis=0).tolist(),components=components,component_count=len(components),boundary_edges=int((ec==1).sum()),nonmanifold_edges=int((ec>2).sum()),degenerate_triangles=int((area<1e-8).sum()),sha256=hashlib.sha256(raw).hexdigest())
 print('Geometry checked',sid,flush=True) if len(geos)%40==0 else None
for rec in m['core']:
 ids=rec['primitive_ids'];valid=ids and all(s in geos for s in ids)
 rec['file_status']='all_required_binary_stl_downloaded_and_validated' if valid else 'not_found_in_release_index' if not ids else 'download_or_validation_incomplete'
 if valid:
  lo=np.min([geos[s]['min'] for s in ids],axis=0);hi=np.max([geos[s]['max'] for s in ids],axis=0)
  rec['bounds']={'min':lo.tolist(),'max':hi.tolist()};rec['files']=[dict(source_id=s,filename=s+'.stl',sha256=geos[s]['sha256'],triangles=geos[s]['triangles']) for s in ids]
for rec in m['extensions']:
 rec['source_components']={s:geos[s]['components'] for s in rec['primitive_ids'] if s in geos}
 rec['status']='group_mesh_downloaded_requires_anatomical_component_assignment' if rec['source_components'] else rec['status']
lookup={r['id']:r for r in m['core']};pairs=[]
for rec in m['core']:
 if rec['side']!='L' or 'bounds' not in rec:continue
 other=lookup[rec['id'][:-1]+'R']
 if 'bounds' not in other:continue
 c1=np.mean([rec['bounds']['min'],rec['bounds']['max']],axis=0);c2=np.mean([other['bounds']['min'],other['bounds']['max']],axis=0)
 ext1=np.subtract(rec['bounds']['max'],rec['bounds']['min']);ext2=np.subtract(other['bounds']['max'],other['bounds']['min']);ratio=np.linalg.norm(ext1)/np.linalg.norm(ext2)
 pairs.append(dict(left=rec['id'],right=other['id'],left_center=c1.tolist(),right_center=c2.tolist(),left_x_larger=bool(c1[0]>c2[0]),bbox_diagonal_ratio=float(ratio)))
coreids={i for r in m['core'] for i in r['primitive_ids'] if i in arrays};alltri=np.concatenate([arrays[s] for s in sorted(coreids)]);bbox={'min':alltri.min(axis=(0,1)).tolist(),'max':alltri.max(axis=(0,1)).tolist()}
# Diagnostic projections of untouched source coordinates, not a generated or repaired model.
W,H=1650,1900;img=Image.new('RGB',(W,H),'#f6f4ef');draw=ImageDraw.Draw(img);font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',23)
draw.text((30,15),'原始骨骼数据投影｜未逐骨缩放或移动｜资源核对，非解剖验收',font=font,fill='#242424')
views=[('X-Z 投影',np.array([1.,0.,0.]),np.array([0.,1.,0.])),('Y-Z 投影',np.array([0.,1.,0.]),np.array([-1.,0.,0.])),('斜向投影',np.array([.7071,.7071,0]),np.array([-.7071,.7071,0]))]
for col,(title,horizontal,depthaxis) in enumerate(views):
 px=alltri@horizontal;py=alltri[:,:,2];depth=alltri.mean(1)@depthaxis
 scale=min(470/(px.max()-px.min()),1740/(py.max()-py.min()));xs=(px-(px.max()+px.min())/2)*scale+col*550+275;ys=(py.max()-py)*scale+95
 normal=np.cross(alltri[:,1]-alltri[:,0],alltri[:,2]-alltri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12);light=.42+.58*np.abs(normal@depthaxis)
 for k in np.argsort(depth):
  shade=int(88+light[k]*137);color=(shade,min(255,shade+1),max(0,shade-8));draw.polygon(list(zip(xs[k],ys[k])),fill=color)
 draw.text((col*550+25,H-48),title,font=font,fill='#444444')
img.save(A/'raw-skeleton-projections.png')
report=dict(scope='Untouched binary STL integrity, exact-coordinate welded topology, AABB scale/laterality and diagnostic projections. Not a clinical or all-joint fit validation.',raw_bounds=bbox,unit_status='STL itself has no units; millimetre-scale dimensions are plausible but official coordinate/unit provenance must be confirmed.',source_meshes=geos,left_right_pairs=pairs,summary=dict(downloaded_meshes=len(geos),core_bones_file_verified=sum('bounds' in x for x in m['core']),source_core_meshes=len(coreids),left_right_pairs_checked=len(pairs),left_right_x_order_failures=sum(not x['left_x_larger'] for x in pairs),open_meshes=sum(x['boundary_edges']>0 for x in geos.values()),nonmanifold_meshes=sum(x['nonmanifold_edges']>0 for x in geos.values())))
(A/'geometry-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(A/'mapping.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['summary']))
