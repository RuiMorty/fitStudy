import urllib.request,concurrent.futures,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
urls=[('z-readme','https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/2b6cf98a8ca012571ecb252e5c077b42a21b3b61/Readme.md'),('z-zip-pointer','https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/2b6cf98a8ca012571ecb252e5c077b42a21b3b61/Z-Anatomy.zip'),('z-license','https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/2b6cf98a8ca012571ecb252e5c077b42a21b3b61/License.txt'),('z-todo','https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/2b6cf98a8ca012571ecb252e5c077b42a21b3b61/TO%20DO%20List')]
def fetch(item):
 name,url=item
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=18) as r: data=r.read(3000000);status=r.status
  (ROOT/(name+'.txt')).write_bytes(data)
  return {'name':name,'url':url,'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as e:return {'name':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(fetch,urls))
(ROOT/'fetch-z-files.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
