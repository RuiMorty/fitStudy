import urllib.request,hashlib,json,zipfile
from pathlib import Path
r=Path(__file__).resolve().parent
url='https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/2b6cf98a8ca012571ecb252e5c077b42a21b3b61/Z-Anatomy.zip'
p=r/'Z-Anatomy.zip'
with urllib.request.urlopen(url,timeout=45) as response, p.open('wb') as out:
 print('HTTP',response.status,'Bytes',response.headers.get('Content-Length'),flush=True)
 total=0;last=0;h=hashlib.sha256()
 while chunk:=response.read(1024*1024):
  total+=len(chunk)
  if total>1000000000:raise RuntimeError('Archive exceeds research size limit')
  out.write(chunk);h.update(chunk)
  if total-last>25*1024*1024:print('Downloaded',total,flush=True);last=total
report={'url':url,'bytes':total,'sha256':h.hexdigest()}
with zipfile.ZipFile(p) as z:
 report['files']=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
 for i in z.infolist():
  if i.filename.endswith('.blend'):
   target=r/Path(i.filename).name
   with z.open(i) as src,target.open('wb') as dest:
    while chunk:=src.read(1024*1024):dest.write(chunk)
   print('Extracted',target.name,i.file_size,flush=True)
(r/'z-archive.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
