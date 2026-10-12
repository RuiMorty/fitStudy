#!/usr/bin/env python3
"""Render the aerobic-fueling Xiaohongshu carousel with native Chinese text."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


ROOT = Path(__file__).resolve().parent
CONTENT = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
SLIDES = {slide["id"]: slide for slide in CONTENT["slides"]}
OUT = ROOT / "images"
GENERATED = ROOT / "generation"
WIDTH, HEIGHT = 1536, 2048
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"

PAPER = "#F8F4EB"
WHITE = "#FFFCF6"
INK = "#1B3040"
NAVY = "#183C50"
RUST = "#9B4537"
RUST_PALE = "#F5E5DD"
SAGE = "#577569"
SAGE_PALE = "#E5EEE6"
GOLD = "#AF7C43"
GOLD_PALE = "#F3E8D4"
BLUE = "#47728A"
BLUE_PALE = "#E7EEF1"
MUTED = "#607079"
RULE = "#C9C7BC"
SHADOW = "#E9E2D6"


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size, index=2 if bold else 0)


def text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    value: str,
    size: int,
    color: str = INK,
    bold: bool = False,
    max_width: int | None = None,
    anchor: str = "lt",
) -> None:
    face = font(size, bold)
    if max_width is not None and draw.textlength(value, font=face) > max_width:
        raise ValueError(f"Text overflows {max_width}px: {value}")
    draw.text((x, y), value, font=face, fill=color, anchor=anchor)


def wrap(draw: ImageDraw.ImageDraw, value: str, size: int, max_width: int) -> list[str]:
    face = font(size)
    lines: list[str] = []
    line = ""
    for char in value:
        candidate = line + char
        if draw.textlength(candidate, font=face) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = char
    if line:
        lines.append(line)
    return lines


def paragraph(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: list[str] | str,
    size: int,
    color: str,
    width: int,
    leading: int,
    bold: bool = False,
) -> int:
    if isinstance(lines, str):
        lines = [lines]
    for source_line in lines:
        for line in wrap(draw, source_line, size, width):
            text(draw, x, y, line, size, color, bold, width)
            y += leading
    return y


def card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str = WHITE,
    border: str = RULE,
    radius: int = 38,
    shadow: bool = True,
) -> None:
    x0, y0, x1, y1 = box
    if shadow:
        draw.rounded_rectangle((x0 + 7, y0 + 9, x1 + 7, y1 + 9), radius=radius, fill=SHADOW)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=2)


def capsule(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    fill: str,
    color: str,
    size: int = 38,
    pad_x: int = 24,
    height: int = 68,
) -> int:
    width = int(draw.textlength(label, font=font(size, True))) + pad_x * 2
    draw.rounded_rectangle((x, y, x + width, y + height), radius=height // 2, fill=fill)
    text(draw, x + pad_x, y + (height - size) // 2 - 1, label, size, color, True)
    return width


def page(index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 17), fill=RUST)
    draw.ellipse((1260, -180, 1650, 210), fill="#F0E9DC")
    text(draw, 108, 88, "FITSTUDY   /   运动科学", 38, NAVY, True)
    text(draw, 1428, 91, f"{index:02d} / 06", 36, RUST, True, anchor="rt")
    draw.line((108, 179, 1428, 179), fill=RULE, width=2)
    draw.line((108, 1932, 1428, 1932), fill=RULE, width=2)
    text(draw, 108, 1954, "有氧运动供能 · 知识图解", 30, MUTED)
    text(draw, 1428, 1954, "保存后按顺序阅读  →", 30, MUTED, anchor="rt")
    return image, draw


def save(image: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    image.save(path, format="PNG", optimize=True)
    return path


def draw_cover() -> Path:
    data = SLIDES["01-cover"]
    image, draw = page(1)
    capsule(draw, 108, 233, "供能时间线 · 6 张图讲清", RUST_PALE, RUST, 36, 25, 66)
    text(draw, 108, 337, data["title"][0], 154, INK, True)
    text(draw, 108, 515, data["title"][1], 154, INK, True)
    text(draw, 108, 713, data["answer"], 91, RUST, True)
    text(draw, 108, 847, data["lead"], 43, MUTED, False, 1320)

    dark = (108, 975, 1428, 1705)
    draw.rounded_rectangle(dark, radius=48, fill=NAVY)
    text(draw, 160, 1026, "先记住这一句", 40, "#D6E5E3", True)
    text(draw, 160, 1098, data["takeaway"], 73, WHITE, True, 1210)
    draw.line((160, 1210, 1375, 1210), fill="#76939B", width=2)
    colors = [RUST, GOLD, SAGE]
    for i, ((label, explanation), color) in enumerate(zip(data["lanes"], colors)):
        y = 1250 + i * 130
        draw.rounded_rectangle((160, y, 345, y + 91), radius=27, fill=color)
        text(draw, 252, y + 43, label, 55, WHITE, True, anchor="mm")
        text(draw, 390, y + 22, explanation, 52, WHITE, True, 900)

    card(draw, (108, 1750, 1428, 1859), fill=RUST_PALE, border=RUST_PALE, radius=33, shadow=False)
    text(draw, 145, 1777, "没有“30 分钟后才燃脂”的开关。", 51, RUST, True, 1240)
    return save(image, data["id"])


def draw_onset() -> Path:
    data = SLIDES["02-onset"]
    image, draw = page(2)
    text(draw, 108, 242, data["title"], 116, INK, True)
    paragraph(draw, 108, 400, data["lead"], 47, MUTED, 1290, 68)

    colors = [(RUST, RUST_PALE), (GOLD, GOLD_PALE), (SAGE, SAGE_PALE)]
    for i, (stage, (accent, pale)) in enumerate(zip(data["stages"], colors)):
        top = 565 + i * 340
        card(draw, (108, top, 1428, top + 309))
        draw.rounded_rectangle((108, top, 128, top + 309), radius=10, fill=accent)
        capsule(draw, 158, top + 37, stage["time"], pale, accent, 42, 21, 72)
        text(draw, 520, top + 39, stage["heading"], 64, INK, True, 845)
        paragraph(draw, 520, top + 139, stage["body"], 46, INK, 835, 62)

    card(draw, (108, 1615, 1428, 1847), fill=RUST_PALE, border=RUST_PALE, shadow=False)
    text(draw, 154, 1650, "关键：时间不是交接点", 53, RUST, True)
    paragraph(draw, 154, 1720, data["note"], 44, INK, 1200, 57)
    text(draw, 154, 1800, "实验参考：Rossiter 2002；Gaitanos 1993", 29, MUTED)
    return save(image, data["id"])


def draw_sources() -> Path:
    data = SLIDES["03-sources"]
    image, draw = page(3)
    text(draw, 108, 240, data["title"], 104, INK, True)
    text(draw, 108, 387, data["lead"], 48, MUTED, False, 1320)

    colors = [
        (RUST, RUST_PALE, "肌"),
        (BLUE, BLUE_PALE, "肝"),
        (SAGE, SAGE_PALE, "脂"),
        (GOLD, GOLD_PALE, "糖"),
    ]
    for i, (source, (accent, pale, glyph)) in enumerate(zip(data["sources"], colors)):
        col, row = i % 2, i // 2
        left = 108 + col * 680
        top = 530 + row * 510
        card(draw, (left, top, left + 640, top + 470))
        draw.ellipse((left + 508, top + 40, left + 594, top + 126), fill=pale)
        text(draw, left + 551, top + 83, glyph, 56, accent, True, anchor="mm")
        text(draw, left + 43, top + 52, source["name"], 69, accent, True, 460)
        text(draw, left + 43, top + 144, source["tag"], 42, INK, True, 548)
        draw.line((left + 43, top + 214, left + 594, top + 214), fill=RULE, width=2)
        paragraph(draw, left + 43, top + 242, source["body"], 44, INK, 548, 61)

    card(draw, (108, 1585, 1428, 1749), fill=NAVY, border=NAVY, shadow=False)
    paragraph(draw, 145, 1619, data["note"], 49, WHITE, 1240, 65, True)
    text(draw, 108, 1804, "储量参考：全身肌糖原约 500 g；肝糖原约 80 g。个体差异很大。", 36, MUTED, False, 1320)
    return save(image, data["id"])


def draw_duration() -> Path:
    data = SLIDES["04-duration"]
    image, draw = page(4)
    text(draw, 108, 238, data["title"][0], 108, INK, True)
    text(draw, 108, 361, data["title"][1], 108, INK, True)
    capsule(draw, 108, 525, data["lead"], BLUE_PALE, BLUE, 38, 24, 70)

    colors = [(RUST, RUST_PALE), (GOLD, GOLD_PALE), (SAGE, SAGE_PALE)]
    for i, (stage, (accent, pale)) in enumerate(zip(data["stages"], colors)):
        top = 645 + i * 320
        card(draw, (108, top, 1428, top + 292))
        draw.rounded_rectangle((141, top + 33, 561, top + 114), radius=24, fill=pale)
        text(draw, 166, top + 49, stage["time"], 55, accent, True)
        text(draw, 610, top + 48, stage["heading"], 61, INK, True, 760)
        paragraph(draw, 160, top + 147, stage["body"], 47, INK, 1210, 61)

    card(draw, (108, 1624, 1428, 1845), fill=RUST_PALE, border=RUST_PALE, shadow=False)
    text(draw, 153, 1666, "时间是趋势，不是开关。", 64, RUST, True)
    text(draw, 154, 1767, data["note"], 39, INK, False, 1210)
    return save(image, data["id"])


def draw_amounts() -> Path:
    data = SLIDES["05-amounts"]
    image, draw = page(5)
    text(draw, 108, 236, data["title"][0], 98, INK, True)
    text(draw, 108, 353, data["title"][1], 104, INK, True)
    text(draw, 108, 515, data["lead"], 47, MUTED, False, 1320)
    capsule(draw, 108, 613, "稳态假设：每小时消耗 600 kcal", GOLD_PALE, GOLD, 39, 26, 76)

    for i, row in enumerate(data["rows"]):
        top = 730 + i * 280
        card(draw, (108, top, 1428, top + 245))
        draw.rounded_rectangle((108, top, 126, top + 245), radius=9, fill=[SAGE, BLUE, RUST][i])
        text(draw, 163, top + 42, "呼吸交换率", 35, MUTED)
        text(draw, 160, top + 105, f"RER {row['rer']}", 55, INK, True)
        draw.line((470, top + 35, 470, top + 207), fill=RULE, width=2)
        text(draw, 522, top + 46, "总糖氧化", 39, RUST, True)
        text(draw, 522, top + 111, f"{row['carbohydrate_g_per_h']} g/h", 80, RUST, True)
        draw.line((913, top + 35, 913, top + 207), fill=RULE, width=2)
        text(draw, 955, top + 46, "总脂肪氧化", 39, SAGE, True)
        text(draw, 955, top + 111, f"{row['fat_g_per_h']} g/h", 80, SAGE, True)

    card(draw, (108, 1600, 1428, 1856), fill=BLUE_PALE, border=BLUE_PALE, shadow=False)
    paragraph(draw, 153, 1640, data["note"], 42, INK, 1210, 60)
    text(draw, 153, 1805, "演算依据：Weir 1949；Frayn 1983。忽略蛋白质氧化。", 31, MUTED)
    return save(image, data["id"])


def draw_summary() -> Path:
    data = SLIDES["06-summary"]
    image, draw = page(6)
    text(draw, 108, 240, data["title"], 109, INK, True)
    text(draw, 108, 401, "把供能变化记成一张清楚的地图", 49, MUTED)

    colors = [(RUST, RUST_PALE), (BLUE, BLUE_PALE), (SAGE, SAGE_PALE), (GOLD, GOLD_PALE)]
    for i, (point, (accent, pale)) in enumerate(zip(data["points"], colors)):
        top = 510 + i * 302
        card(draw, (108, top, 1428, top + 260))
        draw.ellipse((154, top + 70, 272, top + 188), fill=pale)
        text(draw, 213, top + 129, f"{i+1:02d}", 55, accent, True, anchor="mm")
        paragraph(draw, 325, top + 69, point, 54, INK, 1030, 75, True)

    card(draw, (108, 1760, 1428, 1870), fill=NAVY, border=NAVY, shadow=False)
    text(draw, 151, 1782, data["takeaway"], 68, WHITE, True)
    return save(image, data["id"])


def contact_sheet(paths: list[Path]) -> Path:
    thumb_width, thumb_height = 462, 616
    gap, margin, header = 27, 40, 106
    canvas = Image.new("RGB", (margin * 2 + thumb_width * 3 + gap * 2, header + margin * 2 + thumb_height * 2 + gap), PAPER)
    draw = ImageDraw.Draw(canvas)
    text(draw, margin, 27, "有氧供能 · 6 张知识图预览", 45, INK, True)
    for i, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        left = margin + (i % 3) * (thumb_width + gap)
        top = header + margin + (i // 3) * (thumb_height + gap)
        canvas.paste(image, (left, top))
        draw.rounded_rectangle((left, top, left + thumb_width, top + thumb_height), radius=8, outline=RULE, width=2)
    result = OUT / "preview-contact-sheet.jpg"
    canvas.save(result, quality=91, optimize=True)
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    paths = [
        draw_cover(),
        draw_onset(),
        draw_sources(),
        draw_duration(),
        draw_amounts(),
        draw_summary(),
    ]
    contact_sheet(paths)
    manifest = {
        "status": "awaiting-user-review",
        "generator": "render_cards.py",
        "pillow": pillow_version,
        "dimensions": [WIDTH, HEIGHT],
        "content_sha256": hashlib.sha256((ROOT / "content.json").read_bytes()).hexdigest(),
        "images": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in paths
        ],
        "preview": "images/preview-contact-sheet.jpg",
    }
    (GENERATED / "render-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Rendered {len(paths)} cards to {OUT}")


if __name__ == "__main__":
    main()
