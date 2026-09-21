# 每日课程与小红书模板

当前状态：Day40 共用页面模板已验收。Day41 revision-02 已于2026-09-17发布；Day42 revision-05 已获用户验收并明确授权部署，于2026-09-18发布，短链 https://fitstudy.cn/go/42/ 已通过线上验证。11张小红书卡片、文案和ZIP保留本地交付，文案包含实际短链。当前记录以 `runs/daily-preview/review.json` 与 `runs/day42/release/status.json` 为准。

2026-09-18：用户要求 Day42 的 XHS 配图恢复 Day41 大小。共用知识页恢复固定 936×240 图区及 Day41 文字、间距，不再用透明边界裁切后放大到310–520px。透明图用原生 img 与正常 alpha 合成；知识图保存2800×900高分辨率母版，不放大源像素，卡片仍为1080×1440。总览沿用多主题分格；每格使用单独请求、单独构图的专用插图，不复用后续知识页图片。Day42 最终验收发布版为 revision-05，旧修订保留记录，Day40、Day41 交付不重写。

## 固定结构

- 首页课程卡片：无字封面只放在课程列表卡片的缩略图位置，不插入课程正文。
- 课程正文：标题与标签、总结、中文详情图、可折叠核心要点、常见误区、记忆口诀、翻转卡、实操关联、练习题、参考资料。保留大图查看与单选、多选、案例题交互。正文顶部不放单独品牌图标。
- 小红书：带标题的封面、可选总览图、每个知识点独立一页。应用案例也使用同一知识页组件。没有固定总页数，不把两个知识点合并成一页。
- 小红书沿用 Day29 的浅底、橙色顶条、黑色标题、对应配图和分块讲解；输出固定为 1080×1440 PNG。
- 品牌位置只用 `html/assets/fitness-study-logo-open-circle.svg`。不增加“健身学习”品牌文字，不使用 FitnessStudy。
- 网站课程页沿用原有绿色、蓝色、橙色分区与标签；翻转卡背面使用浅绿色，避免大面积深绿色压迫阅读。

## 内容与样式分离

唯一渲染入口是 `scripts/render-study-package.js`，内容参考 `runs/day40/lesson.json`。`cover` 是首页卡片缩略图，也可供小红书封面使用；`detailImage` 才是网站正文图。

日常只新增 JSON 内容和图片，不修改 `course.css`、`slides.css`、`tokens.css`、`course.js` 或渲染器。禁止新增 `buildDayXXSlides`，禁止按 Day 或题材写 CSS 条件分支。旧脚本 `scripts/generate-xhs-package.js` 仅供历史内容参考，不作为新自动任务的生成入口。

JSON 不允许 CSS、HTML、脚本或样式覆盖字段，正文以纯文本段落和固定组件组织。图片必须有实际本地文件，知识页不得用无关图片、占位图冒充。超限内容必须改写；浏览器检测到溢出会终止导出，不自动缩字号、不截断、不切换备用渲染器。

知识页可选 `emphases: [{ block, bullet, keyword }]`，每张卡可在不同步骤里标出 1–6 个现有短语；`keyword` 必须是其所指要点中的原文，且每条要点只对应一个短语。共用样式只突出这个词或短语，不整行着色、不另加重复文案。可选 `mistakeIndexes: [n]` 将课程 HTML 的第 n 条 `mistakes` 内容附在对应知识卡下方；不得复制第二份误区文案或传入单课样式。

候选版总览可提供 `xhs.overview.items`（2–6项，每项只有 `title`、`description`、`image`）与可选 `note`，由同一两列网格排版。标题和说明直接排字，不再把整个网站横版详情图缩进卡片；未提供 items 的既有内容仍使用详情图。网站详情图保持原文件与原版式。

知识页使用原生 `<img>` 在固定图区等比展示整幅规范画布，不自动裁透明边界、不拉伸。高分辨率知识图保存为2800×900（1400×450逻辑画布的2倍），原始响应始终保留；`scripts/prepare-study-images.py` 的 `allowUpscale: false` 可避免把低分辨率源图放大。最终卡片内的缩小显示仍有物理像素限制，应以最终1080×1440 PNG检查细节。XHS 总览使用共用两列网格，网站有字详情使用三列总览；两者使用同一组专用插图。专用总览图不与后续知识页共用源图。

首次 Day40 包含 6 个核心知识点、1 个应用页，加封面和总览共 9 张。这个数量来自本课内容，不是之后每天的固定数量。Day40 页面模板已验收；这不代表后续图片自动通过。

## 运行

先安装 `package.json` 中固定版本的依赖，或使用 Codex 自带 Node 依赖路径。Playwright 需要已安装 Chromium；macOS 自动使用系统 Chrome，也可通过 `CHROME_EXECUTABLE` 指定。

```bash
node --test tests/study-template.test.js tests/study-draft.test.js
node scripts/render-study-package.js --input runs/day41/lesson.json --out /tmp/fitstudy-day41-stage
node scripts/install-study-draft.js --input runs/day41/lesson.json --from /tmp/fitstudy-day41-stage
node scripts/verify-study-package.js --day 41
```

