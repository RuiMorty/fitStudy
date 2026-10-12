#!/usr/bin/env python3
"""Extract the established warm-up Rick illustration onto a transparent canvas.

The source is an RGB illustration on pale cream paper. A connected background
flood fill removes only paper reachable from the image border, so the light
shirt and shoes inside the dark character outline remain opaque. This uses
Pillow only; no image-generation service or vector conversion is involved.
"""

from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "xhs-wrong-notebook/2026-09-22-joint-actions/00-rick-muscular-cartoon-model-v4.png"
OUTPUT = ROOT / "xhs-knowledge/2026-10-08-aerobic-fueling/assets/rick-standing-cutout.png"
PADDING = 24


def resembles_paper(rgb: tuple[int, int, int]) -> bool:
    """Accept the source's warm paper, including its lightly blended edge."""
    red, green, blue = rgb
    return (
        red >= 215
        and green >= 207
        and blue >= 190
        and -2 <= red - green <= 26
        and 1 <= green - blue <= 33
    )


def connected_component(mask: bytearray, width: int, height: int, seeds: list[int]) -> bytearray:
    """Find a four-connected component of 1-valued pixels."""
    found = bytearray(width * height)
    queue: deque[int] = deque()
    for index in seeds:
        if mask[index] and not found[index]:
            found[index] = 1
            queue.append(index)

    while queue:
        index = queue.popleft()
        x = index % width
        y = index // width
        for neighbor in (
            index - 1 if x else -1,
            index + 1 if x + 1 < width else -1,
            index - width if y else -1,
            index + width if y + 1 < height else -1,
        ):
            if neighbor >= 0 and mask[neighbor] and not found[neighbor]:
                found[neighbor] = 1
                queue.append(neighbor)
    return found


def largest_foreground(mask: bytearray, width: int, height: int) -> bytearray:
    """Drop tiny isolated paper flecks left by the source's RGB texture."""
    unseen = bytearray(mask)
    largest: list[int] = []

    for start in range(width * height):
        if not unseen[start]:
            continue
        unseen[start] = 0
        queue: deque[int] = deque([start])
        component = [start]
        while queue:
            index = queue.popleft()
            x = index % width
            y = index // width
            for neighbor in (
                index - 1 if x else -1,
                index + 1 if x + 1 < width else -1,
                index - width if y else -1,
                index + width if y + 1 < height else -1,
            ):
                if neighbor >= 0 and unseen[neighbor]:
                    unseen[neighbor] = 0
                    queue.append(neighbor)
                    component.append(neighbor)
        if len(component) > len(largest):
            largest = component

    result = bytearray(width * height)
    for index in largest:
        result[index] = 1
    return result


def extract() -> None:
    with Image.open(SOURCE) as source:
        image = source.convert("RGB")

    width, height = image.size
    paper = bytearray(resembles_paper(pixel) for pixel in image.getdata())
    border = [x for x in range(width)]
    border += [(height - 1) * width + x for x in range(width)]
    border += [y * width for y in range(height)]
    border += [y * width + width - 1 for y in range(height)]
    background = connected_component(paper, width, height, border)

    foreground = bytearray(0 if pixel else 1 for pixel in background)
    foreground = largest_foreground(foreground, width, height)
    alpha = Image.frombytes("L", (width, height), bytes(255 if value else 0 for value in foreground))
    bounds = alpha.getbbox()
    if bounds is None:
        raise RuntimeError("No character found in source image")

    left = max(0, bounds[0] - PADDING)
    top = max(0, bounds[1] - PADDING)
    right = min(width, bounds[2] + PADDING)
    bottom = min(height, bounds[3] + PADDING)
    rgba = image.convert("RGBA")
    rgba.putalpha(alpha)
    rgba = rgba.crop((left, top, right, bottom))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(OUTPUT, format="PNG", optimize=True)
    print(f"source={SOURCE}")
    print(f"output={OUTPUT} size={rgba.width}x{rgba.height} alpha_bbox={rgba.getchannel('A').getbbox()}")


if __name__ == "__main__":
    extract()
