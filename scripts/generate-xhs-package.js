const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
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

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:700}.brand b{color:#111113}.brand b span{color:#ff5a1f}.kicker,.eyebrow{color:#ff5a1f;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.cover{display:flex;flex-direction:column}.cover h1{margin:26px 0 14px;font-size:66px;line-height:1.14;letter-spacing:-.025em}.cover-body{flex:1;display:flex;flex-direction:column}.cover-copy{margin-top:128px}.daymark{color:#ff5a1f;font-size:32px;font-weight:900}.subtitle{font-size:28px;color:#71717a}.cover .hero{height:520px;margin:24px 0 0}.hero{margin:22px 0 22px;border:1px solid #e4e4e7;border-radius:28px;background:#fff;overflow:hidden;height:540px;display:grid;place-items:center}.hero-img{width:100%;height:100%;object-fit:cover}.cover .hero-img{object-fit:contain}.hero-placeholder{width:82%;height:64%;border-radius:28px;background:repeating-linear-gradient(135deg,#f4f4f5 0 18px,#ececef 18px 36px)}.chips{display:flex;flex-wrap:wrap;gap:16px;margin-top:18px}.chips span,.tag{display:inline-flex;align-items:center;border-radius:999px;padding:12px 18px;font-size:24px;font-weight:800}.chips span:nth-child(1),.tag.green{background:rgba(74,222,128,.18);color:#15803d}.chips span:nth-child(2),.tag.blue{background:rgba(96,165,250,.18);color:#2563eb}.chips span:nth-child(3),.tag.orange{background:rgba(255,90,31,.1);color:#ff5a1f}.content{padding-top:34px}.eyebrow{font-size:26px}.content h1{margin:14px 0 16px;font-size:56px;line-height:1.12;letter-spacing:-.015em}.lead{margin:0 0 20px;color:#52525b;font-size:27px;line-height:1.62}.visual{height:300px;margin:0 0 18px;border:0;border-radius:24px;background:transparent;overflow:hidden;box-shadow:none}.visual img{width:100%;height:100%;object-fit:contain;display:block;mix-blend-mode:multiply}.bullets{display:grid;gap:12px;margin:0;padding:0;list-style:none}.bullets li{border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:18px 24px;box-shadow:0 8px 20px rgba(0,0,0,.03)}.bullets b{display:block;margin-bottom:7px;font-size:27px;line-height:1.35}.bullets span{display:grid;gap:5px;color:#52525b;font-size:22px;line-height:1.58}.bullets span i{display:block;position:relative;padding-left:20px;font-style:normal}.bullets span i:before{content:"";position:absolute;left:0;top:.78em;width:7px;height:7px;border-radius:999px;background:#60a5fa}.steps{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0 0 16px;padding:0;list-style:none}.steps li{min-height:168px;border:1px solid #e4e4e7;border-radius:24px;background:#fff;padding:22px;display:flex;flex-direction:column;justify-content:space-between}.steps em{display:grid;place-items:center;width:54px;height:54px;border-radius:17px;background:#ff5a1f;color:#fff;font-size:27px;font-style:normal;font-weight:900}.steps span{font-size:31px;font-weight:900;line-height:1.3}.notes{display:grid;gap:11px;margin:0;padding:0;list-style:none}.notes li{border-radius:18px;background:rgba(96,165,250,.13);padding:14px 17px;color:#2563eb;font-size:23px;font-weight:800;line-height:1.48}.fill{position:absolute;left:72px;right:72px;bottom:108px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.fill:empty{display:none}.fill span{border:1px solid #dbeafe;border-radius:22px;background:linear-gradient(135deg,rgba(255,90,31,.08),rgba(96,165,250,.12));padding:18px 16px;text-align:center;color:#27272a;font-size:24px;font-weight:900;line-height:1.25}.image .hero{height:1035px;margin:8px 0 8px;background:transparent;border:0;box-shadow:none;overflow:hidden;display:grid;place-items:center}.lesson-img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block}.lesson-figure{background-size:contain;background-position:center;background-repeat:no-repeat}.image .bullets,.image .fill,.image .footer{display:none}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;align-items:center;color:#a1a1aa;font-size:24px;font-weight:700}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:0 0 24px}
</style>
</head>
<body>
<main class="page ${slide.type === "cover" ? "cover" : `content ${slide.type}`}">
  <div class="brand"><b>Fitness<span>Study</span></b><span>${lesson.cert}</span></div>
  ${
    slide.type === "cover"
      ? `<div class="cover-body"><div class="hero">${image}</div><div class="cover-copy"><div class="daymark">Day ${lesson.day}</div><h1>${slide.title}</h1><p class="subtitle">${slide.subtitle}</p><div class="chips">${chips}</div></div></div>`
      : `<div class="rule"></div><div class="eyebrow">${slide.eyebrow}</div><h1>${slide.title}</h1><p class="lead">${slide.lead}</p>${slide.type === "image" ? lessonFigure : visual}${slide.type === "denseSteps" ? `<ul class="steps">${steps}</ul><ul class="notes">${notes}</ul>` : `<ul class="bullets">${bullets}</ul>`}<div class="fill">${fill}</div>`
  }
  <div class="footer"><span>Day ${lesson.day}/112</span><span>每天复习 1 个知识点</span></div>
</main>
</body>
</html>`;
}

function titleText(lesson) {
  const aliases = new Map([[12, "核心肌群四抗"]]);
  const cleanTitle = aliases.get(lesson.day) || lesson.title.replace(/[（(].*?[）)]/g, "").replace(/【.*?】/g, "");
  const base = `Day${lesson.day}｜${cleanTitle}`;
  return base.length <= 20 ? base : base.slice(0, 20);
}

function captionText(lesson) {
  return `今天学：${lesson.title}

核心线索：
${lesson.points.map((point, index) => `${index + 1}. ${point}`).join("\n")}`;
}

function tagsText(lesson) {
  const certTags = lesson.cert === "双证" ? "#NSCA #NASM" : `#${lesson.cert}`;
  return `#健身教练 ${certTags} #运动科学 #健身知识 #解剖学 #力量训练 #健身学习`;
}

function lessonImageHtml(lesson, slide) {
  const image = assetDataUrl(findLessonImage(lesson.day) || findThumbnail(lesson.day));
  const omitLead = lesson.day === 16;
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
  <div class="brand"><b>Fitness<span>Study</span></b><span>${lesson.cert}</span></div>
  <div class="rule"></div>
  <div class="eyebrow">${slide.eyebrow}</div>
  <h1 class="title">${slide.title}</h1>
  ${omitLead ? "" : `<p class="lead">${slide.lead}</p>`}
  <div class="figure"></div>
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
