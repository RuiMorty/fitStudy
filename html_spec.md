# 健身学习推送 HTML 生成规范(明亮清爽风 · 核心要点可折叠版)

每次推送生成一个**独立完整**的 HTML 文件, 内联所有 CSS/JS, 无外部依赖, 双击即可浏览器打开。

## 推送节奏与文件命名
- 工作日 06:00 生成【早间新知识】, 推进 `.progress.json`。
- 工作日 12:00 生成【中午复习】, 复习当天早上新知识 + 艾宾浩斯间隔复习, **不推进** `.progress.json`。
- 早间新知识文件名: `html/dayNN-知识点名称.html`, 例如 `html/day05-动作平面与运动轴.html`。
- 中午复习文件名: `html/review-dayNN-知识点名称.html`, 其中 NN 是当天早上新知识 day。
- 不再使用日期命名, 不再使用 `morning_YYYY-MM-DD.html` 或 `evening_YYYY-MM-DD.html`。
- 正文学习图统一保存到 `html/assets/阶段名/`, 例如 `html/assets/阶段1基础科学/day05-动作平面与运动轴.png`。
- 课程卡片缩略图单独保存到 `html/thumbs/`, 文件名格式 `dayNN-short-english-slug-thumbnail.png`, 例如 `html/thumbs/day06-muscle-sliding-filament-thumbnail.png`。缩略图用于网站首页卡片和中午复习卡片, 不替代早间正文学习图。
- 小红书轮播辅助图统一保存到 `xhs/dayNN/ai-visuals/`, 文件名格式 `visual-00-cover.png`, `visual-01-short-english-slug-base.png`, `visual-02-short-english-slug.png` 递增到最后一张。该目录必须在运行小红书发布包脚本前生成。

## 输出要求
- **纯 HTML 代码**, 从 `<!DOCTYPE html>` 开始到 `</html>` 结束
- **第一行必须是 `<!DOCTYPE html>`**(不许多出一行解释/寒暄/思考文字, 否则会被脚本判废重试)
- 不输出任何解释文字、不包裹 markdown 代码块、不写"下面是完整的 HTML"之类前言
- 内联所有 CSS/JS, 无外部依赖
- 体量目标: **30-40KB**(早间理论版)

## 视觉风格(明亮清爽风)
- 背景 `#f6f8f7`, 卡片纯白 `#ffffff`, 边框 `#e2e8e4`, 卡片二级背景 `#f0f4f2`
- 强调色: 绿 `#0ea66b`(墨绿, 主色)/ 蓝 `#0ea5e9`/ 橙 `#ea7a17`/ 红 `#e23b3b`
- **颜色禁忌**: 按钮实色背景用 `#0ea66b`, **严禁用 `#0c4a35` 等近黑深绿**(对比太低像坏掉); 深色渐变背景(如 review/mnemonic 区)内的文字/strong 必须用浅色(`#fff`/`#fff7d6`)保证对比。
- 字体: `-apple-system,"PingFang SC",sans-serif`, 行高 1.7
- 圆角 14px 卡片, 柔和阴影
- 响应式

