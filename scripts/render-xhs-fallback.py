#!/usr/bin/env python3
import argparse
import base64
import html
import os
import re
from pathlib import Path
from urllib.parse import quote

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


def base_page():
    im = Image.new("RGB", (WIDTH, HEIGHT), "#f7f7f8")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, WIDTH, 12), fill="#ff5a1f")
    draw.text((72, 50), "健身学习", font=F_SMALL, fill="#111113")
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
    if args.day == 25:
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