输出必须沿用原项目目录，不把交付文件集中在临时预览目录：

- `html/dayNN-主题.html`：课程正文，不含无字封面。
- `html/thumbs/dayNN-英文标识-thumbnail.png`：首页课程卡片的无字封面。
- `html/assets/阶段名/dayNN-主题.png`：正文中文详情图。
- `xhs/dayNN/`：`cover.png`、`slide-XX.png`、文案、`index.html`、`manifest.json`、`dayNN-xhs.zip`。
- `xhs/dayNN/ai-visuals/`：小红书配图及独立预览所需图片。
- `runs/dayNN/`：输入 JSON、生图提示词与验证记录，不是用户交付页面的目录。

渲染器先在临时目录校验完整包，通过后再写入这些固定位置。当前草稿阶段不修改 `app.js`、`library/index.html`、首页、`go/` 短链或两份进度文件。先用 `--out` 隔离渲染，再通过通用 `scripts/install-study-draft.js` 安装；它复用既有安装器，仅复制获准的课程与小红书文件，并从文案和 ZIP 中排除未发布公开链接。后续获得对应安装授权后，才同步 `publishedPages`、`generatedThumbs` 与脚本缓存版本，并验证课程卡片到详情的链接。

`--out` 只用于隔离测试，不能把它的临时包当作最终目录。`--html-only` 必须同时提供隔离的 `--out`，不落入站点目录。只有所有 PNG 成功渲染并打包后状态才变为 `ready`；仍须浏览器交互验证与人工看图。不得覆盖其他课程或未知的已有文件。

## 图片与审核

2026-09-17 角色方向：固定波吉＋德斯帕，统一二维动漫教学画法，透明背景融入卡片。最初两张样图保存在 `runs/day41/character-preview/`；后续整包的10次独立请求、处理及技术纠正保存在 `runs/day41/character-final/`，无失败重试。无字封面复用合格样图，中文详情与9张知识配图已完成；不包含历史全量替换或发布。

新图片准备前读取 [image-style.md](image-style.md) 与 [image-style.json](image-style.json)，分别固定封面、中文详情与知识页配图的画布、构图、文字和色彩。角色方向已用于 Day41 整包；格式可由 `scripts/prepare-study-images.py` 按 JSON 清单统一，人物与动作仍须逐张目检，不能只靠尺寸通过。

用户已明确授权 Day40 使用灵智生图。按已安装的 `lingzhi-image` 技能使用质量预设，凭据只由技能从环境或钥匙串读取，不写进任务、文件或日志。每张图独立请求，失败不自动重试，避免重复计费。

Day40 的完整生图提示词保存在 `runs/day40/image-prompts.json`。有效图片路径以 `runs/day40/lesson.json` 和 `xhs/day40/manifest.json` 为准。旧 `runs/daily-preview/day40/` 仅保留首轮试跑记录，不再作为交付入口。封面无文字，详情图有中文标注，知识页配图无文字。必须逐张检查主题对应关系、中文准确性、人体与器械合理性，以及最终海报中的实际显示效果。

## 定时任务边界

- 北京时间每日 06:00，附在当前 Codex 任务的 heartbeat 运行，不是服务器 crontab。
- 先读取 `runs/daily-preview/review.json`。`generating` 表示正在制作；`awaiting-review` 表示等待用户验收，不重复生成或覆盖。生成失败时保留结果并报告缺失项，不自动反复调用生图。
- 模板经用户确认后才允许开始后续每日草稿。确认版式不等于授权发布。
- 用户已要求把本地首页卡片封面、详情索引和课程短链接好；这不等于允许部署服务器、重做首页或推进进度。本阶段不部署、不改 `progress.json` 或 `.progress.json`。
- 后续正式生成前要核对两份进度与实际课程；Day40、Day41 已上线，两份正式进度仍未因发布更改。不能只读旧 `.progress.json` 后倒退、跳课或重生成已完成草稿。
- 未发布草稿不在小红书文案里伪造可访问的完整学习链接。发布获得授权且验证成功后，由生成脚本写入实际课程短链。
- 模板调整必须是用户批准的共用版本变更，重新回归测试，不按日期打补丁。

中文详情图采用 `scripts/compose-study-overview.py` 从审核JSON排字；模型只生成无字图。总览默认沿用 `panels` 分格，每格提供单独生成的专用插图与短说明。仅当用户选择单主图时使用 `scene` 模式。Day41修正版保留前一版成品备份，修正04连续前杠、05配重连接、07前肩推举及10图示标记，并重排全部总览文字。

2026-09-18 补充修订：Day42 知识／应用页按 Day41 的三块讲解结构，从已有课程正文补全设置、动作与检查／纠错信息；不得为放大配图删减文字卡片。第10页面向读者命名为“实操对照”，不把课纲中的“晚间”时间安排写成知识概念。
