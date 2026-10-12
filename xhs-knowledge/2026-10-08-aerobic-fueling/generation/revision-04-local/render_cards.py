#!/usr/bin/env python3
"""Render plain-language aerobic-fueling cards in a character-led layout."""
from __future__ import annotations
import hashlib, json
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'images'; ASSETS=ROOT/'assets'
W,H=1536,2048
PAPER='#FCF8EF'; RED='#92362A'; RED_LIGHT='#F2DCD3'; INK='#29302E'; MUTED='#626962'
GREEN='#5D8066'; GREEN_LIGHT='#E7EFE5'; BLUE='#377995'; BLUE_LIGHT='#E3F0F2'
GOLD='#A2773D'; GOLD_LIGHT='#F5EAD7'; RULE='#D7CDC0'; WHITE='#FFFEFA'
SERIF='/System/Library/Fonts/Supplemental/Songti.ttc'
SANS='/System/Library/Fonts/STHeiti Medium.ttc'

@lru_cache(None)
def font(size,serif=False): return ImageFont.truetype(SERIF if serif else SANS,size)
def put(d,x,y,s,size,color=INK,serif=False,anchor='lt',maxw=None):
    f=font(size,serif)
    if maxw and d.textlength(s,font=f)>maxw: raise ValueError(f'Text too wide: {s}')
    d.text((x,y),s,font=f,fill=color,anchor=anchor)
def para(d,x,y,rows,size,gap,color=INK):
    for i,s in enumerate(rows): put(d,x,y+i*gap,s,size,color)
def rounded(d,box,fill=WHITE,outline=RULE,radius=30,width=3):
    d.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)
def art(im,name,box):
    x,y,w,h=box
    with Image.open(ASSETS/name) as src: a=src.convert('RGBA')
    a.thumbnail((w,h),Image.Resampling.LANCZOS)
    im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2),a)
def rick(im,box,bust=True):
    x,y,w,h=box
    with Image.open(ASSETS/'rick-standing-cutout.png') as src: a=src.convert('RGBA')
    if bust: a=a.crop((0,0,a.width,930))
    a.thumbnail((w,h),Image.Resampling.LANCZOS)
    im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2),a)
def presenter(im,box):
    x,y,w,h=box
    with Image.open(ASSETS/'rick-presenter-arms-open.png') as src: a=src.convert('RGBA')
    scale=min(w/a.width,h/a.height)
    a=a.resize((round(a.width*scale),round(a.height*scale)),Image.Resampling.LANCZOS)
    im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2),a)
def base(n,section,title,subtitle):
    im=Image.new('RGB',(W,H),PAPER); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,18),fill=RED)
    put(d,78,49,'FITSTUDY  ·  运动科学',34,MUTED)
    put(d,1458,50,f'{n:02d} / 07',36,RED,anchor='rt')
    d.line((78,125,1458,125),fill=RULE,width=3)
    put(d,80,155,section,36,RED)
    for i,s in enumerate(title): put(d,76,220+i*116,s,105,RED,True,maxw=1380)
    put(d,82,220+len(title)*116+25,subtitle,43,INK,maxw=1380)
    d.line((78,1940,1458,1940),fill=RULE,width=3)
    put(d,80,1962,'从起步到长距离 · 供能指南',28,MUTED)
    put(d,1458,1962,'时间是趋势，不是开关',28,MUTED,anchor='rt')
    return im,d
def speech(d,box,rows,color=RED,size=45):
    rounded(d,box,WHITE,color,28,4)
    para(d,box[0]+27,box[1]+22,rows,size,size+17,color)
def save(im,name):
    OUT.mkdir(exist_ok=True)
    p=OUT/name; im.save(p,optimize=True); return p

def cover():
    im,d=base(1,'先回答那个最常见的问题',['跑步 30 分钟，','才开始燃脂？'],'答案：脂肪从起步就参与，没有 30 分钟开关。')
    rounded(d,(78,635,1458,1560))
    presenter(im,(135,665,1260,690))
    for x,num,head,detail,color in [
        (126,'01','起步几秒','PCr 快速响应',BLUE),
        (575,'02','稳定跑起来','糖和脂肪一起用',RED),
        (1023,'03','跑得更久','肝脏帮忙稳血糖',GREEN)]:
        rounded(d,(x,1374,x+394,1522),WHITE,color,22,3)
        put(d,x+18,1391,num,36,color)
        put(d,x+93,1389,head,39,INK)
        put(d,x+20,1456,detail,32,MUTED)
    rounded(d,(78,1640,1458,1844),RED,RED)
    put(d,123,1682,'看懂 5 个时间节点 + 4 种供能角色',54,WHITE,True)
    put(d,125,1772,'每张图只讲一件事。',38,WHITE)
    return save(im,'01-cover.png')

