const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const HTML_DIR = path.join(ROOT, "html");
const REVIEWS_PATH = path.join(ROOT, "reviews.json");
const INDEX_PATH = path.join(ROOT, "index.html");
const PROGRESS_PATH = path.join(ROOT, ".progress.json");

function parseArgs() {
  const args = new Map(
    process.argv.slice(2).map((arg) => {
      const [key, ...rest] = arg.split("=");
      return [key, rest.length ? rest.join("=") : "true"];
    }),
  );
  const rawDay = args.get("--day");
  const day = rawDay ? Number(rawDay) : inferDay();
  if (!Number.isInteger(day) || day < 1) {
    throw new Error("Usage: node scripts/sync-review-index.js --day=9 [--check-only]");
  }
  return {
    day,
    checkOnly: args.has("--check-only"),
  };
}

function inferDay() {
  const progress = JSON.parse(fs.readFileSync(PROGRESS_PATH, "utf8"));
  return Math.max(1, Number(progress.day) - 1);
}

function dayToken(day) {
  return `day${String(day).padStart(2, "0")}`;
}

function findReviewFile(day) {
  const prefix = `review-${dayToken(day)}-`;
  const filename = fs.readdirSync(HTML_DIR).find((item) => item.startsWith(prefix) && item.endsWith(".html"));
  if (!filename) throw new Error(`Missing review html for ${dayToken(day)}`);
  return {
    filename,
    abs: path.join(HTML_DIR, filename),
    rel: `html/${filename}`,
  };
}

function stripTags(value) {
  return String(value)
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function extractTitle(html, day) {
  const h1 = stripTags(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1] || "");
  const title = h1 || stripTags(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] || "");
  return title
    .replace(new RegExp(`^Day\\s*${day}\\s*(中午复习)?\\s*[·｜|-]?\\s*`, "i"), "")
    .replace(/^中午复习\s*[·｜|-]?\s*/i, "")
    .trim();
}

function extractCards(html) {
  const cards = [];
  const cardRegex = /<article class="card">([\s\S]*?)<\/article>/g;
  let match;
  while ((match = cardRegex.exec(html))) {
    const raw = match[1];
    const meta = stripTags(raw.match(/<div class="meta">([\s\S]*?)<\/div>/i)?.[1] || "");
    const heading = stripTags(raw.match(/<h3[^>]*>([\s\S]*?)<\/h3>/i)?.[1] || "");
    const dayMatch = meta.match(/Day\s*(\d+)/i);
    if (!dayMatch) continue;
    const day = Number(dayMatch[1]);
    const type = meta.includes("今天早上") || meta.includes("新知识")
      ? "R0"
      : meta.includes("1天")
        ? "R1"
        : meta.includes("3天")
          ? "R2"
          : meta.includes("7天")
            ? "R3"
            : meta.includes("14天")
              ? "R4"
              : "R?";
    const label = type === "R0" ? "今日回忆" : type === "R1" ? "次日复习" : type === "R2" ? "第3天复习" : type === "R3" ? "第7天复习" : type === "R4" ? "第14天复习" : "间隔复习";
    cards.push({ type, day, label, heading });
  }
  return cards;
}

function validateReviewHtml(html, reviewAbs) {
  const errors = [];
  if (!html.startsWith("<!DOCTYPE html>")) errors.push("first line must be <!DOCTYPE html>");
  if (!/<\/html>\s*$/i.test(html)) errors.push("missing closing </html>");
  if (/class="section lead"/.test(html) || /\.lead\s*\{[^}]*display\s*:\s*grid/i.test(html)) {
    errors.push("today review block must use a single article.card, not a side-by-side .lead grid");
  }
  const qCount = (html.match(/<div class="q">/g) || []).length;
  if (qCount < 6) errors.push(`active recall question count ${qCount} < 6`);

  const dir = path.dirname(reviewAbs);
  for (const [, href] of html.matchAll(/href="([^"#][^"]*)"/g)) {
    if (/^[a-z]+:/i.test(href)) continue;
    if (!fs.existsSync(path.join(dir, href))) errors.push(`missing href target: ${href}`);
  }
  for (const [, src] of html.matchAll(/src="([^"]+)"/g)) {
    if (/^[a-z]+:/i.test(src)) continue;
    if (!fs.existsSync(path.join(dir, src))) errors.push(`missing image target: ${src}`);
  }
  return errors;
}

function updateReviewsJson(day, title, reviewRel, cards) {
  const reviews = fs.existsSync(REVIEWS_PATH) ? JSON.parse(fs.readFileSync(REVIEWS_PATH, "utf8")) : [];
  const items = cards.map(({ type, day, label }) => ({ type, day, label }));
  const intervalText = items
    .filter((item) => item.type !== "R0")
    .map((item) => `Day${item.day}`)
    .join("/");
  const entry = {
    day,
    title,
    path: reviewRel,
    summary: `复习${title}，并连接 ${intervalText || "已生成历史课程"} 间隔复习。`,
    items,
  };
  const next = [entry, ...reviews.filter((item) => item.day !== day)].sort((a, b) => b.day - a.day);
  fs.writeFileSync(REVIEWS_PATH, `${JSON.stringify(next, null, 2)}\n`);
}

function updateLatestReviewLink(reviewRel) {
  const html = fs.readFileSync(INDEX_PATH, "utf8");
  const current = html.match(/<a([^>]*)href="(html\/review-day\d{2}-[^"]+\.html)"([^>]*)>最新复习<\/a>/);
  if (!current) return;
  if (current[2] === reviewRel) return;
  const next = html.replace(current[0], `<a${current[1]}href="${reviewRel}"${current[3]}>最新复习</a>`);
  fs.writeFileSync(INDEX_PATH, next);
}

function main() {
  const { day, checkOnly } = parseArgs();
  const review = findReviewFile(day);
  const html = fs.readFileSync(review.abs, "utf8");

  const cards = extractCards(html);
  const title = extractTitle(html, day);
  if (!title) throw new Error(`Could not extract review title for ${dayToken(day)}`);
  if (!cards.some((card) => card.day === day && card.type === "R0")) {
    throw new Error(`Missing R0 today card for ${dayToken(day)}`);
  }

  const errors = validateReviewHtml(html, review.abs);
  if (errors.length) throw new Error(errors.join("\n"));

  if (!checkOnly) {
    updateReviewsJson(day, title, review.rel, cards);
    updateLatestReviewLink(review.rel);
  }

  console.log(JSON.stringify({ day, title, review: review.rel, cards: cards.length, checkOnly }, null, 2));
}

main();