- ## 内容质量要求(关键! 避免空洞)
- **早间新知识必须包含 1 张 AI 生成的直观中文标注图**: 解剖课用医学插图, 生物力学课用动作/力线/关节示意, 生理课用机制流程图, 训练课用动作分析图。图片白底或浅色底、黑色中文标签、清晰可读, 保存到 `html/assets/阶段名/` 并用相对路径嵌入 HTML。
- **早间新知识还必须生成 1 张首页卡片缩略图**: 保存到 `html/thumbs/dayNN-short-english-slug-thumbnail.png`。缩略图为 16:9 横图, 无文字/无标签/无水印, 现代医学教育插画风格, 白底或浅色底, 使用少量绿色 `#4ade80`、蓝色 `#60a5fa` 点缀, 橙色 `#ff5a1f` 仅作极少强调。缩略图表达当天主题, 不能直接复用正文中文标注图。
- 每次生成新缩略图后, 必须更新 `app.js` 的 `generatedThumbs` 映射, 让首页 Day N 卡片优先使用该缩略图。
- **早间新知识必须先用 imagegen 生成小红书轮播辅助图 `ai-visuals`**: 在运行 `node scripts/generate-xhs-package.js --day=N` 前, 必须创建 `xhs/dayNN/ai-visuals/`。至少包含 `visual-00-cover.png` 和 `visual-01-主题-base.png`; 对每个核心要点轮播页再生成 1 张无文字视觉图, 文件名按 slide 眉标对齐, 例如 `visual-02-origin-anchor.png`, `visual-03-insertion-mobile-end.png`。若页面有 8 条核心要点, 通常应有 `visual-00` 到 `visual-10` 共 11 张。轮播辅助图必须无文字/无标签/无水印, 白底或浅色底, 现代医学教育插画风格, 少量使用绿色 `#4ade80` 和蓝色 `#60a5fa`, 橙色 `#ff5a1f` 只作极少强调。不得直接复用正文中文标注图作为核心要点视觉图; `visual-00-cover.png` 可复用首页缩略图, `visual-01-*-base.png` 可用主题无字概念图。
- 每次早间新知识生成成功后, 必须运行 `node scripts/generate-xhs-package.js --day=N` 生成小红书发布包到 `xhs/dayNN/`。发布包必须包含 `cover.png`, `slide-01.png` 至少 5 张轮播图, `title.txt`, `caption.txt`, `tags.txt`。图片规格为 1080x1440 PNG, 内容适合图文轮播, 最终仍由用户人工发布。脚本会读取已有 `xhs/dayNN/ai-visuals/visual-XX...` 并嵌入轮播, 但不会自动调用 imagegen; 因此 `ai-visuals` 缺失时必须先补图再运行脚本。
- **小红书发布包校验必须包含 `ai-visuals`**: 验证 `xhs/dayNN/ai-visuals/` 存在, `visual-00-cover.png` 存在, 每个核心要点 slide 对应的 `visual-XX-*.png` 存在, 且 `cover.png`, `slide-01.png` 至少 5 张轮播图、`title.txt`, `caption.txt`, `tags.txt` 都存在。若 `ai-visuals` 生成失败, 记录到 `logs/gen_err.log`, 不要删除已生成 HTML/正文图/缩略图; 但必须在最终说明里明确发布包缺少哪些辅助图, 并优先补齐后重跑发布包。
- **首次出现缩写/机制词必须讲透, 不能只丢名词**: 遇到 ATP-PCr、EPOC、GTO、SSC、RPE、神经输出、局部离子环境、长度-张力关系、力-速度曲线等术语时, 第一次出现必须按“字面意思 → 大白话类比 → 为什么影响训练/考试”的顺序解释。示例: `ATP-PCr = ATP(三磷酸腺苷, 直接供能物质) + PCr(磷酸肌酸, ATP 的备用仓库); 大白话是短时大重量的火箭点火燃料; 因为 PCr 储量少, 全力输出 6-8 秒后 ATP 再生速度下降, 所以力量掉速, 这和乳酸不是一回事。`
- **复杂原因链要拆开讲**: 如果写“短时大重量受 ATP-PCr、神经输出、局部离子环境等多因素限制”, 必须分别解释每一项: ① ATP-PCr 是什么、像什么、为什么耗尽后举不动; ② 神经输出/神经驱动是什么、像油门踏板、为什么中枢疲劳会让身体不听使唤; ③ 局部离子环境是什么(K⁺/Ca²⁺/H⁺ 等)、像电解质平衡、为什么会影响兴奋传导和横桥结合。禁止一句话带过。
- **长解释必须做视觉拆分, 禁止整屏大段文字**: 同一个知识点若超过 2 段解释, 必须改成小标题卡片、表格、步骤条、对比框或“先抓结论/训练判断”提示框。推荐结构: 先用 1 个 takeaway 框给结论, 再用 2-3 张卡片分别写“字面意思 / 大白话 / 卡在哪里”, 每段控制在 2-3 行内。不要把 5-6 个 `<p>` 连续堆在一起。
- **讲到具体肌肉时, 用文字详细讲透, 并配合 AI 生成医学图**。每块肌肉必讲:① 精确起止点(起点哪根骨头/骨性标志, 止点哪根骨头)② 主要功能(做什么关节运动)③ 训练中怎么体会到(摸哪、做什么动作能感受它收缩)④ 常见搭档/拮抗肌。用类比帮助定位(如"肱二头肌像上臂前侧的 sausage")。
- **不要手写粗糙 SVG 肌肉图/简笔人体**。允许表格, 允许复用已生成图片。需要视觉说明时优先使用 AI 生成图片, 不用手画 SVG 充数。
- **力矩/曲线类悬停图表防抖动**(若万不得已用了曲线): `.curve:hover` 只改 `filter`(drop-shadow)和 `opacity`, 不要改 `stroke-width` 或 `transform`(会触发重排导致鼠标抖动); 加 `will-change:opacity,filter`。

