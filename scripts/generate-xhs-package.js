const fs = require("fs");
const path = require("path");
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
  const prefix = `visual-${eyebrow}`;
  const files = fs.readdirSync(dir).filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).sort();
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
        .filter(Boolean)
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
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:700}.brand b{color:#111113}.brand b span{color:#ff5a1f}.kicker,.eyebrow{color:#ff5a1f;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.cover{display:flex;flex-direction:column}.cover h1{margin:26px 0 14px;font-size:66px;line-height:1.14;letter-spacing:-.025em}.cover-body{flex:1;display:flex;flex-direction:column}.cover-copy{margin-top:128px}.daymark{color:#ff5a1f;font-size:32px;font-weight:900}.subtitle{font-size:28px;color:#71717a}.cover .hero{height:520px;margin:24px 0 0}.hero{margin:22px 0 22px;border:1px solid #e4e4e7;border-radius:28px;background:#fff;overflow:hidden;height:540px;display:grid;place-items:center}.hero-img{width:100%;height:100%;object-fit:cover}.cover .hero-img{object-fit:contain}.hero-placeholder{width:82%;height:64%;border-radius:28px;background:repeating-linear-gradient(135deg,#f4f4f5 0 18px,#ececef 18px 36px)}.chips{display:flex;flex-wrap:wrap;gap:16px;margin-top:18px}.chips span,.tag{display:inline-flex;align-items:center;border-radius:999px;padding:12px 18px;font-size:24px;font-weight:800}.chips span:nth-child(1),.tag.green{background:rgba(74,222,128,.18);color:#15803d}.chips span:nth-child(2),.tag.blue{background:rgba(96,165,250,.18);color:#2563eb}.chips span:nth-child(3),.tag.orange{background:rgba(255,90,31,.1);color:#ff5a1f}.content{padding-top:34px}.eyebrow{font-size:26px}.content h1{margin:14px 0 16px;font-size:56px;line-height:1.12;letter-spacing:-.015em}.lead{margin:0 0 20px;color:#52525b;font-size:27px;line-height:1.62}.visual{height:300px;margin:0 0 18px;border:0;border-radius:24px;background:transparent;overflow:hidden;box-shadow:none}.visual img{width:100%;height:100%;object-fit:contain;display:block}.bullets{display:grid;gap:12px;margin:0;padding:0;list-style:none}.bullets li{border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:18px 24px;box-shadow:0 8px 20px rgba(0,0,0,.03)}.bullets b{display:block;margin-bottom:7px;font-size:27px;line-height:1.35}.bullets span{display:grid;gap:5px;color:#52525b;font-size:22px;line-height:1.58}.bullets span i{display:block;position:relative;padding-left:20px;font-style:normal}.bullets span i:before{content:"";position:absolute;left:0;top:.78em;width:7px;height:7px;border-radius:999px;background:#60a5fa}.steps{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0 0 16px;padding:0;list-style:none}.steps li{min-height:168px;border:1px solid #e4e4e7;border-radius:24px;background:#fff;padding:22px;display:flex;flex-direction:column;justify-content:space-between}.steps em{display:grid;place-items:center;width:54px;height:54px;border-radius:17px;background:#ff5a1f;color:#fff;font-size:27px;font-style:normal;font-weight:900}.steps span{font-size:31px;font-weight:900;line-height:1.3}.notes{display:grid;gap:11px;margin:0;padding:0;list-style:none}.notes li{border-radius:18px;background:rgba(96,165,250,.13);padding:14px 17px;color:#2563eb;font-size:23px;font-weight:800;line-height:1.48}.fill{position:absolute;left:72px;right:72px;bottom:108px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.fill:empty{display:none}.fill span{border:1px solid #dbeafe;border-radius:22px;background:linear-gradient(135deg,rgba(255,90,31,.08),rgba(96,165,250,.12));padding:18px 16px;text-align:center;color:#27272a;font-size:24px;font-weight:900;line-height:1.25}.image .hero{height:1035px;margin:8px 0 8px;background:transparent;border:0;box-shadow:none;overflow:hidden;display:grid;place-items:center}.lesson-img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block}.lesson-figure{background-size:contain;background-position:center;background-repeat:no-repeat}.image .bullets,.image .fill,.image .footer{display:none}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;align-items:center;color:#a1a1aa;font-size:24px;font-weight:700}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:0 0 24px}
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
  const maxLength = 20;
  const dayPrefix = `Day${lesson.day}｜`;
  const aliases = new Map([
    ["主要肌群-核心肌群与McGill核心功能分类(完整4项首讲)", "核心肌群四抗"],
  ]);
  const normalizedTitle = lesson.title
    .replace(/[（(].*?[）)]/g, "")
    .replace(/NSCA高频/g, "")
    .trim();
  const shortTitle = aliases.get(lesson.title) || aliases.get(normalizedTitle) || normalizedTitle;
  const room = Math.max(1, maxLength - Array.from(dayPrefix).length);
  return `${dayPrefix}${Array.from(shortTitle).slice(0, room).join("")}`;
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
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:700}.brand b{color:#111113}.brand b span{color:#ff5a1f}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:34px 0 24px}.eyebrow{color:#ff5a1f;font-size:26px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.title{margin:14px 0 16px;font-size:56px;line-height:1.12;letter-spacing:-.015em}.lead{margin:0;color:#52525b;font-size:27px;line-height:1.62}.figure{position:absolute;left:72px;right:72px;top:338px;bottom:92px;background-image:url('${image}');background-size:contain;background-repeat:no-repeat;background-position:center}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;align-items:center;color:#a1a1aa;font-size:24px;font-weight:700}
</style>
</head>
<body>
<main class="page">
  <div class="brand"><b>Fitness<span>Study</span></b><span>${lesson.cert}</span></div>
  <div class="rule"></div>
  <div class="eyebrow">${slide.eyebrow}</div>
  <h1 class="title">${slide.title}</h1>
  <p class="lead">${slide.lead}</p>
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
  console.error(error);
  process.exit(1);
});
