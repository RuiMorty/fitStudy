import urllib.request,json,hashlib
from html.parser import HTMLParser
from pathlib import Path
P=Path(__file__).resolve().parent/'references'
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if not self.skip and s.strip():self.parts.append(s.strip())
urls={'selected-joints':'https://openstax.org/books/anatomy-and-physiology-2e/pages/9-6-anatomy-of-selected-synovial-joints','fibrous-joints':'https://openstax.org/books/anatomy-and-physiology-2e/pages/9-2-fibrous-joints','vertebral-column':'https://openstax.org/books/anatomy-and-physiology-2e/pages/7-3-the-vertebral-column'}
rows=[]
for id,url in urls.items():
 try:
  with urllib.request.urlopen(url,timeout=30) as r:raw=r.read();status=r.status
  parser=Text();parser.feed(raw.decode());text='\n'.join(parser.parts);(P/(id+'.txt')).write_text(text)
  rows.append({'id':id,'url':url,'http_status':status,'retrieved':'2026-10-13','sha256':hashlib.sha256(raw).hexdigest(),'text_chars':len(text)})
 except Exception as e:rows.append({'id':id,'url':url,'error':str(e)})
(P/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows,ensure_ascii=False))
