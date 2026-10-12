import urllib.request,urllib.error,concurrent.futures,json,hashlib,struct,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'source-audit';m=json.loads((R/'mapping.json').read_text());base=f"https://raw.githubusercontent.com/Kevin-Mattheus-Moerman/BodyParts3D/{m['commit']}/assets/BodyParts3D_data/"
ids=sorted({v for r in m['core']+m['extensions'] for v in r['primitive_ids']})
probes=['FMA74053','FMA74051','FMA74049','FMA74052','FMA74050','FMA74048','FMA20229']
def get(sid):
 p=R/'raw'/(sid+'.stl');url=base+'stl/'+sid+'.stl'
 try:
  if p.exists():b=p.read_bytes();status='cached_previous_download'
  else:
   with urllib.request.urlopen(url,timeout=40) as r:b=r.read()
   status='downloaded'
  n=struct.unpack('<I',b[80:84])[0] if len(b)>=84 else -1
  if len(b)!=84+50*n:raise ValueError('Not valid binary STL: size/count mismatch')
  p.write_bytes(b)
  return dict(source_id=sid,url=url,status=status,bytes=len(b),triangles=n,sha256=hashlib.sha256(b).hexdigest(),probe_only=sid in probes)
 except urllib.error.HTTPError as e:return dict(source_id=sid,url=url,status='http_error',http_status=e.code,probe_only=sid in probes)
 except Exception as e:return dict(source_id=sid,url=url,status='error',error=str(e),probe_only=sid in probes)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for r in pool.map(get,ids+probes):
  results.append(r)
  if len(results)%25==0:print('Checked',len(results),'of',len(ids)+len(probes),flush=True)
(R/'mesh-download.json').write_text(json.dumps(dict(commit=m['commit'],files=results),indent=2)+'\n')
try:
 with urllib.request.urlopen(base+'FMA.csv',timeout=40) as response:b=response.read()
 (R/'upstream/FMA.csv').write_bytes(b)
 (R/'ontology-download.json').write_text(json.dumps(dict(url=base+'FMA.csv',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))+'\n')
except Exception as e:print('Ontology fetch:',str(e))
from collections import Counter
print(Counter(x['status'] for x in results));print([x for x in results if x['status'] not in ['downloaded','cached_previous_download']])
