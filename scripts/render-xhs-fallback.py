#!/usr/bin/env python3
import argparse
import base64
import html
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1080, 1440


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size, index=1 if bold else 0)
            except Exception:
                continue
    return ImageFont.load_default()


F_TITLE = font(58, True)
F_H1 = font(48, True)
F_H2 = font(34, True)
F_BODY = font(27)
F_SMALL = font(23)
F_TINY = font(20)


def wrap(draw, text, ft, max_width):
    lines, line = [], ""
    for ch in text:
        test = line + ch
        if draw.textlength(test, font=ft) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


def strip_tags(value):
    value = re.sub(r"<script[\s\S]*?</script>", "", value)
    value = re.sub(r"<style[\s\S]*?</style>", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def parse_syllabus(day):
    text = (ROOT / "fitness_syllabus.md").read_text(encoding="utf-8")
    m = re.search(rf"### Day\s+{day}\s*·\s*(.+?)\s*【(.+?)】([\s\S]*?)(?=\n### Day|\n---|\Z)", text)
    if not m:
        raise SystemExit(f"Day {day} not found")
    title, cert, block = m.group(1), m.group(2), m.group(3)
    points = [line[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]
    phase_match = list(re.finditer(r"## 第\s*(\d+)\s*周\s*·\s*(.+)", text[: m.start()]))[-1]
    phase = f"第{phase_match.group(1)}周 · {phase_match.group(2).strip()}"
    return {"day": day, "title": title, "cert": cert, "phase": phase, "points": points}


def find_lesson_html(day):
    prefix = f"day{day:02d}-"
    matches = sorted((ROOT / "html").glob(prefix + "*.html"))
    return matches[0] if matches else None


def find_first_img(day):
    file = find_lesson_html(day)
    if not file:
        return None
    text = file.read_text(encoding="utf-8")
    m = re.search(r'<img[^>]+src="([^"]+)"', text)
    return ROOT / "html" / m.group(1) if m else None


def find_thumbnail(day):
    matches = sorted((ROOT / "html" / "thumbs").glob(f"day{day:02d}-*-thumbnail.png"))
    return matches[0] if matches else None


def extract_items(day, fallback_points):
    file = find_lesson_html(day)
    items = []
    if file:
        text = file.read_text(encoding="utf-8")
        heads = re.findall(r'<span class="kp-head">([\s\S]*?)</span>', text)
        for head in heads:
            clean = strip_tags(head)
            if "：" in clean:
                title, lead = clean.split("：", 1)
            elif ":" in clean:
                title, lead = clean.split(":", 1)
            else:
                title, lead = clean, ""
            items.append((title[:18], lead[:90]))
    if not items:
        for point in fallback_points:
            title, _, lead = point.partition("：")
            items.append((title[:18], lead[:90] or point[:90]))
    return items[:6]


def fit_image(path, box):
    img = Image.open(path).convert("RGB")
    x, y, w, h = box
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), "white")
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def base_page():
    im = Image.new("RGB", (WIDTH, HEIGHT), "#f7f7f8")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, WIDTH, 12), fill="#ff5a1f")
    draw.text((72, 50), "FitnessStudy", font=F_SMALL, fill="#111113")
    return im, draw


def draw_wrapped(draw, xy, text, ft, fill, max_width, line_gap=8, max_lines=None):
    x, y = xy
    lines = wrap(draw, text, ft, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=ft, fill=fill)
        y += ft.size + line_gap
    return y


def draw_card(draw, xy, size, title, body):
    x, y = xy
    w, h = size
    draw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill="white", outline="#e4e4e7", width=2)
    draw.text((x + 24, y + 18), title, font=F_H2, fill="#111113")
    draw_wrapped(draw, (x + 24, y + 64), body, F_SMALL, "#52525b", w - 48, max_lines=4)


