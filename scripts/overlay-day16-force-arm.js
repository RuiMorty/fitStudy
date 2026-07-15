const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const source = "/Users/zhaoqr/.codex/generated_images/019f4b43-69a0-7433-b6d1-90c765a88fc0/exec-e10efd90-adc0-4c5f-9219-84da930a489b.png";
const output = path.join(root, "html", "assets", "阶段1基础科学", "day16-杠杆系统与力矩.png");
const image = fs.readFileSync(source).toString("base64");

const html = `<!doctype html>
<style>html,body{margin:0;width:1024px;height:1536px;overflow:hidden}img,svg{position:absolute;inset:0;width:1024px;height:1536px}</style>
<img src="data:image/png;base64,${image}">
<svg viewBox="0 0 1024 1536" xmlns="http://www.w3.org/2000/svg">
  <!-- Force direction: extend existing dashed biceps line to perpendicular contact. -->
  <path d="M315 570 L323 587" fill="none" stroke="#16a34a" stroke-width="7" stroke-dasharray="10 7" stroke-linecap="round"/>
  <!-- dF: unique green segment from elbow pivot to force-direction line. -->
  <path d="M289 604 L323 587" fill="none" stroke="#ffffff" stroke-width="18" stroke-linecap="round"/>
  <path d="M289 604 L323 587" fill="none" stroke="#16a34a" stroke-width="10" stroke-linecap="round"/>
  <!-- Three sides only; fourth side is the dF segment itself. -->
  <path d="M323 587 L315 571 L299 579 L307 595" fill="none" stroke="#16a34a" stroke-width="6" stroke-linecap="square" stroke-linejoin="miter"/>
  <!-- Rebuilt dF label and one clean leader terminating on dF midpoint. -->
  <path d="M414 456 L362 456 L300 598" fill="none" stroke="#16a34a" stroke-width="6" stroke-linecap="round" stroke-linejoin="miter"/>
  <text x="426" y="455" fill="#16a34a" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="31" font-weight="700">力臂 (dF)</text>
  <text x="426" y="492" fill="#111827" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="24" font-weight="600">支点到力的作用线的</text>
  <text x="426" y="524" fill="#111827" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="24" font-weight="600">垂直距离（⊥）</text>
</svg>`;

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1024, height: 1536 }, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: "networkidle" });
  await page.screenshot({ path: output });
  await browser.close();
})();