## 视觉风格补充
- 背景 `#f6f8f7`, 卡片纯白 `#ffffff`, 边框 `#e2e8e4`, 卡片二级背景 `#f0f4f2`
- 强调色: 绿 `#0ea66b`(墨绿, 主色)/ 蓝 `#0ea5e9`/ 橙 `#ea7a17`/ 红 `#e23b3b`
- 字体: `-apple-system,"PingFang SC",sans-serif`, 行高 1.7
- 标题渐变 绿→蓝
- 圆角 14px 卡片, 柔和阴影 `0 2px 12px rgba(20,40,30,.06)`
- 响应式, 手机可读

## 完整结构(早间理论版, 严格按此顺序)

### 1. 标题区
- h1: Day N · 主题名(渐变文字)
- meta: tag chips(阶段/学科/日期)+ 副标题(今日主题)

### 2. 一句话总结(panel green)
- 用类比把整个主题讲明白 + 关键推论加粗

### 3. 主题图片(figure)
- 放在标题区后或一句话总结后。
- `<img>` 使用相对路径, 例如 `assets/阶段1基础科学/day05-动作平面与运动轴.png`。
- 配一句短 caption, 说明图中看什么。
- 图片必须支持点击放大: `.figure img` 使用 `cursor:zoom-in`; 点击后打开全屏深色遮罩, 大图 `max-width:96vw; max-height:92vh`; 点击空白处或按 `Esc` 关闭。所有 CSS/JS 内联, 不依赖外部库。

### 4. 核心要点(panel, 每条**可点击折叠**) ⭐ 关键
用 `ul.kp > li` 结构, 每个 li 含:
- `.kp-head`(可见, 点击触发折叠): 一句话要点 + term 高亮术语
- `.kp-body`(默认隐藏, 点击展开): 深入补充, 按维度分块

**kp-head 写法**: 像列表项, 前面带 `▸` 符号(用 CSS `::before`, 点击时旋转 90°)。一句话讲核心(术语 + 定义 + 例子)。

**kp-body 深入维度**(用 `.dim` 小标签分块, 每块 1-2 段):
- 底层机制(为什么, 分子/细胞层面)
- 真实例子(具体肌肉/动作/人群)
- 训练含义(怎么用)
- 常见误解(❌以为 X, ✅其实 Y)
- 可选: 对比表/动画/图表(嵌在相关要点的 body 里)

核心要点 **6-8 条**, 覆盖当日主题的多个子知识点。

### 5. 常见误区(warn 框)
2-3 条 "❌很多人以为 X, ✅其实是 Y" 格式

### 6. 记忆口诀(mnemonic 渐变框)
朗朗上口, 把核心串起来

### 7. 翻转卡复习(card-grid)
6-10 张, onclick 翻面, 正面问题背面答案

