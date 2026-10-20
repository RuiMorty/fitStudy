"""Directional collagen-like illustration, not histology or measured optical properties."""
import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent;folder=P/'textures';folder.mkdir(exist_ok=True)
n=512;y,x=np.mgrid[0:n,0:n]/(n-1)
phase=x+.0009*np.sin(y*19+x*27)+.0005*np.sin(y*43+x*15)
fib=(.5+.5*np.sin(phase*2*np.pi*133+.7*np.sin(x*31)))**5
fine=(.5+.5*np.sin(phase*2*np.pi*211+1.4))**8
bundle=.5+.5*np.sin(x*2*np.pi*15+.15*np.sin(y*9))
fade=np.clip(np.minimum(y,1-y)/.13,0,1);fade=fade*fade*(3-2*fade)
height=(.65*fib+.25*fine+.10*bundle)*fade
shade=.72+.19*fib+.05*fine+.035*bundle
rgb=np.stack([shade*1.02,shade,shade*.95],axis=-1)
edge=1-fade;rgb=rgb*(1-edge[...,None]*.25)+np.array([.77,.74,.66])*edge[...,None]*.25
nx=-np.gradient(height,axis=1)*1.5;ny=-np.gradient(height,axis=0)*1.5;nz=np.ones_like(nx);norm=np.sqrt(nx*nx+ny*ny+nz*nz)
normal=np.stack([nx/norm*.5+.5,ny/norm*.5+.5,nz/norm*.5+.5],axis=-1)
rough=np.repeat((.62+.23*(1-height))[...,None],3,axis=-1)
images={}
for key,values in [('color',rgb),('normal',normal),('roughness',rough)]:
 image=bpy.data.images.new('UCL fibers '+key,width=n,height=n,alpha=True)
 if key!='color':image.colorspace_settings.name='Non-Color'
 rgba=np.concatenate([np.clip(values,0,1),np.ones((n,n,1))],axis=-1).astype(np.float32);image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str(folder/('ucl-fiber-'+key+'.png'));image.file_format='PNG';image.save();image.pack();images[key]=image
FIBER_MATERIAL=bpy.data.materials.new('UCL directional fibers');FIBER_MATERIAL.use_nodes=True
nodes=FIBER_MATERIAL.node_tree.nodes;links=FIBER_MATERIAL.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
for key,socket in [('color','Base Color'),('roughness','Roughness')]:
 node=nodes.new('ShaderNodeTexImage');node.image=images[key];links.new(node.outputs['Color'],bs.inputs[socket])
tex=nodes.new('ShaderNodeTexImage');tex.image=images['normal'];normalnode=nodes.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.65;links.new(tex.outputs['Color'],normalnode.inputs['Color']);links.new(normalnode.outputs['Normal'],bs.inputs['Normal'])
bs.inputs['Sheen Weight'].default_value=.15
