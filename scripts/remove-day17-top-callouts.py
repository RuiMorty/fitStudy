from PIL import Image, ImageDraw
from statistics import median


SOURCE = "html/assets/阶段1基础科学/day17-动作的生物力学分析-动作模式.png"
OUTPUT = "/private/tmp/day17-top-callouts-removed.png"


def in_region(x, y):
    return (10 <= x <= 280 and 210 <= y <= 590) or (760 <= x <= 1023 and 210 <= y <= 565)


def callout_color(rgb):
    r, g, b = rgb
    green = g > r + 10 and g > b + 10 and g > 90
    orange = r > 180 and g < 150 and b < 120
    return green or orange


image = Image.open(SOURCE).convert("RGB")
pixels = image.load()
width, height = image.size
mask = set()

for y in range(210, 591):
    for x in range(10, 281):
        if callout_color(pixels[x, y]):
            mask.add((x, y))

for y in range(210, 566):
    for x in range(760, width):
        if callout_color(pixels[x, y]):
            mask.add((x, y))

# Replace colored leader/arrow pixels from their nearest surrounding colors.
for x, y in mask:
    samples = []
    for radius in range(2, 14):
        for dx, dy in ((radius, 0), (-radius, 0), (0, radius), (0, -radius),
                       (radius, radius), (-radius, radius), (radius, -radius), (-radius, -radius)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < width and 0 <= yy < height and (xx, yy) not in mask:
                samples.append(pixels[xx, yy])
        if len(samples) >= 8:
            break
    if samples:
        pixels[x, y] = tuple(int(median([sample[i] for sample in samples])) for i in range(3))

# Remove all title and text blocks for the two top "joint movement" callouts.
draw = ImageDraw.Draw(image)
for box in (
    (15, 214, 111, 261), (15, 269, 108, 330), (15, 385, 108, 446), (15, 501, 108, 566),
    (896, 214, 1023, 261), (894, 268, 1023, 330), (894, 383, 1023, 446), (894, 500, 1023, 566),
):
    draw.rectangle(box, fill=(255, 255, 255))

image.save(OUTPUT)
