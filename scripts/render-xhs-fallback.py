#!/usr/bin/env python3
import argparse
import base64
import html
import os
import re
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1080, 1440


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                # Hiragino Sans GB W6/W3 keeps Chinese headings dense and legible in image posts.
                index = 2 if bold and "Hiragino" in path else 0
                return ImageFont.truetype(path, size=size, index=index)
            except Exception:
                continue
    return ImageFont.load_default()


F_TITLE = font(58, True)
F_H1 = font(48, True)
F_H2 = font(34, True)
F_BODY = font(27)
F_SMALL = font(23)
F_BRAND = font(28, True)
F_TAG = font(24, True)
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


def lesson_page_url(day):
    matches = sorted((ROOT / "html").glob(f"day{day:02d}-*.html"))
    if not matches:
        return ""
    rel = matches[0].relative_to(ROOT).as_posix()
    return "https://fitstudy.cn/" + "/".join(quote(part) for part in rel.split("/"))


def clean_title(title):
    return re.sub(r"[（(].*?[）)]", "", title).strip()


def title_text(day, title):
    aliases = {
        12: "核心肌群四抗",
        28: "能量系统与神经肌肉",
        30: "FITT-VP与ACSM指南",
    }
    base = f"Day{day}｜{aliases.get(day, clean_title(title))}"
    return base if len(base) <= 20 else base[:20]


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


def fit_image_tight(path, box):
    """Crop generated visual whitespace before fitting it into a social card."""
    img = Image.open(path).convert("RGB")
    difference = ImageChops.difference(img, Image.new("RGB", img.size, "white"))
    mask = difference.convert("L").point(lambda value: 255 if value > 22 else 0)
    bounds = mask.getbbox()
    if bounds:
        left, top, right, bottom = bounds
        padding = 38
        img = img.crop((max(0, left - padding), max(0, top - padding), min(img.width, right + padding), min(img.height, bottom + padding)))
    x, y, w, h = box
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), "white")
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def paste_day32_cutout(canvas, path, box, trim=0):
    """Place a Day32 illustration without its generated pale background."""
    x, y, width, height = box
    image = Image.open(path).convert("RGBA")
    if trim:
        image = image.crop((trim, trim, image.width - trim, image.height - trim))
    image.thumbnail((width, height), Image.LANCZOS)
    pixels = []
    for red, green, blue, alpha in image.getdata():
        minimum = min(red, green, blue)
        spread = max(red, green, blue) - minimum
        if minimum >= 194 and spread <= 78:
            pixels.append((red, green, blue, 0))
        elif minimum >= 170 and spread <= 78:
            fade = int((194 - minimum) / 24 * 255)
            pixels.append((red, green, blue, min(alpha, max(0, fade))))
        else:
            pixels.append((red, green, blue, alpha))
    image.putdata(pixels)
    canvas.paste(image, (x + (width - image.width) // 2, y + (height - image.height) // 2), image)


def paste_transparent(canvas, path, box):
    """Place an illustration that already has an alpha channel."""
    x, y, width, height = box
    image = Image.open(path).convert("RGBA")
    image.thumbnail((width, height), Image.LANCZOS)
    canvas.paste(image, (x + (width - image.width) // 2, y + (height - image.height) // 2), image)


def paste_rounded(canvas, image, xy, radius=22):
    x, y = xy
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
    canvas.paste(image, (x, y), mask)


def base_page():
    im = Image.new("RGB", (WIDTH, HEIGHT), "#f7f7f8")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, WIDTH, 12), fill="#ff5a1f")
    draw.text((72, 50), "健身", font=F_BRAND, fill="#111113")
    brand_width = draw.textlength("健身", font=F_BRAND)
    draw.text((72 + brand_width, 50), "学习", font=F_BRAND, fill="#ff5a1f")
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


def save_cards_slide(lesson, out_dir, index, title, lead, cards, visual_name=None):
    im, draw = base_page()
    draw.rectangle((72, 120, 192, 126), fill="#ff5a1f")
    draw.text((72, 160), f"{index:02d}", font=F_SMALL, fill="#ff5a1f")
    draw_wrapped(draw, (72, 205), title, F_H1, "#111113", 900, max_lines=2)
    y = draw_wrapped(draw, (72, 335), lead, F_BODY, "#52525b", 900, max_lines=3)
    if visual_name:
        visuals = sorted((out_dir / "ai-visuals").glob(f"{visual_name}*.png"))
        if visuals:
            visual = fit_image(visuals[0], (72, y + 20, 936, 280))
            im.paste(visual, (72, y + 20))
            y += 310
    card_w = 456
    card_h = 154
    gap_x = 24
    gap_y = 16
    positions = [
        (72, y + 10),
        (72 + card_w + gap_x, y + 10),
        (72, y + 10 + card_h + gap_y),
        (72 + card_w + gap_x, y + 10 + card_h + gap_y),
    ]
    for (card_title, card_body), pos in zip(cards, positions):
        draw_card(draw, pos, (card_w, card_h), card_title, card_body)
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / f"slide-{index:02d}.png")


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
    if lesson["day"] == 26:
        lead = "先定位神经末梢、ACh（acetylcholine，乙酰胆碱）、肌膜、T 管、肌浆网和钙离子，再看横桥为什么此时才抓得上肌动蛋白。"
    else:
        lead = "先看整张图，再把关键结构、机制顺序和训练判断串起来。"
    draw_wrapped(draw, (72, 275), lead, F_BODY, "#52525b", 900, max_lines=3)
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


def day32_page(index):
    return base_page()


def day32_card(draw, xy, size, title, body, accent):
    x, y = xy
    width, height = size
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill="white", outline="#e4e4e7", width=2)
    draw.rounded_rectangle((x + 16, y + 17, x + 24, y + height - 17), radius=4, fill=accent)
    draw.text((x + 44, y + 18), title, font=F_H2, fill="#111113")
    draw_wrapped(draw, (x + 44, y + 65), body, F_SMALL, "#52525b", width - 68, line_gap=6, max_lines=3)


