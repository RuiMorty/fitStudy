#!/usr/bin/env python3
"""Deterministic headline color and Chinese label corrections after generation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parent
RED = (180, 67, 57)
INK = (5, 27, 47)
FONT = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc'


def font(size):
    return ImageFont.truetype(FONT, size, index=11)


def label(im, box, value, size, color=INK, background=None, align='center'):
    """Replace only the requested label using real Simplified Chinese glyphs."""
    x1, y1, x2, y2 = box
    if background is None:
        background = tuple(int(v) for v in ImageStat.Stat(im.crop((x1, y1, x2, y1+2))).median)
    d = ImageDraw.Draw(im)
    f = font(size)
    while d.textbbox((0, 0), value, font=f)[2] > x2-x1-2:
        size -= 1
        f = font(size)
    scale = 4
    patch = Image.new('RGB',((x2-x1+1)*scale,(y2-y1+1)*scale),background)
    pd = ImageDraw.Draw(patch)
    pd.text((patch.width/2,patch.height/2),value,font=font(size*scale),fill=color,anchor='mm')
    im.paste(patch.resize((x2-x1+1,y2-y1+1),Image.Resampling.LANCZOS),(x1,y1))


def headline_color(im, bottom=120):
    pix = im.load()
    for y in range(bottom):
        for x in range(im.width):
            r,g,b = pix[x,y]
            if r > g+30 and r > b+30:
                alpha = 1 if g < 90 else max(0, min(1, (245-g)/155))
                pix[x,y] = tuple(round(RED[k]*alpha + (248,243,231)[k]*(1-alpha)) for k in range(3))
    return im


def finish02():
    im = Image.open(ROOT/'raw/02.png').convert('RGB')
    headline_color(im)
    label(im,(371,518,474,551),'肱三头肌',26,(62,12,13),(249,246,236))
    label(im,(909,492,1010,525),'肱三头肌',26,(62,12,13),(250,247,237))
    label(im,(217,1057,313,1091),'肱三头肌',25,(62,12,13),(250,247,238))
    label(im,(729,842,1001,883),'主要肌肉：肱三头肌',31,(5,32,73),(224,235,243))
    im.save(ROOT/'02-窄握杠铃仰卧臂屈伸-修订.png')


def erase_marker(im, box, circle, line):
    """Interpolate beneath a small callout marker without changing the diagram."""
    mask = Image.new('L', im.size)
    d = ImageDraw.Draw(mask)
    d.ellipse(circle, fill=255)
    d.line(line, fill=255, width=9)
    mp, px = mask.load(), im.load()
    x1, y1, x2, y2 = box
    for y in range(y1, y2):
        xs = [x for x in range(x1, x2) if mp[x,y]]
        if not xs:
            continue
        left, right = min(xs)-1, max(xs)+1
        a, b = px[left,y], px[right,y]
        for x in xs:
            t = (x-left)/(right-left)
            px[x,y] = tuple(round(a[k]*(1-t)+b[k]*t) for k in range(3))


def finish03():
    im = Image.open(ROOT/'raw/03.png').convert('RGB')
    headline_color(im)
    # Sternoclavicular: the joint at the medial clavicle / manubrium interface.
    erase_marker(im,(343,236,379,309),(346,278,376,308),[(366,236),(360,294)])
    # Acromioclavicular: move the point from the clavicle shaft onto the seam.
    erase_marker(im,(585,239,626,272),(588,239,619,271),[(624,236),(605,256)])
    d = ImageDraw.Draw(im)
    for start, end in [((365,236),(326,292)),((625,239),(620,265))]:
        d.line([start,end],fill=(210,24,29),width=4)
        x,y=end
        d.ellipse((x-8,y-8,x+8,y+8),fill=(210,24,29),outline=(255,249,237),width=1)
    label(im,(106,612,179,654),'肱骨',36,background=(249,245,232))
    label(im,(469,637,737,681),'肱尺关节：屈、伸',31,background=(251,247,237))
    label(im,(469,738,792,782),'肱桡关节：参与屈、伸',30,background=(251,247,237))
    im.save(ROOT/'03-关节构成速记-修订.png')


def finish04():
    im = Image.open(ROOT/'raw/04.png').convert('RGB')
    headline_color(im)
    label(im,(667,995,991,1034),'前臂与肩关节旋转对比',28,(148,31,24))
    label(im,(679,1045,785,1077),'前臂旋转',24,(10,10,9))
    label(im,(858,1045,990,1077),'肩关节旋转',24,(10,10,9))
    im.save(ROOT/'04-肩关节动作地图-修订.png')


def finish05():
    im = Image.open(ROOT/'raw/05.png').convert('RGB')
    headline_color(im,160)
    im.save(ROOT/'05-多裂肌与短肌长肌对比-修订.png')


if __name__ == '__main__':
    finish02()
    finish03()
    finish04()
    finish05()
