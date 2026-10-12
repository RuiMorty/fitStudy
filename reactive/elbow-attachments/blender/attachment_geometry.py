"""Editable candidate footprints and proximal binding; no claim of anatomical validation."""
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def tree_for(o):
 return BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])

def region_distance(points,spec):
 return np.min([np.linalg.norm((points-r['center'])/r['radii'],axis=1) for r in spec['regions']],axis=0)

def smoothstep(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

class AttachmentBinding:
 def __init__(self,objects,landmarks):
  self.landmarks=landmarks;self.trees={s['bone']:tree_for(objects[s['bone']]) for s in landmarks.values()};self.cache={};self.humerus=tree_for(objects['bone_humerus_R']);self.wrap_cache={};self.brachialis_source=tree_for(objects['muscle_brachialis_R'])
 def weights(self,mid,arr):
  key=(mid,arr.tobytes())
  if key not in self.cache:
   spec=self.landmarks[mid];tree=self.trees[spec['bone']]
   hits=[tree.find_nearest(Vector(p)) for p in arr]
   surface=np.array([list(h[0]) for h in hits]);distance=np.array([h[3] for h in hits])
   w=(1-smoothstep(.0005,.004,distance))*(1-smoothstep(.85,1.35,region_distance(surface,spec)))
   if mid=='muscle_brachialis_R':
    # The bone-facing side of this broad origin must not peel away with the
    # superficial belly. Use source surface orientation, not a filler mesh.
    source_normals=np.array([list(self.brachialis_source.find_nearest(Vector(p))[1]) for p in arr])
    bone_normals=np.array([list(h[1]) for h in hits])
    facing=-np.sum(source_normals*bone_normals,axis=1)
    mantle=smoothstep(.05,.35,facing)*(1-smoothstep(.008,.012,distance))*(1-smoothstep(.95,1.35,region_distance(surface,spec)))
    w=np.maximum(w,mantle)
   self.cache[key]=(surface,w)
  return self.cache[key]
 def constrain(self,mid,arr,deformed):
  surface,w=self.weights(mid,arr)
  # Broad origin sheets must stay on their original side of the humerus.
  # A tangential half-space constraint prevents interpolation through the shaft;
  # blend out near the joint so distal tendon endpoints can rotate normally.
  if 'triceps' in mid or 'brachialis' in mid:
   key=arr.tobytes()
   if key not in self.wrap_cache:
    hits=[self.humerus.find_nearest(Vector(p)) for p in arr]
    q=np.array([list(h[0]) for h in hits]);n=np.array([list(h[1]) for h in hits])
    margin=np.maximum(0,np.sum((arr-q)*n,axis=1));self.wrap_cache[key]=(q,n,margin)
   q,n,margin=self.wrap_cache[key]
   penetration=np.minimum(0,np.sum((deformed-q)*n,axis=1)-margin)
   wrap=smoothstep(.025,.055,arr[:,2])
   deformed=deformed-n*(penetration*wrap)[:,None]
  return deformed*(1-w[:,None])+surface*w[:,None]


def create_regions(objects,landmarks,attachments,collection,parent):
 material=bpy.data.materials.new('Attachment candidate | amber annotation');material.diffuse_color=(.9,.36,.045,.72);material.use_nodes=True
 p=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.9,.36,.045,1);p.inputs['Roughness'].default_value=.7
 report={'status':'candidate-pending-anatomist','displayOffsetMetres':.00012,'note':'These overlays are representative bone contact regions, not verified complete anatomical footprints.','regions':{}}
 for mid,spec in landmarks.items():
  bone=objects[spec['bone']];tissue=tree_for(objects[spec['tissue']]);verts=[];faces=[]
  # Subdivide only annotation triangles, retaining the exact source bone surface.
  def add_triangle(a,b,c,depth=0):
   center=(a+b+c)/3
   r=float(region_distance(np.array([center]),spec)[0])
   edge=max(np.linalg.norm(a-b),np.linalg.norm(b-c),np.linalg.norm(c-a))
   if r>1+edge/min(min(x['radii']) for x in spec['regions']):return
   if edge>.0025 and depth<9:
    k=int(np.argmax([np.linalg.norm(a-b),np.linalg.norm(b-c),np.linalg.norm(c-a)]))
    u,v,w=[(a,b,c),(b,c,a),(c,a,b)][k];m=(u+v)/2
    add_triangle(u,m,w,depth+1);add_triangle(m,v,w,depth+1)
   elif r<=1 and tissue.find_nearest(Vector(center))[3]<=.0012:
    normal=np.cross(b-a,c-a);norm=np.linalg.norm(normal)
    if norm<1e-14:return
    normal=normal/norm;start=len(verts);verts.extend([list(v+normal*.00012) for v in [a,b,c]]);faces.append((start,start+1,start+2))
  for poly in bone.data.polygons:
   vs=[np.array(bone.data.vertices[i].co) for i in poly.vertices]
   for j in range(1,len(vs)-1):add_triangle(vs[0],vs[j],vs[j+1])
  assert faces,f'{mid}: candidate region has no source bone / tissue contact'
  mesh=bpy.data.meshes.new('footprint_surface__'+mid);mesh.from_pydata(verts,[],faces);mesh.update()
  obj=bpy.data.objects.new('attachment_region__'+mid,mesh);collection.objects.link(obj);obj.parent=parent;obj.data.materials.append(material)
  obj['annotationOwner']=mid;obj['annotationType']='candidate-origin-region';obj['review_status']='pending-anatomist';obj['label_zh']=spec['landmark'];obj['is_anatomical_structure']=False
  report['regions'][mid]={'name':spec['landmark'],'faces':len(faces),'bone':spec['bone'],'tissue':spec['tissue'],'anchor':attachments[mid][0].tolist(),'status':'candidate-pending-anatomist'}
 return report