def save_day32_cover(lesson, out_dir):
    im, draw = base_page()
    thumb = find_thumbnail(lesson["day"])
    if thumb:
        visual = fit_image(thumb, (72, 118, 936, 520))
        paste_rounded(im, visual, (72, 118), radius=26)
    draw.text((72, 710), f"Day {lesson['day']}", font=F_H2, fill="#ff5a1f")
    title_end = draw_wrapped(draw, (72, 760), lesson["title"], F_TITLE, "#111113", 900, max_lines=3)
    summary = "把心脏、血管、肺和呼吸肌看成一套氧气运输管线：空气进肺，血液带氧，心脏做泵，肌肉才有持续输出。"
    summary_end = draw_wrapped(draw, (72, title_end + 42), summary, F_BODY, "#71717a", 900, line_gap=8, max_lines=2)
    chips = [lesson["phase"].replace(" · ", "·"), "训练科学", "心肺解剖"]
    chip_top = summary_end + 24
    x = 72
    for chip, background, color in zip(chips, ["#dcfce7", "#dbeafe", "#ffede7"], ["#15803d", "#2563eb", "#ff5a1f"]):
        chip_width = int(draw.textlength(chip, font=F_TAG)) + 36
        draw.rounded_rectangle((x, chip_top, x + chip_width, chip_top + 56), radius=28, fill=background)
        draw.text((x + 18, chip_top + 12), chip, font=F_TAG, fill=color)
        x += chip_width + 16
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / "cover.png")


def save_day32_overview(lesson, out_dir):
    im, draw = base_page()
    draw.rectangle((72, 120, 192, 126), fill="#ff5a1f")
    draw.text((72, 160), "01", font=F_SMALL, fill="#ff5a1f")
    draw.text((72, 205), "先看图，再看概念", font=F_H1, fill="#111113")
    draw_wrapped(draw, (72, 275), "先把心脏、血管、肺和呼吸肌放进同一条氧运输链，再看每一环怎样影响训练表现。", F_BODY, "#52525b", 900, max_lines=3)
    visual = out_dir / "ai-visuals" / "visual-01-labelled-overview.png"
    if visual.exists():
        paste_day32_cutout(im, visual, (72, 400, 936, 680))
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / "slide-01.png")