### 8. 实操关联(panel orange, ▸ 列表)
4-6 条, 不同训练目标(增肌/减脂/爆发/耐力/康复)怎么用

### 9. 练习题(panel, **至少 4 道**) ⭐
题型混合:
- 单选题 ×2(可点击选项验证, 正确绿框错误红框)
- 多选题 ×1(逐项点击切换状态)
- 案例题 ×1(真实训练情境, 详细分析)
每题配"查看解析"按钮 + 详细解析(逐选项说为何错)

### 10. footer
`阶段X · Day N/112 · 今日早间新知识(工作日6:00) · 中午12:00复习巩固`

## 中午复习版结构
工作日 12:00 生成, 不推进 `.progress.json`。

复习集合:
- 今日新知识: `day0 = .progress.json day - 1`
- 艾宾浩斯间隔复习: `day0-1`, `day0-3`, `day0-7`, `day0-14`
- 只保留 `>=1` 且存在对应 `html/dayNN-*.html` 的页面。

结构:
1. 标题区: `Day N · 中午复习`
2. 今日新知识速复盘: 3-5 条要点 + 跳转到当天早间 HTML。必须使用与艾宾浩斯复习区一致的单张卡片结构: `section` 内放 `article.card`, 图片使用 `img.thumb` 置于卡片内部, 文字/口诀/按钮同卡上下排列。禁止把今日新知识区做成左右分栏, 禁止使用 `.lead` grid 让文字和图片左右并排。
3. 艾宾浩斯复习区: 按 1/3/7/14 天分卡片, 每卡含 day、主题、口诀/核心、旧页链接、可用图片缩略图
4. 主动回忆题: 至少 6 道, 答案默认隐藏, 点击显示
5. 错因辨析: 2-3 条今日最易混点
6. 今日复盘: 三句话收束
7. footer: `阶段X · Day N/112 · 中午复习(工作日12:00) · 明早6:00继续新知识`

复习 HTML 中所有课程图片必须使用 `thumbs/dayNN-...-thumbnail.png` 无字缩略图, 不使用 `assets/阶段.../dayNN-...png` 早间正文图。

中午复习 HTML 生成并校验通过后，同步生成小红书复习预览:
- 命令: `node scripts/generate-xhs-review-package.js --day=<day0>`
- 该命令会先自动运行 `scripts/sync-review-index.js --day=<day0>`, 同步 `reviews.json`, 更新 `index.html` 最新复习链接, 并把复习页里的正文详情图替换为 `thumbs/` 无字缩略图。
- 若只需同步/校验首页与复习索引, 可单独运行 `node scripts/sync-review-index.js --day=<day0>`；CI/自动化可用 `--check-only` 做硬校验。
- 输出目录: `xhs-review/dayNN/`
- 成功写入 `logs/push.log`: `xhs review package ready at xhs-review/dayNN/`
- 失败写入 `logs/gen_err.log`, 但不要修改 `.progress.json`

---

## 必备交互组件(复制此模式)

### 1. 核心要点可折叠(关键!)
```html
<ul class="kp">
  <li>
    <span class="kp-head"><span class="term">术语</span>: 一句话要点。</span>
    <div class="kp-body">
      <span class="dim">底层机制</span>
      <p>深入讲解...</p>
      <span class="dim">真实例子</span>
      <p>...</p>
      <span class="dim">常见误解</span>
      <p>❌以为 X。✅其实 Y。</p>
    </div>
  </li>
</ul>
```
CSS:
```css
ul.kp{padding-left:0;list-style:none}
ul.kp>li{border-bottom:1px dashed #e2e8e4}
ul.kp>li>.kp-head{padding:12px 8px 12px 32px;cursor:pointer;position:relative;display:block}
ul.kp>li>.kp-head::before{content:"▸";color:#0ea66b;position:absolute;left:8px;transition:transform .2s}
ul.kp>li.open>.kp-head::before{transform:rotate(90deg)}
ul.kp>li>.kp-head:hover{background:#f0f4f2}
.kp-body{display:none;padding:6px 16px 14px 32px}
ul.kp>li.open>.kp-body{display:block}
.dim{font-size:.75rem;font-weight:700;color:#0c6da3;text-transform:uppercase;letter-spacing:.5px;display:block;margin:12px 0 4px}
```
JS:
```javascript
document.querySelectorAll('ul.kp>li>.kp-head').forEach(function(h){
  h.addEventListener('click',function(){h.parentElement.classList.toggle('open')});
});
```

