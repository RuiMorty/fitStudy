import json,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
A=Path(__file__).resolve().parents[1]/'source-audit';m=json.loads((A/'mapping.json').read_text());dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',22)
def triangles(sid):
 b=(A/'raw'/(sid+'.stl')).read_bytes();return np.frombuffer(b,dtype=dt,offset=84,count=struct.unpack('<I',b[80:84])[0])['v'].astype(float)
def project(draw,tri,h,d,box,scale=None):
 x,y,w,height=box;px=tri@h;pz=tri[:,:,2];dep=tri.mean(1)@d
 scale=scale or min((w-30)/max(.01,np.ptp(px)),(height-30)/max(.01,np.ptp(pz)))
 xs=(px-(px.min()+px.max())/2)*scale+x+w/2;ys=(pz.max()-pz)*scale+y
 n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12);v=.42+.58*np.abs(n@d)
 for k in np.argsort(dep):
  sh=int(88+137*v[k]);draw.polygon(list(zip(xs[k],ys[k])),fill=(sh,sh+1,sh-8))
views=[('后面投影',np.array([1,0,0]),np.array([0,1,0])),('侧面投影',np.array([0,1,0]),np.array([-1,0,0])),('斜向投影',np.array([.7071,.7071,0]),np.array([-.7071,.7071,0]))]
ids=sorted({sid for b in m['core'] for sid in b['primitive_ids']});tri=np.concatenate([triangles(s) for s in ids]);scale=min(490/max(np.ptp(tri@h) for _,h,d in views),1280/np.ptp(tri[:,:,2]));im=Image.new('RGB',(1650,1450),'#f6f4ef');dr=ImageDraw.Draw(im);dr.text((25,15),'同一源坐标、相同比例｜199块已映射骨的原始投影｜非解剖验收',font=font,fill='#222222')
for i,(title,h,d) in enumerate(views):project(dr,tri,h,d,(i*550,80,550,1280),scale);dr.text((i*550+30,1390),title,font=font,fill='#444444')
im.save(A/'raw-skeleton-projections.png')
im=Image.new('RGB',(1400,650),'#f6f4ef');dr=ImageDraw.Draw(im)
for i,(sid,title,h,d) in enumerate([('FMA16202','骶骨源网格 · 后面',np.array([1,0,0]),np.array([0,1,0])),('FMA16202','骶骨源网格 · 侧面',np.array([0,1,0]),np.array([-1,0,0])),('FMA45097','右足籽骨组 · 两个连通体',np.array([1,0,0]),np.array([0,1,0])),('FMA45098','左足籽骨组 · 两个连通体',np.array([1,0,0]),np.array([0,1,0]))]):
 dr.text((i*350+10,15),title,font=font,fill='#333333');project(dr,triangles(sid),h,d,(i*350,65,350,500))
dr.text((20,605),'局部独立缩放，仅供识别；尾骨边界、籽骨内外侧归属尚待审核',font=font,fill='#555555');im.save(A/'source-detail-inspection.png')
