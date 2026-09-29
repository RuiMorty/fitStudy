from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import hashlib
import json

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT.parent / '2026-09-21-错题复盘-封面.png'
SCENE = ROOT / 'rick-door-scene.png'
OUTPUT = ROOT.parent / '2026-09-21-错题复盘-封面-Rick.png'

reference = Image.open(REFERENCE).convert('RGB')
assert reference.size == (1080, 1440), reference.size
paper = reference.getpixel((0, 0))
scene = Image.open(SCENE).convert('RGB')
source_size = scene.size
scale = min(1030 / source_size[0], 1030 / source_size[1])
scene = scene.resize(
    (round(source_size[0] * scale), round(source_size[1] * scale)),
    Image.Resampling.LANCZOS,
)

# Feather only the blank peripheral margin, retaining the whole seated figure.
mask = Image.new('L', scene.size, 0)
draw = ImageDraw.Draw(mask)
feather = 44
for inset in range(feather):
    value = round(255 * (inset / (feather - 1)) ** 0.65)
    draw.rectangle((inset, inset, scene.width - inset - 1, scene.height - inset - 1), fill=value)

cover = Image.new('RGB', reference.size, paper)
cover.paste(scene, ((1080 - scene.width) // 2, 410 + (1030 - scene.height) // 2), mask)
# Preserve the exact supplied title, logo and both red lines pixel for pixel.
header = reference.crop((0, 0, 1080, 410))
cover.paste(header, (0, 0))
cover.save(OUTPUT)

saved = Image.open(OUTPUT).convert('RGB')
assert saved.size == (1080, 1440)
assert ImageChops.difference(header, saved.crop((0, 0, 1080, 410))).getbbox() is None
assert OUTPUT.stat().st_size > 0

metadata = {
    'reference': REFERENCE.name,
    'reference_sha256': hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
    'generated_asset': SCENE.name,
    'generated_size': source_size,
    'preset': 'quality',
    'model': 'gpt-image-2.5-sunburst',
    'output': OUTPUT.name,
    'size': saved.size,
    'preserved_header_rows': [0, 409],
    'header_pixel_match': True,
}
(ROOT / 'composition.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'output': str(OUTPUT), 'size': saved.size, 'bytes': OUTPUT.stat().st_size, 'header_pixel_match': True}, ensure_ascii=False))
