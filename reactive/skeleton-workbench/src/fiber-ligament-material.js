import * as THREE from 'three';
// Tileable collagen-fiber detail for rebuilt ligament bodies (UV v runs along the
// ligament, 8 mm per repeat). Illustrative surface detail, not histology.
const N=256,TAU=Math.PI*2;
let seed=7;const rand=()=>(seed=(seed*16807)%2147483647)/2147483647;
// Integer frequencies keep the tile seamless; ~3-14 fascicle lines per mm-scale tile.
const waves=[...Array(12)].map((_,i)=>({k:[5,7,9,11,13,17,19,23,29,31,37,43][i],a:1/(1+i*.6),p:rand()*TAU}));
const crimp=[...Array(3)].map((_,i)=>({k:[2,3,5][i],a:[.006,.004,.002][i],p:rand()*TAU}));
// Fibres run along v; a gentle periodic crimp wobbles them sideways.
function height(u,v){let x=u;for(const c of crimp)x+=c.a*Math.sin(TAU*c.k*v+c.p);let h=0;for(const w of waves)h+=w.a*Math.sin(TAU*w.k*x+w.p);return h/4;}
const h=new Float32Array(N*N);
for(let y=0;y<N;y++)for(let x=0;x<N;x++)h[y*N+x]=height(x/N,y/N);
const at=(x,y)=>h[((y+N)%N)*N+(x+N)%N];
const normal=new Uint8Array(N*N*4),color=new Uint8Array(N*N*4),rough=new Uint8Array(N*N*4);
for(let y=0;y<N;y++)for(let x=0;x<N;x++){
 const i=(y*N+x)*4,dx=(at(x+1,y)-at(x-1,y))*3,dy=(at(x,y+1)-at(x,y-1))*3,l=Math.hypot(dx,dy,1),v=at(x,y);
 normal[i]=128-127*dx/l;normal[i+1]=128-127*dy/l;normal[i+2]=128+127/l;normal[i+3]=255;
 const c=Math.round(238+12*v);color[i]=c;color[i+1]=c;color[i+2]=Math.min(255,c+3);color[i+3]=255;
 rough[i]=0;rough[i+1]=Math.round(120-40*v);rough[i+2]=0;rough[i+3]=255;
}
function texture(data,srgb){const t=new THREE.DataTexture(data,N,N,THREE.RGBAFormat);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.magFilter=THREE.LinearFilter;t.minFilter=THREE.LinearMipmapLinearFilter;t.generateMipmaps=true;t.anisotropy=8;if(srgb)t.colorSpace=THREE.SRGBColorSpace;t.needsUpdate=true;return t;}
const maps={normal:texture(normal),color:texture(color,true),roughness:texture(rough)};
export const isFiberLigament=row=>/-fiber-v\d+$/.test(row?.geometry_revision||'');
// Selection keeps each viewer's existing highlight (main 0xb6c891, review page passes its own).
export function applyFiberMaterial(mesh,selected=false,strength=1,highlight=0xb6c891,highlightEmissive=0x16220d){
 if(!mesh.material.userData.fiberLigament){
  const old=mesh.material;mesh.material=new THREE.MeshPhysicalMaterial({side:THREE.FrontSide});mesh.material.userData.fiberLigament=true;old.dispose();
 }
 const m=mesh.material;
 m.vertexColors=!selected&&!!mesh.geometry.attributes.color;m.map=maps.color;m.normalMap=maps.normal;m.roughnessMap=selected?null:maps.roughness;
 m.color.set(selected?highlight:0xffffff);m.emissive.set(selected?highlightEmissive:0);m.roughness=selected?.65:1;m.metalness=0;m.normalScale.set(.35*strength,.35*strength);
 // Moist, pearly connective tissue: soft sheen, thin wet coat, highlights stretched along fibres.
 m.sheen=selected?0:.45;m.sheenColor.set(0xf3efe6);m.sheenRoughness=.42;m.clearcoat=selected?0:.22;m.clearcoatRoughness=.38;m.anisotropy=.4;m.anisotropyRotation=Math.PI/2;
 m.transparent=false;m.opacity=1;m.depthWrite=true;m.needsUpdate=true;
}
