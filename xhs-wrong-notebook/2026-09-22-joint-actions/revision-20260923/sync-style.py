#!/usr/bin/env python3
"""Reuse 04's approved paper, brush underline and lightbulb tip appearance.

This is local composition of existing Lingzhi artwork. It does not regenerate
characters, anatomical diagrams, callouts or movement arrows.
Run with the bundled Python runtime (NumPy + Pillow).
"""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'style-unified'
OUT.mkdir(exist_ok=True)
VERIFY = OUT / 'verification'
VERIFY.mkdir(exist_ok=True)
W, H = 1024, 1536
RED = (180, 67, 57)
FONT = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc'
FILES = {f.name[:2]: f for f in ROOT.glob('[0-9][0-9]-*-修订.png')}
REFERENCE = Image.open(FILES['04']).convert('RGB')


def paper_color(im):
    a = np.asarray(im, dtype=np.float32)
    samples = np.concatenate([a[:10].reshape(-1, 3), a[-20:].reshape(-1, 3),
                              a[:110, :100].reshape(-1, 3)])
    samples = samples[(samples[:, 0] > 220) & (samples[:, 1] > 220) & (samples[:, 2] > 207)]
    return np.median(samples, axis=0)


PAPER = paper_color(REFERENCE)


def paper_canvas():
    # The reference's blank lower margin supplies the actual grey paper tone.
    strip = REFERENCE.crop((0, 1507, W, 1536))
    canvas = strip.resize((W, H), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    return canvas


def harmonize_paper(im):
    a = np.asarray(im, dtype=np.float32)
    source = paper_color(im)
    # Smooth highlight-only chromatic adaptation; lines and saturated anatomy
    # remain untouched, while paper and light card backgrounds share 04's tone.
    brightness = np.min(a, axis=2)
    lum_weight = np.clip((brightness - 198) / 27, 0, 1)
    lum_weight = lum_weight * lum_weight * (3 - 2 * lum_weight)
    chroma = np.stack([a[:, :, 0]-a[:, :, 1], a[:, :, 1]-a[:, :, 2]], axis=2)
    source_chroma = np.array([source[0]-source[1], source[1]-source[2]])
    chroma_distance = np.sum((chroma-source_chroma)**2, axis=2)
    weight = lum_weight * np.exp(-chroma_distance / 1250)
    a += weight[:, :, None] * (PAPER-source)
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8))


def headline(im, number):
    a = np.asarray(im, dtype=np.float32)[:160 if number == '05' else 110]
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (r > g+30) & (r > b+30)
    yy, xx = np.where(mask)
    x1, x2, y1, y2 = xx.min(), xx.max()+1, yy.min(), yy.max()+1
    alpha = np.clip((paper_color(im)[1]-g)/(paper_color(im)[1]-RED[1]), 0, 1)
    alpha *= mask
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[:, :, :3] = RED
    rgba[:, :, 3] = np.rint(alpha*255).astype(np.uint8)
    result = Image.fromarray(rgba).crop((x1, y1, x2, y2))
    result.thumbnail((912, 88), Image.Resampling.LANCZOS)
    return result


def tip_blank():
    tip = REFERENCE.crop((0, 1350, W, 1504))
    a = np.asarray(tip).copy()
    # Remove the old sentence, keeping the original brush edges and bulb.
    rng = np.random.default_rng(423)
    for y in range(26, 134):
        row = a[y, 150:989].astype(np.int16)
        reds = (row[:, 0]-row[:, 1] > 70) & (row[:, 1] < 95)
        color = np.median(row[reds], axis=0) if reds.any() else np.array([172, 41, 29])
        erase = ((row[:, 0]-row[:, 1]) < 119) | (row[:, 1] > color[1]+8)
        texture = color + rng.normal(0, .45, row.shape)
        row[erase] = np.clip(np.rint(texture[erase]), 0, 255)
        a[y, 150:989] = row.astype(np.uint8)
    return Image.fromarray(a)


TIP = tip_blank()
TIP.save(OUT/'verification/brush-tip-template.png')


def draw_tip(canvas, lines):
    tip = TIP.copy()
    s = 4
    layer = Image.new('RGBA', (W*s, tip.height*s))
    draw = ImageDraw.Draw(layer)
    size = 58 if len(lines) == 1 else 43
    while True:
        font = ImageFont.truetype(FONT, size*s, index=11)
        if max(draw.textbbox((0, 0), text, font=font)[2] for text in lines) <= 805*s:
            break
        size -= 1
    for i, text in enumerate(lines):
        cy = 77 if len(lines) == 1 else 48 + i*57
        draw.text((568*s, cy*s), text, font=font, anchor='mm',
                  fill=(249, 246, 237, 255), stroke_width=1)
    layer = layer.resize(tip.size, Image.Resampling.LANCZOS)
    tip.paste(layer, (0, 0), layer)
    canvas.paste(tip, (0, 1350))
    return {'font_size': size, 'lines': lines}


