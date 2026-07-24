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
    throw new Error("Usage: node scripts/generate-xhs-review-package.js --day=7");
  }
  return { day };
}

const day7Deck = {
  day: 7,
  title: "艾宾浩斯复习区",
  subtitle: "今天 + 次日 + 第3天 + 第7天",
  groups: [
    {
      label: "R0 今日回忆",
      day: 7,
      topic: "研究方法与统计学",
      questions: [
        {
          q: "同一名教练连续三天测同一客户皮褶，结果非常接近。主要说明什么？",
          options: ["A. 信度较好", "B. 效度一定很高", "C. 能证明客户体脂下降", "D. 能推出训练计划有效"],
          answer: "A",
          explain: "结果接近说明重复测量一致，是信度；稳定不等于测得准。",
        },
        {
          q: "横断面研究发现“喝补剂的人肌肉量更高”。最稳妥结论是？",
          options: ["A. 补剂一定导致增肌", "B. 补剂摄入和肌肉量存在相关", "C. 不需要控制训练经验", "D. p 值显著就适合所有客户"],
          answer: "B",
          explain: "横断面通常只能说明相关，不能直接推出因果。",
        },
      ],
      scenario: {
        q: "场景题：客户问“这篇补剂研究说喝的人肌肉更多，我是不是也该买？”你先问哪 3 个问题？",
        answer: "先问研究设计是不是实验/RCT；再问有没有控制训练经验、总蛋白、热量和睡眠；最后看结局指标是不是实际增肌，而不是只看相关或 p 值。",
      },
    },
    {
      label: "R1 次日复习",
      day: 6,
      topic: "肌丝滑行理论",
      questions: [
        {
          q: "肌小节缩短时，真正发生的是哪件事？",
          options: ["A. 肌丝本身变短", "B. 肌动蛋白和肌球蛋白相互滑动", "C. A 带明显变短", "D. 肌束直接缩短"],
          answer: "B",
          explain: "肌丝长度基本不变，细肌丝向肌小节中心滑动，Z 线靠近。",
        },
        {
          q: "横桥循环里，ATP 最关键作用是什么？",
          options: ["A. 让肌球蛋白头部解离并复位", "B. 直接拉短肌动蛋白", "C. 直接打开结合位点", "D. 让关节开始运动"],
          answer: "A",
          explain: "ATP 让横桥解离并准备下一次抓拉；钙离子负责暴露结合位点。",
        },
      ],
      scenario: {
        q: "场景题：客户做等长平板支撑，关节没明显运动。你怎么用肌丝滑行解释“肌肉仍在工作”？",
        answer: "关节不动不代表横桥不循环。肌球蛋白仍持续抓拉肌动蛋白，用 ATP 维持张力，只是外部长度变化被姿势和负荷抵消。",
      },
    },
    {
      label: "R2 第3天复习",
      day: 5,
      topic: "动作平面与运动轴",
      questions: [
        {
          q: "二头弯举主要发生在哪个平面，绕哪条轴？",
          options: ["A. 矢状面，绕额状轴", "B. 额状面，绕矢状轴", "C. 水平面，绕垂直轴"],
          answer: "A",
          explain: "肘屈伸主要在矢状面完成，矢状面动作绕额状轴。",
        },
        {
          q: "哑铃侧平举主要属于哪类动作？",
          options: ["A. 矢状面屈伸", "B. 额状面外展", "C. 水平面旋转"],
          answer: "B",
          explain: "手臂从身体侧方远离中线，是肩外展，主要在额状面。",
        },
      ],
      scenario: {
        q: "场景题：客户做侧平举时总说“手往上抬”。你怎么把它改成平面和轴的表达？",
        answer: "侧平举主要是肩外展，发生在额状面，绕矢状轴。用这个表达能更准确判断动作方向和代偿。",
      },
    },
    {
      label: "R3 第7天复习",
      day: 1,
      topic: "骨学基础",
      questions: [
        {
          q: "股骨最准确分类是？",
          options: ["A. 长骨", "B. 扁骨", "C. 短骨"],
          answer: "A",
          explain: "股骨长度明显大于宽度，承担承重和杠杆功能，是典型长骨。",
        },
        {
          q: "哪些属于骨的功能？",
          options: ["A. 支撑身体", "B. 保护内脏", "C. 储存钙磷", "D. 主动收缩产生关节运动"],
          answer: "A/B/C",
          explain: "主动收缩是肌肉功能；骨提供支撑、保护、储矿物和杠杆。",
        },
      ],
      scenario: {
        q: "场景题：客户问“骨头只是支架吗？”你用 3 点解释骨在训练里的作用。",
        answer: "骨提供支撑和杠杆，保护重要器官，还储存钙磷。动作产生来自肌肉收缩，但力量需要通过骨杠杆传递。",
      },
    },
  ],
};