### 2. 悬停图表(关键! 支持 stroke 和 fill)
```html
<div class="panel">
  <div class="chart-tip" id="chartTipN">👆 悬停曲线查看说明</div>
  <div class="chart-wrap">
    <svg viewBox="0 0 400 220">
      <path class="curve" data-name="名称" data-info="说明"
            d="..." stroke="#色" stroke-width="3" fill="none"/>
      <!-- 或柱状: <rect class="curve" data-name=... data-info=... fill="#色" .../> -->
    </svg>
    <div class="legend"><span><i class="dot" style="background:#色"></i>说明</span></div>
  </div>
</div>
```
JS(每个 chart-wrap 内的曲线绑到同 panel 的 chart-tip):
```javascript
document.querySelectorAll('.chart-wrap').forEach(function(wrap){
  var tip=wrap.parentElement.querySelector('.chart-tip');if(!tip)return;
  var td=tip.textContent;
  wrap.querySelectorAll('.curve').forEach(function(c){
    c.addEventListener('mouseenter',function(){
      var col=c.getAttribute('stroke')||c.getAttribute('fill');
      tip.innerHTML='<b style="color:'+col+'">'+c.dataset.name+':</b> '+c.dataset.info;
      tip.style.borderLeftColor=col;
    });
    c.addEventListener('mouseleave',function(){tip.textContent=td;tip.style.borderLeftColor='#0ea66b'});
  });
});
```

### 3. CSS 动画(keyframes)
```css
.fiber{animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scaleY(.35);opacity:.5}50%{transform:scaleY(1);opacity:1}}
```

### 4. 翻转卡
```html
<div class="flip" onclick="this.classList.toggle('flipped')">
  <div class="flip-inner">
    <div class="face front">问题</div>
    <div class="face back">答案</div>
  </div>
</div>
```

### 5. 选择题
单选:
```html
<div class="opt" onclick="pick(this,'correct')"><span class="lbl">A.</span>正确项</div>
<div class="opt" onclick="pick(this,'wrong')"><span class="lbl">B.</span>错项</div>
<button onclick="document.getElementById('ansN').classList.add('show')">查看解析</button>
<div class="reveal" id="ansN">答案+逐选项解析</div>
```
多选(用 data-c):
```html
<div class="opt" data-c="1" onclick="pickMulti(this)"><span class="lbl">A.</span>正确项</div>
<div class="opt" onclick="pickMulti(this)"><span class="lbl">B.</span>错项</div>
```
JS:
```javascript
function pick(el,type){
  document.querySelectorAll('.quiz .opt').forEach(o=>o.classList.remove('correct','wrong-show'));
  el.classList.add(type==='correct'?'correct':'wrong-show');
}
function pickMulti(el){
  if(el.classList.contains('correct')||el.classList.contains('wrong-show')){
    el.classList.remove('correct');el.classList.remove('wrong-show');
  } else {
    el.classList.add(el.dataset.c==='1'?'correct':'wrong-show');
  }
}
```

## 写作风格(严格遵守 feedback_clarity.md)
1. 大白话+类比, 不堆术语
2. 新术语第一次出现配中文+一句话解释
3. 每个要点配真实训练场景例子
4. 主动指出误区("很多人以为 X, 其实是 Y")
5. 练习题解析详细, 解释每个错误选项为何错
6. 篇幅宁可长, 讲透胜过讲全
