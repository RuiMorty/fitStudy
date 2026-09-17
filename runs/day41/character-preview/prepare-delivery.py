"""Normalize transparent samples and show their appearance over the card gradient."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from PIL import Image, ImageOps

ROOT = Path('/Users/agiuser/Documents/fit')
HERE = Path(__file__).resolve().parent
DELIVERIES = [
    ('cover', (1600, 900), 'html/thumbs/day41-bojji-despa-thumbnail-preview.png'),
    ('detail', (1536, 1024), 'html/assets/阶段2训练科学/day41-下肢杠铃技术-波吉德斯帕预览.png'),
]
records = []
for name, size, relative in DELIVERIES:
    source = HERE / 'source' / (name + '.png')
    im = Image.open(source).convert('RGBA')
    alpha = im.getchannel('A')
    if alpha.getextrema()[0] != 0:
        raise SystemExit('Background is not transparent; manual review required.')
    # Discard only nearly invisible alpha specks; preserve original art and white clothing.
    alpha = alpha.point(lambda a: 0 if a <= 8 else a)
    im.putalpha(alpha)
    bounds = alpha.getbbox()
    if not bounds:
        raise SystemExit('No visible subject.')
    bounds = (max(0,bounds[0]-3), max(0,bounds[1]-3), min(im.width,bounds[2]+3), min(im.height,bounds[3]+3))
    margin = round(min(size) * .06)
    fitted = ImageOps.contain(im.crop(bounds), (size[0]-2*margin, size[1]-2*margin), Image.Resampling.LANCZOS)
    result = Image.new('RGBA', size, (0,0,0,0))
    offset = ((size[0]-fitted.width)//2, (size[1]-fitted.height)//2)
    result.alpha_composite(fitted, offset)
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    result.save(target)
    # The same white -> #f7f7f8 palette as the shared XHS card; not a final XHS export.
    ramp = Image.new('RGB', (1,size[1]))
    ramp.putdata([(round(255-8*y/(size[1]-1)), round(255-8*y/(size[1]-1)), round(255-7*y/(size[1]-1))) for y in range(size[1])])
    background = ramp.resize(size).convert('RGBA')
    preview = Image.alpha_composite(background, result)
    preview_path = HERE / (name + '-on-card.jpg')
    preview.convert('RGB').save(preview_path, quality=97)
    a = result.getchannel('A')
    corners = [result.getpixel((x,y))[3] for x,y in [(0,0),(size[0]-1,0),(0,size[1]-1),(size[0]-1,size[1]-1)]]
    assert corners == [0,0,0,0]
    border = [a.crop((0,0,size[0],margin//2)).getbbox(),a.crop((0,size[1]-margin//2,size[0],size[1])).getbbox(),a.crop((0,0,margin//2,size[1])).getbbox(),a.crop((size[0]-margin//2,0,size[0],size[1])).getbbox()]
    assert not any(border)
    # Every fully transparent pixel reproduces the underlying card gradient exactly.
    transparent = [i for i,value in enumerate(a.getdata()) if value == 0]
    bg_pixels = list(background.getdata()); preview_pixels = list(preview.getdata())
    mismatches = sum(bg_pixels[i] != preview_pixels[i] for i in transparent)
    assert mismatches == 0
    records.append({'role':name,'source':str(source.relative_to(ROOT)),'sourceSize':list(im.size),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceCropBox':bounds,'delivery':relative,'deliverySize':list(size),'preview':str(preview_path.relative_to(ROOT)),'resizedSubjectSize':list(fitted.size),'subjectOffset':offset,'transparentCorners':corners,'transparentPixels':len(transparent),'backgroundPixelMismatches':mismatches,'method':'remove alpha<=8 noise; crop transparent margin; scale uniformly; add transparent safe margin; preserve original source'})

manifest = {'createdAt':datetime.now(timezone.utc).isoformat(),'status':'style-samples-awaiting-user-review','generatedImages':2,'automaticRetries':0,'characters':['Bojji','Despa'],'background':'true-alpha-PNG','previewBackground':'linear-gradient(180deg,#fff,#f7f7f8)','finalXhsExport':False,'assets':records}
(HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'delivered':[r['delivery'] for r in records],'backgroundPixelMismatches':[r['backgroundPixelMismatches'] for r in records]},ensure_ascii=False))
