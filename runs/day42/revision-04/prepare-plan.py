from pathlib import Path
import json
base=Path('runs/day42/revision-04');preset=json.loads(Path('templates/study/v1/image-style.json').read_text())
common=preset['commonPrompt']+'\n本次重点：人物结构清楚，德斯帕沿用Day41成年男性自然比例，头、胸廓、骨盆、上臂前臂和大腿小腿连接合理，不画扁长躯干、过小头部、异常短腿或拉长肢体。波吉保留约三头身的原作小男孩比例，绝不长腿成人化。线条清晰，不模糊不柔焦，身体内部平涂为完全不透明色块，只有轮廓抗锯齿含半透明像素。全身和器械必须完整，边缘8%安全留白。'
assets=[
 {'file':'cover.png','role':'cover','prompt':'横向16:9完整单一场景：波吉坐在卧推凳的脚端，双脚稳固落地，尚未开始动作；德斯帕站在侧方指向安全臂做训练前器械检查。杆已安全放回头端的J形钩，两位均不举杠。凳子纵轴从画面左后方头端指向右前方脚端。必须看清一根连续水平银色杠铃横跨两个黑色架柱前侧的突出J钩，杆在架柱之前，杆与J钩接触支撑但绝不穿入柱子！杠铃两端袖套与蓝色小杠片都在两架柱外侧，总杆长明显大于架子外宽。左右安全臂从柱子前方朝凳子脚端延伸，位于胸部可能下降路径的两侧和下方。架柱不要与人物手臂重叠。只画训练前坐姿检查，主题是上肢杠铃课安全准备。无箭头无文字。'},
 {'file':'visual-03-bench-path.png','role':'knowledge','prompt':'横向16:9高清单幅卧推顶端教学插画，非长扁画面。德斯帕一个人，完整侧方偏脚端30度三分之四视角，头在画面左侧脚在右侧，躺在足够长的平凳。躯干自然长度，完整臀部贴凳，髋膝弯曲自然，左右大腿和小腿长度正常，双脚完整落地，头枕凳，颈部自然。双手闭合握轻杆于肩上方，肘伸直而不反折，肩至肘与肘至腕长度接近，手腕堆叠，胸腹不拉长。两端小杠片连在连续杠的袖套上。只保留平凳和杠铃，不画架柱避免器械遮挡，训练姿势为示意。无标线、无箭头、无文字。要看到左右两条腿，脚不能在画面边缘。'},
 {'file':'overview-art.png','role':'detail','prompt':'为上肢杠铃技术课程独立设计一整张横向3:2教材总览的无字主插画，绝不是六张小图网格、现成知识页拼贴、漫画分镜或重复小人。一个整体三角构图，透明背景。画面左侧德斯帕以规范髋铰链俯身划船的拉起位置示范，红褐衣服白毛领，膝轻屈，臀后移，腰背自然，杠在腹部前方，肘向后，手在腿外。画面右侧矮小波吉站立观察，手指自己的上臂，表情认真。中央下方是单独一根轻训练杠和两只相同小杠片的清楚器械示意，用于解释左右等距握点，杠连续且片穿在袖套上，无架柱。三个主体组成一个有联系的原创教学场景。留出顶部四分之一与底部五分之一完全透明，供程序独立排中文标题和短说明；图像内部绝对无字母数字汉字。背景无图表框、无卡片、无圆形窗，不画小图缩略拼贴。'}
]
plan={'model':'gpt-image-2.5-sunburst','authorization':'用户2026-09-18要求修正Day42封面、独立总览、人体比例和卡片清晰度；本地草稿修订','commonPrompt':common,'assets':assets}
(base/'image-prompts.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
src=Path('runs/day41/revision-02/generate.py').read_text();(base/'generate.py').write_text(src)
print('Prepared 3 independent new artwork requests; existing revision-03 sources will be inspected for the other corrections.')
