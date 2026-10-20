import urllib.request,json,hashlib,re
from pathlib import Path
from html import unescape
out=Path(__file__).parent/'references'
urls={
 'imaios-radiate':'https://www.imaios.com/en/e-anatomy/anatomical-structure/radiate-carpal-ligament-1537020404',
 'kenhub-intercarpal':'https://www.kenhub.com/en/library/anatomy/intercarpal-joints',
 'kenhub-tmj':'https://www.kenhub.com/en/library/anatomy/the-temporomandibular-joint',
 'gray-wrist':'https://en.wikipedia.org/wiki/Radiate_carpal_ligament'}
rows=[]
for key,url in urls.items():
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=30) as f:raw=f.read();status=f.status;final=f.url
  html=raw.decode('utf-8');html=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',html,flags=re.S|re.I)
  text=unescape(re.sub('<[^>]+>',' ',html));text=re.sub(r'\s+',' ',text)
  (out/(key+'.txt')).write_text(text)
  rows.append(dict(id=key,url=url,final=final,status=status,sha256=hashlib.sha256(raw).hexdigest()))
 except Exception as e:rows.append(dict(id=key,url=url,error=str(e)))
(out/'index.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
