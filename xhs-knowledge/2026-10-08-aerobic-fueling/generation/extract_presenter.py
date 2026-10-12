from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter
src=Path(__file__).resolve().parent/'user-reference/rick-open-arms.png'
out=Path(__file__).resolve().parents[1]/'assets/rick-presenter-arms-open.png'
im=Image.open(src).convert('RGB').crop((122,5,670,306))
w,h=im.size; px=im.load(); seen=bytearray(w*h); q=deque()
def pale(x,y):
 r,g,b=px[x,y]; return r>225 and g>219 and b>205 and abs(r-g)<34 and abs(g-b)<47
for x in range(w):
 for y in (0,h-1):
  if pale(x,y):q.append((x,y))
for y in range(h):
 for x in (0,w-1):
  if pale(x,y):q.append((x,y))
while q:
 x,y=q.popleft(); k=y*w+x
 if seen[k] or not pale(x,y):continue
 seen[k]=1
 if x:q.append((x-1,y))
 if x+1<w:q.append((x+1,y))
 if y:q.append((x,y-1))
 if y+1<h:q.append((x,y+1))
mask=Image.new('L',(w,h)); mask.putdata([0 if v else 255 for v in seen]); mask=mask.filter(ImageFilter.GaussianBlur(.45))
im.putalpha(mask); im.save(out)
print(out)