const day8Deck = {
  day: 8,
  title: "艾宾浩斯复习区",
  subtitle: "今天 + 次日 + 第3天 + 第7天",
  groups: [
    {
      label: "R0 今日回忆",
      day: 8,
      topic: "本体感觉与前庭系统",
      questions: [
        {
          q: "肌梭主要感受什么？",
          options: ["A. 肌肉长度变化和拉伸速度", "B. 肌腱张力", "C. 血乳酸浓度", "D. 头部旋转"],
          answer: "A",
          explain: "肌梭关键词是长度和速度，快速拉长会触发牵张反射。",
        },
        {
          q: "GTO 最符合哪项描述？",
          options: ["A. 位于内耳管平衡", "B. 位于肌腱感受张力", "C. 位于肌腹感受长度", "D. 位于关节腔产生滑液"],
          answer: "B",
          explain: "GTO 位于肌腱，感受张力，参与自生抑制和保护机制。",
        },
      ],
      scenario: {
        q: "场景题：快速下蹲再起跳为什么可能跳得更高？",
        answer: "快速预拉伸会让肌梭感到长度和速度变化，触发牵张反射；同时 SSC 储存并释放弹性势能。前提是落地、膝髋对线和躯干控制稳定。",
      },
    },
    {
      label: "R1 次日复习",
      day: 7,
      topic: "研究方法与统计学",
      questions: [
        {
          q: "同一测试多次测量结果接近，主要说明什么？",
          options: ["A. 信度较好", "B. 效度一定高", "C. 因果成立", "D. 样本足够大"],
          answer: "A",
          explain: "信度看重复测量是否稳定；稳定不等于测得准。",
        },
        {
          q: "p<0.05 最稳妥理解是什么？",
          options: ["A. 效果一定很大", "B. 结论一定正确", "C. 结果不太像纯偶然", "D. 适合所有客户"],
          answer: "C",
          explain: "p 值不等于效果量，也不代表实际训练意义。",
        },
      ],
      scenario: {
        q: "场景题：补剂研究说喝的人肌肉更多，你能直接建议客户买吗？",
        answer: "不能直接建议。先看研究设计是否 RCT，有无对照，是否控制训练经验、热量、蛋白、睡眠和依从性，再看效果量和实际意义。",
      },
    },
    {
      label: "R2 第3天复习",
      day: 5,
      topic: "动作平面与运动轴",
      questions: [
        {
          q: "二头弯举主要发生在哪个平面，绕哪条轴？",
          options: ["A. 矢状面，绕额状轴", "B. 额状面，绕矢状轴", "C. 水平面，绕垂直轴"],
          answer: "A",
          explain: "肘屈伸主要在矢状面完成，矢状面动作绕额状轴。",
        },
        {
          q: "转体动作主要属于哪组配对？",
          options: ["A. 矢状面-额状轴", "B. 额状面-矢状轴", "C. 水平面-垂直轴"],
          answer: "C",
          explain: "旋转主要发生在水平面，绕垂直轴。",
        },
      ],
      scenario: {
        q: "场景题：只练固定器械很重，为什么不等于动作能力全面？",
        answer: "固定器械多偏矢状面和固定轨迹。真实运动还需要额状面侧向控制、水平面旋转/抗旋转，以及多关节协同。",
      },
    },
    {
      label: "R3 第7天复习",
      day: 1,
      topic: "骨学基础",
      questions: [
        {
          q: "中轴骨主要包括哪组？",
          options: ["A. 颅骨、脊柱、胸廓", "B. 肱骨、股骨、胫骨", "C. 肩带、上肢、下肢"],
          answer: "A",
          explain: "中轴骨是身体中线主梁，偏保护和中线稳定。",
        },
        {
          q: "Wolff 定律核心意思是什么？",
          options: ["A. 骨会沿受力方向重塑", "B. 肌肉主动收缩产生骨", "C. 骨成年后完全不变", "D. 关节都能三轴运动"],
          answer: "A",
          explain: "骨会根据长期机械负荷重塑，骨小梁沿应力线排列。",
        },
      ],
      scenario: {
        q: "场景题：新手力量涨很快，为什么加重量仍要渐进？",
        answer: "肌肉和神经适应可能很快，但骨、肌腱、韧带适应较慢。渐进负荷能给骨重塑信号，也降低关节和结缔组织超载风险。",
      },
    },
  ],
};

const decks = new Map([
  [7, day7Deck],
  [8, day8Deck],
]);

