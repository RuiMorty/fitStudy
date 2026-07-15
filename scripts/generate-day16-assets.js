const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const bodyOut = path.join(ROOT, "html", "assets", "阶段1基础科学", "day16-杠杆系统与力矩.png");
const visualDir = path.join(ROOT, "xhs", "day16", "ai-visuals");

function esc(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function svgPage(content, width = 1600, height = 1120) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
<defs>
  <marker id="arrowBlue" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 Z" fill="#2563eb"/></marker>
  <marker id="arrowGreen" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 Z" fill="#16a34a"/></marker>
  <marker id="arrowOrange" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 Z" fill="#f97316"/></marker>
  <style>
    .title{font:800 54px 'PingFang SC','Microsoft YaHei',sans-serif;fill:#111827}.sub{font:400 26px 'PingFang SC','Microsoft YaHei',sans-serif;fill:#4b5563}.label{font:700 28px 'PingFang SC','Microsoft YaHei',sans-serif;fill:#111827}.small{font:600 22px 'PingFang SC','Microsoft YaHei',sans-serif;fill:#374151}.blue{fill:#2563eb}.green{fill:#16a34a}.orange{fill:#f97316}.line{stroke-linecap:round;stroke-linejoin:round}
  </style>
</defs>
<rect width="100%" height="100%" fill="#fbfdfc"/>${content}</svg>`;
}

function bodyDiagram() {
  return svgPage(`
  <text x="800" y="78" text-anchor="middle" class="title">二头弯举：杠杆、力矩与力臂</text>
  <text x="800" y="122" text-anchor="middle" class="sub">力臂 = 支点到力作用线的垂直距离，不是骨头长度</text>
  <rect x="54" y="160" width="960" height="575" rx="26" fill="#ffffff" stroke="#dbe5df" stroke-width="3"/>
  <text x="92" y="212" class="label">肘关节弯举（第三类杠杆）</text>
  <path d="M250 274 L282 470" class="line" stroke="#e3d2b5" stroke-width="56"/>
  <path d="M278 470 L728 470" class="line" stroke="#e3d2b5" stroke-width="48"/>
  <path d="M230 260 C310 254 366 325 349 439 C341 464 327 474 305 468 C322 364 279 311 230 260Z" fill="#86c96f" stroke="#4f9d50" stroke-width="4"/>
  <path d="M326 450 L370 476" class="line" stroke="#e9ecef" stroke-width="30"/>
  <path d="M333 463 L206 270" class="line" stroke="#16a34a" stroke-width="11" marker-end="url(#arrowGreen)"/>
  <path d="M333 463 L176 225" class="line" stroke="#16a34a" stroke-width="4" stroke-dasharray="12 11"/>
  <text x="126" y="245" class="label green">肌肉拉力 F</text><text x="126" y="277" class="small">沿肌腱，指向肩部</text>
  <circle cx="282" cy="470" r="14" fill="#2563eb" stroke="#fff" stroke-width="6"/>
  <path d="M242 507 L282 470" class="line" stroke="#2563eb" stroke-width="4"/>
  <text x="84" y="542" class="label blue">支点</text><text x="84" y="574" class="small">肘关节旋转轴</text>
  <path d="M282 470 L332 438" class="line" stroke="#f97316" stroke-width="7"/>
  <path d="M324 432 L336 450 L318 462" fill="none" stroke="#f97316" stroke-width="4"/>
  <text x="382" y="422" class="label orange">肌肉力臂 dF</text><text x="382" y="452" class="small">到绿色作用线的垂距</text>
  <path d="M282 505 L716 505" class="line" stroke="#2563eb" stroke-width="6" stroke-dasharray="13 11"/>
  <path d="M282 495 L282 515 M716 495 L716 515" stroke="#2563eb" stroke-width="4"/>
  <text x="462" y="548" class="label blue">阻力臂 dR</text><text x="454" y="578" class="small">到重力作用线的垂距</text>
  <circle cx="735" cy="468" r="24" fill="#475569"/><path d="M735 444 L735 492 M711 468 L759 468" stroke="#fff" stroke-width="5"/>
  <path d="M735 468 L735 633" class="line" stroke="#2563eb" stroke-width="10" marker-end="url(#arrowBlue)"/>
  <text x="768" y="610" class="label blue">阻力 R</text><text x="768" y="641" class="small">哑铃重力向下</text>
  <rect x="1054" y="160" width="492" height="575" rx="26" fill="#ffffff" stroke="#dbe5df" stroke-width="3"/>
  <text x="1098" y="218" class="label">读图顺序</text>
  <circle cx="1118" cy="278" r="22" fill="#2563eb"/><text x="1158" y="287" class="label">1. 先找支点：肘关节</text>
  <path d="M1122 348 L1170 292" class="line" stroke="#16a34a" stroke-width="8" marker-end="url(#arrowGreen)"/><text x="1198" y="341" class="label">2. 找肌肉拉力方向</text>
  <path d="M1120 417 L1285 417" class="line" stroke="#f97316" stroke-width="7"/><path d="M1285 378 L1285 456" class="line" stroke="#16a34a" stroke-width="7"/><text x="1096" y="492" class="label">3. 力臂画到作用线</text><text x="1096" y="526" class="small">必须成 90°</text>
  <text x="1096" y="612" class="label">力矩 = 力 × 力臂</text><text x="1096" y="652" class="sub">肌肉力矩超过阻力力矩，前臂才会上转</text>
  <text x="800" y="804" text-anchor="middle" class="title" style="font-size:38px">三类杠杆：只看谁在中间</text>
  ${leverCard(76, 852, "第一类", ["力", "支", "阻"], "支点在中间：颈部伸展")}
  ${leverCard(558, 852, "第二类", ["支", "阻", "力"], "阻力在中间：提踵")}
  ${leverCard(1040, 852, "第三类", ["支", "力", "阻"], "力点在中间：二头弯举")}`);
}

function leverCard(x, y, title, order, caption) {
  const colors = { 支: "#2563eb", 力: "#16a34a", 阻: "#f97316" };
  return `<rect x="${x}" y="${y}" width="420" height="208" rx="22" fill="#fff" stroke="#dbe5df" stroke-width="3"/>
  <text x="${x + 28}" y="${y + 43}" class="label">${title}</text>
  <line x1="${x + 72}" y1="${y + 112}" x2="${x + 350}" y2="${y + 112}" stroke="#64748b" stroke-width="7" stroke-linecap="round"/>
  ${order.map((item, index) => `<circle cx="${x + 92 + index * 130}" cy="${y + 112}" r="25" fill="${colors[item]}"/><text x="${x + 92 + index * 130}" y="${y + 121}" text-anchor="middle" style="font:800 23px 'PingFang SC','Microsoft YaHei';fill:white">${item}</text>`).join("")}
  <text x="${x + 28}" y="${y + 170}" class="small">${caption}</text>`;
}

function visual(kind) {
  const base = `<rect width="1600" height="1120" fill="#f8fbfa"/><path d="M0 1050 H1600" stroke="#dbe5df" stroke-width="4"/>`;
  if (kind === "cover") return svgPage(`${base}<circle cx="800" cy="570" r="310" fill="#e6f7ed"/><line x1="505" y1="650" x2="1100" y2="650" stroke="#d6c5a8" stroke-width="72" stroke-linecap="round"/><circle cx="520" cy="650" r="38" fill="#2563eb"/><path d="M615 615 L520 425" stroke="#16a34a" stroke-width="70" stroke-linecap="round"/><path d="M615 615 L465 330" stroke="#16a34a" stroke-width="11" marker-end="url(#arrowGreen)"/><circle cx="1120" cy="650" r="55" fill="#475569"/><path d="M1120 585 L1120 830" stroke="#2563eb" stroke-width="12" marker-end="url(#arrowBlue)"/><path d="M520 730 L1120 730" stroke="#f97316" stroke-width="9" stroke-dasharray="18 15"/>`);
  if (kind === "elements") return svgPage(`${base}<line x1="260" y1="610" x2="1340" y2="610" stroke="#d6c5a8" stroke-width="70" stroke-linecap="round"/><circle cx="390" cy="610" r="45" fill="#2563eb"/><path d="M740 610 L740 360" stroke="#16a34a" stroke-width="16" marker-end="url(#arrowGreen)"/><circle cx="1180" cy="610" r="72" fill="#475569"/><path d="M1180 520 L1180 820" stroke="#f97316" stroke-width="16" marker-end="url(#arrowOrange)"/>`);
  if (kind === "classes") return svgPage(`${base}${[370,800,1230].map((cx,i)=>`<line x1="${cx-190}" y1="560" x2="${cx+190}" y2="560" stroke="#94a3b8" stroke-width="16" stroke-linecap="round"/><circle cx="${cx-110}" cy="560" r="36" fill="${i===0?'#16a34a':'#2563eb'}"/><circle cx="${cx}" cy="560" r="36" fill="${i===1?'#f97316':i===2?'#16a34a':'#2563eb'}"/><circle cx="${cx+110}" cy="560" r="36" fill="${i===0?'#f97316':i===1?'#16a34a':'#f97316'}"/>`).join("")}`);
  if (kind === "moment") return svgPage(`${base}<circle cx="510" cy="700" r="42" fill="#2563eb"/><line x1="510" y1="700" x2="1210" y2="470" stroke="#d6c5a8" stroke-width="62" stroke-linecap="round"/><line x1="1210" y1="190" x2="1210" y2="875" stroke="#2563eb" stroke-width="13" stroke-dasharray="20 16"/><line x1="510" y1="700" x2="1210" y2="700" stroke="#f97316" stroke-width="13" stroke-dasharray="20 16"/><path d="M1210 330 L1210 800" stroke="#2563eb" stroke-width="16" marker-end="url(#arrowBlue)"/>`);
  if (kind === "curl") return svgPage(`${base}<circle cx="390" cy="710" r="44" fill="#2563eb"/><path d="M390 710 L1120 710" stroke="#d6c5a8" stroke-width="70" stroke-linecap="round"/><path d="M500 690 L385 420" stroke="#16a34a" stroke-width="62" stroke-linecap="round"/><path d="M495 685 L330 305" stroke="#16a34a" stroke-width="13" marker-end="url(#arrowGreen)"/><circle cx="1170" cy="710" r="60" fill="#475569"/><path d="M1170 620 L1170 910" stroke="#f97316" stroke-width="15" marker-end="url(#arrowOrange)"/>`);
  if (kind === "advantage") return svgPage(`${base}<path d="M800 250 L470 850 H1130 Z" fill="#e5e7eb" stroke="#64748b" stroke-width="8"/><line x1="350" y1="570" x2="1250" y2="570" stroke="#64748b" stroke-width="24" stroke-linecap="round"/><circle cx="540" cy="570" r="84" fill="#16a34a"/><circle cx="1100" cy="570" r="120" fill="#f97316"/><path d="M500 380 L500 210" stroke="#16a34a" stroke-width="14" marker-end="url(#arrowGreen)"/><path d="M1140 340 L1140 910" stroke="#f97316" stroke-width="14" marker-end="url(#arrowOrange)"/>`);
  if (kind === "angles") return svgPage(`${base}<circle cx="450" cy="720" r="42" fill="#2563eb"/>${[0,35,70].map((angle,i)=>{const rad=angle*Math.PI/180;const x=450+580*Math.cos(rad);const y=720-580*Math.sin(rad);return `<line x1="450" y1="720" x2="${x}" y2="${y}" stroke="${['#cbd5e1','#60a5fa','#16a34a'][i]}" stroke-width="45" stroke-linecap="round"/><line x1="${x}" y1="${y-175}" x2="${x}" y2="${y+175}" stroke="#f97316" stroke-width="10" stroke-dasharray="16 14"/>`;}).join("")}`);
  if (kind === "rdl") return svgPage(`${base}<circle cx="690" cy="250" r="72" fill="#f2c6a5"/><path d="M690 330 L820 625 L655 870" fill="none" stroke="#64748b" stroke-width="76" stroke-linecap="round"/><path d="M820 625 L1120 690" stroke="#d6c5a8" stroke-width="62" stroke-linecap="round"/><path d="M805 620 L565 690" stroke="#d6c5a8" stroke-width="62" stroke-linecap="round"/><line x1="1110" y1="780" x2="1110" y2="410" stroke="#f97316" stroke-width="18"/><line x1="975" y1="735" x2="975" y2="390" stroke="#16a34a" stroke-width="18"/><circle cx="1110" cy="790" r="45" fill="#475569"/><circle cx="975" cy="745" r="45" fill="#475569"/>`);
  return svgPage(`${base}<circle cx="375" cy="760" r="45" fill="#2563eb"/><path d="M440 760 L700 520 L1080 520" fill="none" stroke="#64748b" stroke-width="30" stroke-linecap="round"/><path d="M690 520 L690 330" stroke="#16a34a" stroke-width="14" marker-end="url(#arrowGreen)"/><path d="M1080 520 L1080 805" stroke="#f97316" stroke-width="14" marker-end="url(#arrowOrange)"/><path d="M375 860 C600 1000 1020 1000 1220 820" fill="none" stroke="#60a5fa" stroke-width="16" stroke-dasharray="18 15"/>`);
}

function writePng(svg, out) {
  const temp = path.join("/tmp", `${path.basename(out, ".png")}.svg`);
  fs.writeFileSync(temp, svg);
  execFileSync("qlmanage", ["-t", "-s", "1600", "-o", "/tmp", temp], { stdio: "inherit" });
  fs.copyFileSync(`${temp}.png`, out);
}

const xhsOnly = process.argv.includes("--xhs-only");
fs.mkdirSync(path.dirname(bodyOut), { recursive: true });
fs.mkdirSync(visualDir, { recursive: true });
if (!xhsOnly) writePng(bodyDiagram(), bodyOut);
[
  ["00-cover", "cover"], ["01-lever-overview", "flow"], ["02-three-elements", "elements"],
  ["03-three-lever-classes", "classes"], ["04-torque-moment-arm", "moment"],
  ["05-curl-third-class", "curl"], ["06-mechanical-advantage", "advantage"],
  ["07-curl-angle-torque", "angles"], ["08-rdl-moment-arm", "rdl"], ["09-analysis-flow", "flow"],
].forEach(([name, kind]) => writePng(visual(kind), path.join(visualDir, `visual-${name}.png`)));