def stage(d,y,time,head,body,color,tint):
    rounded(d,(80,y,1456,y+229),tint,color,27,3)
    rounded(d,(107,y+35,400,y+192),color,color,22)
    put(d,253,y+67,time,53,WHITE,anchor='mt')
    put(d,443,y+29,head,56,color)
    put(d,445,y+111,body,38,INK,maxw=970)
def timeline():
    im,d=base(2,'把“先后”讲明白',['不是轮流上场，','而是一起工作'],'下面是中等强度、持续运动的常见变化。')
    stage(d,636,'0–10 秒','突然起步，PCr 反应最快','现成 ATP 很少；PCr 快速帮忙再生 ATP。',BLUE,BLUE_LIGHT)
    stage(d,884,'10 秒–3 分','有氧供能逐渐跟上','肌糖原、血糖和脂肪都已参与；PCr 趋稳。',RED,RED_LIGHT)
    stage(d,1132,'3–30 分','糖 + 脂肪并行','工作肌用自己的糖，也在氧化脂肪酸。',GREEN,GREEN_LIGHT)
    stage(d,1380,'30–120 分','脂肪占比常增加','肌糖原利用速率常降；肝脏继续稳血糖。',GOLD,GOLD_LIGHT)
    rounded(d,(80,1635,1456,1866))
    rick(im,(107,1655,205,185))
    put(d,314,1664,'2 小时以后呢？',51,RED,True)
    put(d,314,1745,'不补糖时，肝糖原变少，糖异生更重要。',38,INK)
    return save(im,'02-timeline.png')

def explainer(n,filename,section,title,subtitle,asset,color,tint,banner,facts,rick_says):
    im,d=base(n,section,title,subtitle)
    rounded(d,(80,629,1456,1280))
    art(im,asset,(105,683,1320,540))
    rounded(d,(83,1306,1453,1435),color,color,25)
    put(d,124,1334,banner,56,WHITE,True,maxw=1290)
    for i,(head,detail) in enumerate(facts):
        y=1460+i*142
        rounded(d,(84,y,1452,y+127),tint,color,21,2)
        put(d,114,y+20,head,41,color)
        put(d,460,y+19,detail,39,INK,maxw=950)
    presenter(im,(1050,448,400,218))
    speech(d,(760,520,1050,620),rick_says,color,29)
    return save(im,filename)
def muscle():
    return explainer(3,'03-muscle-glycogen.png','第一站：工作肌',['肌糖原：','肌肉自己的糖'],'它储存在肌肉里，主要由这块工作肌自己使用。',
      'muscle-glycogen.png',RED,RED_LIGHT,'看图：红色小颗粒在肌纤维内部',[
      ('什么时候用','从起步就用，不等 PCr 耗尽'),('何时更依赖','跑快、爬坡或强度高时'),('跑久了怎样','储量逐渐减少，利用速率常下降')],['看这里：','糖在肌肉里。'])
def liver():
    return explainer(4,'04-liver-glycogen.png','第二站：肝脏',['肝糖原：','给血液补糖'],'肝脏把储存的糖分解为葡萄糖，送进血液。',
      'liver-glycogen.png',BLUE,BLUE_LIGHT,'看图：肝脏 → 血液 → 工作肌',[
      ('什么时候参与','运动早期就可释放葡萄糖'),('主要任务','帮助维持血糖，支持持续运动'),('跑久了怎样','不补糖时储量逐渐下降')],['这条蓝色路','就是血液。'])
def fat():
    return explainer(5,'05-fat-oxidation.png','第三站：脂肪酸',['脂肪：','从起步就能用'],'脂肪酸进入工作肌，在肌肉里被氧化供能。',
      'fat-oxidation.png',GREEN,GREEN_LIGHT,'看图：脂肪组织 → 血液 → 肌肉',[
      ('什么时候参与','运动开始就参与，不等 30 分钟'),('持续中低强度','时间越久，供能占比通常越高'),('强度升高时','身体通常更依赖糖')],['不是 30 分钟','才开始燃脂！'])
