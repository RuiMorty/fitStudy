"""Compose a transparent study overview with reviewed art and exact font-rendered text."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    config = json.loads(Path(args.input).read_text())
    width, height = config.get('size', [1536, 1024])
    scale = 2
    canvas = Image.new('RGBA', (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font_path = config.get('font', '/System/Library/Fonts/STHeiti Medium.ttc')
    text_records = []

    def label(text, x, y, size, max_width, center=False, color='#111113'):
        font = ImageFont.truetype(font_path, size * scale)
        length = draw.textlength(text, font=font) / scale
        if length > max_width:
            raise ValueError(f'Text exceeds its slot: {text}')
        if center:
            x -= length / 2
        draw.text((round(x * scale), round(y * scale)), text, font=font, fill=color, anchor='lt')
        text_records.append({'text': text, 'fontSize': size, 'width': length, 'position': [x, y]})

    label(config['title'], width / 2, 52, 68, width - 128, center=True)
    label(config['subtitle'], width / 2, 138, 32, width - 128, center=True, color='#535963')
    columns = config.get('columns', 3)
    rows = math.ceil(len(config['panels']) / columns)
    gap, margin, top, bottom = 28, 64, 211, height - 138
    cell_width = (width - margin * 2 - gap * (columns - 1)) / columns
    cell_height = (bottom - top - gap * (rows - 1)) / rows
    for i, panel in enumerate(config['panels']):
        x = margin + (i % columns) * (cell_width + gap)
        y = top + (i // columns) * (cell_height + gap)
        label(panel['title'], x, y, 42, cell_width)
        label(panel['description'], x, y + 48, 32, cell_width, color='#3f4650')
        legend = panel.get('legend')
        box = (round(x * scale), round((y + 89) * scale), round(cell_width * scale), round((cell_height - 95 - (29 if legend else 0)) * scale))
        art = Image.open(root / panel['image']).convert('RGBA')
        art = art.crop(art.getchannel('A').getbbox())
        fitted = ImageOps.contain(art, box[2:], Image.Resampling.LANCZOS)
        canvas.alpha_composite(fitted, (box[0] + (box[2] - fitted.width) // 2, box[1] + (box[3] - fitted.height) // 2))
        if legend:
            label(legend, x + cell_width / 2, y + cell_height - 25, 26, cell_width, center=True, color='#535963')
        if i % columns < columns - 1:
            line_x = round((x + cell_width + gap / 2) * scale)
            draw.line((line_x, round(y * scale), line_x, round((y + cell_height) * scale)), fill='#d9dee4', width=2)
    draw.line((margin * scale, (height - 119) * scale, (width - margin) * scale, (height - 119) * scale), fill='#d9dee4', width=2)
    for i, text in enumerate(config['footer']):
        label(text, width / 2, height - 99 + i * 38, 32 if i == 0 else 26, width - 128, center=True, color='#3f4650')
    target = root / config['output']
    target.parent.mkdir(parents=True, exist_ok=True)
    delivery_scale = config.get('deliveryScale', 1)
    if delivery_scale not in (1, 2):
        raise ValueError('deliveryScale must be 1 or 2')
    canvas.save(target.with_name(f'{target.stem}-2x.png'))
    delivery = canvas if delivery_scale == scale else canvas.resize((width, height), Image.Resampling.LANCZOS)
    delivery.save(target)
    record = {'method': 'font-rendered text; reviewed transparent art; two-times master', 'textSource': str(Path(args.input)), 'texts': text_records, 'output': str(target), 'logicalSize': [width, height], 'size': list(delivery.size)}
    target.with_suffix('.typesetting.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(target), 'textBlocks': len(text_records), 'size': list(delivery.size)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
