import bpy,json,re,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent
p=r.parents[2]/'skeleton-workbench/research/ossicles/Startup.blend'
with bpy.data.libraries.load(str(p),link=False) as (src,dst):
 names=list(src.objects)
 matches=[n for n in names if re.search(r'cartilage|menisc|labrum|articular disc|intervertebral disc|annulus fibrosus|nucleus pulposus|joint capsule|synovial|ligament',n,re.I)]
 dst.objects=matches
objects=[]
for o in dst.objects:
 if o is None:continue
 objects.append({'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None})
result={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Local library object inspection only; no registration or anatomical validation','total_object_names':len(names),'objects':objects}
(r/'z-joint-objects.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('SOURCE_OBJECTS',len(names),'JOINT_CANDIDATES',len(objects))