def gng():
    return explainer(6,'06-gluconeogenesis.png','第四站：肝脏再造糖',['糖异生：','用原料重新造糖'],'这是一种造葡萄糖的过程，不是另一种燃料。',
      'gluconeogenesis.png',GOLD,GOLD_LIGHT,'看图：乳酸 / 甘油等 → 肝脏 → 血糖',[
      ('什么时候开始','运动早期就可能参与'),('跑得越久','不补糖时，对维持血糖越重要'),('别理解错','脂肪酸不能直接变成葡萄糖')],['肝脏也会','自己造糖。'])

def bar(d,x,y,label,carb,fat_g):
    rounded(d,(x,y,x+637,y+604))
    put(d,x+35,y+31,label,45,INK)
    for i,(name,value,color) in enumerate([('总糖氧化',carb,RED),('总脂肪氧化',fat_g,GREEN)]):
        yy=y+165+i*180
        put(d,x+37,yy,name,39,color)
        rounded(d,(x+37,yy+75,x+555,yy+117),RULE,RULE,18)
        rounded(d,(x+37,yy+75,x+37+round(518*value/120),yy+117),color,color,18)
        put(d,x+557,yy-2,f'约 {value} g',43,color,anchor='rt')
def amounts():
    im,d=base(7,'最后看消耗量',['同样运动 1 小时，','糖脂能差多少？'],'举例：都消耗 600 千卡，糖和脂肪的分配可以不同。')
    bar(d,80,652,'偏脂肪供能的情况',54,42)
    bar(d,819,652,'偏糖供能的情况',108,20)
    rounded(d,(80,1293,1456,1765),RED_LIGHT,RED)
    put(d,123,1336,'这些数不能直接叫“肌糖原消耗量”',54,RED,True)
    para(d,125,1447,['图中是总糖、总脂肪的氧化量。总糖可能来自肌糖原、',
                      '血糖等多处；脂肪氧化量也不等于体脂减少量。'],38,66)
    put(d,125,1630,'所以：没有固定“第几分钟才开始烧脂肪”。',42,INK)
    put(d,85,1811,'演算条件：稳态 RER 0.80 / 0.90；忽略蛋白质氧化。',31,MUTED)
    put(d,85,1857,'基于 Weir 与 Frayn 公式；不是个人实测值。',31,MUTED)
    return save(im,'07-amounts.png')

def contact(paths):
    sheet=Image.new('RGB',(1520,2078),PAPER); d=ImageDraw.Draw(sheet)
    put(d,40,27,'有氧供能 · 通俗讲解版',55,RED,True)
    for i,p in enumerate(paths):
        with Image.open(p) as src: a=src.copy()
        a.thumbnail((462,616),Image.Resampling.LANCZOS)
        col=1 if i==6 else i%3; x=42+col*488; y=150+(i//3)*642
        sheet.paste(a,(x,y)); d.rectangle((x,y,x+462,y+616),outline=RULE,width=2)
    p=OUT/'preview-contact-sheet.jpg'; sheet.save(p,quality=93,optimize=True); return p

def main():
    paths=[cover(),timeline(),muscle(),liver(),fat(),gng(),amounts()]
    preview=contact(paths)
    manifest={'status':'awaiting-user-review','revision':4,
      'render':'Pillow text and diagrams; Lingzhi RGBA paintings; no SVG',
      'title_font':SERIF,'body_font':SANS,
      'rick_source':'xhs-wrong-notebook/2026-09-22-joint-actions/00-rick-muscular-cartoon-model-v4.png',
      'artwork_provider':'lingzhi-image / gpt-image-2.5-sunburst',
      'artwork_prompt_file':'generation/lingzhi-revision-03/prompts.json',
      'dimensions':[W,H],'pillow':pillow_version,
      'content_sha256':hashlib.sha256((ROOT/'content.json').read_bytes()).hexdigest(),
      'images':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
      'artwork':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ASSETS/'rick-standing-cutout.png',ASSETS/'muscle-glycogen.png',ASSETS/'liver-glycogen.png',ASSETS/'fat-oxidation.png',ASSETS/'gluconeogenesis.png']],
      'preview':str(preview.relative_to(ROOT))}
    (ROOT/'generation/render-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Rendered',len(paths),'cards')
if __name__=='__main__': main()
