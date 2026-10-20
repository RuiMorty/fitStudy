import * as THREE from 'three';
// Shared by the main viewer and review viewer; aligned with the new UCL UVs.
const loader=new THREE.TextureLoader();
const [color,normal,roughness]=await Promise.all(['color','normal','roughness'].map(kind=>loader.loadAsync(new URL('../elbow-review/textures/ucl-fiber-'+kind+'.png?v=9',import.meta.url).href)));
color.colorSpace=THREE.SRGBColorSpace;
for(const texture of [color,normal,roughness]){texture.flipY=false;texture.anisotropy=4;texture.wrapS=texture.wrapT=THREE.ClampToEdgeWrapping;}
export const isUcl=id=>/^elbow_ucl_(anterior|posterior|transverse)_[RL](?:__refined)?$/.test(id);
export function applyUclMaterial(mesh,selected=false,strength=1){
 if(!mesh.material.userData.uclFibers){
  const old=mesh.material;
  const material=new THREE.MeshPhysicalMaterial();THREE.MeshStandardMaterial.prototype.copy.call(material,old);
  mesh.material=material;material.userData.uclFibers=true;old.dispose();
 }
 const m=mesh.material;m.map=color;m.normalMap=normal;m.roughnessMap=roughness;m.roughness=.82;m.metalness=0;
 m.normalScale.setScalar(.65*strength);m.color.set(selected?0xb8d0bf:0xf8f5ed);m.emissive.set(0);
 m.sheen=.15;m.sheenColor.set(0xf1eee5);m.sheenRoughness=.7;m.anisotropy=.3;m.anisotropyRotation=Math.PI/2;
 m.clearcoat=0;m.needsUpdate=true;
}
