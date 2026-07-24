const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const SITE_URL = "https://fitstudy.cn";
const WIDTH = 1080;
const HEIGHT = 1440;

function parseArgs() {
  const dayArg = process.argv.find((arg) => arg.startsWith("--day="));
  const day = Number(dayArg?.split("=")[1] || process.argv[2]);
  if (!Number.isInteger(day) || day < 1) {
    throw new Error("Usage: node scripts/generate-xhs-package.js --day=6");
  }
  return { day };
}

function parseSyllabus() {
  const markdown = fs.readFileSync(path.join(ROOT, "fitness_syllabus.md"), "utf8");
  const lines = markdown.split(/\r?\n/);
  const lessons = [];
  let phase = "";
  let goal = "";
  let lesson = null;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const phaseMatch = line.match(/^## 第\s*(\d+)\s*周\s*·\s*(.+)$/);
    if (phaseMatch) {
      phase = `第${phaseMatch[1]}周 · ${phaseMatch[2]}`;
      goal = "";
      continue;
    }
    const goalMatch = line.match(/^\*目标:\s*(.+)\*$/);
    if (goalMatch) {
      goal = goalMatch[1];
      continue;
    }
    const lessonMatch = line.match(/^### Day\s+(\d+)\s*·\s*(.+?)\s*【(.+?)】$/);
    if (lessonMatch) {
      lesson = {
        day: Number(lessonMatch[1]),
        title: lessonMatch[2],
        cert: lessonMatch[3],
        phase,
        goal,
        points: [],
        practice: "",
      };
      lessons.push(lesson);
      continue;
    }
    if (!lesson) continue;
    if (line.startsWith("- ")) lesson.points.push(line.slice(2));
    if (line.startsWith(">")) lesson.practice = line.replace(/^>\s*/, "").replace(/^🌙\s*/, "");
  }
  return lessons;
}

function assetDataUrl(relativePath) {
  if (!relativePath) return "";
  const absolute = path.join(ROOT, relativePath);
  if (!fs.existsSync(absolute)) return "";
  const ext = path.extname(absolute).toLowerCase();
  const mime = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
  return `data:${mime};base64,${fs.readFileSync(absolute).toString("base64")}`;
}

function findThumbnail(day) {
  const prefix = `day${String(day).padStart(2, "0")}`;
  const thumbsDir = path.join(ROOT, "html", "thumbs");
  if (!fs.existsSync(thumbsDir)) return "";
  const match = fs
    .readdirSync(thumbsDir)
    .filter((file) => file.startsWith(prefix) && /\.(png|jpe?g|webp)$/i.test(file))
    .sort()[0];
  return match ? path.join("html", "thumbs", match) : "";
}

function findCoverVisual(day) {
  const dir = path.join(ROOT, "xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals");
  if (!fs.existsSync(dir)) return "";
  const files = fs.readdirSync(dir).filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).sort();
  const base = files.find((file) => /^visual-00-|cover|hero/i.test(file));
  return base ? path.join("xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals", base) : "";
}

function findLessonHtml(day) {
  const prefix = `day${String(day).padStart(2, "0")}-`;
  const htmlDir = path.join(ROOT, "html");
  if (!fs.existsSync(htmlDir)) return "";
  const match = fs
    .readdirSync(htmlDir)
    .filter((file) => file.startsWith(prefix) && file.endsWith(".html"))
    .sort()[0];
  return match ? path.join(htmlDir, match) : "";
}

function lessonPageUrl(day) {
  const lessonFile = findLessonHtml(day);
  if (!lessonFile) return "";
  const relativePath = path.relative(ROOT, lessonFile).split(path.sep).map(encodeURIComponent).join("/");
  return `${SITE_URL}/${relativePath}`;
}

function findLessonImage(day) {
  const file = findLessonHtml(day);
  if (!file) return "";
  const html = fs.readFileSync(file, "utf8");
  const match = html.match(/<img[^>]+src="([^"]+)"/i);
  if (!match) return "";
  return path.join("html", match[1]);
}

function stripHtml(value) {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function extractHtmlKnowledge(day) {
  const file = findLessonHtml(day);
  if (!file) return { items: [], mistakes: [], practice: [] };
  const html = fs.readFileSync(file, "utf8");
  const items = [];
  const kpSection = html.match(/<ul class="kp">([\s\S]*?)<\/ul>/);
  const kpBlocks = kpSection
    ? kpSection[1]
        .split(/<li>\s*/g)
        .slice(1)
        .map((block) => block.split(/<\/li>/)[0])
    : [];

  kpBlocks.forEach((block) => {
    const headMatch = block.match(/<span class="kp-head">([\s\S]*?)<\/span>/);
    if (!headMatch) return;
    const headText = stripHtml(headMatch[1]);
    const [titlePart, ...summaryParts] = headText.split(/[：:]/);
    const details = [];
    let body = block.slice(block.indexOf(headMatch[0]) + headMatch[0].length);
    const cardDetails = [];
    const cardPattern = /<div class="explain-card">\s*<h4>([\s\S]*?)<\/h4>\s*<p>([\s\S]*?)<\/p>\s*<\/div>/g;
    let cardMatch;
    while ((cardMatch = cardPattern.exec(body))) {
      const title = stripHtml(cardMatch[1]);
      const text = stripHtml(cardMatch[2]);
      if (title && text) cardDetails.push(`${title}：${text}`);
    }
    if (cardDetails.length) {
      details.push(...cardDetails);
      body = body.replace(cardPattern, "");
    }
    const blockPattern = /(?:<span class="dim">([^<]*)<\/span>\s*)?<p>([\s\S]*?)<\/p>/g;
    let blockMatch;
    while ((blockMatch = blockPattern.exec(body))) {
      const label = stripHtml(blockMatch[1] || "");
      const text = stripHtml(blockMatch[2]);
      if (!text) continue;
      details.push(label ? `${label}：${text}` : text);
    }
    const rowPattern = /<tr>\s*<td>([\s\S]*?)<\/td>\s*<td>([\s\S]*?)<\/td>\s*<td>([\s\S]*?)<\/td>\s*<\/tr>/g;
    let rowMatch;
    while ((rowMatch = rowPattern.exec(body))) {
      const [name, plain, example] = rowMatch.slice(1).map(stripHtml);
      if (name && plain && example) details.push(`${name}：${plain}。${example}`);
    }
    const stepPattern = /<li>\s*<span class="tag">([\s\S]*?)<\/span>\s*([\s\S]*?)<\/li>/g;
    let stepMatch;
    while ((stepMatch = stepPattern.exec(body))) {
      const label = stripHtml(stepMatch[1]);
      const text = stripHtml(stepMatch[2]);
      if (label && text) details.push(`${label}：${text}`);
    }
    items.push({
      title: titlePart || headText,
      summary: summaryParts.join("："),
      details,
    });
  });

  const mistakes = [];
  const mistakeSection = html.match(/<section class="warn">([\s\S]*?)<\/section>/);
  if (mistakeSection) {
    mistakes.push(
      ...[...mistakeSection[1].matchAll(/<p>([\s\S]*?)<\/p>/g)].map((entry) => stripHtml(entry[1])).filter(Boolean),
    );
  }

  const practice = [];
  const practiceSection = html.match(/<section class="panel orange">[\s\S]*?<h2>实操关联<\/h2>([\s\S]*?)<\/section>/);
  if (practiceSection) {
    practice.push(
      ...[...practiceSection[1].matchAll(/<li>([\s\S]*?)<\/li>/g)].map((entry) => stripHtml(entry[1])).filter(Boolean),
    );
  }

  return { items, mistakes, practice };
}

function splitPoint(point) {
  const parts = point.split(/[：:]/);
  if (parts.length < 2) return { head: point, body: "" };
  return { head: parts[0], body: parts.slice(1).join("：") };
}

function compactText(value, maxLength = 92) {
  if (!value) return "";
  return value.length > maxLength ? `${value.slice(0, maxLength - 1)}…` : value;
}

function pushUnique(list, value, maxLength = 132) {
  const clean = compactText(stripHtml(value || "").replace(/\s+/g, " ").trim(), maxLength);
  if (!clean || list.includes(clean)) return;
  list.push(clean);
}

function splitSentences(value) {
  return (value || "")
    .split(/(?<=[。！？；])\s*/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function detailToPoint(value) {
  const labeled = value.match(/^([^：:]{1,12})[：:]\s*(.+)$/);
  if (labeled) {
    const bodySentences = splitSentences(labeled[2]);
    return `${labeled[1]}：${bodySentences.slice(0, 3).map((item) => compactText(item, 76)).join("｜")}`;
  }
  const sentences = splitSentences(value);
  if (sentences.length <= 1) return compactText(value, 132);
  const [head, ...rest] = sentences;
  return `${compactText(head, 58)}：${rest.slice(0, 3).map((item) => compactText(item, 76)).join("｜")}`;
}

function itemSlide(item, fallbackPoint, index) {
  const fallback = splitPoint(fallbackPoint || "");
  const title = item?.title || fallback.head || `知识点 ${index}`;
  const details = item?.details?.length ? item.details : [fallback.body || fallbackPoint].filter(Boolean);
  const points = [];
  details.slice(0, 3).forEach((detail) => pushUnique(points, detailToPoint(detail)));
  if (!item?.details?.length) splitSentences(fallback.body).forEach((sentence) => pushUnique(points, sentence));
  if (points.length < 3 && fallback.body) pushUnique(points, fallback.body);
  if (/动作分析顺序/.test(title) && points.length === 0) {
    [
      "第一步：识别动作：卧推看肩水平内收 + 肘伸；划船看肩伸 + 肘屈；侧平举看肩外展。",
      "第二步：找主动肌：谁跨过目标关节，谁能制造同方向力矩，谁就是主要输出。",
      "第三步：找协同肌：推类常有三角肌前束、肱三头肌；拉类常有肱二头肌和肩胛肌群。",
      "第四步：找稳定肌：肩袖、肩胛稳定肌、核心让关节保持可发力位置。",
    ].forEach((point) => pushUnique(points, point));
  }
  return {
    type: "dense",
    eyebrow: String(index).padStart(2, "0"),
    title,
    lead: compactText(item?.summary || fallback.body || "先看概念，再看训练怎么用。", 76),
    visualTitle: title,
    points,
    fill: [`关键词：${title}`, "看图定位", "讲回训练"],
  };
}

function findAiVisual(day, eyebrow, title = "") {
  const dir = path.join(ROOT, "xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals");
  if (!fs.existsSync(dir)) return "";
  const files = fs.readdirSync(dir).filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).sort();
  const day16Slugs = {
    "00": "cover", "01": "lever-overview", "02": "three-elements", "03": "three-lever-classes",
    "04": "torque-moment-arm", "05": "curl-third-class", "06": "mechanical-advantage",
    "07": "curl-angle-torque", "08": "rdl-moment-arm", "09": "analysis-flow",
  };
  if (day === 16 && day16Slugs[eyebrow]) {
    const exact = `visual-${eyebrow}-${day16Slugs[eyebrow]}.png`;
    const match = files.find((file) => file === exact);
    if (match) return path.join("xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals", match);
  }
  const day17Visuals = {
    "02": "visual-02-seven-patterns.png",
    "03": "visual-03-open-closed-chain.png",
    "04": "visual-03-open-closed-chain.png",
    "05": "visual-04-stable-unstable.png",
    "06": "visual-06-push-pull.png",
    "07": "visual-05-analysis-workflow.png",
    "08": "visual-07-lower-body-patterns.png",
    "09": "visual-01-movement-analysis-base.png",
  };
  if (day === 17 && day17Visuals[eyebrow]) {
    const match = files.find((file) => file === day17Visuals[eyebrow]);
    if (match) return path.join("xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals", match);
  }
  const prefix = `visual-${eyebrow}`;
  let match = files.filter((file) => file.startsWith(prefix)).sort()[0];
  if (!match) {
    const titleVisualMap = [
      [/信度/, "reliability"],
      [/效度/, "validity"],
      [/相关|因果/, "correlation-causation"],
      [/RCT|研究设计/, "research-design"],
      [/统计陷阱|样本量|选择性报告|混杂/, "statistical-traps"],
    ];
    const mapped = titleVisualMap.find(([pattern]) => pattern.test(title))?.[1];
    match = mapped ? files.find((file) => file.includes(mapped)) : "";
  }
  return match ? path.join("xhs", `day${String(day).padStart(2, "0")}`, "ai-visuals", match) : "";
}

function buildSlides(lesson) {
  if (lesson.day === 16) return buildDay16Slides(lesson);
  if (lesson.day === 17) return buildDay17Slides(lesson);
  if (lesson.day === 18) return buildDay18Slides(lesson);
  if (lesson.day === 19) return buildDay19Slides(lesson);
  if (lesson.day === 20) return buildDay20Slides(lesson);
  if (lesson.day === 21) return buildDay21Slides(lesson);
  if (lesson.day === 22) return buildDay22Slides(lesson);
  if (lesson.day === 23) return buildDay23Slides(lesson);
  if (lesson.day === 24) return buildDay24Slides(lesson);
  if (lesson.day === 25) return buildDay25Slides(lesson);
  if (lesson.day === 26) return buildDay26Slides(lesson);
  if (lesson.day === 27) return buildDay27Slides(lesson);
  if (lesson.day === 28) return buildDay28Slides(lesson);
  if (lesson.day === 29) return buildDay29Slides(lesson);
  if (lesson.day === 30) return buildDay30Slides(lesson);
  if (lesson.day === 31) return buildDay31Slides(lesson);
  const htmlKnowledge = extractHtmlKnowledge(lesson.day);
  const items = htmlKnowledge.items;
  const practiceItems = htmlKnowledge.practice.length ? htmlKnowledge.practice : [lesson.practice || "用一个训练动作把今天知识讲出来。"];
  const lessonImage = assetDataUrl(findLessonImage(lesson.day) || findThumbnail(lesson.day));
  const itemSlides = (items.length ? items : lesson.points.map((point) => null)).map((item, index) =>
    itemSlide(item, lesson.points[index], index + 2),
  );
  const finalIndex = itemSlides.length + 2;
  return [
    {
      type: "cover",
      kicker: `Day ${lesson.day} · ${lesson.cert}`,
      title: lesson.title,
      subtitle: "NSCA / NASM 双证健身知识",
      image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)),
      chips: [lesson.phase, "运动科学"],
    },
    {
      type: "image",
      eyebrow: "01",
      title: "先看图，再看概念",
      lead: "后面提到的位置、结构和动作，都先在这张图里找一遍。",
      image: lessonImage,
      points: [],
      fill: [],
    },
    ...itemSlides,
    {
      type: "dense",
      eyebrow: String(finalIndex).padStart(2, "0"),
      title: "训练里怎么用",
      lead: "把研究结论翻译成训练判断，重点看测量、设计和结果能不能支持你的选择。",
      visualTitle: "训练里怎么用",
      points: [
        ...practiceItems.slice(0, 4),
        htmlKnowledge.mistakes[2] || "看到显著差异时，还要继续看效果量、样本和实际训练意义。",
      ],
      fill: [],
    },
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay28Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  const visuals = {
    "02": "visual-02-energy-systems.png",
    "03": "visual-05-duration.png",
    "04": "visual-06-rest-intervals.png",
    "05": "visual-03-ec-coupling.png",
    "06": "visual-07-calcium-chain.png",
    "07": "visual-04-motor-units.png",
    "08": "visual-08-review.png",
    "09": "visual-10-training-application.png",
  };
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: "能量系统与神经肌肉", subtitle: "第4周复盘 · 从 ATP 供给到运动单位募集", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动生理", "神经肌肉"] },
    { type: "image", eyebrow: "01", title: "先串起燃料、点火和输出", lead: "能量系统补 ATP，兴奋-收缩耦联把神经信号变成横桥滑动，运动单位募集决定参与输出的肌纤维数量。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "三能量系统：一直并行", "ATP-PCr、糖酵解和氧化系统始终同时工作；差别在于不同动作里，谁贡献得更多、谁能维持更久。", [
      "ATP-PCr：细胞内 ATP 直接供能，PCr 快速补回 ATP｜启动最快，适合几秒钟高功率输出｜库存小，峰值很难久撑。",
      "糖酵解：把葡萄糖或肌糖原快速拆开来补 ATP｜高强度重复输出时贡献明显｜酸胀、呼吸急和掉速常随压力上升。",
      "氧化系统：在线粒体内用氧气持续处理糖和脂肪｜启动较慢但可长时间供能｜也支持组间恢复和长时稳定输出。",
    ]),
    visual("03", "先看时长，再看强度", "供能占比不是按项目名称决定，而是看一次用力持续多久、强度多高、能否连续输出。", [
      "时间线：0-10 秒常见 ATP-PCr 主导｜约 30 秒到 2 分钟糖酵解压力更大｜时间再拉长，氧化系统占比持续增加。",
      "强度影响：同样 1 分钟，轻松走路和全力冲刺不是同一供能逻辑｜强度越高，PCr 与糖的贡献通常越大｜供能比例会随配速实时调整。",
      "不要当开关：100 米前段和后段都在用三套系统｜只是前段更像快速供能，后段糖酵解和氧化贡献逐步上升｜系统不会轮流开机。",
    ]),
    visual("04", "组间休息：是在恢复什么", "休息不是偷懒，而是在决定下一组要保留峰值力量、爆发速度，还是接受疲劳下的重复输出。", [
      "PCr 回补：高强度动作会快速消耗 PCr｜短休时库存回补不足，下一组峰值力量和速度更容易下降｜休息长度因此是训练变量。",
      "神经与局部环境：高质量输出还依赖神经驱动、钙处理和离子环境｜疲劳累积后，动作路径和发力时机也会变差｜同样重量会感觉突然变重。",
      "按目标安排：最大力量和爆发常需较长休息｜一般增肌可用中等休息累积训练量｜密度训练可短休，但要接受输出下降。",
    ]),
    visual("05", "E-C coupling：电信号变成收缩", "兴奋-收缩耦联不是一个抽象名词，而是从神经指令到肌丝滑动的一条连续生理链。", [
      "神经接头：运动神经动作电位到末梢后释放 ACh，乙酰胆碱｜ACh 让肌膜去极化｜它是“点火信号”，不是直接收缩力。",
      "信号深入：去极化沿肌膜和 T 管传入肌纤维深处｜肌浆网接到信号后释放 Ca2+｜这样整根肌纤维能更同步地启动。",
      "横桥启动：Ca2+ 结合肌钙蛋白，原肌球蛋白移开｜肌动蛋白结合位点暴露｜肌球蛋白才能反复抓拉，产生滑动和张力。",
    ]),
    visual("06", "Ca2+：开门，也负责关门", "钙离子既是启动横桥的信号，也是终止收缩时必须被回收的信号；它来自肌浆网，而非血液直接灌入。", [
      "主要来源：收缩触发的 Ca2+ 由肌浆网释放｜它在肌纤维内部距离横桥很近｜血液钙不是这次快速收缩的直接开关。",
      "怎样停止：神经刺激结束后，SERCA 泵把 Ca2+ 送回肌浆网｜肌钙蛋白失去 Ca2+｜原肌球蛋白重新遮住结合位点。",
      "疲劳关联：反复高强度收缩会改变 Ca2+ 释放与回收效率｜这会和 PCr 降低、离子变化一起影响力量和动作稳定性｜不是单一代谢物造成疲劳。",
    ]),
    visual("07", "运动单位：一根神经带一组纤维", "运动单位由一个运动神经元和它支配的全部肌纤维组成；募集越多，参与输出的纤维数量越多。", [
      "小运动单位：一个神经元连接的纤维较少｜阈值低、控制细、耐疲劳｜适合低强度和精细控制任务。",
      "大运动单位：一个神经元可支配更多纤维｜阈值高、输出大、较易疲劳｜需要更高力量或更强神经驱动时加入。",
      "训练意义：轻重量开始时不必动员全部单位｜负荷变高、快速发力或接近力竭时，更多高阈值单位会参与工作｜动作控制仍决定目标肌能否有效受力。",
    ]),
    visual("08", "大小原则：通常小到大", "骨骼肌募集通常从低阈值、小运动单位开始，再随着力量需求与疲劳增加，逐步加入高阈值、大单位。", [
      "基本方向：低阈值、耐疲劳单位先加入｜需求继续提高时再补高阈值单位｜这是稳定发力与节省资源的默认顺序。",
      "何时加人：更大负荷、更快速度意图或接近力竭，会提高高阈值单位参与概率｜不必每组都用极限重量才能做到｜不同方法可通向相似募集结果。",
      "常见误会：快速动作能提高神经驱动，但不等于“快肌永远先上”｜基础募集顺序仍以小到大解释｜技术和恢复也不能跳过。",
    ]),
    visual("09", "训练里怎么串起来", "看一个训练组时，同时问：供能靠谁、休息要补什么、神经信号怎样变成收缩、哪些运动单位需要加入。", [
      "爆发或力量：单次或低次数重组依赖快速 ATP 供给与高神经驱动｜用足够长休息保住 PCr、速度和动作路径｜质量下降就先停或延长休息。",
      "增肌训练：中高次数可让疲劳下的高阈值单位逐步加入｜仍要保留机械张力和动作控制｜短休能加密度，但不能让技术完全崩掉。",
      "HIIT：冲刺段提高 ATP-PCr 与糖酵解压力｜恢复段由氧化系统支持 PCr 回补和代谢处理｜下一轮速度能否保住，就是恢复是否足够的反馈。",
    ]),
  ].map((slide) => {
    const visualFile = visuals[slide.eyebrow];
    if (!visualFile) return slide;
    return { ...slide, visualImage: assetDataUrl(path.join("xhs", "day28", "ai-visuals", visualFile)) };
  });
}

