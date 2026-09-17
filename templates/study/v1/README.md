# 每日课程与小红书模板

当前状态：Day40 首轮样稿待用户验收。旧版 `xhs/day29` 是视觉基准，网站沿用原有课程模块。本轮未发布，未推进正式进度。

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

首次 Day40 包含 6 个核心知识点、1 个应用页，加封面和总览共 9 张。这个数量来自本课内容，不是之后每天的固定数量。示例页面仅供样式和内容验收，不应宣称用户已批准。

## 运行

先安装 `package.json` 中固定版本的依赖，或使用 Codex 自带 Node 依赖路径。Playwright 需要已安装 Chromium；macOS 自动使用系统 Chrome，也可通过 `CHROME_EXECUTABLE` 指定。

```bash
npm test
node scripts/render-study-package.js --input runs/day40/lesson.json
node scripts/verify-study-package.js --day 40
```

输出必须沿用原项目目录，不把交付文件集中在临时预览目录：

- `html/dayNN-主题.html`：课程正文，不含无字封面。
- `html/thumbs/dayNN-英文标识-thumbnail.png`：首页课程卡片的无字封面。
- `html/assets/阶段名/dayNN-主题.png`：正文中文详情图。
- `xhs/dayNN/`：`cover.png`、`slide-XX.png`、文案、`index.html`、`manifest.json`、`dayNN-xhs.zip`。
- `xhs/dayNN/ai-visuals/`：小红书配图及独立预览所需图片。
- `runs/dayNN/`：输入 JSON、生图提示词与验证记录，不是用户交付页面的目录。

渲染器先在临时目录校验完整包，通过后再写入这些固定位置。生成后必须同步 `app.js` 的 `publishedPages` 和 `generatedThumbs` 两个索引，并按项目惯例更新 `library/index.html` 的脚本缓存版本。索引数据更新不属于按天定制样式。验证真实课程卡片显示封面，点击卡片各区域可到达对应详情。

`--out` 只用于隔离测试，不能把它的临时包当作最终目录。`--html-only` 必须同时提供隔离的 `--out`，不落入站点目录。只有所有 PNG 成功渲染并打包后状态才变为 `ready`；仍须浏览器交互验证与人工看图。不得覆盖其他课程或未知的已有文件。

## 图片与审核

用户已明确授权 Day40 使用灵智生图。按已安装的 `lingzhi-image` 技能使用质量预设，凭据只由技能从环境或钥匙串读取，不写进任务、文件或日志。每张图独立请求，失败不自动重试，避免重复计费。

Day40 的完整生图提示词保存在 `runs/day40/image-prompts.json`。有效图片路径以 `runs/day40/lesson.json` 和 `xhs/day40/manifest.json` 为准。旧 `runs/daily-preview/day40/` 仅保留首轮试跑记录，不再作为交付入口。封面无文字，详情图有中文标注，知识页配图无文字。必须逐张检查主题对应关系、中文准确性、人体与器械合理性，以及最终海报中的实际显示效果。

## 定时任务边界

- 北京时间每日 06:00，附在当前 Codex 任务的 heartbeat 运行，不是服务器 crontab。
- 先读取 `runs/daily-preview/review.json`。`generating` 表示正在制作；`awaiting-review` 表示等待用户验收，不重复生成或覆盖。生成失败时保留结果并报告缺失项，不自动反复调用生图。
- 模板经用户确认后才允许开始后续每日草稿。确认版式不等于授权发布。
- 用户已要求把本地首页卡片封面、详情索引和课程短链接好；这不等于允许部署服务器、重做首页或推进进度。本阶段不部署、不改 `progress.json` 或 `.progress.json`。
- 后续正式生成前要核对两份进度与实际课程；Day40 已生成到本地原目录但未上线，两份正式进度仍未更改。不能只读旧 `.progress.json` 后倒退、跳课或重生成 Day40。
- 未发布草稿不在小红书文案里伪造可访问的完整学习链接。发布获得授权且验证成功后，由生成脚本写入实际课程短链。
- 模板调整必须是用户批准的共用版本变更，重新回归测试，不按日期打补丁。
