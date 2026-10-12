// Display offsets only: never joint motion, scale, rotation or anatomical attachment data.
export function explosionOffsets(mode, bones, connections, selected) {
  const zero=()=>[0,0,0], sub=(a,b)=>a.map((v,i)=>v-b[i]), add=(a,b)=>a.map((v,i)=>v+b[i]);
  const mul=(v,n)=>v.map(x=>x*n), unit=v=>mul(v,1/(Math.hypot(...v)||1));
  const center=items=>items.length?mul(items.reduce((s,b)=>add(s,b.position),zero()),1/items.length):zero();
  const out=new Map(bones.map(b=>[b.id,zero()])), byId=new Map(bones.map(b=>[b.id,b]));
  if(!bones.length)return out;
  const body=center(bones), grouped=new Map();
  for(const b of bones){let k=b.region;if(k==='上肢')k+=b.side;if(k==='下肢')k=b.id.startsWith('bone_hip_')?'骨盆':k+b.side;if(!grouped.has(k))grouped.set(k,[]);grouped.get(k).push(b);}
  if(mode==='single') {if(byId.has(selected)){const b=byId.get(selected);out.set(selected,[b.side==='R'?-.25:.25,0,.08]);}return out;}
  if(mode==='layers') {const z=bones.map(b=>b.position[2]),mid=(Math.max(...z)+Math.min(...z))/2,span=Math.max(...z)-Math.min(...z)||1;for(const b of bones)out.set(b.id,[0,0,(b.position[2]-mid)/span*.65]);return out;}
  if(mode==='parts') {for(const [k,list] of grouped){const c=center(list);let d=mul(unit(sub(c,body)),.20);if(k.startsWith('上肢'))d=[k.endsWith('R')?-.20:.20,.035,0];if(k.startsWith('下肢'))d=[k.endsWith('R')?-.12:.12,-.14,0];if(k==='骨盆')d=[0,-.04,.16];for(const b of list)out.set(b.id,d);}return out;}
  if(mode==='outward'){for(const b of bones)out.set(b.id,mul(sub(b.position,body),.65));return out;}
  const neighbors=new Map(bones.map(b=>[b.id,new Set()]));
  for(const c of connections){const ids=c.bone_ids.filter(id=>byId.has(id));for(const a of ids)for(const b of ids)if(a!==b)neighbors.get(a).add(b);}
  if(mode==='local') {if(!byId.has(selected))return out;const ids=[selected,...neighbors.get(selected)],items=ids.map(id=>byId.get(id)),c=center(items);for(const b of items){let v=sub(b.position,c);if(Math.hypot(...v)<1e-8)v=[0,0,1];out.set(b.id,mul(unit(v),.10));}return out;}
  if(mode==='chain') {
    // A display-only spanning forest of registered connections, not a kinematic skeleton.
    const visited=new Set();const ordered=[...bones].sort((a,b)=>Math.hypot(...sub(a.position,body))-Math.hypot(...sub(b.position,body)));
    for(const root of ordered){if(visited.has(root.id))continue;visited.add(root.id);const queue=[root.id];for(let i=0;i<queue.length;i++){const a=queue[i];for(const id of neighbors.get(a)){if(visited.has(id))continue;visited.add(id);queue.push(id);const delta=mul(unit(sub(byId.get(id).position,byId.get(a).position)),.045);out.set(id,add(out.get(a),delta));}}}return out;
  }
  // Original regional radial mode, retained for comparison.
  const regions=new Map();for(const b of bones){if(!regions.has(b.region))regions.set(b.region,[]);regions.get(b.region).push(b);}
  for(const list of regions.values()){const c=center(list);for(const b of list){let d=sub(b.position,c);if(Math.hypot(...d)<1e-8)d=[0,0,1];out.set(b.id,mul(unit(d),.22));}}return out;
}
