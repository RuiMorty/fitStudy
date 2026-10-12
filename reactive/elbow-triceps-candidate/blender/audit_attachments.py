"""Independent evaluation of saved meshes: checks contacts, not just marker projection."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
LM=json.loads((ROOT/'data/attachment-landmarks.json').read_text())['muscles']
def mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([list(e.matrix_world@p.co) for p in m.vertices]);f=[list(p.vertices) for p in m.polygons];e.to_mesh_clear();return v,f

def tree(o):
 v,f=mesh(o);return BVHTree.FromPolygons([Vector(p) for p in v],f)

def inspect(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.scene.frame_set(1)
 bones={s['bone']:tree(bpy.data.objects[s['bone']]) for s in LM.values()};pins={};maxima={}
 for mid,s in LM.items():
  o=bpy.data.objects[s['tissue']];v,_=mesh(o);r=np.min([np.linalg.norm((v-x['center'])/x['radii'],axis=1) for x in s['regions']],axis=0);dist=np.array([bones[s['bone']].find_nearest(Vector(p))[3] for p in v]);indices=np.flatnonzero((r<.85)&(dist<.0000002))
  group=o.vertex_groups.get('Origin_fixed_to_bone')
  if group:indices=np.array([x.index for x in o.data.vertices if any(g.group==group.index and g.weight>.999 for g in x.groups)],dtype=int)
  pins[mid]=(indices,v[indices]);maxima[mid]={'pinVertices':len(indices),'fixedSamplePositions':v[indices[::max(1,len(indices)//3)]][:3].tolist(),'maxPinDisplacementMm':0,'maxMarkerToTissueMm':0,'maxMarkerToBoneMm':0,'oldOrNewOrigin':list(bpy.data.objects['origin__'+mid].matrix_world.translation)}
 for a in np.arange(0,120.01,2.5):
  bpy.context.scene.frame_set(int(a)+1,subframe=float(a)%1)
  for mid,s in LM.items():
   v,f=mesh(bpy.data.objects[s['tissue']]);t=BVHTree.FromPolygons([Vector(p) for p in v],f);p=bpy.data.objects['origin__'+mid].matrix_world.translation;r=maxima[mid]
   r['maxMarkerToTissueMm']=max(r['maxMarkerToTissueMm'],t.find_nearest(p)[3]*1000);r['maxMarkerToBoneMm']=max(r['maxMarkerToBoneMm'],bones[s['bone']].find_nearest(p)[3]*1000)
   ids,rest=pins[mid]
   if len(ids):r['maxPinDisplacementMm']=max(r['maxPinDisplacementMm'],float(np.linalg.norm(v[ids]-rest,axis=1).max()*1000))
 return maxima
old_file=ROOT.parent/'elbow-studio/assets/elbow-right.blend'
if old_file.exists():
 old=inspect(old_file);(ROOT/'qa/baseline-attachment-audit.json').write_text(json.dumps(old,indent=2)+'\n')
else:old=json.loads((ROOT/'qa/baseline-attachment-audit.json').read_text())
new=inspect(ROOT/'assets/elbow-right.blend')
report={'scope':'Geometric checks on saved Blender geometry. Anatomical identity and complete footprints remain pending professional review.','angles':list(np.arange(0,120.01,2.5)),'before':old,'after':new,'checks':{}}
report['checks']['old_long_head_marker_fails_1mm_tissue_contact']=old['muscle_biceps_long_R']['maxMarkerToTissueMm']>1
report['checks']['six_regions_have_fixed_contact_vertices']=all(r['pinVertices']>=3 for r in new.values())
report['checks']['fixed_origin_vertices_do_not_drift_over_motion']=all(r['maxPinDisplacementMm']<.001 for r in new.values())
report['checks']['markers_are_on_bone']=all(r['maxMarkerToBoneMm']<.001 for r in new.values())
report['checks']['all_origin_markers_within_0_5mm_of_their_tissue']=all(r['maxMarkerToTissueMm']<.5 for r in new.values())
report['status']='passed' if all(report['checks'].values()) else 'failed'
(ROOT/'qa/attachment-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='passed':raise RuntimeError('Attachment audit failed; inspect report')
