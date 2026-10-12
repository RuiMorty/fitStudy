"""Illustrative triceps path routing and distributed belly strain, not muscle-force simulation."""
import numpy as np

def smoothstep(x):
 t=np.clip(x,0,1);return t*t*(3-2*t)

def rotate(points,a):
 out=points.copy();out[:,1]=points[:,1]*np.cos(a)-points[:,2]*np.sin(a);out[:,2]=points[:,1]*np.sin(a)+points[:,2]*np.cos(a);return out

def arclength(p):
 return np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]

class TricepsPath:
 def __init__(self,profiles,cuts):
  self.profiles=profiles;self.cuts=cuts;self.cache={}
  self.low=.016;self.high=.090
  zs=np.linspace(self.low,self.high,160)
  self.common_z=zs
  self.common=np.mean([np.column_stack([np.interp(zs,z,c[:,j]) for j in range(3)]) for k,(z,c) in profiles.items() if 'triceps' in k],axis=0)
  self.common[:,2]=zs
 def common_at(self,z):return np.column_stack([np.interp(z,self.common_z,self.common[:,j]) for j in range(3)])
 def route(self,arr,a):
  z=arr[:,2];t=np.clip((z-self.low)/(self.high-self.low),0,1);theta=a*(1-smoothstep(t));p0=self.common[0];p3=self.common[-1];length=(self.high-self.low)/3
  def curve(angle):
   low=rotate(p0[None,:],angle)[0];direction=np.array([0,-np.sin(angle),np.cos(angle)])
   p1=low+direction*length;p2=p3-np.array([0,0,length])
   return (1-t[:,None])**3*low+3*(1-t[:,None])**2*t[:,None]*p1+3*(1-t[:,None])*t[:,None]**2*p2+t[:,None]**3*p3
  center=self.common_at(z);center[:,2]=z
  out=rotate(arr-center,theta)+center+curve(a)-curve(0)
  out[z<=self.low]=rotate(arr[z<=self.low],a)
  out[z>=self.high]=arr[z>=self.high]
  return out
 def belly_map(self,mid,a):
  key=(mid,a)
  if key in self.cache:return self.cache[key]
  z,profile=self.profiles[mid];lo=.023;hi=self.cuts[mid.replace('muscle_','').replace('_R','')][1] or z[-1]
  zs=np.linspace(lo,hi,240);center=np.column_stack([np.interp(zs,z,profile[:,j]) for j in range(3)]);center[:,2]=zs
  # Smooth only the reference centreline used for material-coordinate sampling.
  for j in [0,1]:center[:,j]=np.convolve(np.pad(center[:,j],(4,4),mode='edge'),np.ones(9)/9,mode='valid')
  rest=arclength(center);target=arclength(self.route(center,a));ratio=target[-1]/rest[-1]
  mapped=np.interp(rest/rest[-1]*target[-1],target,zs)
  self.cache[key]=(zs,center,mapped,ratio)
  return self.cache[key]
 def deform(self,mid,arr,a):
  if abs(a)<1e-12:return arr.copy()
  zs,center,mapped,ratio=self.belly_map(mid,a);z=arr[:,2];t=np.clip((z-zs[0])/(zs[-1]-zs[0]),0,1)
  zm=np.interp(z,zs,mapped);source=np.column_stack([np.interp(z,zs,center[:,j]) for j in range(3)]);dest=np.column_stack([np.interp(zm,zs,center[:,j]) for j in range(3)])
  work=arr.copy();body=(z>zs[0])&(z<zs[-1]);scale=1+(min(1,ratio**-.5)-1)*np.sin(np.pi*t)**2
  work[body,:2]=dest[body,:2]+(arr[body,:2]-source[body,:2])*scale[body,None];work[body,2]=zm[body]
  return self.route(work,a)
