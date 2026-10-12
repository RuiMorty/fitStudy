#!/usr/bin/env python3
"""Render chart-first aerobic-fueling cards in the September 28 visual style."""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


ROOT = Path(__file__).resolve().parent
CONTENT = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
OUT = ROOT / "images"
ASSETS = ROOT / "assets"
W, H = 1536, 2048
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

# The paper, headline, ink and blue are taken from the 2026-09-28 knowledge image.
PAPER = "#F4EFE5"
RED = "#92362A"
INK = "#323331"
GRAY = "#686A65"
RULE = "#A5A39B"
SOFT_RULE = "#D3C7BA"
BLUE = "#4B91B3"
PALE_BLUE = "#DCECF2"
GREEN = "#5D8066"
PALE_GREEN = "#DCE8DC"
GOLD = "#B1854B"
PALE_GOLD = "#F0E2CA"
PALE_RED = "#EAD5CF"
WHITE = "#FFFCF6"


@lru_cache(maxsize=None)
def face(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size=size, index=2 if bold else 0)


def text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    value: str,
    size: int,
    fill: str = INK,
    bold: bool = False,
    anchor: str = "lt",
    max_width: int | None = None,
) -> None:
    ft = face(size, bold)
    if max_width is not None and draw.textlength(value, font=ft) > max_width:
        raise ValueError(f"Text exceeds {max_width}px: {value}")
    draw.text((x, y), value, font=ft, fill=fill, anchor=anchor)


def lines(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    values: list[str],
    size: int,
    leading: int,
    fill: str = INK,
    bold: bool = False,
) -> None:
    for i, value in enumerate(values):
        text(draw, x, y + leading * i, value, size, fill, bold)


def rule(draw: ImageDraw.ImageDraw, y: int, x0: int = 80, x1: int = 1456, width: int = 3) -> None:
    draw.line((x0, y, x1, y), fill=RULE, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str,
    width: int = 9,
    head: int = 25,
) -> None:
    draw.line((*start, *end), fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - 0.48), end[1] - head * math.sin(angle - 0.48))
    right = (end[0] - head * math.cos(angle + 0.48), end[1] - head * math.sin(angle + 0.48))
    draw.polygon((end, left, right), fill=fill)


def dot(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, fill: str, outline: str | None = None) -> None:
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=3)


def page(index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 19), fill=RED)
    text(draw, 80, 56, "FITSTUDY / 运动科学", 39, INK, True)
    text(draw, 1456, 59, f"{index:02d} / 07", 37, RED, True, anchor="rt")
    rule(draw, 136)
    rule(draw, 1940)
    text(draw, 80, 1960, "有氧供能图解", 29, GRAY)
    text(draw, 1456, 1960, "时间表示趋势，不是切换点", 29, GRAY, anchor="rt")
    return image, draw