def save_cover(lesson, out_dir):
    im, draw = base_page()
    thumb = find_thumbnail(lesson["day"])
    if thumb:
        visual = fit_image(thumb, (72, 118, 936, 520))
        im.paste(visual, (72, 118))
    draw.text((72, 710), f"Day {lesson['day']}", font=F_H2, fill="#ff5a1f")
    draw_wrapped(draw, (72, 760), lesson["title"], F_TITLE, "#111113", 900, max_lines=3)
    draw.text((72, 980), "NSCA / NASM 双证健身知识", font=F_BODY, fill="#71717a")
    chips = [lesson["phase"], "运动科学", lesson["cert"]]
    x = 72
    for chip, color in zip(chips, ["#dcfce7", "#dbeafe", "#ffedd5"]):
        tw = int(draw.textlength(chip, font=F_SMALL)) + 34
        draw.rounded_rectangle((x, 1040, x + tw, 1084), radius=22, fill=color)
        draw.text((x + 17, 1048), chip, font=F_SMALL, fill="#111113")
        x += tw + 16
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / "cover.png")


def save_image_slide(lesson, out_dir):
    im, draw = base_page()
    draw.rectangle((72, 120, 192, 126), fill="#ff5a1f")
    draw.text((72, 160), "01", font=F_SMALL, fill="#ff5a1f")
    draw.text((72, 205), "先看图，再看概念", font=F_H1, fill="#111113")
    draw_wrapped(draw, (72, 275), "先定位 ATP、PCr、ADP 与恢复时间，再理解为什么力量训练需要足够休息。", F_BODY, "#52525b", 900, max_lines=3)
    img = find_first_img(lesson["day"]) or find_thumbnail(lesson["day"])
    if img:
        visual = fit_image(img, (72, 380, 936, 880))
        im.paste(visual, (72, 380))
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / "slide-01.png")


def save_dense_slide(lesson, out_dir, index, title, lead):
    im, draw = base_page()
    draw.rectangle((72, 120, 192, 126), fill="#ff5a1f")
    draw.text((72, 160), f"{index:02d}", font=F_SMALL, fill="#ff5a1f")
    draw_wrapped(draw, (72, 205), title, F_H1, "#111113", 900, max_lines=2)
    y = draw_wrapped(draw, (72, 335), lead, F_BODY, "#52525b", 900, max_lines=3)
    visuals = sorted((out_dir / "ai-visuals").glob(f"visual-{index:02d}-*.png"))
    if visuals:
        visual = fit_image(visuals[0], (72, y + 20, 936, 310))
        im.paste(visual, (72, y + 20))
        y += 350
    bullets = [
        "看时间：越短、越爆发，ATP-PCr 占比越高。",
        "看休息：PCr 未恢复时，下一组峰值输出下降。",
        "看目标：力量爆发要保质量，体能密度可接受疲劳。",
    ]
    if "恢复" in title or "休息" in title:
        bullets = ["30 秒约恢复一半，不等于满格。", "3-5 分钟接近恢复，适合高质量大重量。", "短休会提高疲劳和密度，但会降低峰值输出。"]
    elif "反应" in title or "PCr" in title:
        bullets = ["PCr 把磷酸基团转给 ADP。", "ADP 重新变成 ATP，肌肉继续有直接燃料。", "反应快，但储量少，不能长时间全力输出。"]
    for b in bullets:
        draw_card(draw, (72, y + 10), (936, 135), title[:10], b)
        y += 155
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / f"slide-{index:02d}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, required=True)
    args = ap.parse_args()
    lesson = parse_syllabus(args.day)
    out_dir = ROOT / "xhs" / f"day{args.day:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "title.txt").write_text(f"Day{args.day}｜{lesson['title']}"[:20], encoding="utf-8")
    (out_dir / "caption.txt").write_text("今天学：" + lesson["title"] + "\n\n核心线索：\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(lesson["points"])), encoding="utf-8")
    (out_dir / "tags.txt").write_text("#健身教练 #NSCA #NASM #运动科学 #健身知识 #能量系统 #力量训练", encoding="utf-8")
    save_cover(lesson, out_dir)
    save_image_slide(lesson, out_dir)
    for idx, (title, lead) in enumerate(extract_items(args.day, lesson["points"]), start=2):
        save_dense_slide(lesson, out_dir, idx, title, lead)


if __name__ == "__main__":
    main()