function buildDay29Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: "训练适应基本原则", subtitle: "NSCA / NASM 双证健身知识 · 训练设计底层规则", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "训练科学", "计划设计"] },
    { type: "image", eyebrow: "01", title: "先看训练适应循环", lead: "先看训练刺激、恢复、适应和下一次进阶，再把特异性、超负荷、可逆性、个体差异放进去。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "特异性：练什么更像什么", "训练效果会贴着动作模式、肌肉群、速度、关节角度和能量系统走；目标不清，刺激就容易跑偏。", [
      "概念：Specificity = 专一性｜身体会优先适应反复经历的刺激｜这种迁移有方向，不是所有能力一起上涨。",
      "匹配维度：看动作模式、关节角度、发力速度、肌肉群和供能需求｜目标越具体，训练信号越要像它｜关键维度偏离越多，迁移越弱。",
      "训练例子：想提高卧推 1RM，要保留水平推、高负荷和长休息｜慢跑与核心能辅助健康，却不能替代主项｜辅助训练要为主项补短板。",
    ]),
    visual("03", "超负荷：刺激要超过旧水平", "身体很省资源；如果训练仍在原来能轻松处理的范围内，它更倾向于维持，而不是升级。", [
      "概念：Overload = 超过既有能力的刺激｜可来自重量、次数、组数、速度、密度、动作难度或总训练量｜比较对象是自己旧水平。",
      "有效区间：刺激要强到足以要求适应，也要留出恢复空间｜练到失控不是超负荷，往往只是疲劳失控｜动作质量必须守住。",
      "训练例子：20kg 深蹲 3x10 已低 RPE，可先加 1-2 次或 2.5kg｜单次只改少量变量，才看得懂反应｜连续多周轻松才继续升级。",
    ]),
    visual("04", "渐进：小步加，不要乱跳", "适应发生后，下一轮刺激要略微升级；真正的计划进步来自可追踪的小台阶。", [
      "进阶变量：重量、次数、组数、动作范围、速度意图、频率和休息时间都能升级｜加重量只是其中一种｜一次优先改一个变量。",
      "为何小步：肌肉、神经、肌腱和骨的适应速度不同｜力量快速上升时，结缔组织未必已准备好承受猛加量｜疼痛和动作变形是过快信号。",
      "安排方式：先把技术和基准量做稳，再逐周小幅加量或加重｜疲劳累积时主动减量，给下一轮进步留空间｜记录才能知道升级来自哪里。",
    ]),
    visual("05", "可逆性：停太久会退档", "训练适应需要持续刺激维持；停训后，身体会逐步撤回不再需要的能力。", [
      "概念：Reversibility = 可逆性｜维持力量、耐力和技术都需要成本｜长期缺少刺激，身体会逐步撤回不需要的能力｜训练适应不是永久存款。",
      "退步节奏：短暂休息通常帮助恢复，不等于退步｜停训数周后，耐力与力量常会开始出现可见下滑｜退步速度因人、项目和训练史而异。",
      "忙碌期策略：用最低有效维持量保住主项｜每周少量高质量抗阻和短有氧，通常比完全停训更稳｜恢复训练时再逐步爬坡。",
    ]),
    visual("06", "个体差异：同计划不同反应", "原则通用，但剂量必须个体化；同一个模板，在不同人身上不会产生同样结果。", [
      "差异来源：训练史、年龄、睡眠、营养、压力、伤病、技术和遗传都会改变反应｜同一模板不是同一剂量｜原则需要靠反馈落到个人。",
      "看什么反馈：记录完成重量、重复次数、RPE、动作质量、疼痛、睡眠和情绪｜比单次练得累不累更可靠｜优先看连续两周趋势。",
      "怎么调整：恢复差时先减量、延长休息或换变式｜进步快也要控制节奏｜短期表现不能掩盖长期疲劳。",
    ]),
    visual("07", "持续变化：变，但别乱变", "长期训练需要变化刺激，但变化必须服务目标；随机换动作只会让适应信号变模糊。", [
      "变化目的：避免适应停滞与重复压力累积｜可调整负荷、次数、节奏、动作变式、训练重点或周内分配｜每项变化都要有明确目的。",
      "保留主线：深蹲目标可加入暂停深蹲、前蹲或节奏蹲｜但主要练的仍是髋膝伸展与深蹲力量｜变式应解决技术或负荷问题。",
      "变化时机：先让一个刺激累积足够久、看清反馈，再改变一个关键变量｜每次全换会让进步和问题都难追踪｜稳定重复也是必要刺激。",
    ]),
    visual("08", "剂量-反应：多不等于更好", "训练效果随剂量变化，但最佳区间在“够刺激”和“能恢复”之间。", [
      "剂量是什么：强度、容量、频率、密度、动作难度与恢复成本共同组成｜训练时长只是其中一项｜同样时长可能是完全不同剂量。",
      "反应曲线：剂量太低多为维持，适中最易进步，过高会让疲劳压过恢复｜最佳区间会随训练水平和生活压力变化｜不是越多越快。",
      "监测方法：连续看重量、速度、疼痛、睡眠和训练欲望｜多项趋势一起变差时，优先检查剂量｜不要只靠意志硬顶。",
    ]),
    visual("09", "训练里怎么用", "所有计划先过五个问题：目标像不像、刺激够不够、进阶稳不稳、恢复跟不跟得上、个人反馈支不支持。", [
      "力量目标：主项要高度特异，常用低到中次数与较长休息｜每组速度、轨迹和技术稳定性比“累不累”更关键｜把高质量重复放在前面。",
      "增肌目标：先让目标肌承受足够机械张力，再用容量、接近力竭程度和频率小步进阶｜酸胀不是唯一标准｜动作控制和恢复同样重要。",
      "耐力或减脂：用频率、持续时间和强度分区渐进，同时保留恢复空间｜能稳定执行数月的剂量，比一次练爆更有价值｜每周总量要能长期维持。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay30Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: "FITT-VP与ACSM指南", subtitle: "训练处方六变量 · 成人身体活动底线", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "训练科学", "运动处方"] },
    { type: "image", eyebrow: "01", title: "先看训练处方六旋钮", lead: "FITT-VP 把训练计划拆成频率、强度、时间、类型、容量和进阶；ACSM 指南给出成人健康活动底线。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "FITT-VP：训练处方框架", "计划不是动作清单，而是六个变量组合；变量写清楚，才知道刺激够不够、方向对不对。", [
      "F = Frequency 频率｜一周练几次，决定刺激出现得够不够密｜频率必须和恢复能力一起看。",
      "I = Intensity 强度｜抗阻可用 %1RM、RM、RPE；有氧可用心率、RPE、谈话测试｜强度决定训练更偏力量、增肌、耐力还是心肺。",
      "T/T/V/P = 时间、类型、容量、进阶｜每次多久、做哪类运动、总量多少、何时加量｜像处方剂量一样必须可记录。",
    ]),
    visual("03", "强度区间：目标先定档", "同样是抗阻训练，强度和次数不同，刺激方向就不同；考试常考力量、肌肥大、耐力和爆发区间。", [
      "最大力量：常用 ≥85%1RM，少于 6 次｜重点是高神经驱动和高张力｜组间休息通常更长。",
      "肌肥大：常见 67-85%1RM、6-12 次｜机械张力、足够容量和接近力竭共同作用｜不是只追酸胀。",
      "肌耐力与爆发：肌耐力常低于 67%1RM、多于 12 次｜爆发可在 30-85%1RM，但速度是限制条件｜太重会把速度压没。",
    ]),
    visual("04", "容量：把总负荷算出来", "容量让训练从感觉变成数字；抗阻常用组数×次数×重量，也可按每肌群周有效组追踪。", [
      "基础公式：容量 = 组数 × 次数 × 重量｜60kg × 10次 × 3组 = 1800kg｜这能比较同一动作负荷变化。",
      "容量不是时长：在健身房待 90 分钟不等于高容量｜真正要看有效组、重复次数、重量和目标肌是否受力。",
      "剂量判断：容量太低刺激不足，太高恢复跟不上｜若速度、疼痛、睡眠连续变差，先查总量和强度是否叠太多。",
    ]),
    visual("05", "ACSM有氧底线：分钟数要达标", "ACSM 给成人健康最低推荐：中等强度 150 分钟或高强度 75 分钟；这是底线，不是专项上限。", [
      "中等强度：每周 ≥150 分钟｜可拆成 30 分钟×5 次，也可按客户时间分配｜快走、骑车、游泳都可算。",
      "高强度：每周 ≥75 分钟｜疲劳成本更高，不适合所有初学者直接上｜久坐客户通常先用中等强度建立习惯。",
      "别漏抗阻：有氧分钟数达标不代表全部达标｜还要每周 ≥2 次全身大肌群抗阻训练｜健康处方要两条都看。",
    ]),
    visual("06", "NASM心率三区：有氧强度分层", "心率三区帮助把有氧强度开到合适档位；Zone1 打基础，Zone2 进阶，Zone3 接近无氧阈值。", [
      "Zone1：65-75%HRmax｜适合基础有氧、恢复和燃脂区间练习｜可持续性强，适合新手起步。",
      "Zone2：76-85%HRmax｜进阶有氧压力更高｜呼吸明显变急，但仍可控制节奏。",
      "Zone3：>86%HRmax｜接近无氧阈值，疲劳成本高｜用于短段高强度，不该替代所有基础有氧。",
    ]),
    visual("07", "进阶P：一次只调少量变量", "进阶把 Day29 渐进性超负荷落到计划里；适应后小步加，恢复差时先维持或轻降。", [
      "进阶路径：先稳定动作和出勤，再加时间、频率、重量、次数或组数｜一次优先调一个变量｜这样才能看懂身体反应。",
      "久坐例子：第1周快走20分钟×3次，第2周25分钟×3次，第3周30分钟×3次｜比一上来每天高强度更稳。",
      "专业判断：疼痛升高、睡眠变差、动作变形时，计划可维持或降量｜退一步不等于失败，是为了长期进步。",
    ]),
    visual("08", "久坐客户：先达健康底线", "初期训练不必复杂；先满足 ACSM 底线，再用 FITT-VP 把处方写清楚。", [
      "有氧处方：每周 3-5 次中等强度活动，逐步累计到 150 分钟｜类型可选快走、车、椭圆机｜安全和坚持优先。",
      "抗阻处方：每周 2 次全身大肌群训练｜动作覆盖推、拉、蹲、髋铰链和核心稳定｜重量先保动作质量。",
      "评估达标：客户快走 30 分钟×4 次 = 120 分钟，还差 30 分钟中等有氧｜若抗阻 2 次，则抗阻部分已达标。",
    ]),
    visual("09", "训练里怎么用", "每次写计划都问六件事：一周几次、多强、多久、什么类型、总量多少、下一步如何进阶。", [
      "肌肥大目标：每肌群每周 2-3 次常见｜强度多在 67-85%1RM，6-12 次为主｜用周有效组数追踪容量。",
      "最大力量目标：主项高特异性，≥85%1RM、低次数、长休息｜进阶优先小幅加重或增加高质量组｜动作速度和稳定性要记录。",
      "减脂目标：有氧分钟数帮助提高总消耗，抗阻帮助保肌肉｜容量增加要慢，避免疲劳让日常活动量下降｜能长期做才有用。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay31Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: "PAR-Q+与医学筛查", subtitle: "训练介入前的安全闸门 · 筛查、分层、转诊、签署", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "训练科学", "风险筛查"] },
    { type: "image", eyebrow: "01", title: "先看训练前安全流程", lead: "先做 PAR-Q+，再量体征基线、分风险；出现红旗时先医师许可，最后才进入训练处方。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "PAR-Q+：先问能不能开始", "PAR-Q+ 是运动前身体活动准备问卷；它不是摆设，而是决定客户能否直接开始训练的第一道筛查。", [
      "问什么：心血管症状、疾病史、药物、疼痛、医生限制和近期异常反应｜这些信息决定训练入口，不是课后再补。",
      "任一是：关键问题答“是”不等于永远不能练｜它代表需要进一步评估、限制条件或医师许可｜不能直接按普通新手开课。",
      "教练边界：教练能识别风险、记录信息、调整训练和建议转诊｜不能诊断疾病，也不能替医生解除禁忌。",
    ]),
    visual("03", "风险分层：疾病、症状、因素", "ACSM 风险分层把客户从“看起来没事”变成可判断的低、中、高风险。", [
      "已知疾病：心血管、肺部、代谢疾病会显著改变训练前流程｜控制情况不清时更要保守｜高强度测试通常不该先做。",
      "症状红旗：胸痛、晕厥、异常气短、心悸、下肢水肿等不是普通疲劳｜这些线索要先医学确认｜记录比口头带过更重要。",
      "风险因素：年龄、吸烟、高血压、血脂异常、血糖异常、肥胖、家族史、久坐会累积风险｜没有诊断也可能需要更保守起步。",
    ]),
    visual("04", "体征基线：先量起点", "静息心率、血压、BMI、腰臀比和体脂，是训练处方前的安全坐标和后续对照。", [
      "生命体征优先：静息心率和血压先看安全｜血压异常会改变训练强度、呼吸提示和是否转诊｜不能只拍照量体重。",
      "体成分辅助：BMI 可粗筛体重风险，腰臀比提示脂肪分布，体脂或围度用于追踪变化｜它们不能替代疾病筛查。",
      "记录条件：记录日期、测量姿势、休息时间和设备｜同一客户后续复测才可比较｜否则“进步”可能只是测量误差。",
    ]),
    visual("05", "转诊红旗：先医师许可", "高风险、症状阳性或体征明显异常时，专业做法是暂停高强度训练并建议医学评估。", [
      "血压红线：静息血压 ≥180/110 mmHg 是重要异常线索｜不要做最大力量、有氧极限或 HIIT 测试｜先医学确认。",
      "症状优先：运动中胸痛、晕厥、异常气短、心律不齐感，都比客户训练意愿更重要｜不靠热身“试试看”。",
      "转诊话术：说明发现需要医生确认的风险，保留测量和问卷记录｜不是吓退客户，而是把训练放到安全边界内。",
    ]),
    visual("06", "知情同意 vs 免责声明", "两个文件作用不同：知情同意负责告知和授权，免责声明只限定部分责任边界。", [
      "知情同意：Informed consent = 被告知后同意｜要说明训练收益、风险、流程、替代选择和停止条件｜重点是沟通。",
      "免责声明：Waiver = 客户理解运动风险并同意部分责任边界｜它不能让高风险训练变安全｜也不能覆盖教练明显疏忽。",
      "医师许可：Medical clearance 是医生确认客户可运动或限定条件｜它不能被教练口头判断、免责声明或客户意愿替代。",
    ]),
    visual("07", "风险因素计数：别只看外表", "风险不是凭身材和年龄感觉判断；多个小线索叠加，训练入口就要更保守。", [
      "客户例子：55 岁、久坐、吸烟、血压偏高、父亲早发心梗｜即使没有胸痛，也不该直接做冲刺间歇或最大心率测试。",
      "训练调整：低强度起步、延长热身、监测心率和 RPE、避免憋气用力｜必要时先医师确认｜进阶幅度更小。",
      "判断逻辑：先问症状和病史，再数风险因素，再看体征｜三者一起决定低中高风险，不靠“客户说没事”。",
    ]),
    visual("08", "安全开始：筛查接上 FITT-VP", "Day31 决定能不能练、怎么限制；Day30 的 FITT-VP 决定具体频率、强度、时间、类型、容量和进阶。", [
      "低风险：可从低到中等强度开始，写清 FITT-VP 六变量｜仍要记录体征和训练反应｜不是随意上强度。",
      "中风险：更保守地选强度和类型，避免一开始最大测试｜观察血压、心率、疼痛和恢复｜进阶先小步。",
      "高风险：先转诊或获取医师许可，再按限制条件设计训练｜有禁忌时宁可暂停，不拿免责声明冒险。",
    ]),
    visual("09", "教练执行清单", "每个新客户都按同一条线处理：先问、再量、再分层、再签署、再处方、再记录。", [
      "课前：PAR-Q+、病史、症状、药物、医生限制、近期受伤｜任何阳性线索都要写进记录。",
      "课中：低风险才做适合水平的测试和训练｜发现胸痛、头晕、异常气短或血压异常，立即停止并建议医学评估。",
      "课后：保存问卷、体征、知情同意、免责声明、转诊建议和训练反应｜专业流程比事后解释更能降低风险。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay22Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看 ATP、PCr 与恢复时间", lead: "先分清谁直接供能、谁快速补货，再理解大重量为什么需要长休息。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "ATP-PCr：即时供能双人组", "最大力量、纵跳、短冲刺等需要立刻高功率的动作，首先调用细胞内现成的 ATP 和 PCr。", [
      "ATP 是直接能量：全称三磷酸腺苷，肌球蛋白横桥每次抓拉都直接用它｜脂肪和糖不能直接推杠铃，最后都要先转成 ATP。",
      "PCr 是快速补给：全称磷酸肌酸，储存在肌细胞内并带着高能磷酸｜当 ATP 被用掉后，它能立刻把磷酸补回去，再生新的 ATP。",
      "为什么只适合极短爆发：反应不用等氧气运到，也不用走长代谢链，所以启动最快｜但 ATP 和 PCr 库存很小，全力输出通常 0-10 秒最典型。",
    ]),
    visual("03", "反应过程：ATP 用掉后怎么补回", "把它看成一次交接：ATP 放能变 ADP，PCr 再把自己的磷酸交给 ADP，让 ATP 重新可用。", [
      "第一步，ATP 放能：ATP 断开最外侧一个磷酸基团，释放能量给横桥做功｜剩下的是 ADP，中文叫二磷酸腺苷，能量较低但不是废物。",
      "第二步，PCr 补磷酸：PCr 把自己携带的磷酸基团转给 ADP｜结果是 ADP 重新变 ATP，PCr 则变成肌酸，暂时失去“快充”能力。",
      "训练里意味着什么：1RM 起杠、起跑前几步和抓举拉起时，身体没时间等慢系统供能｜PCr 库存下降后，同样重量的速度和峰值输出会掉。",
    ]),
    visual("04", "0-10 秒：快，但库存很小", "ATP-PCr 系统的特点不是能量总量大，而是供能速度最快，特别适合短到来不及等氧气参与的动作。", [
      "无氧不等于憋气：意思是这次快速再生 ATP 的反应不直接依赖氧气到场｜ATP 和 PCr 本来就在肌细胞内，位置近、步骤少。",
      "典型场景：单次最大深蹲或卧推、3 次以内重硬拉、一次纵跳、起跑前 10 秒｜共同点是时间短、用力猛、需要高功率。",
      "别把时间线当开关：100 米前段 ATP-PCr 占比高，后段糖酵解贡献会上升｜三套系统始终同时工作，只是主导比例随时间和强度变化。",
    ]),
    visual("05", "恢复：休息是在补 PCr 库存", "PCr 输出时不靠氧气，但补回库存需要恢复过程支持；所以高质量力量训练必须把组间休息算进计划。", [
      "休 30 秒：PCr 大约只恢复一半｜下一组仍能练，但峰值力量、速度和动作稳定性常会打折，更接近密度或代谢训练。",
      "休 1-2 分钟：库存恢复更多，适合一般增肌和技术练习｜若目标是 3RM 或爆发速度，仍可能不够让每组回到接近峰值。",
      "休 3-5 分钟：PCr 接近完全恢复，神经输出也更容易回到高水平｜适合大重量、跳跃、冲刺等需要每组高质量的训练。",
    ]),
    visual("06", "运动判断：先看时长与强度", "判断主供能系统别先背运动名称，先问动作全力持续多久、是否需要连续不断输出。", [
      "1 次最大硬拉：ATP-PCr 主导｜动作只持续几秒，功率极高，PCr 能在这段时间快速补 ATP。",
      "10 秒全力冲刺：ATP-PCr 为主，糖酵解开始加入｜越接近后段，PCr 越不够，速度维持开始更依赖其他供能。",
      "400 米后段或马拉松：不能只靠 ATP-PCr｜前者糖酵解明显增加，后者以氧化系统为主，因为时间太长，PCr 库存早已不足。",
    ]),
    visual("07", "休息策略：目标不同，休法不同", "休息长短不是勤不勤奋问题，而是决定你下一组练峰值输出，还是练疲劳下重复输出。", [
      "练最大力量：低次数、高负荷，组间 3-5 分钟｜目标是让每一组重量、速度和动作路径都接近最好状态。",
      "练爆发速度：宁可少做，也要快｜若跳跃高度、冲刺速度或杠铃速度明显下降，继续堆次数已从练爆发变成练疲劳。",
      "练增肌或密度：可用中等甚至短休累积训练量和张力｜会更喘不代表更适合力量目标，训练效果取决于你刻意保留什么。",
    ]),
    visual("08", "训练决策：先定目标，再定休息", "同一个深蹲动作，休 45 秒还是 4 分钟，会把训练推向完全不同的适应方向。", [
      "目标是 5 组 3 次力量：优先保重量、速度和技术｜组间休 3-5 分钟，让 PCr 和神经输出恢复，避免后面几组只是在硬撑。",
      "目标是肌肥大训练量：可缩短到中等休息，接受部分疲劳｜同时要相应调整重量和次数，别把峰值输出要求套到每一组。",
      "判断是否该停：速度明显掉、动作变形或同样重量突然失控，先问 PCr 是否恢复不足｜延长休息或结束高质量组，不要只为凑次数。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay23Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看糖、丙酮酸和乳酸", lead: "先分清糖怎么快速拆成 ATP，丙酮酸为什么会走向乳酸或线粒体。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "糖酵解：快拆糖供能", "糖酵解把葡萄糖或肌糖原快速拆开，再把能量转成肌肉能直接使用的 ATP。", [
      "原料从哪里来：血糖来自血液，肌糖原储存在肌肉里｜高强度重复动作时，工作肌优先用本地肌糖原，因为距离近、调动快。",
      "它到底产什么：糖酵解不是直接“烧糖推杠铃”｜它把糖拆成丙酮酸，同时快速再合成 ATP，ATP 才是肌肉横桥真正能用的能量。",
      "为什么叫快拆厨房：步骤比 ATP-PCr 多，所以不如 0-10 秒爆发快｜但糖库存更大，能撑 30 秒到 2 分钟这段中高强度。",
      "怎么判断题干：看到 400 米、HIIT、8-15 次多组、后半段腿酸掉速｜先想糖酵解，而不是一上来就写有氧或乳酸中毒。",
    ]),
    visual("03", "无氧糖酵解：强度高时先顶住", "当强度太高、线粒体处理速度跟不上时，丙酮酸更容易转成乳酸，让供能继续周转。", [
      "无氧不是不呼吸：你仍在吸氧，氧化系统也没关闭｜只是强度太高，线粒体来不及把所有丙酮酸慢慢处理完。",
      "为什么转乳酸：丙酮酸转成乳酸能让糖酵解继续周转｜大白话是先把车流分流出去，让短时间供能别堵死。",
      "身体感受是什么：局部灼烧、呼吸急、动作速度掉、同样重量突然变沉｜这些都提示糖酵解压力和相关代谢压力上来了。",
      "训练例子怎么套：400 米后段、1 分钟冲刺车、搏击一回合后半段、12 次深蹲最后几次｜都不是单纯 PCr 能解决。",
    ]),
    visual("04", "有氧糖酵解：丙酮酸进线粒体", "当氧气和线粒体处理能力跟得上时，丙酮酸会进入线粒体，继续产生更多 ATP。", [
      "分岔点在丙酮酸：糖先被拆成丙酮酸｜强度可控时，丙酮酸进入线粒体；强度太高时，更多转成乳酸。",
      "线粒体像慢炖发电厂：它不如无氧路线快，但能榨出更多 ATP｜所以更适合持续输出，而不是几十秒硬冲。",
      "为什么训练后会变强：有氧基础和阈值训练会提高线粒体处理能力｜同样配速下，更多丙酮酸能被处理，乳酸堆积更慢。",
      "怎么用在配速：能说短句但不能聊天的强度，常接近阈值训练区｜目标不是冲爆，而是把可持续高强度往上推。",
    ]),
    visual("05", "乳酸阈：产出超过清除", "乳酸阈不是乳酸第一次出现，而是乳酸产生速度开始明显超过清除速度的转折区。", [
      "低于阈值是什么感觉：乳酸产生和清除大体平衡｜呼吸快但还能维持，腿有压力但不会立刻崩。",
      "超过阈值会怎样：产生速度大于清除速度｜代谢压力快速上升，速度、动作质量和主观用力都会更快恶化。",
      "它不是开关：阈值是一个转折区，不是某一秒突然从无乳酸变成有乳酸｜休息时身体也有少量乳酸在周转。",
      "考试关键句：看到“血乳酸堆积、阈值、中高强度可持续时长”｜答案核心是产生与清除失衡，不是乳酸中毒。",
    ]),
    visual("06", "运动判断：400 米和多次中等重量", "判断主供能系统不要只背项目名，先看强度和持续时间。", [
      "第一步看时间：0-10 秒先想 ATP-PCr；30 秒到 2 分钟先看糖酵解；2 分钟以上氧化系统占比越来越高。",
      "第二步看强度：强度越高，糖和 PCr 贡献越大｜同样 1 分钟，轻松走路和全力冲刺不是同一个供能逻辑。",
      "400 米为什么典型：持续 45-90 秒，中高强度且超过 PCr 主导窗口｜后段常靠忍受代谢压力维持速度。",
      "力量训练怎么判断：8-15 次多组、短休、后半组酸胀掉速，糖酵解参与高｜单次 1RM 则更偏 ATP-PCr。",
    ]),
    visual("07", "乳酸不是废物：它能回收再用", "乳酸是可运输、可再利用的燃料和强度信号，不是留在肌肉里几天的垃圾。", [
      "乳酸能去哪：它可被心脏、其他肌肉和肝脏利用｜这叫乳酸穿梭，说明它是能量周转的一部分。",
      "为什么不是废物：高强度时乳酸增加，代表糖酵解很忙｜它像物流包裹，可以被运走再利用，不是坏东西堆在肌肉里。",
      "腿酸别全怪乳酸：灼烧和疲劳还受氢离子、无机磷、离子环境、神经输出影响｜延迟性酸痛更主要和微损伤有关。",
      "恢复怎么理解：轻松走路或低强度骑车能促进血流和底物转运｜这不是排毒，而是帮身体更快处理代谢产物。",
    ]),
    visual("08", "训练安排：目标决定压力大小", "糖酵解训练能提升中高强度重复输出，但过多疲劳会干扰力量和爆发质量。", [
      "增肌怎么用：中等重量、多次重复、适度短休可制造代谢压力｜但机械张力仍是底盘，不能只追求酸胀感。",
      "体能怎么用：高强度间歇能训练糖酵解耐受和清除能力｜但恢复成本高，安排频率要看睡眠、总量和下次训练质量。",
      "力量日怎么避开：最大力量和爆发需要高速度、高神经输出｜如果糖酵解疲劳太早上来，后面会变成硬撑，不是练峰值。",
      "停组判断：速度明显下降、动作变形、局部酸到发力路线乱｜这时应延长休息、降负荷或结束高质量组。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay24Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识 · 有氧供能主课", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学", "耐力"] },
    { type: "image", eyebrow: "01", title: "先看图：燃料怎么进线粒体", lead: "先分清糖、脂肪和少量蛋白质怎么进入线粒体，再看三羧酸循环和电子传递链怎么把它们变成大量 ATP。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "氧化系统不是“慢”，是“久”", "它启动不如 ATP-PCr 快，但能在更长时间里稳定产 ATP，是耐力和恢复的底盘。", [
      "字面意思：氧化 = 依赖氧气把底物逐步氧化，主要在线粒体内完成。｜结果不是一次猛推，而是持续产出大量 ATP。",
      "大白话：像慢炖发电厂，出力不炸裂，但能一直供电。｜所以它更像长跑、长骑和长时间体能的底座。",
      "考试判断：出现 2 分钟以上、长时稳定、低到中等强度、线粒体、脂肪氧化时，优先想到氧化系统。",
      "训练意义：氧化能力好的人，恢复更稳、组间掉速更慢、长时间输出更可控。",
    ]),
    visual("03", "三羧酸循环：先拆燃料，再送电子", "Krebs 循环更像加工厂中段，把乙酰辅酶 A 继续处理成可供后续发电的电子载体。", [
      "糖路线：葡萄糖先经糖酵解变丙酮酸，再进入线粒体变成乙酰辅酶 A。｜这条路在中高强度时很关键。",
      "脂肪路线：脂肪酸先经 β 氧化，再汇入乙酰辅酶 A。｜所以脂肪并不是“直接烧掉”，也要先进线粒体处理。",
      "少量蛋白质：极端长时或能量压力下，氨基酸也可参与供能。｜但日常训练不该把它当主要目标。",
      "训练意义：线粒体酶活性、氧气运输和毛细血管越好，燃料处理越顺。",
    ]),
    visual("04", "电子传递链：氧气在最后接球", "真正大量 ATP 的地方在电子传递链。氧气做最终电子受体，整条链才能持续跑起来。", [
      "字面意思：电子从一系列载体转移到内膜上的蛋白复合体，最后交给氧气。｜这个过程建立梯度，再驱动 ATP 合酶工作。",
      "大白话：像把能量一层层传过去，最后让氧气把这条线接通。｜没有氧，整套发电会卡住。",
      "考试判断：题干出现“氧气、内膜、ATP 合酶、电子传递链”时，说明重点在氧化系统后半段。",
      "训练意义：心肺、血管、血红蛋白和肌内线粒体都在决定这段链条的效率。",
    ]),
    visual("05", "底物切换：不是二选一", "低强度时脂肪比例高，高强度时糖比例升高，但身体一直在混合用燃料。", [
      "低强度：脂肪比例更高，因为脂肪库存大、供能慢但耐用。｜慢走、轻松骑行、长时低心率活动常见。",
      "中等强度：糖和脂肪都明显参与。｜这也是很多稳态有氧最常见的区间。",
      "高强度：糖比例升高，因为糖供能更快。｜冲刺、节奏跑、爬坡间歇时更明显。",
      "误区提醒：脂肪供能比例高，不等于减脂一定更好。｜减脂看长期能量平衡和可坚持性。",
    ]),
    visual("06", "2 分钟以上：氧化系统越来越像主角", "前 10 秒看 ATP-PCr，30 秒到 2 分钟看糖酵解，2 分钟以上氧化系统占比通常越来越大。", [
      "时间线不是开关：三大系统一直同时工作，只是主导比例变。｜所以别把系统当互斥按钮。",
      "耐力项目怎么想：60 分钟骑行、半马、长距离慢跑，氧化系统是主角。｜它撑的是“久”，不是“猛”。",
      "力量恢复怎么想：组间恢复、训练后回落心率、第二天状态，也很依赖氧化能力。｜恢复慢的人常表现为后面组掉速更快。",
      "训练意义：基础有氧不是附属品，而是整个训练容量的底盘。",
    ]),
    visual("07", "乳酸阈：看产出和清除谁快", "乳酸阈是生产速度开始压过清除速度的转折区，不是“乳酸毒死你”的点。", [
      "低于阈值：乳酸产生和清除大体平衡。｜能稳定输出较久。",
      "接近阈值：呼吸急、腿有压，但还可控。｜适合阈值训练和节奏训练。",
      "高于阈值：堆积更快、掉速更快。｜强度再往上，持续时间会明显缩短。",
      "误区提醒：乳酸不是废物，它也能被心脏、肌肉和肝脏再利用。",
    ]),
    visual("08", "训练怎么用：不同目标，不同配速", "氧化训练不只是慢跑。你要的是可恢复的量、可持续的强度和明确的目标。", [
      "耐力：低到中等强度稳定跑、骑、划，累积线粒体和毛细血管适应。｜不是每次都冲到爆。",
      "减脂：用能坚持的有氧量加总消耗，再配合饮食制造能量缺口。｜不要只盯燃脂心率。",
      "力量：把有氧放在不干扰大重量的位置，帮助组间恢复和总训练容量。｜不是越多越好。",
      "康复：低冲击有氧如步行、椭圆机、轻松骑车，目标是恢复而不是刷疲劳。",
    ]),
    visual("09", "一眼判断题：先看谁在主导", "看到题干时，先抓时间、强度和场景，再决定答案是 PCr、糖酵解还是氧化系统。", [
      "0-10 秒爆发：ATP-PCr。｜单次 1RM、起跳、短冲刺先想到它。",
      "30 秒-2 分钟：糖酵解。｜400 米、HIIT、短间歇多组常见。",
      "2 分钟以上：氧化系统。｜长跑、长骑、稳态有氧、长时恢复。",
      "一句话收束：氧化系统不是慢吞吞，而是长时间稳定产能的主力。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay25Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识 · 强度时程主课", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学", "供能交互"] },
    { type: "image", eyebrow: "01", title: "先看整张图", lead: "先定位短时爆发、中高强度间歇和长时耐力，再看 EPOC 和氧债怎么接在后面。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "三大系统同时供能", "不是三套互斥机器，而是同一组引擎的不同档位。", [
      "看结论：ATP-PCr、糖酵解、氧化系统始终一起工作｜只是时间和强度一变，主导比例就变。",
      "看强度：越爆发，快系统越靠前｜1RM、起跑、跳起先想 ATP-PCr，再看糖酵解。",
      "看时长：时间一长，氧化系统越来越像主角｜2 分钟以上的持续输出更依赖它。",
      "看目标：爆发要保峰值，增肌可容忍部分疲劳｜耐力要保持续性和恢复底盘。",
    ]),
    visual("03", "强度越高，快系统越大", "高强度不是关掉氧化系统，而是把 ATP-PCr 和糖酵解推到前台。", [
      "0-10 秒：最典型是 ATP-PCr｜单次 1RM、短冲刺、起跳、举重爆发阶段都在这里。",
      "30 秒-2 分钟：糖酵解明显加入｜400 米、HIIT 冲刺段、多次中等重量都很典型。",
      "越爆发：动作时间越短、功率越高｜PCr 和糖比例越大，氧化系统仍参与但不主导。",
      "训练判断：想练峰值，就别把每组拖成喘爆｜想练密度，才去接受更多代谢压力。",
    ]),
    visual("04", "时间越长，氧化越接棒", "时间拉长后，身体会把更多 ATP 生产任务交给氧化系统。", [
      "2 分钟以上：氧化系统占比持续上升｜长跑、长骑、稳态有氧、长时恢复都靠它托底。",
      "底物切换：低强度更偏脂肪，高强度更偏糖｜但不是二选一，身体一直混合用燃料。",
      "恢复意义：氧化能力强，组间回落更快、第二组更稳｜训练容量更容易保住。",
      "误区：低强度不是没用｜它是在练耐久和恢复，不是只在烧热量。",
    ]),
    visual("05", "HIIT 让三系统一起上场", "冲刺段、恢复段、再冲刺，三个系统都被叫去干活。", [
      "冲刺段：ATP-PCr 和糖酵解猛拉起来｜功率高、代谢压力大，动作质量会很快受疲劳影响。",
      "恢复段：氧化系统开始接管回补｜帮忙恢复 PCr、搬运代谢产物、让下一轮能再发力。",
      "重复段：反复切换，让爆发、恢复和再爆发都变成训练刺激｜这才是间歇的核心价值。",
      "训练判断：HIIT 不是只练无氧｜冲、歇、再冲都算进来的多系统训练。",
    ]),
    visual("06", "EPOC 与氧债", "运动后还在喘，不是白喘；是在补运动中欠下的氧需求。", [
      "EPOC：运动后过量耗氧｜恢复时呼吸、心率、体温和代谢都还没回到静息。",
      "氧债：运动中欠下的氧，需要在结束后慢慢偿还｜这是恢复需求的形象说法。",
      "别误会：EPOC 不是减脂捷径｜真正结果还要看总消耗、训练量和饮食。",
      "训练感受：高强度后还喘一会儿很正常｜身体还在修复、回补和降温。",
    ]),
    visual("07", "训练里怎么排", "先定目标，再定强度、间歇和主供能系统。", [
      "爆发：高强度、极短时、长休息｜目标是保速度、保质量，而不是练到喘爆。",
      "增肌：中等强度、多组，允许部分糖酵解压力｜但机械张力仍是底盘。",
      "耐力：低到中等强度、较长时间｜持续累积氧化系统和恢复能力。",
      "减脂：优先可坚持的总量｜别只盯燃脂区，长期能量缺口更关键。",
    ]),
    visual("08", "一眼判断题", "先抓时长、强度、恢复，再决定答案该落在哪个系统。", [
      "问时长：越短越爆发，先看 ATP-PCr｜30 秒到 2 分钟再看糖酵解；2 分钟以上再看氧化。",
      "问恢复：休息太短，PCr 没补满｜下一组峰值、速度和动作稳定性会掉。",
      "问目标：力量爆发要保峰值｜密度训练能接受更多疲劳；耐力要保持续性。",
      "问概念：HIIT、EPOC、氧债都不是孤立名词｜它们是训练设计和供能比例的线索。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay26Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识 · 钙链条主课", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学", "神经肌肉"] },
    { type: "image", eyebrow: "01", title: "先看整条 E-C coupling 链", lead: "先定位神经末梢、ACh(acetylcholine，乙酰胆碱)、肌膜、T 管、肌浆网和钙离子，再看横桥为什么此时才抓得上肌动蛋白。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "神经肌肉接头：先把信号送到门口", "ACh 是 acetylcholine，中文叫乙酰胆碱；运动神经在接头处释放它，让肌膜先产生动作电位。", [
      "ACh 是乙酰胆碱：全称 acetylcholine，神经肌肉接头最关键的传话分子｜它从运动神经末梢释放到突触间隙｜作用是把神经端信号交给肌肉端。",
      "肌膜去极化：受体打开后，肌膜电位改变｜这一步把“神经来了”翻译成动作电位｜后面 T 管和肌浆网才会接上。",
      "训练判断：起跳、起杠、冲刺前几步都需要神经快速叫醒肌肉｜神经驱动慢，动作会先表现为启动慢和发力散｜不是只靠咬牙解决。",
      "常见误区：ACh 不是能量，也不是钙｜它更像门铃，按响后才进入后面的钙链条｜别把点火和真正收缩混在一起。",
    ]),
    visual("03", "T 管与 SR：把表面信号送进深处", "动作电位沿肌膜传播后，必须通过 T-tubule 深入肌纤维，才能触发肌浆网放钙。", [
      "T-tubule 是隧道：横管把肌膜表面的电信号带到肌纤维内部｜否则只有表层知道“该收缩了”｜深层纤维响应会慢半拍。",
      "SR 是钙仓库：肌浆网储存 Ca2+，收到 T 管信号后释放钙｜这一步把电信号变成化学开关｜收缩许可从这里开始。",
      "为什么要同步：大肌群不是几根纤维单独发力｜越多纤维同时接到信号，动作越干脆｜峰值输出越容易上来。",
      "训练判断：疲劳后动作变慢、抖、发力断续｜可能不只是意志问题｜也可能是膜兴奋性、钙释放和离子环境变差。",
    ]),
    visual("04", "钙开锁：横桥位点才暴露", "Ca2+ 结合肌钙蛋白后，原肌球蛋白移位，肌球蛋白横桥才有机会抓住肌动蛋白。", [
      "钙不是燃料：真正直接供能仍是 ATP｜Ca2+ 的角色是打开横桥结合位点｜让收缩具备发生条件。",
      "肌钙蛋白像锁芯：钙一结合，构象改变｜原肌球蛋白从阻挡位置移开｜肌动蛋白可被横桥抓住。",
      "回填 Day6：肌丝滑行需要横桥循环｜但没有钙先开门，横桥循环连第一抓都难发生｜这就是 Day6 伏笔。",
      "训练判断：高强度后半段掉速，可能和 Ca2+ 释放/回收有关｜H+、K+ 等局部环境也会干扰兴奋和横桥效率。",
    ]),
    visual("05", "运动单位：神经按包叫醒肌纤维", "一个 α 运动神经元加上它支配的所有肌纤维，就是一个运动单位。", [
      "不是单根调度：身体不会一根肌纤维一根肌纤维点名｜一个运动单位被激活，它支配的肌纤维一起响应｜这才是募集基本单位。",
      "小单位用途：阈值低、控制细、耐疲劳｜站姿控制、轻重量技术练习、低力输出常先用它｜适合省电和稳定。",
      "大单位用途：阈值高、力量大、易疲劳｜接近最大力量、爆发跳跃、重冲刺时更需要它上场｜成本高但输出强。",
      "训练判断：肌肉变大只是硬件，神经能否高效募集是软件｜新手早期力量增长常先来自这里｜不是每次都先看围度。",
    ]),
    visual("06", "大小原则：小先上，大后上", "低力任务先募集小运动单位；负荷或发力需求升高后，高阈值大单位才逐步加入。", [
      "顺序不是随机：身体优先用省电、耐疲劳的小单位｜任务够重或够快时，再把高阈值大单位拉进来｜这是大小原则核心。",
      "轻重量也有机会：轻重量做到接近力竭时，小单位疲劳｜身体会逐渐补叫更大单位｜但来得更晚、疲劳成本更高。",
      "重重量更直接：大重量、高速度意图、爆发动作更快要求大单位参与｜但需要更长休息保持质量｜否则后面组变成硬撑。",
      "考试判断：题干出现 Size Principle、小单位、I 型、II 型、募集顺序｜优先记“小先大后”｜别答成大单位先上。",
    ]),
    visual("07", "去募集：力降时大单位先退", "当外部负荷变轻或输出需求下降时，高阈值大运动单位通常先退出。", [
      "降档逻辑：不需要大力时，身体会优先撤掉成本更高、易疲劳的大单位｜保留更省电的小单位维持控制｜输出按需求下降。",
      "动作例子：深蹲最难点需要大单位帮忙｜站稳后负荷需求下降，大单位会逐步退出｜不是肌肉突然关机。",
      "训练判断：爆发训练要避免太早疲劳｜否则高阈值单位上场时间短｜后面变成硬撑而不是练峰值。",
      "常见误区：募集不是只会增加｜去募集也是神经控制｜关系到落杠、减速和动作结束时的平稳度。",
    ]),
    visual("08", "一条链串起来", "从神经信号到横桥结合，再到运动单位募集，这些不是碎知识，而是一套输出系统。", [
      "接头负责点火：神经末梢释放 ACh(乙酰胆碱)，肌膜去极化｜信号先从神经传到肌肉门口｜这一步出错，后面都接不上。",
      "钙链负责开门：T 管把信号送深，SR 放钙｜钙让原肌球蛋白移开，横桥位点开放｜横桥循环才有起点。",
      "募集负责派人：小单位先上，大单位后上；力下降时大单位先退｜这决定输出规模和控制质量｜也是 Day27 前置知识。",
      "训练收束：动作慢、抖、掉速快时，同时想神经驱动、钙处理、局部疲劳和动作技术｜不只怪肌肉小。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay27Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "denseCompact", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识 · 神经控制主课", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学", "神经肌肉"] },
    { type: "image", eyebrow: "01", title: "先看募集、频率和效率", lead: "先定位 S、FR、FF 三类运动单位，再看力量升高时身体怎么从招更多单位，切到提高放电频率和同步化。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "三类运动单位：耐久到爆发", "运动单位不是只有大小差别，还同时决定收缩速度、抗疲劳能力和适合承担的任务。", [
      "S 单位：慢收缩、抗疲劳、力量小｜像省电小灯，适合站姿控制、轻松有氧、轻重量技术练习｜看到 low force / endurance，优先想它。",
      "FR 单位：快收缩、较抗疲劳、力量中等｜像中档发动机，能做较快但还能反复输出｜中等强度多次、间歇训练常用到。",
      "FF 单位：快收缩、易疲劳、力量最大｜像涡轮爆发，适合冲刺、跳跃、重重量关键发力｜强但耗得快，不能长期维持。",
      "判断开关：先看任务要“稳多久”还是“爆多强”｜别把所有快单位混成一类；FR 偏平衡，FF 偏峰值。",
    ]),
    visual("03", "募集：低力先叫小单位", "大小原则说的是低阈值小单位先上，高阈值大单位后上；这让身体用最省成本方式完成任务。", [
      "低力任务：站立、慢走、空杆热身，先靠小单位｜输出细、稳定、耐疲劳，不需要动用高成本大单位。",
      "力量升高：重量变大、速度意图更强、越接近力竭，身体逐步叫上 FR 和 FF｜参与单位更多，输出规模变大。",
      "轻重量问题：轻重量不是永远招不到大单位｜但要做到足够接近力竭，大单位才更可能加入，疲劳代价也更高。",
      "训练判断：练最大力量和爆发，用重负荷或高速意图更直接｜练技术/康复，低负荷先把小单位控制练稳。",
    ]),
    visual("04", "频率编码：同一单位发得更密", "力量继续升高时，身体不只招更多单位，还会让已募集单位用更高频率放电。", [
      "字面意思：频率编码 = rate coding｜指同一个运动神经元每秒发放动作电位的次数，脉冲从稀疏变密。",
      "大白话：像教练口令从慢拍变成密集鼓点｜同一组运动单位没换人，但命令更密，肌肉张力叠得更高。",
      "训练例子：1RM 起杠、冲刺第一步、纵跳起跳、重重量粘滞点，都需要高频神经输出｜频率掉了，动作会慢、散、卡。",
      "常见误区：力量提升不只靠招更多单位｜同一单位发得更密，也能把输出继续推高。",
    ]),
    visual("05", "同步化：一起放电，峰值更高", "训练能让更多运动单位在时间上更协调地放电，尤其影响爆发力和瞬间峰值输出。", [
      "字面意思：同步化 = 多个运动单位在同一时间窗口放电｜不是永久一起开火，而是关键瞬间更整齐。",
      "大白话：像划船一起下桨｜每个人都用力还不够，还要同一拍子用力，合力才集中。",
      "训练例子：纵跳起跳、抓举拉起、冲刺蹬地、1RM 突破粘滞点｜都吃“同时上力”的能力。",
      "训练判断：用重负荷、爆发意图、充分休息、低疲劳高质量重复｜动作变形后继续堆量，会把同步质量练差。",
    ]),
    visual("06", "神经肌肉效率：少浪费，多集中", "训练后主动肌更会出力，协同肌更会帮忙，拮抗肌和无关肌肉少抢戏。", [
      "字面意思：同样任务下，用更少多余激活完成更有效输出｜主动肌出力更集中，协同肌帮得更准。",
      "大白话：像团队分工变清楚｜主力推进，辅助稳定，反方向拉扯和无关紧张减少，能量浪费更少。",
      "动作例子：新手弯举常耸肩、前臂乱紧、身体后仰｜熟练者更能把张力集中到肱二头肌，肩和躯干只做稳定。",
      "训练判断：技术练习、节奏控制、合适 cue、渐进负荷，能让力量更干净｜早期力量增长常来自效率提升。",
    ]),
    visual("07", "训练应用：重、快、稳，各练不同神经能力", "神经控制不是抽象概念，它决定你该用大重量、爆发速度、接近力竭，还是技术练习。", [
      "最大力量：高负荷、低到中等次数、长休息｜目标是高阈值募集 + 高频率编码，每组保技术和速度。",
      "爆发训练：中低负荷到高负荷都可用，但必须有速度意图｜目标是快速募集和同步化，不是练到酸爆。",
      "肌肥大：中等负荷也能招到大单位，但常要接近力竭｜只用轻重量随便做几下，不等于高阈值刺激。",
      "康复与技术：低负荷先练效率和控制｜主动肌要清楚，协同代偿要减少，动作路径要稳定。",
    ]),
    { type: "comparison", eyebrow: "08", title: "别混：运动单位 vs 肌纤维", lead: "S、FR、FF 讲的是神经控制的一支“队伍”；I、IIa、IIx 讲的是单根肌纤维的表型。" },
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay21Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "一张图串起第3周", lead: "先找外力和力臂，再看动作模式、核心稳定、力量输出和组织耐受。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "力矩与杠杆：先看力臂", "同样重量不一定同样难；外力作用线离关节越远，关节要抵抗的力矩越大。", [
      "力矩 = 力 × 力臂：力臂是关节支点到外力作用线的垂直距离｜不是骨头长度，也不是看起来离得远不远。",
      "训练里先缩短无效力臂：硬拉让杠铃贴近小腿和大腿，能减少腰髋要抵抗的外力矩｜动作更稳不是“偷力”。",
      "人体多为第三类杠杆：肌肉力点常在支点和阻力之间｜机械上更费力，但换来更快、更大幅度和更精细的远端运动。",
    ]),
    visual("03", "动作模式：先认任务，再找肌肉", "推、拉、深蹲、铰链、箭步、旋转和携带，是不同受力任务，不是肌肉名称清单。", [
      "分析顺序固定：先看关节怎么动，再看哪些肌肉跨过关节并制造同方向力矩｜最后看谁在稳定躯干和关节。",
      "深蹲和铰链别混：深蹲是髋膝踝共同下沉；铰链以髋主导折叠｜两者都练下肢，但受力分配不同。",
      "开链与闭链看远端：远端自由是开链，远端固定是闭链｜不要只背动作名称，要看当下任务。",
    ]),
    visual("04", "脊柱与核心：把位置稳住", "核心主业不是反复卷腹，而是在负荷和动作中守住中立脊柱、腹压和对线。", [
      "中立脊柱是可控区间：保留自然曲度，让压力分散到椎体、椎间盘、韧带和肌肉｜不是把腰背硬掰成直线。",
      "腹内压像内部压力罐：吸气撑开腹壁和侧腰，帮助躯干抗压和抗弯｜腰带只能提供外壁，不能替代主动支撑。",
      "核心四抗是任务单：抗伸展、抗屈曲、抗旋转、抗侧屈｜深蹲、硬拉和划船先守住位置，再增加负荷。",
    ]),
    visual("05", "力量输出：神经、肌肉与速度", "力量上限由神经募集、肌肉横截面积、关节角度、收缩速度和离心控制共同决定。", [
      "新手力量先涨常是神经适应：募集更多运动单位，发放更快更稳，动作协同更好｜不一定先长出明显肌肉。",
      "长度和速度会改产力：肌肉太短或太长都不占便宜；向心越快，通常越难产生大力｜重重量自然更慢。",
      "离心和 SSC 要分清：离心是被拉长但仍发力的刹车；SSC 是快速预拉伸后立刻缩短｜爆发训练重速度和质量，不靠疲劳堆量。",
    ]),
    visual("06", "损伤机制：峰值、累计与叠加", "风险不只看疼不疼。先分单次峰值还是重复累计，再看剪切、压缩、张力和扭转怎样叠加。", [
      "急性损伤看峰值：踩空、落地、变向、碰撞或一次错误发力，让组织承受超过当下耐受的力量｜题干常出现突然和当场。",
      "过度使用看累计：跑量、跳跃量、负荷或频率加得太快，恢复跟不上｜单次不重，也会把组织逐步推向超载。",
      "高风险常是组合题：膝内扣、减速、足固定后身体旋转、疲劳下落地变硬，会让张力、扭转和剪切一起上升。",
    ]),
    visual("07", "易混点：抓住判断开关", "考试别靠整段死记；每组概念都有一个优先判断开关。", [
      "开链 vs 闭链：看远端是否固定｜远端固定就是闭链，远端自由就是开链。",
      "向心 / 离心 / 等长：看肌肉长度变化｜向心变短，离心被拉长但仍发力，等长不变长短。",
      "三类杠杆：看支点、阻力、动力谁在中间｜人体最常见第三类；遇到“力量先于肌肥大”优先想到神经适应。",
    ]),
    visual("08", "训练决策：先路径，再剂量", "动作质量、负荷剂量、恢复和疲劳管理，共同决定训练能否变成适应而非磨损。", [
      "先让力走对路：杠铃贴身、躯干稳定、髋膝踝对线清楚｜技术修正不是为了好看，而是管理力矩和组织受力。",
      "剂量决定主要适应：重量、次数、速度和组间休息要服务目标｜增肌看张力和训练量，爆发看速度和低疲劳，耐力看重复输出。",
      "把停止信号写进计划：速度明显掉、动作反复变形、疼痛改样或局部先失控时，降负荷、停组或改动作｜别硬凑次数。",
    ]),
    visual("09", "第3周复盘：一条训练判断链", "外力变成力矩，力矩落到动作模式，再由核心、神经肌肉和组织耐受共同决定表现与风险。", [
      "看动作：先找支点、外力作用线和力臂，再判断哪段关节力矩最大。",
      "看表现：再看动作模式、核心稳定、神经驱动和肌肉能力，找出最先限制输出的环节。",
      "看风险：最后核对负荷进阶、疲劳、恢复和组织耐受，让计划逐步缩小外部负荷与当前能力的差距。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay20Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看图，再看概念", lead: "先分清四种力，再把急性、过度使用、ACL 风险和动作筛查串起来。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "急性 vs 过度使用", "损伤不只分疼不疼，还要分单次峰值过载，还是重复负荷累计。", [
      "急性损伤看峰值：落地、变向、碰撞或一次错误发力，让组织承受超过当下上限的力量｜常见表现是扭伤、拉伤、撞击伤，题干会出现突然、踩空、落地或碰撞。",
      "过度使用看累计：单次训练可能不重，但跑量、跳跃次数、负荷和频率增长太快，恢复跟不上｜肌腱炎、应力反应和慢性小腿痛常见于这个逻辑。",
      "训练判断先问时间线：突然发生优先找峰值和动作失控；慢慢变重优先找训练量、恢复和重复代偿。",
    ]),
    visual("03", "剪切与压缩：关节面怎么受力", "剪切是层间滑移，压缩是两端挤压；两者常在关节和脊柱里叠加。", [
      "剪切力像两层扑克牌错开推：它平行于组织面，让相邻结构发生相对滑移｜膝、腰、肩在不稳轨迹里承受水平错位时，剪切风险会上升。",
      "压缩力像按海绵：适量压缩能促进骨和软骨适应，但过量、偏斜或疲劳下反复压在一点，会让局部压力集中｜深蹲、硬拉、跳跃落地都需要管理压缩力。",
      "关键不是禁止受力，而是让受力可控：髋膝踝对线、中立脊柱、腹压和落地吸收，都是把力分散到更安全路径。",
    ]),
    visual("04", "张力与扭转：拉长和旋转最怕失控", "张力拉开组织，扭转拧动组织；变向、落地和高速离心里最常见。", [
      "张力像拉橡皮筋：肌肉、肌腱和韧带被拉长时承受拉应力｜高速冲刺、突然拉伸或大量离心训练，都可能让张力超过组织耐受。",
      "扭转像拧毛巾：一端固定，另一端继续旋转，组织就会承受扭矩｜鞋底抓地太牢、脚固定但身体转向，是变向损伤常见背景。",
      "这两种力常一起出现：踝扭伤、膝内扣和腰椎负重旋转，通常不是单一方向受力，而是张力、扭转、剪切叠加。",
    ]),
    visual("05", "ACL风险：膝内扣 + 减速 + 旋转", "前交叉韧带像膝关节里的安全带，最怕高速失控组合题。", [
      "ACL 限制胫骨相对股骨过度前移和旋转：当落地或变向时膝盖向内塌，安全带会承受更大拉力和扭力｜这不是单纯“膝盖前移”的问题。",
      "高风险组合常是非接触的：足固定在地面、身体继续旋转、髋控制不足、膝内扣、疲劳后落地变硬｜几个因素叠加时，风险明显上升。",
      "训练重点是减速和对线：练单腿落地、侧向刹车、臀中肌和腘绳肌强化，让髋膝踝在高速动作里仍能保持可控。",
    ]),
    visual("06", "动作筛查：找代偿，不是贴诊断", "筛查能发现风险线索，但不能替代医生诊断，也不能预测所有损伤。", [
      "筛查看身体怎么分配力：深蹲看脊柱、骨盆、膝、足；弓步看左右控制；单腿平衡看足踝和髋稳定；落地看吸收冲击和减速能力。",
      "发现代偿要转成训练任务：活动度不足补活动度，控制差补稳定，负荷太快就降量，疲劳导致走样就调整休息｜不要只写“动作不好”。",
      "筛查结果要结合情境：同一个膝内扣，轻负荷热身和高速变向风险不同；新手学习期和疲劳后半段也不能用同一标准粗暴判断。",
    ]),
    visual("07", "训练决策：先管剂量，再管动作", "损伤风险来自组织耐受和外部负荷的差距，计划要让差距慢慢缩小。", [
      "负荷进阶别只看肌肉感觉：肌肉可能恢复快，肌腱、骨和关节适应更慢｜突然加跑量、跳跃量或离心量，是过度使用常见起点。",
      "技术修正要服务受力路径：杠铃贴身减少腰椎外力矩，落地柔和分散冲击，膝盖对准脚尖减少不必要扭转和剪切｜动作不是为了好看，是为了让力走对路。",
      "疼痛下降不等于完全恢复：回归训练要看动作质量、负荷耐受、次日反应和专项速度，而不是只看今天能不能忍。",
    ]),
    visual("08", "疲劳与恢复：后半段最容易变形", "很多风险不是第一组出现，而是在速度、注意力和稳定性下降后放大。", [
      "疲劳会让动作控制变差：膝内扣、圆背、落地过硬、核心松掉，常在训练后半段出现｜这时相同重量会变成更高风险刺激。",
      "恢复决定组织能不能变强：睡眠、营养、休息日和负荷波动，让微损伤有机会修复成适应｜恢复不足时，训练刺激会更像磨损。",
      "停止信号要写进计划：速度明显下降、疼痛改变、姿势反复崩、局部先失控时，应降负荷、停组或改动作，而不是硬凑次数。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay19Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看图，再看概念", lead: "后面提到的神经、横截面积、长度、速度和 SSC，都先在这张图里定位。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "神经因素：新手力量先涨", "力量不是只看肌肉大小。刚开始训练时，神经系统先学会把现有肌肉用得更好。", [
      "运动单位像“发力小队”：一个 alpha 运动神经元和它支配的全部肌纤维，合起来才叫一个运动单位｜当身体需要更大力量时，神经系统会募集更多运动单位，让更多肌纤维同时收缩。",
      "发放频率决定张力能否叠加：同一运动单位收到神经信号越频繁，单次收缩越容易连续叠加｜这样肌肉能在短时间维持更高、更平稳的张力，而不是断断续续地发力。",
      "动作协调让力量真正传出去：主动肌负责发力，协同肌帮忙，稳定肌负责固定关节和躯干｜三者配合更好时，深蹲和卧推路径更稳，新手力量往往会先因此上升。",
    ]),
    visual("03", "横截面积：肌肉量是力量底盘", "肌肉越粗，通常能并联更多肌纤维，潜在最大产力越高。", [
      "横截面积越大，不是“单根纤维更蛮力”：它代表可以并排收缩的肌纤维数量更多，因而潜在产力更高｜可以把它理解为更多人同时拉同一根绳，而不是某一个人突然变得更强。",
      "肌肉大不等于立刻举得更重：更大的横截面积只提高力量潜力，不会自动变成动作成绩｜神经驱动、动作技术、关节角度和力臂，也决定这份力量能不能真正用到杠铃上。",
      "长期力量不能只练技术：训练早期可以主要靠神经适应进步，但这种进步不会无限持续｜想继续提高力量上限，仍要用渐进超负荷、足够训练量和恢复把肌肉底盘做大。",
    ]),
    visual("04", "长度-张力：不太短也不太长", "肌肉处在合适长度时，肌动蛋白和肌球蛋白重叠最理想，张力最大。", [
      "肌肉不是越缩短或越拉长越能发力：太短时粗细肌丝会拥挤，太长时又难以形成足够横桥｜处在合适长度时，有效横桥数量最多，所以产生的主动张力最大。",
      "同一动作每个角度，难度可能不同：关节角度一变，肌肉长度和外部阻力的力臂都会变化｜这就是为什么弯举、深蹲或卧推在中段、底部、顶部会有不同发力感。",
      "全幅度训练不是形式要求：它让肌肉在更多长度区间练习产生张力，也减少只会某个角度发力的问题｜专项力量训练还要额外补上比赛动作中最容易卡住的角度。",
    ]),
    visual("05", "力-速度曲线：快举轻，慢顶重", "向心收缩速度越快，可产生的力量通常越小；重负荷自然会变慢。", [
      "向心收缩越快，横桥越难充分工作：肌肉缩短太快时，横桥来不及大量结合并完成有效拉动｜因此向心速度越高，肌肉能主动产生的力量通常越低。",
      "轻重量能快推，重重量只能慢顶：这是力和速度相互制约的正常表现，不代表动作一定做错｜当外部负荷接近当下最大能力时，向心速度自然会变慢。",
      "爆发训练看速度，不只看累不累：目标是每一次都快速且动作稳定地输出力量，而不是把自己练到精疲力尽｜当速度明显下降时，应停组或延长休息，避免训练变成普通疲劳堆量。",
    ]),
    visual("06", "离心收缩：刹车时更能扛", "肌肉被拉长时仍主动发力，通常能承受高于向心收缩的张力。", [
      "离心不是“没在发力”：外力正在把肌肉拉长，但肌肉仍主动产生张力来控制动作速度｜下楼、下放杠铃或下放引体时，肌肉做的就是类似刹车的工作。",
      "为什么下放常比推起更能扛重量：离心阶段的横桥和被动弹性结构会共同承担张力｜因此离心收缩通常能承受比向心收缩更大的外部负荷，是力-速度曲线的特殊一段。",
      "离心刺激强，不能一口气堆太多：慢速下放和北欧腿弯举都会带来较高张力，也更容易出现延迟性酸痛｜新手、恢复不足或赛前训练时，应从少量开始逐步增加。",
    ]),
    visual("07", "SSC：先压弹簧，再快速放开", "牵张-缩短循环是快速离心预拉伸后，立刻接向心发力。", [
      "SSC 不是两个分开的动作：Stretch 指肌肉快速被拉长，Shortening 指紧接着立刻缩短发力｜关键不是先下再上，而是两个阶段之间转换足够快。",
      "快速预拉伸能借到两种帮助：肌腱和肌肉的弹性组织会储存一部分弹性势能，像压缩后的弹簧｜牵张反射也会让神经兴奋短暂提高，帮助随后向心阶段输出更多力量。",
      "跳跃、冲刺、变向都在用 SSC：如果停顿太久，储存的弹性势能会消散；疲劳后接触地面变软，帮助也会变少｜完整三阶段与训练方法留到 Day 76 增强式统一讲。",
    ]),
    visual("08", "肌耐力：看能否一直高质量输出", "肌耐力不是单次最大力量，而是重复收缩中维持张力和动作质量能力。", [
      "肌耐力看“续航”，不只看意志力：局部能源补给、代谢副产物处理、毛细血管和线粒体功能，都会影响肌肉在高次数中能否持续收缩｜所以同样重量，有人能稳定完成 20 次，有人很快就掉速。",
      "动作越经济，后半组越不容易乱：以俯卧撑为例，轨迹稳定、核心不塌时，力量会持续留在胸肩三头｜如果身体不断扭动或塌腰，体力会浪费在代偿上，而不是目标肌持续工作。",
      "高次数训练也有质量底线：中低负荷、高次数、短休息常用于练肌耐力，但每一次仍要保持动作标准｜当姿势明显变形时，应先降难度或休息，而不是为了数字硬凑次数。",
    ]),
    visual("09", "同一动作，变量决定练到什么", "深蹲、卧推、划船只是工具；负荷、次数、速度和休息，决定主要训练适应。", [
      "最大力量优先练峰值输出：通常使用较高负荷、较低次数和更充分的组间休息，让每次尝试都能保持技术｜重点是神经输出、动作路径，以及专项动作中最容易卡住的位置。",
      "增肌与耐力不是只看次数：增肌更看足够训练量、目标肌张力和接近力竭；肌耐力更看重复输出、短休息和抗疲劳｜同一个动作做几次，并不能单独决定训练效果。",
      "爆发训练不能练成疲劳堆量：目标是高速度、低疲劳条件下的快速发力，因此每组不应拖得太长｜一旦动作速度明显下降，就该停止或增加休息，避免变成普通体能消耗。",
    ]),
    visual("10", "训练判断：先找限制因素", "卡重量或高次数掉速时，先判断问题在神经、肌肉量、角度、速度还是疲劳。", [
      "大重量卡住，先别只加肌肉量：先看动作路径是否稳定、神经输出是否充分，以及是否总在同一关节角度失败｜这些没处理好时，单纯加肌肉也未必能立刻提高杠铃成绩。",
      "高次数崩盘，不一定是“不够狠”：先检查局部代谢能力、组间休息、动作经济性和核心稳定性，找出最先失控的环节｜再针对性调整负荷、次数、休息或动作难度。",
      "把考试线索串起来：“力量先于肌肥大”通常联想神经适应；“离心更大力”联想力-速度曲线的离心段｜题干出现快速离心接向心、跳跃或变向时，则联想 SSC。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay18Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看图，再看概念", lead: "后面提到的位置、结构和动作，都先在这张图里找一遍。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "中立脊柱：自然曲度不是直线", "中立位是可控受力区间，不是把腰背硬掰成一条直线。", [
      "判断标准：保留颈椎、胸椎、腰椎自然曲度；不过度弓腰，也不过度圆背。",
      "力学意义：像把弓形桥放回设计角度，让压力分散到椎体、椎间盘、韧带和肌肉。",
      "训练提示：深蹲、硬拉、划船先看肋骨和骨盆是否叠住，再看腰椎是否被负重拉弯。",
    ]),
    visual("03", "腰椎骨盆节律：髋动，腰别抢", "躯干前屈时，髋关节和骨盆应承担主要折叠，腰椎负责保持可控。", [
      "髋铰链：骨盆向前倾，髋向后坐，腰椎保持接近中立。",
      "常见代偿：髋动不了时，腰椎会用圆背替代髋折叠。",
      "纠正顺序：先练无负重髋铰链，再加壶铃或杠铃，不急着上大重量。",
    ]),
    visual("04", "椎间盘受压：怕的是压偏叠加", "椎间盘能承压，但大重量下反复屈曲、旋转和疲劳会让压力更集中。", [
      "正中受压：中立负重时，椎间盘压力更容易上下分散。",
      "弯曲受压：负重屈曲像斜着按果冻垫，压力更容易被挤向一侧。",
      "考试线索：NSCA/NASM 常把负重屈曲、旋转和疲劳放在损伤风险情境中考。",
    ]),
    visual("05", "腹内压：核心像压力罐", "腹内压由呼吸、膈肌、腹横肌、腹斜肌和骨盆底共同建立。", [
      "压力结构：膈肌像上盖，骨盆底像底部，腹壁像罐壁，腰背肌像后侧支架。",
      "大白话：吸气撑住不是把肚子吸瘪，而是把腹部和侧腰向四周撑开。",
      "训练用途：深蹲、硬拉、农夫走都靠腹压抵抗脊柱被压弯或扭转。",
    ]),
    visual("06", "举重腰带：给腹压一面墙", "腰带不是替核心发力，而是给腹部一个可以主动撑住的外壁。", [
      "适用场景：接近大重量、低次数、深蹲硬拉等轴向或髋铰链负荷高的动作。",
      "不必依赖：技术学习、轻重量、核心控制训练、需要自然呼吸节奏的耐力训练。",
      "使用要点：腰带紧到能撑住但还能吸气，把腹部和侧腰向腰带四周撑开。",
    ]),
    visual("07", "核心四抗：目标是稳住位置", "核心常见任务是抵抗外力改变脊柱，而不是一直制造卷腹动作。", [
      "抗伸展：抵抗腰被拉成反弓；例：平板支撑、死虫、健腹轮退阶。",
      "抗屈曲：抵抗背被重量压圆；例：硬拉、农夫走、前蹲。",
      "抗旋转与侧屈：抵抗身体被拉转或拉歪；例：Pallof press、单侧提壶铃走、侧桥。",
    ]),
    visual("08", "动作策略：先控路径再加重量", "保护脊柱不是怕负重，而是让杠铃路径、髋关节、腹压和中立位配合。", [
      "硬拉：杠铃贴近小腿，髋向后，背保持长，缩短外力线到腰椎的力臂。",
      "训练含义：新手先学无负重髋铰链和呼吸支撑，再上杠铃。",
      "停止信号：进阶者也要用速度下降、姿势明显变形、腹压掉掉判断是否该停本组。",
    ]),
    visual("09", "训练里怎么用：把稳定变成决策", "脊柱核心生物力学帮你判断动作、负重、退阶和停止时机。", [
      "增肌：俯身划船、罗马尼亚硬拉先稳住脊柱，否则目标肌没练够，腰椎先疲劳。",
      "减脂与体能：循环训练疲劳时更容易腹压掉、圆背和耸肩，动作质量优先。",
      "康复与考试：腰背不适先练呼吸支撑、死虫、鸟狗和髋铰链；看到腰带、腹内压、中立脊柱就联想核心稳定。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay17Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findCoverVisual(lesson.day) || findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先看图，再看概念", lead: "后面提到的位置、结构和动作，都先在这张图里找一遍。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "七大动作模式：先分类再分析", "动作模式不是肌肉部位，而是身体主要在解决哪类力学任务。", [
      "推 / 拉：阻力离开身体或靠近身体；例：俯卧撑、卧推、划船、引体。",
      "深蹲 / 铰链 / 箭步：下肢三大基础；深蹲髋膝踝协同，铰链髋主导，箭步偏单腿控制。",
      "旋转 / 携带：躯干转动或抗偏移；例：药球转体、绳索伐木、农夫走、单侧提壶铃走。",
    ]),
    visual("03", "开放链：远端自由移动", "手或脚没有固定在地面或稳定表面上，动作更容易集中在某个关节。", [
      "判断标准：看远端是否自由；手端或脚端能在空间里移动，就是开放链。",
      "常见例子：坐姿腿屈伸、腿弯举、哑铃弯举、侧平举、坐姿推胸。",
      "训练用途：局部强化、找目标肌感受、康复后期单关节控制；但不能完全替代整体传力。",
    ]),
    visual("04", "闭合链：远端固定传力", "脚或手固定后，身体围绕固定点移动，关节协同和稳定要求更高。", [
      "字面意思：链条末端固定；深蹲时脚固定，俯卧撑时手固定。",
      "大白话：脚像钉在地上，身体在脚上方升降、转移和调整。",
      "为什么重要：更接近日常站立、跑跳、上楼、搬物，能暴露膝内扣、足弓塌陷、骨盆失控。",
    ]),
    visual("05", "稳定与不稳定：别把晃当高级", "不稳定表面会增加控制需求，但通常降低最大力量输出。", [
      "稳定地面：更多资源用于产力，适合力量、增肌、爆发输出。",
      "不稳定表面：先防晃再发力，核心和小稳定肌参与上升，主力输出下降。",
      "使用场景：热身、平衡、康复控制可用；大重量主项优先稳定地面。",
    ]),
    visual("06", "三类肌肉角色：主攻、帮忙、稳住", "先按动作目标分角色，不要只看哪块肌肉酸。", [
      "主动肌：主要制造目标动作；卧推看胸大肌，划船看背阔肌、菱形肌和斜方肌中下部。",
      "协同肌：帮助完成动作；卧推有前三角和肱三头，划船有肱二头，深蹲有臀大肌和腘绳肌协同。",
      "稳定肌：让关节和躯干不乱晃；卧推靠肩袖和肩胛稳定肌，深蹲靠核心与髋外展肌，农夫走靠核心抗侧屈。",
    ]),
    visual("07", "动作分析流程：四步判断", "碰到任何动作，按同一顺序看，就能把“哪里难”说清楚。", [
      "看关节：哪几个关节在动，方向是什么；卧推是肩水平内收 + 肘伸。",
      "找肌肉：谁能制造主要运动，谁只是协同，谁负责稳定。",
      "看外力：画外力线、力臂和支点，判断力矩压力落在哪个关节。",
    ]),
    visual("08", "动作模式筛查：先找失控环节", "代偿不是只有拉伸能解决，要判断活动度、稳定性、力量和负荷。", [
      "深蹲膝内扣：先看髋外展外旋控制、足踝路线、负荷是否过高。",
      "硬拉圆背：先看髋铰链模式、核心抗屈能力、杠铃是否离身体太远。",
      "划船耸肩：先看肩胛下压后缩、重量是否过大、手臂是否抢工。",
    ]),
    visual("09", "训练里怎么用：把分类变成决策", "动作模式帮你选动作、排计划、找代偿，也帮你解释不同器械差异。", [
      "增肌：开放链补局部，闭合链练整体；腿屈伸补股四头，深蹲练下肢协同。",
      "减脂与体能：推、拉、深蹲、铰链、携带组合，动员更多肌群，提高训练密度。",
      "康复与纠错：早期用开放链精确强化，后期回闭合链整合；遇到膝内扣、圆背、耸肩先找原因再加难度。",
    ]),
  ].map((slide) => {
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function buildDay16Slides(lesson) {
  const visual = (eyebrow, title, lead, points) => ({ type: "dense", eyebrow, title, lead, visualTitle: title, points, fill: [] });
  return [
    { type: "cover", kicker: `Day ${lesson.day} · ${lesson.cert}`, title: lesson.title, subtitle: "NSCA / NASM 双证健身知识", image: assetDataUrl(findThumbnail(lesson.day)), chips: [lesson.phase, "运动科学"] },
    { type: "image", eyebrow: "01", title: "先用二头弯举定位三件事", lead: "蓝点是肘关节支点；绿色虚线是肱二头肌拉力方向；绿色实线 dF 与蓝色虚线 dR 是两条力臂。", image: assetDataUrl(findLessonImage(lesson.day)), points: [], fill: [] },
    visual("02", "杠杆三要素：先定位旋转问题", "所有关节动作都可先问：绕哪里转、谁在拉、什么在阻碍它转。", ["支点：关节旋转轴；弯举里是肘关节。", "力点：肌肉经肌腱把力施加到骨头的位置；不是整块肌肉。", "阻力点：外部重量或身体段重量作用的位置；弯举里看哑铃与前臂重量。"]),
    visual("03", "三类杠杆：只看谁在中间", "分类看支点、力点、阻力点相对位置，不看动作名称。", ["第一类：力-支-阻；支点居中，例子是颈部伸展。", "第二类：支-阻-力；阻力居中，提踵常是此类，偏力量优势。", "第三类：支-力-阻；力点居中，二头弯举典型，人体最常见。"]),
    visual("04", "力矩：先找外力作用线", "力矩 = 力 × 力臂。力臂不是骨头长度，是支点到作用线的最短垂直距离。", ["作用线：哑铃重力始终竖直向下，这条竖线就是阻力作用线。", "作垂线：从肘关节向该竖线作垂线，得到阻力臂 dR。", "难点区间：同一哑铃，前臂接近水平时 dR 更长，肘屈阻力矩更大。"]),
    visual("05", "二头弯举：典型第三类杠杆", "肱二头肌肌腱附着在桡骨近端，拉力从附着点朝肩部，力点位于支点与哑铃之间。", ["支点与阻力：肘关节是支点；哑铃与前臂重量构成阻力。", "力的方向：二头肌拉力指向肩部，沿肌腱/肱二头肌线向近端，不顺着前臂。", "为什么费力：肌肉力臂很短，肌肉张力必须远大于手中外部重量对应的力。"]),
    visual("06", "机械优势：为何人体多费力", "机械优势 = 肌肉力臂 ÷ 阻力臂。", ["第二类：常有较大机械优势，适合把大重量抬起。", "第三类：肌肉力臂短、阻力臂长，机械优势常小于 1。", "代价与收益：肌肉更费力；远端移动更快、幅度更大、控制更细。"]),
    visual("07", "同一哑铃，为何 90 度附近更难", "重力方向不变，关节角度变了，阻力臂就变了。", ["手臂垂下：重力线几乎穿过肘关节，阻力臂接近 0。", "前臂水平：重力线离肘关节最远，阻力矩最大。", "训练含义：自由重量动作有难点区间；重量相同不等于全程难度相同。"]),
    visual("08", "技术调整：管理无效力臂", "以罗马尼亚硬拉为例：杠铃离髋越远，髋与腰背必须抵抗的外部力矩越大。", ["杠铃路径：贴近小腿和大腿，可缩短杠铃重力线到髋的水平距离。", "不是偷力：这是减少无效力臂，让髋伸肌更有效处理负荷。", "技术变量：握距、站距、负重位置都在改变不同关节的力臂分配。"]),
    visual("09", "动作分析流程：四步判断", "碰到任何训练动作，按同一顺序看，就能把“感觉难”说清楚。", ["定支点：找主要旋转关节。", "画外力：画作用线，再画支点到作用线的垂距。", "找肌肉：确定主动肌拉力方向与肌肉力臂。", "作调整：比较哪侧力矩变大，再改角度、负重位置或器械。"]),
  ].map((slide) => {
    if (slide.eyebrow === "03") {
      const requestedVisual = path.join("xhs", "day16", "ai-visuals", "visual-02-three-lever-classes.png");
      return { ...slide, visualImage: assetDataUrl(requestedVisual) };
    }
    const visualPath = slide.visualTitle ? findAiVisual(lesson.day, slide.eyebrow, slide.title) : "";
    return visualPath ? { ...slide, visualImage: assetDataUrl(visualPath) } : slide;
  });
}

function slideHtml(slide, lesson) {
  const image = slide.image
    ? `<img class="hero-img" src="${slide.image}" alt="">`
    : `<div class="hero-placeholder"></div>`;
  const lessonFigure = slide.image
    ? `<div class="hero lesson-figure" style="background-image:url('${slide.image}')"></div>`
    : `<div class="hero"><div class="hero-placeholder"></div></div>`;
  const visual = slide.visualImage ? `<div class="visual"><img src="${slide.visualImage}" alt=""></div>` : "";
  const cards = (slide.cards || [])
    .map((card) => `<div class="card"><h3>${card.title}</h3><p>${card.body}</p></div>`)
    .join("");
  const bullets = (slide.points || [])
    .map((point) => {
      const { head, body } = splitPoint(point);
      const bodyItems = (body || "")
        .split("｜")
        .map((item) => item.trim())
        .filter((item) => item && !/^[。！？；…]+$/.test(item))
        .map((item) => `<i>${item}</i>`)
        .join("");
      return `<li><b>${head}</b>${bodyItems ? `<span>${bodyItems}</span>` : ""}</li>`;
    })
    .join("");
  const steps = (slide.steps || []).map((step, index) => `<li><em>${index + 1}</em><span>${step}</span></li>`).join("");
  const notes = (slide.notes || []).map((note) => `<li>${note}</li>`).join("");
  const chips = (slide.chips || ["健身知识", lesson.cert, "收藏复习"]).map((chip) => `<span>${chip}</span>`).join("");
  const focus = (slide.focus || lesson.points.slice(0, 4).map((point) => splitPoint(point).head))
    .map((item) => `<span>${item}</span>`)
    .join("");
  const fill = (slide.fill || []).map((item) => `<span>${item}</span>`).join("");
  const comparisonImage = slide.type === "comparison"
    ? assetDataUrl("xhs/day27/ai-visuals/visual-09-motor-unit-vs-fiber.png")
    : "";
  const comparison = slide.type === "comparison" ? `<section class="comparison">
    <div class="comparison-visual"><img src="${comparisonImage}" alt="运动单位与单根肌纤维示意"></div>
    <div class="compare-grid">
      <div class="compare-card unit-card"><span class="compare-tag">控制单位</span><h2>S / FR / FF</h2><p class="unit-formula"><b>S 运动单位</b><span>=</span><em>1 个低阈值 α 运动神经元<br>+ 一组 I 型肌纤维</em></p><strong>看谁先募集、谁更耐疲劳、谁输出更大。</strong></div>
      <div class="compare-card fiber-card"><span class="compare-tag">组织表型</span><h2>I / IIa / IIx</h2><p><b>肌纤维</b> = 单根肌肉细胞，按 MyHC、收缩速度与代谢特征分类。</p><strong>看单根纤维慢快、氧化与糖酵解特征。</strong></div>
    </div>
    <div class="mapping"><h2>常用近似映射 <span>不是严格等号</span></h2><div class="mapping-row"><b class="s">S</b><i>≈</i><strong>I 型慢氧化</strong></div><div class="mapping-row"><b class="fr">FR</b><i>≈</i><strong>IIa 型快氧化糖酵解</strong></div><div class="mapping-row"><b class="ff">FF</b><i>≈</i><strong>IIx 型快糖酵解</strong></div></div>
    <p class="compare-note">人体可有 I/IIa、IIa/IIx 混合纤维；IIb 主要是动物研究中的分类。</p>
  </section>` : "";

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:700}.brand b{color:#111113}.brand b span{color:#ff5a1f}.kicker,.eyebrow{color:#ff5a1f;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.cover{display:flex;flex-direction:column}.cover h1{margin:26px 0 14px;font-size:66px;line-height:1.14;letter-spacing:-.025em}.cover-body{flex:1;display:flex;flex-direction:column}.cover-copy{margin-top:128px}.daymark{color:#ff5a1f;font-size:32px;font-weight:900}.subtitle{font-size:28px;color:#71717a}.cover .hero{height:520px;margin:24px 0 0}.hero{margin:22px 0 22px;border:1px solid #e4e4e7;border-radius:28px;background:#fff;overflow:hidden;height:540px;display:grid;place-items:center}.hero-img{width:100%;height:100%;object-fit:cover}.cover .hero-img{object-fit:contain}.hero-placeholder{width:82%;height:64%;border-radius:28px;background:repeating-linear-gradient(135deg,#f4f4f5 0 18px,#ececef 18px 36px)}.chips{display:flex;flex-wrap:wrap;gap:16px;margin-top:18px}.chips span,.tag{display:inline-flex;align-items:center;border-radius:999px;padding:12px 18px;font-size:24px;font-weight:800}.chips span:nth-child(1),.tag.green{background:rgba(74,222,128,.18);color:#15803d}.chips span:nth-child(2),.tag.blue{background:rgba(96,165,250,.18);color:#2563eb}.chips span:nth-child(3),.tag.orange{background:rgba(255,90,31,.1);color:#ff5a1f}.content{padding-top:34px}.eyebrow{font-size:26px}.content h1{margin:14px 0 16px;font-size:56px;line-height:1.12;letter-spacing:-.015em}.lead{margin:0 0 20px;color:#52525b;font-size:27px;line-height:1.62}.visual{height:300px;margin:0 0 18px;border:0;border-radius:24px;background:transparent;overflow:hidden;box-shadow:none}.visual img{width:100%;height:100%;object-fit:contain;display:block;mix-blend-mode:multiply}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:0 0 16px}.card{border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:18px 20px;box-shadow:0 8px 20px rgba(0,0,0,.03);min-height:168px}.card h3{margin:0 0 8px;font-size:24px;line-height:1.26}.card p{margin:0;color:#52525b;font-size:21px;line-height:1.6;white-space:pre-line}.bullets{display:grid;gap:12px;margin:0;padding:0;list-style:none}.bullets li{border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:18px 24px;box-shadow:0 8px 20px rgba(0,0,0,.03)}.bullets b{display:block;margin-bottom:7px;font-size:27px;line-height:1.35}.bullets span{display:grid;gap:5px;color:#52525b;font-size:22px;line-height:1.58}.bullets span i{display:block;position:relative;padding-left:20px;font-style:normal}.bullets span i:before{content:"";position:absolute;left:0;top:.78em;width:7px;height:7px;border-radius:999px;background:#60a5fa}.denseCompact .visual{height:240px;margin-bottom:12px}.denseCompact .content h1,.content.denseCompact h1{font-size:52px}.denseCompact .lead,.content.denseCompact .lead{font-size:25px;line-height:1.52;margin-bottom:12px}.denseCompact .bullets{gap:9px}.denseCompact .bullets li{padding:13px 22px;border-radius:20px}.denseCompact .bullets b{font-size:25px;margin-bottom:4px}.denseCompact .bullets span{font-size:20px;line-height:1.42;gap:2px}.steps{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0 0 16px;padding:0;list-style:none}.steps li{min-height:168px;border:1px solid #e4e4e7;border-radius:24px;background:#fff;padding:22px;display:flex;flex-direction:column;justify-content:space-between}.steps em{display:grid;place-items:center;width:54px;height:54px;border-radius:17px;background:#ff5a1f;color:#fff;font-size:27px;font-style:normal;font-weight:900}.steps span{font-size:31px;font-weight:900;line-height:1.3}.notes{display:grid;gap:11px;margin:0;padding:0;list-style:none}.notes li{border-radius:18px;background:rgba(96,165,250,.13);padding:14px 17px;color:#2563eb;font-size:23px;font-weight:800;line-height:1.48}.fill{position:absolute;left:72px;right:72px;bottom:108px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.fill:empty{display:none}.fill span{border:1px solid #dbeafe;border-radius:22px;background:linear-gradient(135deg,rgba(255,90,31,.08),rgba(96,165,250,.12));padding:18px 16px;text-align:center;color:#27272a;font-size:24px;font-weight:900;line-height:1.25}.comparison{margin-top:16px}.comparison-visual{height:270px;margin:0 0 14px;display:flex;align-items:center;justify-content:center;overflow:hidden}.comparison-visual img{width:100%;height:100%;object-fit:contain;display:block}.compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.compare-card{min-height:215px;border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:23px;box-shadow:0 8px 20px rgba(0,0,0,.03)}.compare-tag{display:inline-block;border-radius:999px;padding:7px 12px;background:#fff0ea;color:#ff5a1f;font-size:19px;font-weight:900}.fiber-card .compare-tag{background:#eaf2ff;color:#2563eb}.compare-card h2{margin:12px 0 8px;font-size:31px;line-height:1.15}.compare-card p{margin:0;color:#52525b;font-size:20px;line-height:1.42}.unit-formula{display:grid;grid-template-columns:auto 26px 1fr;gap:7px;align-items:start}.unit-formula b{font-size:21px;color:#111113;white-space:nowrap}.unit-formula span{font-size:22px;font-weight:900;color:#ff5a1f;text-align:center}.unit-formula em{font-style:normal;font-size:17px;line-height:1.35;color:#52525b}.compare-card strong{display:block;margin-top:12px;color:#111113;font-size:18px;line-height:1.35}.mapping{margin-top:12px;border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:21px 23px}.mapping h2{margin:0 0 13px;font-size:27px}.mapping h2 span{font-size:18px;font-weight:700;color:#71717a}.mapping-row{display:grid;grid-template-columns:74px 34px 1fr;align-items:center;min-height:40px;border-top:1px solid #eef0f2;font-size:22px}.mapping-row b{font-size:25px}.mapping-row i{font-style:normal;color:#9aa1ad}.mapping-row strong{font-size:22px}.mapping-row .s{color:#15803d}.mapping-row .fr{color:#2563eb}.mapping-row .ff{color:#7c3aed}.compare-note{margin:12px 0 0;border-left:5px solid #ff5a1f;background:#fff7f3;padding:10px 14px;color:#52525b;font-size:18px;line-height:1.4}.image .hero{height:1035px;margin:8px 0 8px;background:transparent;border:0;box-shadow:none;overflow:hidden;display:grid;place-items:center}.lesson-img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block}.lesson-figure{background-size:contain;background-position:center;background-repeat:no-repeat}.image .bullets,.image .cards,.image .fill,.image .footer{display:none}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;align-items:center;color:#a1a1aa;font-size:24px;font-weight:700}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:0 0 24px}
</style>
</head>
<body>
<main class="page ${slide.type === "cover" ? "cover" : `content ${slide.type}`}">
  <div class="brand"><b>健身<span>学习</span></b><span>${lesson.cert}</span></div>
  ${
    slide.type === "cover"
      ? `<div class="cover-body"><div class="hero">${image}</div><div class="cover-copy"><div class="daymark">Day ${lesson.day}</div><h1>${slide.title}</h1><p class="subtitle">${slide.subtitle}</p><div class="chips">${chips}</div></div></div>`
      : `<div class="rule"></div><div class="eyebrow">${slide.eyebrow}</div><h1>${slide.title}</h1><p class="lead">${slide.lead}</p>${slide.type === "comparison" ? comparison : slide.type === "image" ? lessonFigure : visual}${slide.type === "comparison" ? "" : slide.cards ? `<div class="cards">${cards}</div>` : slide.type === "denseSteps" ? `<ul class="steps">${steps}</ul><ul class="notes">${notes}</ul>` : `<ul class="bullets">${bullets}</ul>`}<div class="fill">${fill}</div>`
  }
  <div class="footer"><span>Day ${lesson.day}/112</span><span>每天复习 1 个知识点</span></div>
</main>
</body>
</html>`;
}

function titleText(lesson) {
  const aliases = new Map([[12, "核心肌群四抗"], [28, "能量系统与神经肌肉"], [30, "FITT-VP与ACSM指南"], [31, "PAR-Q+与医学筛查"]]);
  const cleanTitle = aliases.get(Number(lesson.day)) || lesson.title.replace(/[（(].*?[）)]/g, "").replace(/【.*?】/g, "");
  const base = `Day${lesson.day}｜${cleanTitle}`;
  return base.length <= 20 ? base : base.slice(0, 20);
}

function captionText(lesson) {
  const pageUrl = lessonPageUrl(lesson.day);
  if (lesson.day === 28) {
    return `今天复盘：能量系统与神经肌肉

把训练中的“燃料、点火、输出”串成一条链：
1. 三套能量系统始终并行；时长和强度决定谁贡献更多。
2. 组间休息在补 PCr、神经驱动和局部环境，决定下一组质量。
3. E-C coupling：神经信号经 ACh、肌膜/T 管，触发肌浆网释放 Ca2+。
4. Ca2+ 结合肌钙蛋白，移开原肌球蛋白，横桥才开始抓拉；回收 Ca2+ 后收缩停止。
5. 运动单位按小到大募集；负荷、速度意图和接近力竭会让更多高阈值单位加入。

训练里：爆发训练保速度和长休息；增肌训练保张力和动作控制；HIIT 观察冲刺后能否恢复输出。${pageUrl ? `

完整学习页：${pageUrl}` : ""}`;
  }
  return `今天学：${lesson.title}

核心线索：
${lesson.points.map((point, index) => `${index + 1}. ${point}`).join("\n")}${pageUrl ? `

完整学习页：${pageUrl}` : ""}`;
}

function tagsText(lesson) {
  const certTags = lesson.cert === "双证" ? "#NSCA #NASM" : `#${lesson.cert}`;
  return `#健身教练 ${certTags} #运动科学 #健身知识 #解剖学 #力量训练 #健身学习`;
}

function lessonImageHtml(lesson, slide) {
  const image = assetDataUrl(findLessonImage(lesson.day) || findThumbnail(lesson.day));
  const omitLead = lesson.day === 16;
  const omitHeading = lesson.day === 28;
  const figureTop = lesson.day === 28 ? 150 : lesson.day === 27 ? 420 : omitLead ? 280 : 338;
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:700}.brand b{color:#111113}.brand b span{color:#ff5a1f}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:34px 0 24px}.eyebrow{color:#ff5a1f;font-size:26px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.title{margin:14px 0 16px;font-size:56px;line-height:1.12;letter-spacing:-.015em}.lead{margin:0;color:#52525b;font-size:27px;line-height:1.62}.figure{position:absolute;left:72px;right:72px;top:${omitLead ? 280 : 338}px;bottom:92px;background-image:url('${image}');background-size:contain;background-repeat:no-repeat;background-position:center}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;align-items:center;color:#a1a1aa;font-size:24px;font-weight:700}
</style>
</head>
<body>
<main class="page">
  <div class="brand"><b>健身<span>学习</span></b><span>${lesson.cert}</span></div>
  ${omitHeading ? "" : `<div class="rule"></div><div class="eyebrow">${slide.eyebrow}</div><h1 class="title">${slide.title}</h1>${omitLead ? "" : `<p class="lead">${slide.lead}</p>`}`}
  <div class="figure" style="top:${figureTop}px"></div>
  <div class="footer"><span>Day ${lesson.day}/112</span><span>每天复习 1 个知识点</span></div>
</main>
</body>
</html>`;
}

async function renderPackage(lesson) {
  const outDir = path.join(ROOT, "xhs", `day${String(lesson.day).padStart(2, "0")}`);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "title.txt"), titleText(lesson));
  fs.writeFileSync(path.join(outDir, "caption.txt"), captionText(lesson));
  fs.writeFileSync(path.join(outDir, "tags.txt"), tagsText(lesson));

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
  const slides = buildSlides(lesson);
  for (let index = 0; index < slides.length; index += 1) {
    const html = index === 1 ? lessonImageHtml(lesson, slides[index]) : slideHtml(slides[index], lesson);
    await page.setContent(html, { waitUntil: "networkidle" });
    const filename = index === 0 ? "cover.png" : `slide-${String(index).padStart(2, "0")}.png`;
    await page.screenshot({ path: path.join(outDir, filename), fullPage: false });
  }
  await browser.close();
  return outDir;
}

async function main() {
  const { day } = parseArgs();
  const lesson = parseSyllabus().find((item) => item.day === day);
  if (!lesson) throw new Error(`Day ${day} not found in fitness_syllabus.md`);
  const outDir = await renderPackage(lesson);
  console.log(outDir);
}

main().catch((error) => {
  const message = String(error && (error.stack || error.message || error));
  if (/MachPortRendezvous|bootstrap_check_in|Permission denied|Target page/.test(message)) {
    try {
      const { day } = parseArgs();
      const fallback = path.join(ROOT, "scripts", "render-xhs-fallback.py");
      execFileSync("python3", [fallback, `--day=${day}`], { stdio: "inherit", cwd: ROOT });
      console.log(path.join(ROOT, "xhs", `day${String(day).padStart(2, "0")}`));
      return;
    } catch (fallbackError) {
      console.error(fallbackError);
      process.exit(1);
    }
  }
  console.error(error);
  process.exit(1);
});
