from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,zipfile
b=Path(__file__).resolve().parent;root=b.parents[2];out=root/'xhs/day42'
files=[out/'cover.png',*sorted(out.glob('slide-*.png'))]
assert len(files)==11
slides=[]
for f in files:
 im=Image.open(f);assert im.size==(1080,1440);assert im.convert('RGBA').getchannel('A').getextrema()==(255,255)
 slides.append({'file':str(f.relative_to(root)),'size':im.size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
with zipfile.ZipFile(out/'day42-xhs.zip') as z:
 assert z.testzip() is None
 for f in files:assert z.read(f.name)==f.read_bytes()
protected=json.loads((b/'protected-before.json').read_text());assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in protected.items())
board=Image.new('RGB',(1620,4*750),'#e8e8eb');draw=ImageDraw.Draw(board)
for i,f in enumerate(files):
 im=Image.open(f).convert('RGB');im.thumbnail((528,704));x=i%3*540+6;y=i//3*750+30;board.paste(im,(x,y));draw.text((x,y-22),f.name,fill='black')
board.save(b/'all-cards.jpg')
sections=[]
for name,label in [('slide-01','01｜六个主题，各自配图'),('slide-03','03｜完整卧推架与动作'),('slide-10','10｜实操对照与完整文字')]:
 sections.append(f'<section><h2>{label}</h2><div class="pair"><figure><figcaption>修订前</figcaption><a href="before/xhs/day42/{name}.png"><img src="before/xhs/day42/{name}.png" loading="lazy"></a></figure><figure><figcaption>修订后</figcaption><a href="../../../xhs/day42/{name}.png?r=05"><img src="../../../xhs/day42/{name}.png?r=05" loading="lazy"></a></figure></div></section>')
art=''.join(f'<figure><figcaption>{i+1}. {item["title"]}</figcaption><a href="{item["image"]["src"].split("revision-05/")[1]}"><img src="{item["image"]["src"].split("revision-05/")[1]}" loading="lazy"></a></figure>' for i,item in enumerate(json.loads((root/'runs/day42/lesson.json').read_text())['xhs']['overview']['items']))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Day42 第五版修订对照</title><style>body{margin:0;background:#f3f4f6;color:#222;font-family:system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:24px}h1{font-size:28px}p{line-height:1.8}a{color:#156c4c}section{margin:36px 0}.pair,.art{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}figcaption{font-weight:700;padding:8px}img{display:block;width:100%;height:auto;background:white;border-radius:12px}.art img{aspect-ratio:4/3;object-fit:contain}h2{font-size:20px}.links{display:flex;gap:20px;flex-wrap:wrap}@media(max-width:650px){main{padding:12px}.pair{gap:8px}}</style><main><h1>Day42 第五版修订对照</h1><p>总览恢复六格，每格分别生成专用插图；03补回完整卧推架。02–10每页三块讲解、九条要点，图片区保持Day41大小。10改为“实操对照”，明确卧推与划船的动作、肌群和稳定提示。</p><nav class="links"><a href="../../../xhs/day42/index.html?r=05">查看全部11张卡片</a><a href="../../../xhs/day42/day42-xhs.zip?r=05">下载完整ZIP</a><a href="../../../html/day42-自由重量-上肢杠铃技术.html?r=05">课程正文</a><a href="assets/detail.png">中文有字图</a></nav>'''+''.join(sections)+'<section><h2>六张总览专用插图</h2><div class="art">'+art+'</div></section></main></html>'
(b/'index.html').write_text(page)
(b/'file-verification.json').write_text(json.dumps({'status':'passed','slides':slides,'archiveMatches':True,'protectedFilesUnchanged':len(protected)},ensure_ascii=False,indent=2)+'\n')
print('All 11 cards and archive verified; comparison page generated')