def fit_piece(canvas, piece, box):
    x1, y1, x2, y2 = box
    old_size = piece.size
    piece.thumbnail((x2-x1, y2-y1), Image.Resampling.LANCZOS)
    x, y = x1+(x2-x1-piece.width)//2, y1+(y2-y1-piece.height)//2
    canvas.paste(piece, (x, y))
    return {'source_size': list(old_size), 'output_size': list(piece.size), 'position': [x,y]}


def sync_one(number):
    original = Image.open(FILES[number]).convert('RGB')
    harmonized = harmonize_paper(original)
    canvas = paper_canvas()
    title = headline(original, number)
    canvas.paste(title, ((W-title.width)//2, 14+(88-title.height)//2), title)
    canvas.paste(REFERENCE.crop((129, 108, 901, 124)), (129, 108))
    pieces = []
    if number == '01':
        pieces.append(fit_piece(canvas, harmonized.crop((0,122,W,842)), (12,128,1012,828)))
        pieces.append(fit_piece(canvas, harmonized.crop((0,950,W,H)), (12,839,1012,1338)))
        tip = ['下行都背屈；提踵向上才跖屈。']
    elif number == '02':
        pieces.append(fit_piece(canvas, harmonized.crop((0,127,W,1379)), (8,129,1016,1334)))
        tip = ['窄握不等于腕关节外展；', '先看肘关节轨迹与腕部稳定。']
    elif number == '03':
        # Preserve the character's overlapping shoe below the old footer edge.
        a = np.asarray(harmonized).copy()
        zone = a[1392:1413].astype(np.int16)
        red = (zone[:, :, 0] > zone[:, :, 1]+60) & (zone[:, :, 0] > zone[:, :, 2]+60)
        zone[red] = PAPER.astype(np.int16)
        a[1392:1413] = zone.astype(np.uint8)
        piece = Image.fromarray(a).crop((0,120,W,1413))
        pieces.append(fit_piece(canvas, piece, (8,129,1016,1334)))
        tip = ['肘是复合关节；踝是踝穴包住距骨。']
    elif number == '05':
        # The top hair spike overlaps the old headline; retain blue artwork,
        # removing only remaining red headline pixels above the content cards.
        a = np.asarray(harmonized).copy()
        zone = a[136:161].astype(np.int16)
        red = (zone[:, :, 0] > zone[:, :, 1]+30) & (zone[:, :, 0] > zone[:, :, 2]+30)
        zone[red] = PAPER.astype(np.int16)
        a[136:161] = zone.astype(np.uint8)
        piece = Image.fromarray(a).crop((0,136,W,1381))
        pieces.append(fit_piece(canvas, piece, (8,129,1016,1334)))
        tip = ['短肌偏稳定；长肌偏动力输出。']
    info = draw_tip(canvas, tip)
    output = OUT/FILES[number].name
    canvas.save(output)
    return {'file':output.name, 'body_composition':pieces, 'tip':info,
            'source_sha256':hashlib.sha256(FILES[number].read_bytes()).hexdigest(),
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}


def preview():
    sheet = Image.new('RGB',(1600,1680),(234,230,221))
    font = ImageFont.truetype(FONT, 25, index=11)
    d = ImageDraw.Draw(sheet)
    for i,n in enumerate(['01','02','03','04','05']):
        im = Image.open(OUT/FILES[n].name)
        im.thumbnail((502,753))
        x,y = 25+(i%3)*525, 49+(i//3)*820
        sheet.paste(im,(x,y))
        d.text((x,y-34),n+' · 样式基准' if n == '04' else n,font=font,fill=RED)
    sheet.save(OUT/'00-统一风格总览.jpg',quality=95)


def main():
    if set(FILES) != {'01','02','03','04','05'}:
        raise RuntimeError('Expected the five verified source PNGs.')
    entries = [sync_one(n) for n in ['01','02','03','05']]
    shutil.copy2(FILES['04'],OUT/FILES['04'].name)
    preview()
    manifest = {'status':'awaiting-user-review','style_reference':str(FILES['04']),
                'style_reference_unchanged':True, 'paper_rgb':PAPER.astype(int).tolist(),
                'method':'local composition of existing Lingzhi artwork',
                'new_generation_requests':0, 'entries':entries}
    (OUT/'review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(OUT/'关节动作错题本-统一风格五图.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for n in ['01','02','03','04','05']:
            archive.write(OUT/FILES[n].name,FILES[n].name)
    print(OUT)


if __name__ == '__main__':
    main()
