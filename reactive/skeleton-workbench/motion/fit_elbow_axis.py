"""Candidate hinge axis from same-source landmarks and trochlear surface, not clinical calibration."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'z-anatomy-candidate/assets/major-joint-surfaces.glb'))
landmarks=json.loads((P/'elbow-review/landmarks.json').read_text())['landmarks'];out={}
# Imported Blender coordinates -> glTF/web metres.
def web(p):return np.array([p[0],p[2],-p[1]])
for side in ['R','L']:
 pts={r['name']:np.array(r['position']) for r in landmarks if r['side']==side}
 a=pts['肱骨内上髁'];b=pts['肱骨外上髁'];axis=(b-a)/np.linalg.norm(b-a)
 # Consistent positive rotation lifts the extended forearm anteriorly (+web Z).
 if axis[0]>0:axis=-axis
 o=bpy.data.objects['surface_patch_humerus_'+side+'_1'];xyz=np.array([web(o.matrix_world@v.co) for v in o.data.vertices]);center=xyz.mean(0)
 # Fit the capitulum's spherical centre to constrain the lateral hinge end.
 cap=bpy.data.objects['surface_patch_humerus_'+side+'_0'];capxyz=np.array([web(cap.matrix_world@v.co) for v in cap.data.vertices]);base=capxyz.mean(0);local=capxyz-base
 coef=np.linalg.lstsq(np.column_stack([2*local,np.ones(len(local))]),(local*local).sum(1),rcond=None)[0];capcenter=base+coef[:3];capradius=np.sqrt(max(0,coef[3]+coef[:3]@coef[:3]))
 for iteration in range(5):
  u=np.cross(axis,[0,1,0]);u/=np.linalg.norm(u);v=np.cross(axis,u);xy=(xyz-center)@np.array([u,v]).T
  mask=np.ones(len(xy),dtype=bool)
  for _ in range(4):
   q=xy[mask];A=np.column_stack([2*q[:,0],2*q[:,1],np.ones(len(q))]);coef=np.linalg.lstsq(A,(q*q).sum(1),rcond=None)[0];cc=coef[:2];rr=np.sqrt(max(0,coef[2]+cc@cc));res=np.abs(np.linalg.norm(xy-cc,axis=1)-rr);mask=res<=np.quantile(res,.8)
  pivot=center+u*cc[0]+v*cc[1]
  axis=(capcenter-pivot)/np.linalg.norm(capcenter-pivot)
  if axis[0]>0:axis=-axis
 out[side]={'pivot':pivot.tolist(),'axis':axis.tolist(),'range_degrees':[0,120],'angle_definition':'相对源模型装配姿态的屈曲增量；0°并非已校准的临床完全伸直位','status':'candidate_static_hinge_not_validated_instantaneous_axis','source_landmarks':['肱骨内上髁','肱骨外上髁'],'source_surface':o.name,'capitulum_surface':cap.name,'capitulum_sphere_center':capcenter.tolist(),'capitulum_fit_radius_mm':float(capradius*1000),'fit_radius_mm':float(rr*1000),'fit_residual_rms_mm':float(np.sqrt(np.mean(res[mask]**2))*1000),'surface_vertex_count':len(xyz)}
(P/'motion/elbow-axis.json').write_text(json.dumps({'units':'metres','coordinates':'glTF X/Y/Z','method':'Epicondylar initialization; same-source trochlear projected circle and capitulum sphere centre constrain candidate hinge. No guessed universal world axis.','sides':out},ensure_ascii=False,indent=2)+'\n');print(json.dumps(out),flush=True)
