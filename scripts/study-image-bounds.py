"""Read image geometry for the shared renderer without changing source pixels."""
import json
import sys

from PIL import Image


def image_bounds(filename):
    with Image.open(filename) as image:
        width, height = image.size
        alpha = image.convert('RGBA').getchannel('A')
        # Ignore faint transparent-edge noise, retaining a small safety border.
        box = alpha.point(lambda value: 255 if value > 8 else 0).getbbox()
        if box is None:
            raise ValueError(f'Image contains no visible pixels: {filename}')
        pad = max(2, round(min(box[2] - box[0], box[3] - box[1]) * .02))
        left, top = max(0, box[0] - pad), max(0, box[1] - pad)
        right, bottom = min(width, box[2] + pad), min(height, box[3] + pad)
        return {'size': [width, height], 'viewBox': [left, top, right - left, bottom - top]}


if __name__ == '__main__':
    print(json.dumps([image_bounds(filename) for filename in json.load(sys.stdin)]))