def save_day32_cards_slide(lesson, out_dir, index, title, lead, cards, visual_name):
    im, draw = day32_page(index)
    draw.rectangle((72, 120, 192, 126), fill="#ff5a1f")
    draw.text((72, 160), f"{index:02d}", font=F_SMALL, fill="#ff5a1f")
    heading_end = draw_wrapped(draw, (72, 205), title, F_H1, "#111113", 900, line_gap=5, max_lines=2)
    lead_end = draw_wrapped(draw, (72, heading_end + 13), lead, F_BODY, "#52525b", 900, line_gap=7, max_lines=2)
    visual_top = max(350, lead_end + 16)
    visual_path = out_dir / "ai-visuals" / visual_name
    if visual_path.exists():
        paste_day32_cutout(im, visual_path, (360, visual_top, 360, 300), trim=70)
    cards_top = visual_top + 324
    for position, (card_title, card_body) in enumerate(cards):
        day32_card(draw, (72, cards_top + position * 164), (936, 150), card_title, card_body, "#ff5a1f")
    draw.text((72, 1345), f"Day {lesson['day']}/112", font=F_TINY, fill="#a1a1aa")
    im.save(out_dir / f"slide-{index:02d}.png")


def save_day32_slides(lesson, out_dir):
    save_day32_cover(lesson, out_dir)
    save_day32_overview(lesson, out_dir)
    save_day32_cards_slide(lesson, out_dir, 2, "心脏四腔：右去肺，左去身", "心脏不是一团混流，而是两台串联泵：右心负责去肺换气，左心负责向全身配送。", [
        ("右心：把血送去肺", "右心房接回全身静脉血，经三尖瓣进入右心室；右室再经肺动脉把血送往肺换气。"),
        ("左心：把氧送去全身", "肺静脉把含氧血送回左房，经二尖瓣进入左室；左室壁最厚，负责高压泵向全身。"),
        ("训练时：输出要提速", "配速上升时，心率和每搏输出量共同抬高心输出量，让工作肌肉更快拿到氧。"),
    ], "visual-02-four-chambers-v2.png")
    save_day32_cards_slide(lesson, out_dir, 3, "双循环：血流不走回头路", "瓣膜确保单向流，肺循环负责换气，体循环负责配送。把路径说顺，心肺题就不会乱。", [
        ("瓣膜：防止倒流", "房室瓣在心房和心室之间，阻止血回流心房；半月瓣在出口处，阻止血回流心室。"),
        ("肺循环：右室 → 肺 → 左房", "右室经肺动脉送出缺氧血；血在肺泡旁卸下二氧化碳、装上氧，再经肺静脉回到左房。"),
        ("体循环：左室 → 全身 → 右房", "左室把含氧血泵入主动脉；组织毛细血管完成交换后，静脉血再回到右心房。"),
    ], "visual-03-circulation-v2.png")
    save_day32_cards_slide(lesson, out_dir, 4, "血管三工种：推、回、换", "血管不只是管子。结构不同，决定它承担高压射血、低压回流，还是物质交换。", [
        ("动脉：厚壁承压", "管壁厚、弹性强，承受心室射血的高压力；运动时收缩压上升主要反映这段压力反应。"),
        ("静脉：低压回心", "管壁较薄、容量大，很多静脉有瓣膜；走路时小腿肌肉泵和呼吸泵都会帮它回流。"),
        ("毛细血管：交换主场", "管壁只有一层细胞厚；氧、二氧化碳、营养和代谢产物在这里跨壁进出组织。"),
    ], "visual-04-vessels-v2.png")
    save_day32_cards_slide(lesson, out_dir, 5, "气道到肺泡：氧在哪进血？", "吸进空气不等于氧已到肌肉。空气必须沿气道进入肺泡，才能和毛细血管完成交换。", [
        ("气道：层层送达", "鼻、咽、喉、气管、支气管到细支气管，像树枝不断分叉，把空气送到肺泡终点。"),
        ("肺泡：气体交换站", "肺泡壁和周围毛细血管壁都很薄；氧沿分压差进入血液，二氧化碳反向进入肺泡排出。"),
        ("为什么跑快会喘", "强度升高时，通气和清除二氧化碳的需求一起上升；喘不是单靠“肺活量”能解释。"),
    ], "visual-05-airway-alveoli-v2.png")
    save_day32_cards_slide(lesson, out_dir, 6, "呼吸肌：膈肌是主力", "吸气靠膈肌下沉扩大胸腔。力量动作里，呼吸还要配合腹压，帮助躯干稳定。", [
        ("膈肌：主要吸气肌", "收缩下沉时胸腔容积变大、胸内压下降，空气被吸入；放松上升后，安静呼气主要靠弹性回缩。"),
        ("肋间肌：帮胸廓扩张", "外肋间肌帮助肋骨上提，扩大胸廓；高通气时胸锁乳突肌、斜角肌等辅助肌参与更明显。"),
        ("腹压：训练里的稳定器", "深蹲和硬拉中，规范呼吸可建立腹内压、帮助躯干稳定；但高风险者不能用憋气硬顶。"),
    ], "visual-06-breathing-muscles-v2.png")
    save_day32_cards_slide(lesson, out_dir, 7, "跑步时的氧运输链", "有氧能力不是“肺活量”单项比赛，而是通气、交换、泵血、配送和肌肉利用共同决定。", [
        ("VO2max：整条链的结果", "空气进肺、氧进入血、心脏泵血、血管配送、肌肉摄氧，任一环受限都会限制有氧表现。"),
        ("同样配速更轻松", "训练后心输出、毛细血管和肌肉利用氧的效率更好；同样速度下，心率和主观喘感可能更低。"),
        ("如何用在编程", "Day33 用心率储备定强度；Day34 看急性反应和长期适应。先筛风险，再决定配速、间歇与进阶。"),
    ], "visual-07-oxygen-delivery-v2.png")


