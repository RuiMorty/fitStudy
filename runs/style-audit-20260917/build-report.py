"""Build the audit viewer from existing inventory and existing images; no API calls."""
from pathlib import Path
from datetime import datetime, timezone
import json
from PIL import Image, ImageOps, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
inventory = json.loads((HERE / 'inventory.json').read_text())
statistics = json.loads((HERE / 'statistics.json').read_text())
spec = json.loads((ROOT / 'templates/study/v1/image-style.json').read_text())
findings = {
    'completedAt': datetime.now(timezone.utc).isoformat(),
    'status': 'audit-complete-image-style-not-approved',
    'scope': 'all-existing-history-plus-day41-sources',
    'visuallyReviewedContactSheets': [x['file'] for x in inventory['contactSheets']],
    'counts': inventory['counts'],
    'conclusion': '存在风格漂移；历史格式本身也未完全统一。小红书最终像素尺寸一致，但源图比例、主体占比和画风不一致。',
    'findings': [
        {'category': 'html-cover', 'text': '40 张无字封面中，39 张为 1672×941，Day09 为 1448×1086。早期反复出现解剖、运动方向、受力和概念关系图；Day40–41 更偏人物与教练场景，Day41 的力量架、皮肤与金属质感更抢眼。'},
        {'category': 'html-detail', 'text': '40 个详情图文件共 11 种尺寸，包含横版、竖版和长图；Day11 文件未被当前正文引用。Day41 的大蓝标题、浓绿蓝标题带、六等分面板使其更像训练海报。历史也有色带与写实人体，差别是组合与视觉重心。'},
        {'category': 'xhs-export', 'text': '现有 Day01–32、Day40 的 310 张最终 PNG 全为 1080×1440（含 33 张封面）。外层尺寸统一，内部图片画风、比例与留白仍有变化。Day33–39 没有现存小红书包，不能列为已检查成品。'},
        {'category': 'xhs-source', 'text': '297 张原始配图含备选版本、拼图和总览，共 30 种尺寸；不能把全部原图都当作在用成品。Day30 混入扁平图标，Day31 更多临床人物场景，Day32 原图含蓝底方图，历史并非单一画风。'},
        {'category': 'day41-source', 'text': '11 张源图有 3 种尺寸，单人场景、多人场景、局部图和对照图的景别混用；人物与完整器械主导，解释关系偏弱。低杠杠位和前架手肩关系另有阻断问题。没有 Day41 最终 PNG 可供审核。'}
    ],
    'cause': '前序锁定了页面组件，但图片提示词只用白底、半写实3D等泛化描述，没有固定按用途的比例、主体占比、绘制语言与跨课比较标准。',
    'proposedStandard': spec['id'],
    'paidImageCallsDuringStyleAudit': 0,
    'historicalAssetsChanged': False,
    'nextGate': '用明确授权的代表样图验证三个用途及实际模板效果；当前不启动生图。'
}
(HERE / 'findings.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2) + '\n')
data = {'inventory': inventory, 'statistics': statistics, 'findings': findings, 'spec': spec}
(HERE / 'audit-data.js').write_text('window.AUDIT_DATA = ' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + ';\n')

# Nine unchanged originals, arranged for comparison. Contain only, never crop.
def asset(kind, day):
    return next(x['file'] for x in inventory['groups'][kind] if x['day'] == day)

rows = [
    ('无字封面｜知识关系 → 人物器械场景', [
        ('Day17 · 动作与解释图', asset('html-cover', 17)),
        ('Day21 · 动作与受力关系', asset('html-cover', 21)),
        ('Day41 · 新源图，未通过', 'runs/day41/source-assets/cover-source.png')]),
    ('中文详情｜同一用途，字色与排版密度变化', [
        ('Day05 · 平面与运动轴', asset('html-detail', 5)),
        ('Day32 · 心肺系统关系', asset('html-detail', 32)),
        ('Day41 · 蓝绿重色标题带', 'runs/day41/source-assets/detail.png')]),
    ('小红书无字配图｜解释方式与主体占比变化', [
        ('Day17 · 动作与关节示意', 'xhs/day17/ai-visuals/visual-07-lower-body-patterns.png'),
        ('Day29 · 横画布内留白较多', 'xhs/day29/ai-visuals/visual-02-specificity.png'),
        ('Day41 · 人物与完整力量架', 'runs/day41/source-assets/visual-02-high-bar.png')])
]
font_path = '/System/Library/Fonts/STHeiti Medium.ttc'
heading = ImageFont.truetype(font_path, 30)
label = ImageFont.truetype(font_path, 22)
small = ImageFont.truetype(font_path, 18)
width, cell_width, row_height = 1560, 500, 385
canvas = Image.new('RGB', (width, 100 + 3 * row_height + 55), '#edf1f5')
draw = ImageDraw.Draw(canvas)
draw.text((24, 20), '全历史图片风格审阅 · 代表对照', font=heading, fill='#142d42')
draw.text((24, 62), '选图用于说明差异；全部 33 张总览及原图见 HTML 报告。以下均为现有图片，未重新生图。', font=small, fill='#52687b')
for r, (title, items) in enumerate(rows):
    y = 100 + r * row_height
    draw.text((24, y), title, font=label, fill='#142d42')
    for c, (text, file) in enumerate(items):
        x = 20 + c * 510
        draw.rounded_rectangle((x, y + 38, x + cell_width, y + row_height - 12), radius=12, fill='white')
        draw.text((x + 14, y + 50), text, font=label, fill='#142d42')
        with Image.open(ROOT / file) as im:
            bg = Image.new('RGBA', im.size, 'white')
            bg.alpha_composite(im.convert('RGBA'))
            thumb = ImageOps.contain(bg.convert('RGB'), (470, 260))
            canvas.paste(thumb, (x + (cell_width - thumb.width) // 2, y + 83 + (260 - thumb.height) // 2))
            draw.text((x + 14, y + row_height - 36), f'{im.width} × {im.height}', font=small, fill='#718293')
draw.text((24, canvas.height - 38), '结论：统一画布还不够，需同时固定绘制语言、主体占比、留白与图中文字层级。', font=small, fill='#142d42')
canvas.save(HERE / 'comparison.jpg', quality=93)
print(json.dumps({'data': 'audit-data.js', 'findings': 'findings.json', 'comparison': 'comparison.jpg', 'contactSheets': len(inventory['contactSheets'])}, ensure_ascii=False))
