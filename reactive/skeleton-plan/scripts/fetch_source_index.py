import urllib.request,concurrent.futures,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'source-audit'
commit='f0eeb6e843380cfe6b83797cf8c3e1af74de5e61'
base=f'https://raw.githubusercontent.com/Kevin-Mattheus-Moerman/BodyParts3D/{commit}/'
paths=['README.md','LICENSE_content']+['assets/BodyParts3D_data/'+n for n in ['parts_list_e.txt','composite_parts.txt','conventional_part_of.txt','README_e.html']]
def fetch(p):
 url=base+p
 try:
  with urllib.request.urlopen(url,timeout=35) as r:b=r.read()
  (R/'upstream'/Path(p).name).write_bytes(b)
  return dict(path=p,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),status='downloaded')
 except Exception as e:return dict(path=p,url=url,status='failed',error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:result=list(ex.map(fetch,paths))
(R/'index-download.json').write_text(json.dumps(dict(commit=commit,files=result),indent=2)+'\n')
print(json.dumps(result,indent=2))