function esc(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function baseCss() {
  return `
*{box-sizing:border-box}body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f4f5;color:#111113}.page{position:relative;width:${WIDTH}px;height:${HEIGHT}px;overflow:hidden;padding:58px 72px 52px;background:linear-gradient(180deg,#fff 0%,#f7f7f8 100%)}.page:before{content:"";position:absolute;left:0;top:0;width:100%;height:12px;background:#ff5a1f}.brand{display:flex;align-items:center;justify-content:space-between;color:#71717a;font-size:28px;font-weight:800}.brand b{color:#111113}.brand b span{color:#ff5a1f}.rule{width:120px;height:6px;border-radius:999px;background:#ff5a1f;margin:34px 0 24px}.eyebrow{color:#ff5a1f;font-size:28px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.h1{margin:18px 0 14px;font-size:66px;line-height:1.12}.lead{margin:0;color:#52525b;font-size:30px;line-height:1.55}.chips{display:flex;flex-wrap:wrap;gap:14px;margin-top:24px}.chip{display:inline-flex;align-items:center;border-radius:999px;padding:13px 18px;font-size:24px;font-weight:900}.chip.orange{background:rgba(255,90,31,.1);color:#ff5a1f}.chip.blue{background:rgba(96,165,250,.16);color:#2563eb}.chip.green{background:rgba(74,222,128,.18);color:#15803d}.timeline{display:grid;gap:16px;margin-top:96px}.slot{border:1px solid #e4e4e7;border-radius:24px;background:#fff;padding:22px 24px;display:grid;grid-template-columns:190px 1fr;gap:20px;align-items:center}.slot b{color:#ff5a1f;font-size:28px;white-space:nowrap}.slot span{font-size:30px;font-weight:900}.slot small{display:block;margin-top:6px;color:#71717a;font-size:22px}.card{margin-top:22px;border:1px solid #e4e4e7;border-radius:26px;background:#fff;padding:22px 28px 21px;box-shadow:0 12px 28px rgba(0,0,0,.04)}.card+.card{margin-top:26px}.qtag{display:flex;align-items:center;gap:12px;margin-bottom:12px}.qtag span{border-radius:999px;background:rgba(255,90,31,.1);color:#ff5a1f;padding:8px 13px;font-size:21px;font-weight:900}.qtag b{font-size:24px;color:#52525b}.question{font-size:29px;font-weight:900;line-height:1.38;margin:0 0 15px}.opts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.opts.single{grid-template-columns:1fr}.opt{border:1px solid #e4e4e7;border-radius:18px;background:#fafafa;padding:14px 16px;font-size:24px;font-weight:800;line-height:1.35}.lbl{font-weight:900;color:#ff5a1f;margin-right:6px}.scenario{border-color:#bfdbfe;background:linear-gradient(135deg,rgba(96,165,250,.13),rgba(74,222,128,.1))}.scenario .qtag span{background:rgba(96,165,250,.18);color:#2563eb}.scenario .question{margin-bottom:0}.answers{display:grid;gap:24px;margin-top:24px}.answer{border:1px solid #e4e4e7;border-radius:22px;background:#fff;padding:20px 22px}.answer h2{margin:0 0 8px;font-size:29px;line-height:1.3}.answer p{margin:0;color:#52525b;font-size:24px;line-height:1.55}.answer-key{color:#ff5a1f}.scenario-answer{border-color:#bbf7d0;background:rgba(74,222,128,.09)}.scenario-answer h2{color:#15803d}.footer{position:absolute;left:72px;right:72px;bottom:42px;display:flex;justify-content:space-between;color:#a1a1aa;font-size:24px;font-weight:800}`;
}

function optionsClass(options) {
  if (options.length === 3) return "opts single";
  return options.some((option) => option.length > 16) ? "opts single" : "opts";
}

function htmlPage(body) {
  return `<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><style>${baseCss()}</style></head><body>${body}</body></html>`;
}

function stripTags(value) {
  return String(value)
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function headlineAnswer(value) {
  const text = stripTags(value);
  if (!text) return "";
  const firstSentence = text.split(/[。！？!?]/).map((part) => part.trim()).find(Boolean) || text;
  if (firstSentence.length <= 28) return firstSentence;
  const compact = firstSentence.replace(/[，,；;、]\s*/g, "，");
  return compact.length > 28 ? `${compact.slice(0, 28)}…` : compact;
}

function briefAnswer(value) {
  const text = stripTags(value);
  if (!text) return "";
  if (text.includes("糖酵解参与明显") || text.includes("糖酵解贡献明显")) return "糖酵解主导，先保动作质量";
  if (text.includes("中高强度") && text.includes("30 秒")) return "30秒到2分钟中高强度";
  if (text.includes("乳酸可被") || text.includes("乳酸能被")) return "乳酸可再利用，不是废物";
  if (text.includes("100 米") && text.includes("400 米")) return "100米偏ATP-PCr，400米偏糖酵解";
  if (text.includes("ACL") || text.includes("膝内扣")) return "疲劳让膝扭转和剪切风险升高";
  if (text.includes("力臂变长") || text.includes("力矩 =")) return "力臂越长，关节力矩越大";
  if (text.includes("马拉松") && text.includes("举重")) return "耐力偏I型，爆发偏II型";
  if (text.includes("PCr") && text.includes("恢复不足")) return "短休导致PCr恢复不足";
  const firstSentence = text.split(/[。！？!?]/).map((part) => part.trim()).find(Boolean) || text;
  const firstClause = firstSentence.split(/[；;，,]/).map((part) => part.trim()).find(Boolean) || firstSentence;
  return firstClause;
}

function expandAnswer(value, topic) {
  const text = stripTags(value);
  if (!text) return "";
  const brief = briefAnswer(text);
  if (text === brief || text.startsWith(`${brief}。`) || text.startsWith(`${brief}，`)) {
    if (topic.includes("糖酵解")) return `${text} 判断时看三个线索：持续时间超过纯 ATP-PCr、强度仍然很高、局部酸胀和速度下降开始明显。训练调整优先保动作质量，再决定休息、负重和次数。`;
    if (topic.includes("ATP-PCr")) return `${text} 关键不是追求更累，而是让快供能储备恢复到能支撑峰值输出。力量和爆发训练要同时安排速度、技术和休息。`;
    if (topic.includes("损伤")) return `${text} 真正要查的是负荷变化、疼痛时序和动作受力来源；风险升高时先降剂量，再修减速、落地和对线控制。`;
    if (topic.includes("杠杆") || topic.includes("力矩")) return `${text} 所以同样重量也会因为负重位置不同而难度不同。训练调整可以改握距、站距、器械路径或负重位置。`;
    if (topic.includes("肌纤维")) return `${text} I 型更耐疲劳，II 型更快更有力。训练感觉差异来自纤维特性、供能方式、休息长度和重复输出要求。`;
    return `${text} 放到 ${topic} 的训练场景里，先判断时间、强度、方向、负荷和动作控制，再对应到训练调整。`;
  }
  if (text.length > 45) return text;
  return `${text}。放到 ${topic} 的训练场景里，再判断负荷、方向和控制。`;
}

function hashString(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function uniqueStrings(values) {
  return [...new Set(values.map((value) => stripTags(value)).filter(Boolean))];
}

function shuffleDeterministic(values, seed) {
  const items = values.slice();
  let state = seed || 1;
  for (let index = items.length - 1; index > 0; index -= 1) {
    state = Math.imul(state ^ (state >>> 13), 2246822519) >>> 0;
    state = Math.imul(state ^ (state >>> 15), 3266489917) >>> 0;
    const swapIndex = state % (index + 1);
    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
  }
  return items;
}

function buildChoiceOptions(question, pool) {
  const correct = headlineAnswer(question.answer);
  const topic = question.topic || question.scope || "";
  const candidates = uniqueStrings(pool.map(headlineAnswer)).filter((item) => item && item !== correct);
  const topicFallbacks = topic.includes("损伤")
    ? ["看疼痛是否提前出现", "看负荷是否突然上调", "看落地和减速控制", "看足踝对线和旋转"]
    : topic.includes("核心")
      ? ["抗伸展和抗旋转", "只看腹肌酸胀", "只做卷腹", "忽略呼吸控制"]
      : topic.includes("力矩") || topic.includes("杠杆")
        ? ["看力臂变化", "只看骨头长度", "只看肌肉酸感", "只看器械重量"]
        : topic.includes("动作")
          ? ["看平面和运动轴", "只看器械外观", "只看出汗多少", "只看重量数字"]
          : ["先看定义", "先看训练变量", "先看代偿模式", "先看恢复条件"];
  const options = uniqueStrings([correct, ...candidates, ...topicFallbacks]).slice(0, 4);
  while (options.length < 4) options.push(topicFallbacks[options.length % topicFallbacks.length]);
  const shuffled = shuffleDeterministic(options, hashString(`${question.q}|${question.answer}|${topic}`));
  return {
    options: shuffled,
    correctIndex: shuffled.indexOf(correct),
  };
}

function splitTopic(value) {
  return String(value).replace(/^Day\s*\d+\s*[·｜|-]\s*/i, "").trim();
}

function findReviewHtml(day) {
  const prefix = `review-day${String(day).padStart(2, "0")}-`;
  const filename = fs.readdirSync(path.join(ROOT, "html")).find((item) => item.startsWith(prefix) && item.endsWith(".html"));
  if (!filename) throw new Error(`Missing review HTML for day ${day}`);
  return path.join(ROOT, "html", filename);
}

function extractReviewCards(html) {
  const cards = [];
  const cardRegex = /<article class="card">([\s\S]*?)<\/article>/g;
  let match;
  while ((match = cardRegex.exec(html))) {
    const raw = match[1];
    const meta = stripTags(raw.match(/<div class="meta">([\s\S]*?)<\/div>/)?.[1] || "");
    const heading = stripTags(raw.match(/<h3>([\s\S]*?)<\/h3>/)?.[1] || "");
    const dayMatch = meta.match(/Day\s*(\d+)/i);
    if (!dayMatch || !heading) continue;
    cards.push({
      day: Number(dayMatch[1]),
      topic: splitTopic(heading),
      label: meta.includes("今天早上") ? "R0 今日回忆" : meta.includes("1天") ? "R1 次日复习" : meta.includes("3天") ? "R2 第3天复习" : meta.includes("7天") ? "R3 第7天复习" : meta.includes("14天") ? "R4 第14天复习" : `R${cards.length} 间隔复习`,
    });
  }
  return cards;
}

function extractRecallQuestions(html) {
  const questions = [];
  const qRegex = /<div class="q"><p><b>([\s\S]*?)<\/b>([\s\S]*?)<\/p><button[\s\S]*?<\/button><div[^>]*class="answer"[^>]*>([\s\S]*?)<\/div><\/div>/g;
  let match;
  while ((match = qRegex.exec(html))) {
    const scope = stripTags(match[1]).replace(/：$/, "");
    const text = stripTags(match[2]);
    const answer = stripTags(match[3]);
    const dayMatch = scope.match(/Day\s*(\d+)/i);
    questions.push({
      scope,
      day: dayMatch ? Number(dayMatch[1]) : null,
      isToday: scope.includes("今日新知识"),
      isScenario: scope.includes("综合题") || scope.includes("场景题"),
      q: text.replace(/^[:：]\s*/, ""),
      answer,
      explain: answer,
      options: [],
    });
  }
  return questions;
}

function generatedScenario(card, fallback) {
  const topic = card.topic;
  const day = card.day;
  if (topic.includes("骨骼肌起止点") || topic.includes("起止点")) {
    return {
      q: `场景题：客户问“为什么弯举是前臂动，引体向上却是身体往上走？”你用 Day ${day} 的起止点和闭链概念怎么解释？`,
      answer: "先说明肌肉收缩方向仍是附着点互相靠近；开链弯举远端自由，所以止点向起点靠近；引体向上手固定，远端成为固定端，身体向固定端移动。",
    };
  }
  if (topic.includes("肌纤维")) {
    return {
      q: `场景题：客户问“为什么大重量低次数和中高次数训练感觉完全不同？”你用 Day ${day} 的肌纤维类型怎么解释？`,
      answer: "大重量低次数更强调高阈值 II 型纤维、快速高力输出和充分休息；中高次数更需要 IIa 与抗疲劳能力。I 型、IIa、IIx 都能发力，只是速度、力量和疲劳特性不同。",
    };
  }
  if (topic.includes("研究方法") || topic.includes("统计")) {
    return {
      q: `场景题：客户拿一篇“补剂显著增肌”的文章来问是否该买。你用 Day ${day} 的循证框架先查哪 3 点？`,
      answer: "先看研究设计是否能支持因果，尤其是否有随机对照；再看是否控制训练经验、蛋白、热量、睡眠等混杂因素；最后看效果量和实际意义，不只看 p 值。",
    };
  }
  if (topic.includes("运动单位募集") || topic.includes("神经肌肉控制")) {
    return {
      q: `场景题：客户练箱跳，计划 5 组×5 次，组间只休 30 秒。第 1 组能跳 60cm 且落地稳；第 3 组开始跳不上同高度，落地膝内扣，起跳前下蹲变深还停顿。你先怎么判断，下一组怎么调？`,
      answer: "先判断目标是不是爆发质量。如果是，表现已说明神经输出和动作质量掉线：高阈值运动单位快速募集、频率编码和同步化被疲劳压低；SSC 从快速离心-立刻向心变成深蹲停顿，弹性势能流失；30 秒休息不足，氧化恢复和 PCr 补充跟不上。下一组把休息拉到 2-3 分钟，降到能稳定完成的箱高或改 3 次/组；若膝内扣仍出现，停止箱跳，回退到低箱落地、反向跳或髋膝踝对线练习。",
    };
  }
  if (topic.includes("糖酵解")) {
    return {
      q: `场景题：客户做 4 组 12 次深蹲，每组最后 3 次腿酸、速度掉，但还想继续加短休。你用 Day ${day} 的糖酵解系统怎么解释，下一组怎么改？`,
      answer: "这是中高强度重复输出，糖酵解参与明显。腿酸和掉速提示代谢压力上升，不代表越短休越好。下一组先保动作质量：可把休息拉长、减轻负重或减少次数，让输出稳定而不是硬堆疲劳。",
    };
  }
  if (topic.includes("氧化系统") || topic.includes("有氧")) {
    return {
      q: `场景题：客户做 60 分钟骑行，20 分钟后开始掉速。应该怎么判断和调整？`,
      answer: "可以分三类判断：1. 如果能稳住 2 分钟以上同一节奏，氧化系统和配速还对得上；2. 如果不能稳住，当前强度或疲劳已经超过有氧底盘，需要回到糖酵解/ATP-PCr 压力和配速安排；3. 掉速时间也要分开判断，0-10 分钟掉速多像起步过快或热身不足，10-20 分钟掉速多像接近阈值、糖酵解顶上来，20 分钟后掉速多像氧化能力或耐久度不够。调整上先降低过快起步和过高强度，再按掉速时间补有氧底盘、节奏控制或恢复安排。",
    };
  }
  if (topic.includes("ATP-PCr")) {
    return {
      q: `场景题：客户做 5 组 3 次 85%1RM 深蹲，每组只休 30 秒。前两组还稳，第三组起身明显变慢、腰开始代偿。你怎么解释，下一组怎么改？`,
      answer: "这是短时高强度力量输出，主要依赖 ATP-PCr。30 秒只能恢复约一半 PCr，第三组快充储备不足，所以速度掉、动作质量下降。下一组先把休息拉到 3-5 分钟；若仍掉速，就降重量或减少组数，目标是保留峰值输出和技术质量，而不是硬撑疲劳。",
    };
  }
  if (topic.includes("核心")) {
    return {
      q: `场景题：客户平板支撑总是腰塌，和做 Pallof press 时躯干还会转。你会先怎么分辨问题？`,
      answer: "先判断是抗伸展不足还是抗旋转不足。平板塌腰更偏抗伸展，Pallof press 乱转更偏抗旋转；再分别用死虫、侧桥、Pallof press 和呼吸撑腹去补。",
    };
  }
  if (topic.includes("上肢")) {
    return {
      q: `场景题：客户卧推卡在下半程、划船时总耸肩。应该怎么判断肌群和动作模式？`,
      answer: "原因通常不是单一肌肉不够大，而是两个环节掉了。卧推下半程需要胸大肌、三角肌前束和肱三头肌继续把杠推过最难点，若肘伸和肩水平内收输出下降，就会卡住；划船总耸肩，多半是背阔肌和下斜方肌没有把肩胛稳住，上斜方肌抢了活，肩胛控制一乱，拉力就散。",
    };
  }
  if (topic.includes("第3周复盘") || topic === "生物力学") {
    return {
      q: `场景题：客户硬拉 100kg 时，杠铃一离开小腿就说“腰特别吃力”，视频里杠铃在脚尖前方、起身时先抬屁股再拉背。你按第3周生物力学先查哪 3 点？`,
      answer: "第一查力臂：杠铃离小腿远，重力线到髋和腰椎距离变长，腰背外力矩变大，先把杠铃拉回足中线上方并贴腿。第二查动作模式：先抬屁股说明髋铰链和腿部推地没接上，要让髋膝同步伸展，保持背角稳定。第三查核心和损伤风险：用腹压和背阔肌把躯干、杠铃固定住；若疲劳后才变形，就降重量或减少次数，避免用腰椎反复代偿。",
    };
  }
  if (topic.includes("生物力学基本概念") || topic === "生物力学基本概念与力") {
    return {
      q: `场景题：客户硬拉时杠铃一离开小腿，腰就明显吃力。你会怎么改？`,
      answer: "先把杠铃贴身，缩短腰椎和髋关节的力臂，再让髋主导后坐、重心落在足中。力没变，外部力矩变小，动作立刻会顺一点。",
    };
  }
  if (topic.includes("杠杆") || topic.includes("力矩")) {
    return {
      q: `场景题：客户做侧平举时，为什么手臂抬到接近水平最难？`,
      answer: "因为那时哑铃重力线到肩关节的力臂最大，肩外展力矩最高。要么缩短力臂，要么降低负荷，要么把动作分段做。",
    };
  }
  if (topic.includes("动作的生物力学分析") || topic.includes("动作模式")) {
    return {
      q: `场景题：客户问腿举和深蹲差在哪。你会怎么从动作模式解释？`,
      answer: "腿举偏开链，远端自由，局部肌群更容易孤立受力；深蹲偏闭链，脚固定在地面，多关节协同和传力更强。训练目的不同，选法就不同。",
    };
  }
  if (topic.includes("脊柱") || topic.includes("核心生物力学")) {
    return {
      q: `场景题：客户硬拉到中段就开始圆背。应该怎么判断和调整？`,
      answer: "先看髋铰链是否真的发生，再看腹压和杠铃是否贴身。髋没主导、杠铃离身，腰椎就容易被迫多吃屈曲力矩。",
    };
  }
  if (topic.includes("肌力与肌耐力")) {
    return {
      q: `场景题：客户 1RM 提升快，但 12 次一组后半程总掉速。你会怎么区分是肌力问题还是肌耐力问题？`,
      answer: "1RM 更看神经驱动、产力上限和技术；12 次后半程掉速更看局部抗疲劳、重复输出和动作经济性。一个能推重，不等于一个能重复撑住。",
    };
  }
  if (topic.includes("肌肉收缩类型")) {
    return {
      q: `场景题：客户深蹲下放、底部停顿、起身三个阶段，你会怎么分别叫法？`,
      answer: "下放是离心，底部停顿是等长，起身是向心。训练分析要分阶段看，不然很容易把控制和发力混成一团。",
    };
  }
  if (topic.includes("运动损伤")) {
    return {
      q: `场景题：客户最近跑量突然翻倍，膝外侧和跟腱开始不舒服。你先按哪 3 步排查？`,
      answer: "第一步查负荷：把近 2-4 周跑量、速度课、爬坡、间歇和恢复日列出来；若周跑量或高冲击课突然增加，先回退到疼痛前最后能稳定完成的剂量，暂时不加量。第二步查疼痛时序：若跑前就痛、热身后也不缓解，或日常走路、上下楼仍痛，停止跑步并转专业评估；若跑中逐渐痛、停下后缓解，说明当前剂量超耐受，减量并改低冲击训练；若跑后或次日更痛，下一次训练继续降量，直到 24 小时内回到原水平。第三步查受力来源：膝外侧重点看步幅过大、下坡和髋膝控制；跟腱重点看突然加速、爬坡、鞋跟落差变化、踝背屈和小腿耐力。只要疼痛越来越早出现、强度上升或改变跑姿，就停止进阶。",
    };
  }
  if (topic.includes("关节分类") || topic.includes("滑膜关节")) {
    return {
      q: `场景题：客户深蹲时脚踝卡、膝盖内扣。你用 Day ${day} 的关节分类和稳定-灵活权衡怎么分析？`,
      answer: "髋、膝、踝都是训练动作常见滑膜关节，但任务不同。踝和髋活动不足时，膝可能用内扣代偿；处理时先补踝背屈和髋控制，再训练膝对线稳定。",
    };
  }
  if (topic.includes("本体感觉") || topic.includes("前庭")) {
    return {
      q: `场景题：客户做跳跃落地总站不稳。你用 Day ${day} 的肌梭、GTO、关节感受器和前庭系统怎么解释？`,
      answer: "肌梭提供长度和速度反馈，GTO 感受张力，关节感受器反馈关节位置，前庭系统感受头部位置和平衡。落地不稳常是这些感觉输入与动作控制没有整合好，需要从低速控制、单脚稳定和落地对线逐步练。",
    };
  }
  if (topic.includes("肌肉微观结构") || topic.includes("肌丝滑行")) {
    return {
      q: `场景题：客户平板支撑时关节没动，却说“肌肉应该没收缩”。你用 Day ${day} 的肌丝滑行和横桥循环怎么解释？`,
      answer: "等长动作外部关节角度不变，不代表肌肉内部没有工作。肌球蛋白仍用 ATP 进行横桥循环并产生张力，只是外部长度变化被负荷和姿势抵消。",
    };
  }
  if (topic.includes("动作平面") || topic.includes("运动轴")) {
    return {
      q: `场景题：客户只会说“手往上抬、身体转一下”。你用 Day ${day} 的平面和轴把侧平举、弯举、转体说准确。`,
      answer: "侧平举主要是额状面肩外展，绕矢状轴；弯举主要是矢状面肘屈，绕额状轴；转体主要是水平面旋转，绕垂直轴。这样能更准确识别动作和代偿。",
    };
  }
  if (topic.includes("关节面形状") || topic.includes("运动学")) {
    return {
      q: `场景题：客户肩外展时夹痛。你用 Day ${day} 的滚动、滑动和凹凸法则怎么分析？`,
      answer: "肩外展时肱骨头需要上滚并配合下滑，肩胛也要上旋。若关节滑动不足或肩胛控制差，肱骨头可能上顶造成夹挤感。先看关节运动学和肩胛节律，不只拉三角肌。",
    };
  }
  if (topic.includes("骨性标志") || topic.includes("骨骼辨识")) {
    return {
      q: `场景题：客户体态评估时把髂前上棘和髂嵴混淆。你用 Day ${day} 解释这会影响哪些判断？`,
      answer: "骨性标志是体表定位、围度/皮褶测量、姿势观察和肌肉起止点分析的坐标。髂前上棘与髂嵴混淆，会让骨盆位置、下肢对线和测量点都出现偏差。",
    };
  }
  if (topic.includes("骨学基础") || topic.includes("骨骼系统")) {
    return {
      q: `场景题：客户做深蹲时总说“骨头只是撑着”，你会怎么解释骨在训练里的作用？`,
      answer: "骨不只是支架，还负责保护、储存矿物、参与造血，并作为肌肉发力的杠杆。力量训练要渐进，因为骨和结缔组织适应慢于神经与肌肉。",
    };
  }
  if (topic.includes("能量系统交互") || topic.includes("运动强度关系")) {
    return {
      q: "场景题：客户做 400 米冲刺，前 120 米很快，250 米后明显掉速、步幅变短。应该怎么判断和调整？",
      answer: "可以分三层判断：1. 如果 0-10 秒就冲得很猛，ATP-PCr 会快速顶上，但储量很少，前段过快会让后面更早掉速；2. 如果 30 秒到 2 分钟内开始腿酸、步频掉、呼吸急，糖酵解压力已经上来，配速可能超过当前乳酸阈或糖酵解耐受；3. 如果后半程步幅变短、髋伸不足、躯干晃动，疲劳已经影响动作力学，力量没有顺利传到地面。调整上先控制前段强度，必要时延长间歇；如果后半程仍塌，再补后半程配速训练和跑姿稳定训练。",
    };
  }
  return {
    q: `场景题：客户做 4 组训练，前 2 组动作稳定；第 3 组开始速度明显下降，最后 2 次出现代偿，还说“目标肌没感觉，关节反而紧”。你用 ${topic} 先查哪 3 件事，下一组怎么调？`,
    answer: `先查动作质量：关节路径、目标肌发力和代偿肌是否抢活；再查负荷剂量：重量、次数、速度和休息是否超过当前能力；最后查恢复状态：疼痛、疲劳和上一组表现是否已经提示该降阶。下一组先保质量，通常降重量或减少次数、拉长休息；若关节不适或代偿仍出现，回退到更简单动作并停止进阶。`,
  };
}

function buildDeckFromReviewHtml(day) {
  const reviewPath = findReviewHtml(day);
  const html = fs.readFileSync(reviewPath, "utf8");
  const cards = extractReviewCards(html);
  const recallQuestions = extractRecallQuestions(html);
  if (!cards.length || !recallQuestions.length) {
    throw new Error(`Could not extract cards/questions from ${reviewPath}`);
  }
  const groups = cards.map((card, index) => {
    const matched = recallQuestions.filter((question) => question.day === card.day || (card.day === day && question.isToday));
    let questions = matched.filter((question) => !question.isScenario).slice(0, 2);
    const scenarioQuestion = matched.find((question) => question.isScenario) || null;
    const skipScenario = day === 21 && card.day === 21 && card.topic === "第3周复盘-生物力学";
    const scenario = skipScenario
      ? null
      : scenarioQuestion
        ? { q: `场景题：${scenarioQuestion.q}`, answer: scenarioQuestion.answer, day: card.day, topic: card.topic }
        : { ...generatedScenario(card), day: card.day, topic: card.topic };
    if (day === 25 && card.day === 11 && card.topic.includes("上肢肌功能分群")) {
      questions = [];
    }
    return {
      label: card.label || `R${index} 复习`,
      day: card.day,
      topic: card.topic,
      questions,
      scenario,
    };
  });
  const answerPool = groups.flatMap((group) => [
    ...group.questions.map((question) => question.answer),
    ...(group.scenario ? [group.scenario.answer] : []),
  ]);
  const enrichedGroups = groups.map((group) => ({
    ...group,
    questions: group.questions.map((question) => ({
      ...question,
      choice: buildChoiceOptions(question, answerPool),
    })),
    scenario: group.scenario
      ? { ...group.scenario, choice: buildChoiceOptions(group.scenario, answerPool) }
      : null,
  }));
  return {
    day,
    title: "艾宾浩斯复习区",
    subtitle: "今天 + 次日 + 第3天 + 第7天",
    groups: enrichedGroups.filter((group) => group.questions.length || group.scenario),
  };
}

function cover(deck) {
  const totalQuestions = deck.groups.reduce((sum, group) => sum + group.questions.length, 0);
  const slots = deck.groups
    .map(
      (group) =>
        `<div class="slot"><b>${group.label}</b><div><span>Day ${group.day} · ${group.topic}</span><small>${group.questions.length} 题快速回忆</small></div></div>`,
    )
    .join("");
  return htmlPage(`<main class="page">
    <div class="brand"><b>Fitness<span>Study</span></b><span>下午复习</span></div>
    <div class="rule"></div>
    <div class="eyebrow">Day ${deck.day} Review</div>
    <h1 class="h1">${deck.title}</h1>
    <p class="lead">${deck.subtitle}。先答题，再翻答案页。</p>
    <div class="chips"><span class="chip orange">艾宾浩斯</span><span class="chip blue">间隔复习</span><span class="chip green">${totalQuestions}题自测</span></div>
    <div class="timeline">${slots}</div>
    <div class="footer"><span>Day ${deck.day}/112</span><span>下午复习区</span></div>
  </main>`);
}

function questionPage(deck, pageIndex, groups) {
  const cards = groups
    .flatMap((group) =>
      [
        ...group.questions.map(
          (question, index) => `<section class="card">
          <div class="qtag"><span>${group.label}</span><b>Day ${group.day} · ${group.topic} · Q${index + 1}</b></div>
          <p class="question">${esc(question.q)}</p>
        </section>`,
        ),
        group.scenario ? `<section class="card scenario">
          <div class="qtag"><span>场景题</span><b>Day ${group.day} · ${group.topic}</b></div>
          <p class="question">${esc(group.scenario.q)}</p>
        </section>` : "",
      ],
    )
    .join("");
  return htmlPage(`<main class="page">
    <div class="brand"><b>Fitness<span>Study</span></b><span>先答再翻</span></div>
    <div class="rule"></div>
    <div class="eyebrow">Questions ${pageIndex}</div>
    <h1 class="h1">先自己答</h1>
    <p class="lead">每题 10 秒，别急着看答案。</p>
    ${cards}
    <div class="footer"><span>Day ${deck.day}/112</span><span>下一页看答案</span></div>
  </main>`);
}

function answerPage(deck, pageIndex, groups) {
  const answers = groups
    .flatMap((group) =>
      [
        ...group.questions.map(
          (question, index) => `<section class="answer">
          <h2>${group.label} · Day ${group.day} · Q${index + 1} 简答：<span class="answer-key">${esc(briefAnswer(question.answer))}</span></h2>
          <p>${esc(expandAnswer(question.answer, group.topic))}</p>
        </section>`,
        ),
        group.scenario ? `<section class="answer scenario-answer">
          <h2>场景题简答：<span class="answer-key">${esc(briefAnswer(group.scenario.answer))}</span></h2>
          <p>${esc(expandAnswer(group.scenario.answer, group.topic))}</p>
        </section>` : "",
      ],
    )
    .join("");
  return htmlPage(`<main class="page">
    <div class="brand"><b>Fitness<span>Study</span></b><span>答案解析</span></div>
    <div class="rule"></div>
    <div class="eyebrow">Answers ${pageIndex}</div>
    <h1 class="h1">对答案</h1>
    <p class="lead">错题不急着清零，隔天还能答对，才是真的记住。</p>
    <div class="answers">${answers}</div>
    <div class="footer"><span>Day ${deck.day}/112</span><span>艾宾浩斯复习区</span></div>
  </main>`);
}

function buildSlides(deck) {
  const slides = [cover(deck)];
  deck.groups.forEach((group, index) => {
    slides.push(questionPage(deck, index + 1, [group]));
    slides.push(answerPage(deck, index + 1, [group]));
  });
  return slides;
}

function caption(deck) {
  const lines = deck.groups.map((group) => `${group.label} Day${group.day} ${group.topic}`).join("\n");
  return `今天下午复习区：
${lines}

先自己答，再看答案页。`;
}

async function render(deck) {
  const outDir = path.join(ROOT, "xhs-review", `day${String(deck.day).padStart(2, "0")}`);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "title.txt"), `Day${deck.day}｜艾宾浩斯复习区`);
  fs.writeFileSync(path.join(outDir, "caption.txt"), caption(deck));
  fs.writeFileSync(path.join(outDir, "tags.txt"), "#健身教练 #NSCA #NASM #运动科学 #健身知识 #艾宾浩斯复习");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
  const slides = buildSlides(deck);
  for (let index = 0; index < slides.length; index += 1) {
    await page.setContent(slides[index], { waitUntil: "networkidle" });
    const filename = index === 0 ? "cover.png" : `slide-${String(index).padStart(2, "0")}.png`;
    await page.screenshot({ path: path.join(outDir, filename), fullPage: false });
  }
  await browser.close();
  return outDir;
}

async function main() {
  const { day } = parseArgs();
  execFileSync(process.execPath, [path.join(__dirname, "sync-review-index.js"), `--day=${day}`], { stdio: "inherit" });
  const deck = decks.get(day) || buildDeckFromReviewHtml(day);
  const outDir = await render(deck);
  console.log(outDir);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