def save(image: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    image.save(path, format="PNG", optimize=True)
    return path


def paste_asset(image: Image.Image, name: str, box: tuple[int, int, int, int]) -> None:
    asset_path = ASSETS / name
    with Image.open(asset_path) as source:
        asset = source.convert("RGBA")
    left, top, width, height = box
    asset.thumbnail((width, height), Image.Resampling.LANCZOS)
    image.paste(asset, (left + (width - asset.width) // 2, top + (height - asset.height) // 2), asset)


def cover() -> Path:
    image, draw = page(1)
    lines(draw, 80, 183, ["跑步 30 分钟，", "才开始燃脂？"], 122, 144, RED, True)
    text(draw, 84, 510, "有氧运动从起步到 2 小时后的供能变化", 48, INK)
    rule(draw, 625)

    text(draw, 82, 681, "三种角色一起上场", 56, INK, True)
    lanes = [
        ("PCr", "ATP 缓冲起步最快", BLUE, 862),
        ("糖", "肌糖原与血糖并行", RED, 1060),
        ("脂肪", "脂肪酸从起步氧化", GREEN, 1258),
    ]
    for label, note, color, y in lanes:
        text(draw, 85, y - 27, label, 71, color, True)
        draw.line((328, y + 10, 789, y + 10), fill=color, width=23)
        dot(draw, 328, y + 10, 15, color)
        text(draw, 328, y + 50, note, 37, GRAY)

    text(draw, 84, 1415, "PCr 是快速缓冲；糖和脂肪是燃料。", 35, GRAY)
    text(draw, 84, 1470, "线段只表示参与，不代表供能占比。", 35, GRAY)

    paste_asset(image, "rick-standing-cutout.png", (866, 675, 555, 1050))
    draw.rectangle((0, 1555, W, 1920), fill=PAPER)
    rule(draw, 1555)
    text(draw, 82, 1605, "答案：脂肪从起步就参与。", 73, RED, True)
    text(draw, 84, 1745, "7 张图看懂时间节点、燃料来源和实际氧化量", 42, INK)
    return save(image, "01-cover.png")


def timeline() -> Path:
    image, draw = page(2)
    lines(draw, 80, 188, ["有氧运动，", "到底先烧什么？"], 143, 166, RED, True)
    text(draw, 82, 562, "肌糖原 / 肝糖原 / 脂肪 / 糖异生", 57, INK, True)
    rule(draw, 665)

    text(draw, 80, 708, "从起步到更久：三条线同时存在", 56, INK, True)
    x0, x1 = 350, 1388
    ticks = [(x0, "起步"), (640, "1–3 分钟"), (1010, "30–120 分钟"), (x1, "更久")]
    for x, label in ticks:
        draw.line((x, 834, x, 1558), fill=SOFT_RULE, width=3)
        text(draw, x, 784, label, 34, GRAY, anchor="mt")

    lane_y = [977, 1184, 1391]
    lane_labels = [("PCr", BLUE), ("糖类", RED), ("脂肪", GREEN)]
    lane_notes = ["起步快速补位，之后仍在周转", "肌糖原与血糖持续参与", "从起步参与，比例常逐渐上升"]
    for y, (label, color), note in zip(lane_y, lane_labels, lane_notes):
        text(draw, 83, y - 44, label, 72, color, True)
        draw.line((x0, y + 10, x1, y + 10), fill=SOFT_RULE, width=10)
        if label == "PCr":
            draw.line((x0, y + 10, 687, y + 10), fill=color, width=27)
            draw.line((687, y + 10, x1, y + 10), fill=color, width=9)
            dot(draw, x0, y + 10, 18, color)
        else:
            draw.line((x0, y + 10, x1, y + 10), fill=color, width=24)
            dot(draw, x0, y + 10, 17, color)
            arrow(draw, (x1 - 75, y + 10), (x1 + 5, y + 10), color, 13, 25)
        text(draw, x0, y + 46, note, 38, GRAY)

    rule(draw, 1622)
    text(draw, 82, 1664, "脂肪从运动开始就参与。", 83, RED, True)
    text(draw, 84, 1781, "线段只表示参与与趋势；阶段间距与供能占比均不按比例。", 36, GRAY)
    return save(image, "02-timeline.png")


def pcr_curve() -> Path:
    image, draw = page(3)
    lines(draw, 80, 185, ["起步 120 秒，", "PCr 怎样变化？"], 110, 130, RED, True)
    text(draw, 82, 463, "PCr 快速下降；肌糖原和有氧代谢也已经参与。", 50, INK)
    rule(draw, 560)
    text(draw, 84, 589, "PCr 完成本次下降幅度的比例", 47, INK, True)

    left, top, right, bottom = 220, 690, 1400, 1240
    for value in (0, 25, 50, 75, 100):
        y = bottom - int(value / 100 * (bottom - top))
        draw.line((left, y, right, y), fill=SOFT_RULE, width=2)
        text(draw, 181, y, f"{value}%", 30, GRAY, anchor="rm")
    draw.line((left, top, left, bottom), fill=INK, width=4)
    draw.line((left, bottom, right, bottom), fill=INK, width=4)

    def x_at(sec: float) -> int:
        return left + int(sec / 120 * (right - left))

    def y_at(sec: float) -> int:
        progress = 100 * (1 - math.exp(-sec / 33))
        return bottom - int(progress / 100 * (bottom - top))

    points = [(x_at(sec), y_at(sec)) for sec in range(0, 121, 2)]
    draw.polygon([(left, bottom), *points, (right, bottom)], fill=PALE_RED)
    draw.line(points, fill=RED, width=12, joint="curve")
    for sec in (0, 33, 66, 99, 120):
        x = x_at(sec)
        draw.line((x, bottom, x, bottom + 14), fill=INK, width=3)
        text(draw, x, bottom + 27, str(sec), 31, GRAY, anchor="mt")
    for sec, label in ((33, "63%"), (66, "86%"), (99, "95%")):
        x, y = x_at(sec), y_at(sec)
        dot(draw, x, y, 15, RED, WHITE)
        text(draw, x + 17, y - 62, label, 39, RED, True)
    text(draw, 900, 1315, "运动开始后时间 / 秒", 33, GRAY)

    rule(draw, 1391)
    text(draw, 82, 1430, "同时参与", 49, INK, True)
    text(draw, 84, 1520, "燃料", 34, GRAY)
    text(draw, 197, 1508, "肌糖原", 48, RED, True)
    arrow(draw, (410, 1538), (1360, 1538), RED, 14, 30)
    text(draw, 84, 1629, "途径", 34, GRAY)
    text(draw, 197, 1617, "有氧氧化", 48, GREEN, True)
    arrow(draw, (410, 1647), (1360, 1647), GREEN, 14, 30)
    text(draw, 84, 1738, "参考 Rossiter 2002 膝伸肌恒负荷实验：τ≈33 秒。", 35, INK)
    text(draw, 84, 1794, "这是归一化示意，并非跑步实测；纵轴不是 PCr 存量", 33, GRAY)
    text(draw, 84, 1850, "或 ATP 供能占比。箭头只表示同时参与。", 33, GRAY)
    return save(image, "03-onset.png")


def illustration_panel(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    note: str,
    color: str,
    asset: str,
) -> None:
    text(draw, x, y, title, 72, color, True)
    paste_asset(image, asset, (x + 8, y + 112, 632, 355))
    text(draw, x + 8, y + 495, note, 43, INK, True)


def routes() -> Path:
    image, draw = page(4)
    lines(draw, 80, 185, ["4 个角色，", "不是 4 个时段"], 116, 133, RED, True)
    text(draw, 83, 471, "四者会同时参与，但角色不同。", 50, INK)
    paste_asset(image, "rick-standing-cutout.png", (1217, 163, 225, 394))
    rule(draw, 585)
    draw.line((768, 615, 768, 1780), fill=RULE, width=3)
    draw.line((80, 1204, 1456, 1204), fill=RULE, width=3)

    illustration_panel(image, draw, 96, 638, "肌糖原", "工作肌自己用", RED, "muscle-glycogen.png")
    illustration_panel(image, draw, 802, 638, "肝糖原", "肝脏补血糖", BLUE, "liver-glycogen.png")
    illustration_panel(image, draw, 96, 1225, "脂肪", "脂肪酸进入肌肉氧化", GREEN, "fat-oxidation.png")
    illustration_panel(image, draw, 802, 1225, "糖异生", "乳酸、甘油等原料造血糖", GOLD, "gluconeogenesis.png")
    text(draw, 82, 1822, "记住：肌糖原主要本肌使用；肝糖原和糖异生帮助维持血糖。", 42, INK)
    return save(image, "04-routes.png")


def spark(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    note: str,
    color: str,
    rising: bool,
    number: str,
) -> None:
    text(draw, x, y, number, 49, color, True)
    text(draw, x + 90, y, title, 54, INK, True)
    x0, x1 = x + 82, x + 572
    top, bottom = y + 190, y + 373
    draw.line((x0, bottom + 22, x1, bottom + 22), fill=RULE, width=3)
    draw.line((x0, top - 20, x0, bottom + 22), fill=SOFT_RULE, width=2)
    for step in (1, 2):
        gy = top - 20 + step * (bottom - top + 42) / 3
        draw.line((x0, gy, x1, gy), fill=SOFT_RULE, width=2)
    if rising:
        pts = [(x0 + 8, bottom - 13), (x0 + 155, bottom - 36), (x0 + 330, top + 81), (x1 - 2, top + 12)]
    else:
        pts = [(x0 + 8, top + 11), (x0 + 155, top + 55), (x0 + 330, bottom - 75), (x1 - 2, bottom - 13)]
    draw.line(pts, fill=color, width=12, joint="curve")
    dot(draw, pts[0][0], pts[0][1], 11, color)
    arrow(draw, pts[-2], pts[-1], color, 10, 28)
    text(draw, x0, bottom + 47, "30 分钟", 31, GRAY)
    text(draw, x1, bottom + 47, "120 分钟", 31, GRAY, anchor="rt")
    text(draw, x + 82, y + 493, note, 42, color, True)


def duration() -> Path:
    image, draw = page(5)
    lines(draw, 80, 184, ["越跑越久，", "四项指标怎么变？"], 111, 137, RED, True)
    text(draw, 83, 471, "中等强度、持续运动的常见方向；无数值刻度。", 48, INK)
    rule(draw, 585)
    draw.line((768, 614, 768, 1802), fill=RULE, width=3)
    draw.line((80, 1208, 1456, 1208), fill=RULE, width=3)
    spark(draw, 96, 635, "肌糖原氧化", "利用速率通常下降", RED, False, "01")
    spark(draw, 802, 635, "血浆脂肪酸", "氧化量通常上升", GREEN, True, "02")
    spark(draw, 96, 1230, "肝糖原储量", "持续运动中逐渐下降", GOLD, False, "03")
    spark(draw, 802, 1230, "糖异生贡献", "占内源产糖的比例常上升", BLUE, True, "04")
    text(draw, 81, 1847, "不同指标不能相加成 100%；进食、强度和补糖会改变趋势。", 36, GRAY)
    return save(image, "05-duration.png")


def amount_bars() -> Path:
    image, draw = page(6)
    lines(draw, 80, 184, ["同样 600 kcal/h，", "糖脂能差多少？"], 106, 126, RED, True)
    text(draw, 83, 457, "70 kg 跑者、稳定运动、忽略蛋白质氧化的演算。", 47, INK)
    rule(draw, 555)

    dot(draw, 112, 615, 15, RED)
    text(draw, 139, 587, "总糖氧化", 45, INK, True)
    dot(draw, 470, 615, 15, GREEN)
    text(draw, 498, 587, "总脂肪氧化", 45, INK, True)
    text(draw, 1450, 600, "单位：g/h", 36, GRAY, anchor="rt")

    left, top, right, bottom = 205, 735, 1400, 1540
    for value in (0, 30, 60, 90, 120):
        y = bottom - int(value / 120 * (bottom - top))
        draw.line((left, y, right, y), fill=SOFT_RULE, width=2)
        text(draw, left - 32, y, str(value), 35, GRAY, anchor="rm")
    draw.line((left, top, left, bottom), fill=INK, width=4)
    draw.line((left, bottom, right, bottom), fill=INK, width=4)

    rows = CONTENT["slides"][5]["rows"]
    centers = (430, 800, 1170)
    bar_width = 120
    for center, row in zip(centers, rows):
        carb = row["carbohydrate_g_per_h"]
        fat = row["fat_g_per_h"]
        for x0, value, color in ((center - 133, carb, RED), (center + 13, fat, GREEN)):
            y0 = bottom - int(value / 120 * (bottom - top))
            draw.rectangle((x0, y0, x0 + bar_width, bottom), fill=color)
            text(draw, x0 + bar_width // 2, y0 - 66, str(value), 53, color, True, anchor="mt")
        text(draw, center, 1580, f"RER {row['rer']}", 44, INK, True, anchor="mt")

    rule(draw, 1691)
    lines(
        draw,
        83,
        1726,
        [
            "这是总糖与总脂肪氧化量，不能拆成肌糖原、肝糖原消耗量；",
            "脂肪氧化也不等于体脂减少量。RER 是呼吸交换率。",
        ],
        37,
        57,
        INK,
    )
    text(draw, 83, 1860, "演算依据：Weir 1949；Frayn 1983。", 30, GRAY)
    return save(image, "06-amounts.png")


def donut() -> Path:
    image, draw = page(7)
    lines(draw, 80, 184, ["饼图看一个例子：", "糖与脂肪同时供能"], 109, 130, RED, True)
    text(draw, 84, 464, "600 kcal/h、RER 0.85 的稳态演算，不是所有人的固定比例。", 45, INK)
    rule(draw, 562)

    box = (389, 650, 1147, 1408)
    draw.pieslice(box, 90, 90 + 360 * 0.51, fill=RED)
    draw.pieslice(box, 90 + 360 * 0.51, 450, fill=GREEN)
    draw.ellipse((582, 843, 954, 1215), fill=PAPER)
    text(draw, 768, 923, "≈1:1", 108, INK, True, anchor="mt")
    text(draw, 768, 1047, "能量占比", 49, GRAY, anchor="mt")
    text(draw, 184, 782, "糖", 72, RED, True)
    text(draw, 183, 876, "约 51%", 57, RED, True)
    draw.line((240, 974, 432, 974), fill=RED, width=5)
    text(draw, 1165, 782, "脂肪", 72, GREEN, True)
    text(draw, 1164, 876, "约 49%", 57, GREEN, True)
    draw.line((1109, 974, 1360, 974), fill=GREEN, width=5)

    rule(draw, 1515)
    text(draw, 82, 1566, "没有“30 分钟后才燃脂”的开关。", 71, RED, True)
    lines(
        draw,
        84,
        1676,
        [
            "3–30 分钟：糖和脂肪并行，有氧供能逐步稳定。",
            "30–120 分钟：肌糖原利用速率常降，血液脂肪酸氧化常升。",
            "2 小时后：肝糖原趋少，糖异生维持血糖更重要。",
        ],
        37,
        61,
        INK,
    )
    return save(image, "07-donut.png")


def make_contact_sheet(paths: list[Path]) -> Path:
    thumb_w, thumb_h, gap = 462, 616, 26
    sheet = Image.new("RGB", (1520, 2078), PAPER)
    draw = ImageDraw.Draw(sheet)
    text(draw, 49, 29, "有氧供能 · 瑞克插画版预览", 51, RED, True)
    for i, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        column = 1 if i == 6 else i % 3
        left = 42 + column * (thumb_w + gap)
        top = 150 + (i // 3) * (thumb_h + gap)
        sheet.paste(image, (left, top))
        draw.rectangle((left, top, left + thumb_w, top + thumb_h), outline=SOFT_RULE, width=2)
    path = OUT / "preview-contact-sheet.jpg"
    sheet.save(path, format="JPEG", quality=91, optimize=True)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [cover(), timeline(), pcr_curve(), routes(), duration(), amount_bars(), donut()]
    contact = make_contact_sheet(paths)
    manifest = {
        "status": "awaiting-user-review",
        "revision": 3,
        "style_reference": "xhs-knowledge/2026-09-28-warmup/images/warmup-preview-v2-rick.png",
        "render": "native text and charts with Pillow; Lingzhi RGBA illustrations; no SVG",
        "artwork_provider": "lingzhi-image / gpt-image-2.5-sunburst",
        "artwork_prompt_file": "generation/lingzhi-revision-03/prompts.json",
        "rick_source": "xhs-wrong-notebook/2026-09-22-joint-actions/00-rick-muscular-cartoon-model-v4.png",
        "dimensions": [W, H],
        "pillow": pillow_version,
        "content_sha256": hashlib.sha256((ROOT / "content.json").read_bytes()).hexdigest(),
        "images": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in paths
        ],
        "artwork": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in [
                ASSETS / "rick-standing-cutout.png",
                ASSETS / "muscle-glycogen.png",
                ASSETS / "liver-glycogen.png",
                ASSETS / "fat-oxidation.png",
                ASSETS / "gluconeogenesis.png",
            ]
        ],
        "preview": str(contact.relative_to(ROOT)),
    }
    (ROOT / "generation/render-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Rendered {len(paths)} chart cards to {OUT}")


if __name__ == "__main__":
    main()