def save_day26_slides(lesson, out_dir):
    save_image_slide(lesson, out_dir)
    save_cards_slide(lesson, out_dir, 2, "神经肌肉接头：先把信号送到门口", "ACh 是 acetylcholine，中文叫乙酰胆碱；运动神经释放它，让肌膜先产生动作电位。", [
        ("ACh=乙酰胆碱", "全称 acetylcholine，是神经肌肉接头最关键的传话分子。"),
        ("肌膜去极化", "受体打开后膜电位改变，把神经信号变成肌纤维能传播的动作电位。"),
        ("训练判断", "起跳、起杠、冲刺前几步都需要神经快速叫醒肌肉。"),
        ("常见误区", "ACh 不是能量，也不是钙；它更像门铃，按响后才进入钙链条。"),
    ], "visual-02-")
    save_cards_slide(lesson, out_dir, 3, "T 管与 SR：把信号送进深处", "动作电位沿肌膜传播后，必须通过 T-tubule 深入肌纤维，才能触发肌浆网放钙。", [
        ("T 管隧道", "横管把肌膜表面电信号带进肌纤维内部，让深层也收到命令。"),
        ("SR 钙仓库", "肌浆网储存 Ca2+，收到 T 管信号后释放钙，把电信号变成化学开关。"),
        ("同步输出", "越多纤维同时接到信号，动作越干脆，峰值输出越容易上来。"),
        ("疲劳线索", "动作变慢、抖、发力断续，可能和兴奋传导及离子环境下降有关。"),
    ], "visual-03-")
    save_cards_slide(lesson, out_dir, 4, "钙开锁：横桥位点才暴露", "Ca2+ 结合肌钙蛋白后，原肌球蛋白移位，肌球蛋白横桥才有机会抓住肌动蛋白。", [
        ("钙不是燃料", "真正直接供能仍是 ATP；Ca2+ 负责打开横桥结合位点。"),
        ("肌钙蛋白", "钙结合后构象改变，原肌球蛋白从阻挡位置移开。"),
        ("回填 Day6", "肌丝滑行需要横桥循环；没有钙先开门，横桥第一抓都难发生。"),
        ("训练判断", "高强度后半段掉速，常和钙处理、H+、K+ 等局部环境一起相关。"),
    ], "visual-04-")
    save_cards_slide(lesson, out_dir, 5, "运动单位：按包叫醒肌纤维", "一个 α 运动神经元加上它支配的所有肌纤维，就是一个运动单位。", [
        ("不是单根调度", "一个运动单位被激活，它支配的肌纤维一起响应。"),
        ("小单位", "阈值低、控制细、耐疲劳，轻稳动作和姿势控制常先用它。"),
        ("大单位", "阈值高、力量大、易疲劳，重重量和爆发动作更需要它。"),
        ("训练判断", "新手早期力量增长常先来自神经募集效率，而不只是肌肉变大。"),
    ], "visual-05-")
    save_cards_slide(lesson, out_dir, 6, "大小原则：小先上，大后上", "低力任务先募集小运动单位；负荷或发力需求升高后，高阈值大单位才逐步加入。", [
        ("顺序固定", "身体优先用省电耐疲劳的小单位；任务够重够快时再叫大单位。"),
        ("轻重量也能到", "接近力竭时小单位疲劳，大单位会逐渐加入，但来得更晚。"),
        ("重重量更直接", "大重量、高速度意图更快要求大单位参与，也更需要长休息。"),
        ("考试判断", "看到 Size Principle、I 型、II 型、募集顺序，先记小先大后。"),
    ], "visual-05-")
    save_cards_slide(lesson, out_dir, 7, "去募集：力降时大单位先退", "当外部负荷变轻或输出需求下降时，高阈值大运动单位通常先退出。", [
        ("降档逻辑", "不需要大力时，身体先撤成本更高、易疲劳的大单位。"),
        ("动作例子", "深蹲最难点需要大单位；站稳后输出需求下降，大单位逐步退出。"),
        ("训练判断", "爆发训练别太早疲劳，否则高阈值单位上场时间短。"),
        ("常见误区", "募集不是只会增加；去募集也影响落杠、减速和动作结束控制。"),
    ], "visual-06-")
    save_cards_slide(lesson, out_dir, 8, "一条链串起来", "从神经信号到横桥结合，再到运动单位募集，这些不是碎知识，而是一套输出系统。", [
        ("接头点火", "神经末梢释放 ACh（乙酰胆碱），肌膜去极化，信号先传到肌肉门口。"),
        ("钙链开门", "T 管传深、SR 放钙，钙让原肌球蛋白移开，横桥位点开放。"),
        ("募集派人", "小单位先上，大单位后上；力下降时大单位先退。"),
        ("训练收束", "动作慢、抖、掉速快，要同时看神经驱动、钙处理、疲劳和技术。"),
    ], "visual-07-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, required=True)
    args = ap.parse_args()
    lesson = parse_syllabus(args.day)
    out_dir = ROOT / "xhs" / f"day{args.day:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "title.txt").write_text(title_text(args.day, lesson["title"]), encoding="utf-8")
    page_url = lesson_page_url(args.day)
    caption = "今天学：" + lesson["title"] + "\n\n核心线索：\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(lesson["points"]))
    if page_url:
        caption += "\n\n完整学习页：" + page_url
    (out_dir / "caption.txt").write_text(caption, encoding="utf-8")
    (out_dir / "tags.txt").write_text("#健身教练 #NSCA #NASM #运动科学 #健身知识 #训练科学 #力量训练", encoding="utf-8")
    save_cover(lesson, out_dir)
    if args.day == 32:
        (out_dir / "title.txt").write_text("Day32｜跑步时氧怎么送到肌肉", encoding="utf-8")
        (out_dir / "caption.txt").write_text(
            "跑步越快，身体不是只把呼吸变急，而是把整条氧运输链提速。\n\n"
            "这 7 张图带你顺一遍：\n"
            "1. 右心把血送去肺，左心把含氧血送去全身。\n"
            "2. 肺循环负责换气，体循环负责配送；瓣膜保证血流不倒退。\n"
            "3. 动脉承压、静脉回流、毛细血管交换，角色不能混。\n"
            "4. 空气需经过气道抵达肺泡，氧才进入血液。\n"
            "5. 膈肌负责主要吸气；力量动作里，呼吸还参与腹压和躯干稳定。\n"
            "6. 有氧能力是通气、交换、泵血、配送和肌肉利用共同结果，不只是肺活量。\n\n"
            "记忆口诀：右心去肺，左心去身；动脉承压，静脉回心；气道分树，肺泡换气。\n\n"
            f"完整学习页：{page_url}",
            encoding="utf-8",
        )
        (out_dir / "tags.txt").write_text("#健身教练 #NSCA #NASM #运动科学 #心肺训练 #解剖学 #健身学习", encoding="utf-8")
        save_day32_slides(lesson, out_dir)
    elif args.day == 25:
        save_image_slide(lesson, out_dir)
        save_cards_slide(lesson, out_dir, 2, "三大系统同时供能", "先分清时间、强度和恢复，再看哪套系统主导。", [
            ("看结论", "三大系统一直同时供能，只是比例随强度和时长变化。"),
            ("看强度", "越爆发，ATP-PCr 和糖酵解越靠前；1RM、起跑、跳起先想快系统。"),
            ("看时长", "时间越长，氧化系统越像主角；2 分钟以上的持续输出更依赖它。"),
            ("看目标", "爆发保峰值，增肌容忍部分疲劳，耐力保持续性和恢复底盘。"),
        ], "visual-02-")
        save_cards_slide(lesson, out_dir, 3, "强度越高，快系统越大", "高强度不是关掉氧化系统，而是把快系统推到前台。", [
            ("0-10 秒", "最典型是 ATP-PCr。单次 1RM、短冲刺、起跳、举重爆发阶段都在这里。"),
            ("30 秒-2 分钟", "糖酵解明显加入。400 米、HIIT 冲刺段、多次中等重量都很典型。"),
            ("越爆发", "动作时间越短、功率越高，PCr 和糖比例越大。"),
            ("训练判断", "想练峰值，就别把每组拖成喘爆；想练密度，才去接受更多代谢压力。"),
        ], "visual-03-")
        save_cards_slide(lesson, out_dir, 4, "时间越长，氧化越接棒", "时间拉长后，身体会把更多 ATP 生产任务交给氧化系统。", [
            ("2 分钟以上", "氧化系统占比持续上升。长跑、长骑、稳态有氧、长时恢复都靠它托底。"),
            ("底物切换", "低强度更偏脂肪，高强度更偏糖，但不是二选一；身体一直混合用燃料。"),
            ("恢复意义", "氧化能力强，组间回落更快、第二组更稳，训练容量更容易保住。"),
            ("误区", "低强度不是没用；它是在练耐久和恢复，不是只在烧热量。"),
        ], "visual-04-")
        save_cards_slide(lesson, out_dir, 5, "HIIT 让三系统一起上场", "冲刺段、恢复段、再冲刺，三个系统都被叫去干活。", [
            ("冲刺段", "ATP-PCr 和糖酵解猛拉起来，功率高、代谢压力大。"),
            ("恢复段", "氧化系统开始接管回补，帮忙恢复 PCr、搬运代谢产物。"),
            ("重复段", "反复切换，让爆发、恢复和再爆发都变成训练刺激。"),
            ("训练判断", "HIIT 不是只练无氧。它是冲、歇、再冲都算进来的多系统训练。"),
        ], "visual-05-")
        save_cards_slide(lesson, out_dir, 6, "EPOC 与氧债", "运动后还在喘，不是白喘；是在补运动中欠下的氧需求。", [
            ("EPOC", "运动后过量耗氧。恢复时呼吸、心率、体温和代谢都还没回到静息。"),
            ("氧债", "运动中欠下的氧，需要在结束后慢慢偿还；是恢复需求的形象说法。"),
            ("别误会", "EPOC 不是减脂捷径。减脂还要看总消耗、训练量和饮食。"),
            ("训练感受", "高强度后还喘一会儿很正常，说明身体还在修复和回补。"),
        ], "visual-06-")
        save_cards_slide(lesson, out_dir, 7, "训练里怎么排", "先定目标，再定强度、间歇和主供能系统。", [
            ("爆发", "高强度、极短时、长休息。目标是保速度、保质量，而不是练到喘爆。"),
            ("增肌", "中等强度、多组，允许部分糖酵解压力，但机械张力仍是底盘。"),
            ("耐力", "低到中等强度、较长时间，持续累积氧化系统和恢复能力。"),
            ("减脂", "优先可坚持的总量。别只盯“燃脂区”，长期能量缺口更关键。"),
        ], "visual-07-")
    elif args.day == 26:
        save_day26_slides(lesson, out_dir)
    elif args.day == 27:
        save_image_slide(lesson, out_dir)
        save_cards_slide(lesson, out_dir, 2, "三类运动单位：耐久到爆发", "运动单位类型决定速度、力量、疲劳和适用任务。", [
            ("S 单位", "慢收缩、抗疲劳、力量小，像省电小灯；适合站姿控制、轻松有氧、技术练习。"),
            ("FR 单位", "快收缩、较抗疲劳、力量中等；适合中等强度反复输出和间歇训练。"),
            ("FF 单位", "快收缩、易疲劳、力量最大；适合冲刺、跳跃、重重量关键发力。"),
            ("判断开关", "先看任务要稳多久还是爆多强；FR 偏平衡，FF 偏峰值。"),
        ], "visual-02-")
        save_cards_slide(lesson, out_dir, 3, "募集：低力先叫小单位", "大小原则：低阈值小单位先上，高阈值大单位后上。", [
            ("低力任务", "站立、慢走、空杆热身先靠小单位，输出稳定且省能。"),
            ("力量升高", "重量变大、速度意图更强、接近力竭时，FR 和 FF 逐步加入。"),
            ("轻重量问题", "轻重量也可能招到大单位，但通常要足够接近力竭。"),
            ("训练判断", "练力量爆发用重负荷或高速意图；练技术康复先练低负荷控制。"),
        ], "visual-03-")
        save_cards_slide(lesson, out_dir, 4, "频率编码：同一单位发得更密", "身体不只招更多单位，还会让已募集单位用更高频率放电。", [
            ("字面意思", "rate coding：同一运动神经元每秒发放动作电位次数增加。"),
            ("大白话", "像口令从慢拍变成密集鼓点；没换人，但命令更密，张力更强。"),
            ("训练例子", "1RM 起杠、冲刺第一步、纵跳起跳、重重量粘滞点都需要高频输出。"),
            ("常见误区", "力量提升不只靠招更多单位；同一单位发得更密也能推高输出。"),
        ], "visual-04-")
        save_cards_slide(lesson, out_dir, 5, "同步化：一起放电，峰值更高", "多个运动单位在同一时间窗口更整齐地放电。", [
            ("字面意思", "不是永久一起开火，而是关键瞬间更协调、更集中。"),
            ("大白话", "像划船一起下桨；每个人都用力，还要同一拍子用力。"),
            ("训练例子", "纵跳、抓举、冲刺蹬地、1RM 突破粘滞点都吃同步能力。"),
            ("训练判断", "重负荷、爆发意图、充分休息、低疲劳高质量重复最匹配。"),
        ], "visual-05-")
        save_cards_slide(lesson, out_dir, 6, "神经肌肉效率：少浪费，多集中", "主动肌更集中出力，协同肌帮得更准，无关肌肉少抢戏。", [
            ("字面意思", "同样任务下，用更少多余激活完成更有效输出。"),
            ("大白话", "像团队分工清楚：主力推进，辅助稳定，反方向拉扯减少。"),
            ("动作例子", "新手弯举耸肩、前臂乱紧；熟练者更能把张力集中到肱二头肌。"),
            ("训练判断", "技术练习、节奏控制、合适 cue 和渐进负荷，会让力量更干净。"),
        ], "visual-06-")
        save_cards_slide(lesson, out_dir, 7, "训练应用：重、快、稳", "神经控制决定你该用大重量、爆发速度、接近力竭，还是技术练习。", [
            ("最大力量", "高负荷、低到中等次数、长休息，目标是高募集和高频率编码。"),
            ("爆发训练", "必须有速度意图和充分休息，目标是快速募集和同步化。"),
            ("肌肥大", "中等负荷也能招到大单位，但常要接近力竭。"),
            ("康复技术", "低负荷先练效率和控制，减少协同代偿，稳定动作路径。"),
        ], "visual-07-")
        save_cards_slide(lesson, out_dir, 8, "和后续课程怎么接", "Day27 是神经适应、爆发训练和抗阻编程的神经基础。", [
            ("接 Day34", "新手早期力量涨，常来自募集、频率编码、同步化和效率提高。"),
            ("接 Day46", "爆发力需要高阈值单位快速参与、放电更密、关键时刻更同步。"),
            ("接编程", "重量、速度意图、次数和休息，会改变主要神经刺激。"),
            ("一句话", "肌肉是发动机，神经控制是油门、换挡和车队调度。"),
        ], "visual-08-")
    else:
        save_image_slide(lesson, out_dir)
        for idx, (title, lead) in enumerate(extract_items(args.day, lesson["points"]), start=2):
            save_dense_slide(lesson, out_dir, idx, title, lead)


if __name__ == "__main__":
    main()
