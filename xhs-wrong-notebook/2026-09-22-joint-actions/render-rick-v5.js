const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

const root = __dirname;
const model = path.join(root, '00-rick-muscular-cartoon-model-v4.png');
const old01 = path.join(root, '01-下行踝关节背屈-rick-v4-带字.png');
const W = 1024;
const H = 1536;
const red = '#B44339';
const ink = '#152B3A';
const paper = '#F8F2E9';
const line = '#D5BFB0';
const font = "'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif";

function svg(inner, width = W, height = H) {
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <style>.cn{font-family:${font}} .ink{fill:${ink}} .red{fill:${red}}</style>${inner}</svg>`);
}

function text(x, y, value, size, options = {}) {
  const { color = ink, weight = 700, anchor = 'start', cls = 'cn' } = options;
  return `<text class="${cls}" x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" fill="${color}">${value}</text>`;
}

function card(x, y, w, h, title, body, accent = red) {
  const bodyLines = body.map((lineText, index) => text(x + 32, y + 112 + index * 44, lineText, 30, { weight: 650 }));
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="28" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    <rect x="${x}" y="${y}" width="${w}" height="70" rx="28" fill="${accent}"/>
    <rect x="${x}" y="${y + 40}" width="${w}" height="30" fill="${accent}"/>
    ${text(x + 32, y + 48, title, 32, { color: '#FFFFFF', weight: 800 })}${bodyLines.join('')}`;
}

function arrow(x1, y1, x2, y2, color = red, width = 7) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const a1 = angle + Math.PI * 0.82;
  const a2 = angle - Math.PI * 0.82;
  const head = 18;
  const p1 = `${x2 + Math.cos(a1) * head},${y2 + Math.sin(a1) * head}`;
  const p2 = `${x2 + Math.cos(a2) * head},${y2 + Math.sin(a2) * head}`;
  return `<path d="M${x1} ${y1} L${x2} ${y2}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round"/>
    <path d="M${p1} L${x2} ${y2} L${p2}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function curvedArrow(d, tipX, tipY, angle, color = red) {
  const head = 16;
  const p1 = `${tipX + Math.cos(angle + 2.55) * head},${tipY + Math.sin(angle + 2.55) * head}`;
  const p2 = `${tipX + Math.cos(angle - 2.55) * head},${tipY + Math.sin(angle - 2.55) * head}`;
  return `<path d="${d}" fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round"/>
    <path d="M${p1} L${tipX} ${tipY} L${p2}" fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function limb(x, y, rotation = 0, accent = '#5D86A0') {
  return `<g transform="translate(${x} ${y}) rotate(${rotation})">
    <circle cx="0" cy="0" r="34" fill="#F2D7C1" stroke="${ink}" stroke-width="5"/>
    <path d="M0 34 L0 144" stroke="${accent}" stroke-width="31" stroke-linecap="round"/>
    <circle cx="0" cy="151" r="17" fill="#F2D7C1" stroke="${ink}" stroke-width="5"/>
    <path d="M0 168 L0 267" stroke="${accent}" stroke-width="27" stroke-linecap="round"/>
    <path d="M-25 287 Q0 304 25 287" fill="none" stroke="${ink}" stroke-width="6" stroke-linecap="round"/>
  </g>`;
}

function spine(x, y, h, shortMuscle) {
  const vertebrae = Array.from({ length: 7 }, (_, i) => {
    const yy = y + i * (h / 8);
    return `<rect x="${x - 23}" y="${yy}" width="46" height="${h / 12}" rx="12" fill="#E8DDCC" stroke="#8C7768" stroke-width="3"/>`;
  }).join('');
  const bands = shortMuscle
    ? Array.from({ length: 4 }, (_, i) => {
        const yy = y + 24 + i * (h / 5.2);
        return `<path d="M${x + 24} ${yy} C${x + 66} ${yy + 10},${x + 62} ${yy + 56},${x + 23} ${yy + 72}" fill="none" stroke="#B64C43" stroke-width="20" stroke-linecap="round"/>`;
      }).join('')
    : `<path d="M${x + 24} ${y + 16} C${x + 106} ${y + 70},${x + 102} ${y + h - 65},${x + 22} ${y + h - 20}" fill="none" stroke="#B64C43" stroke-width="28" stroke-linecap="round"/>`;
  return `<g>${vertebrae}${bands}</g>`;
}

async function render01() {
  const header = svg(`<rect width="1024" height="180" fill="${paper}"/>
    <path d="M44 150 H980" stroke="${red}" stroke-width="5" opacity=".55"/>
    ${text(512, 103, '下行时，踝关节做什么？', 54, { color: red, weight: 850, anchor: 'middle' })}`);
  await sharp(old01).composite([{ input: header, top: 0, left: 0 }]).png().toFile(path.join(root, '01-下行踝关节背屈-rick-v5-带字.png'));
}

async function render02() {
  const modelPng = await sharp(model).resize({ width: 310, height: 510, fit: 'contain' }).png().toBuffer();
  const diagram = svg(`
    <rect width="1024" height="1536" fill="${paper}"/>
    ${text(64, 104, '窄握杠铃仰卧臂屈伸', 50, { color: red, weight: 850 })}
    <path d="M64 134 H960" stroke="${red}" stroke-width="5" opacity=".55"/>
    <rect x="52" y="198" width="920" height="610" rx="32" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    <rect x="88" y="674" width="580" height="52" rx="18" fill="#6E8790"/>
    <rect x="138" y="726" width="34" height="124" rx="14" fill="#536970"/>
    <rect x="590" y="726" width="34" height="124" rx="14" fill="#536970"/>
    <rect x="210" y="575" width="420" height="32" rx="14" fill="#B7C7C8"/>
    <circle cx="284" cy="521" r="44" fill="#F2D7C1" stroke="${ink}" stroke-width="5"/>
    <path d="M322 540 C390 564 488 578 578 584" fill="none" stroke="#FFFFFF" stroke-width="84" stroke-linecap="round"/>
    <path d="M352 545 L458 461 L512 510" fill="none" stroke="#E4C8B2" stroke-width="42" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M457 460 L532 516" fill="none" stroke="#E4C8B2" stroke-width="38" stroke-linecap="round"/>
    <path d="M370 470 L592 470" stroke="#272F38" stroke-width="14" stroke-linecap="round"/>
    <circle cx="357" cy="470" r="25" fill="#272F38"/><circle cx="605" cy="470" r="25" fill="#272F38"/>
    ${arrow(498, 425, 548, 375, '#477B98', 7)}
    ${text(108, 264, 'Rick-v4 示范者', 29, { color: red, weight: 800 })}
    ${text(104, 364, '起始位置', 34, { color: ink, weight: 800 })}
    ${text(104, 408, '肘关节弯曲', 29, { weight: 650 })}
    ${text(668, 364, '结束位置', 34, { color: ink, weight: 800 })}
    ${text(668, 408, '肘关节伸直', 29, { weight: 650 })}
    ${text(374, 446, '杠铃握距', 27, { color: red, weight: 800, anchor: 'middle' })}
    ${card(52, 866, 440, 225, '主动作', ['肘关节伸'], red)}
    ${card(532, 866, 440, 225, '主要肌肉', ['肱三头肌'], red)}
    <rect x="52" y="1140" width="920" height="238" rx="28" fill="#FFF4EE" stroke="${red}" stroke-width="3"/>
    ${text(92, 1212, '练习观察', 34, { color: red, weight: 850 })}
    ${text(92, 1274, '窄握时，重点观察肘的位置', 33, { weight: 700 })}
    ${text(92, 1324, '与腕部是否中立。', 33, { weight: 700 })}
  `);
  await sharp({ create: { width: W, height: H, channels: 4, background: paper } }).composite([
    { input: diagram, top: 0, left: 0 },
    { input: modelPng, top: 205, left: 650 },
  ]).png().toFile(path.join(root, '02-窄握杠铃仰卧臂屈伸-rick-v5-带字.png'));
}

async function render03() {
  const modelPng = await sharp(model).resize({ width: 205, height: 340, fit: 'contain' }).png().toBuffer();
  const content = svg(`
    <rect width="1024" height="1536" fill="${paper}"/>
    ${text(64, 104, '关节构成速记', 54, { color: red, weight: 850 })}
    <path d="M64 134 H960" stroke="${red}" stroke-width="5" opacity=".55"/>
    <rect x="52" y="182" width="920" height="330" rx="30" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    ${text(84, 240, '上肢带关节', 38, { color: red, weight: 850 })}
    ${text(84, 292, '胸锁关节 + 肩锁关节', 33, { weight: 750 })}
    ${text(84, 338, '（功能上：肩胛胸廓关节）', 28, { weight: 620 })}
    <path d="M430 380 Q520 246 625 382" fill="none" stroke="#E4D6C5" stroke-width="26" stroke-linecap="round"/>
    <path d="M520 254 L520 405 M458 365 L582 365" stroke="#B59C86" stroke-width="16" stroke-linecap="round"/>
    <circle cx="458" cy="365" r="14" fill="${red}"/><circle cx="582" cy="365" r="14" fill="${red}"/>
    ${arrow(447, 344, 398, 312, red, 5)} ${text(385, 305, '胸锁关节', 24, { color: red, weight: 750, anchor: 'end' })}
    ${arrow(595, 344, 653, 313, red, 5)} ${text(663, 305, '肩锁关节', 24, { color: red, weight: 750 })}
    ${card(52, 556, 920, 322, '肘关节复合体', ['肱尺关节：屈、伸', '肱桡关节：参与屈、伸', '近侧桡尺关节：旋前、旋后'], red)}
    <path d="M730 666 L730 800 M775 666 L750 800 M730 666 Q752 645 775 666" fill="none" stroke="#CDB9A4" stroke-width="20" stroke-linecap="round"/>
    <circle cx="752" cy="666" r="17" fill="${red}"/>
    <rect x="52" y="932" width="920" height="368" rx="30" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    ${text(84, 990, '踝关节（距小腿关节）', 38, { color: red, weight: 850 })}
    ${text(84, 1043, '胫骨下端 + 腓骨下端形成踝穴', 30, { weight: 700 })}
    ${text(84, 1089, '与距骨滑车构成', 30, { weight: 700 })}
    <path d="M640 1045 L640 1190 M778 1045 L778 1190 M640 1190 Q709 1228 778 1190" fill="none" stroke="#D7C3AD" stroke-width="32" stroke-linecap="round"/>
    <path d="M662 1214 Q710 1168 758 1214" fill="none" stroke="#7795A4" stroke-width="38" stroke-linecap="round"/>
    <rect x="52" y="1350" width="920" height="100" rx="22" fill="#FFF4EE" stroke="${red}" stroke-width="3"/>
    ${text(512, 1414, '肘是复合关节；踝是踝穴包住距骨。', 30, { color: red, weight: 800, anchor: 'middle' })}
  `);
  await sharp({ create: { width: W, height: H, channels: 4, background: paper } }).composite([
    { input: content, top: 0, left: 0 }, { input: modelPng, top: 186, left: 748 }
  ]).png().toFile(path.join(root, '03-关节构成速记-rick-v5-带字.png'));
}

async function render04() {
  const modelPng = await sharp(model).resize({ width: 230, height: 390, fit: 'contain' }).png().toBuffer();
  const content = svg(`
    <rect width="1024" height="1536" fill="${paper}"/>
    ${text(64, 104, '肩关节动作地图', 54, { color: red, weight: 850 })}
    <path d="M64 134 H960" stroke="${red}" stroke-width="5" opacity=".55"/>
    ${card(52, 188, 430, 310, '矢状面', ['屈', '伸'], red)}
    ${limb(252, 286, -35)}${arrow(186, 354, 146, 282, red, 6)}${arrow(308, 354, 350, 414, red, 6)}
    ${card(542, 188, 430, 310, '冠状面', ['外展', '内收'], red)}
    ${limb(760, 292, 0)}${arrow(722, 356, 675, 290, red, 6)}${arrow(798, 356, 846, 420, red, 6)}
    ${card(52, 550, 430, 330, '水平面', ['水平内收（水平屈）', '水平外展'], red)}
    <circle cx="266" cy="704" r="34" fill="#F2D7C1" stroke="${ink}" stroke-width="5"/>
    <path d="M266 738 L266 822 M266 765 L150 710 M266 765 L388 705" stroke="#5D86A0" stroke-width="29" stroke-linecap="round"/>
    ${arrow(154, 686, 235, 735, red, 6)}${arrow(376, 685, 297, 734, red, 6)}
    ${card(542, 550, 430, 330, '旋转', ['内旋', '外旋'], red)}
    ${limb(758, 650, 88)}
    ${curvedArrow('M685 752 C672 689 705 650 755 649', 755, 649, -0.5, red)}
    ${curvedArrow('M828 752 C844 688 815 647 770 645', 770, 645, 3.8, '#477B98')}
    ${text(758, 850, '每条箭头均为单向', 23, { color: red, weight: 750, anchor: 'middle' })}
    <rect x="52" y="934" width="920" height="305" rx="30" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    ${text(84, 995, '前臂与肩关节：别混写', 38, { color: red, weight: 850 })}
    <rect x="84" y="1040" width="390" height="146" rx="22" fill="#EEF4F5"/>
    <rect x="550" y="1040" width="390" height="146" rx="22" fill="#FFF1EC"/>
    ${text(279, 1102, '前臂', 34, { color: ink, weight: 850, anchor: 'middle' })}
    ${text(279, 1152, '旋前、旋后', 30, { weight: 700, anchor: 'middle' })}
    ${text(745, 1102, '肩关节', 34, { color: ink, weight: 850, anchor: 'middle' })}
    ${text(745, 1152, '内旋、外旋', 30, { weight: 700, anchor: 'middle' })}
    <rect x="52" y="1294" width="920" height="104" rx="22" fill="#FFF4EE" stroke="${red}" stroke-width="3"/>
    ${text(512, 1358, '肩：屈伸、展收、水平、旋转。', 31, { color: red, weight: 850, anchor: 'middle' })}
  `);
  await sharp({ create: { width: W, height: H, channels: 4, background: paper } }).composite([
    { input: content, top: 0, left: 0 }, { input: modelPng, top: 905, left: 399 }
  ]).png().toFile(path.join(root, '04-肩关节动作地图-rick-v5-带字.png'));
}

async function render05() {
  const content = svg(`
    <rect width="1024" height="1536" fill="${paper}"/>
    ${text(64, 104, '多裂肌与深层短肌', 54, { color: red, weight: 850 })}
    <path d="M64 134 H960" stroke="${red}" stroke-width="5" opacity=".55"/>
    <rect x="36" y="204" width="460" height="720" rx="28" fill="#FFFDF9" stroke="${red}" stroke-width="3"/>
    <path d="M36 232 Q36 204 64 204 H468 Q496 204 496 232 V315 H36Z" fill="${red}"/>
    ${text(266, 277, '短肌', 52, { color: '#FFFFFF', weight: 850, anchor: 'middle' })}
    ${text(76, 388, '短肌＝跨越节段少、', 33, { weight: 800 })}
    ${text(76, 438, '贴近脊柱、偏局部稳定。', 33, { weight: 800 })}
    ${spine(372, 492, 320, true)}
    <rect x="528" y="204" width="460" height="720" rx="28" fill="#FFFDF9" stroke="${red}" stroke-width="3"/>
    <path d="M528 232 Q528 204 556 204 H960 Q988 204 988 232 V315 H528Z" fill="${red}"/>
    ${text(758, 277, '长肌', 52, { color: '#FFFFFF', weight: 850, anchor: 'middle' })}
    ${text(568, 388, '长肌＝跨越节段多、', 33, { weight: 800 })}
    ${text(568, 438, '偏动力输出。', 33, { weight: 800 })}
    ${spine(864, 492, 320, false)}
    <rect x="52" y="992" width="920" height="338" rx="30" fill="#FFFDF9" stroke="${line}" stroke-width="3"/>
    ${text(84, 1056, '多裂肌在哪里？', 42, { color: red, weight: 850 })}
    <path d="M650 1100 L650 1266" stroke="#E2D1C0" stroke-width="42" stroke-linecap="round"/>
    ${spine(650, 1090, 170, true)}
    ${text(84, 1123, '位于脊柱两侧的深层', 32, { weight: 720 })}
    ${text(84, 1175, '跨越数个椎体', 32, { weight: 720 })}
    ${text(84, 1227, '稳定 + 伸展 + 旋转控制', 32, { weight: 720 })}
    <rect x="52" y="1382" width="920" height="92" rx="22" fill="#FFF4EE" stroke="${red}" stroke-width="3"/>
    ${text(512, 1442, '短肌偏稳定；长肌偏动力输出。', 31, { color: red, weight: 850, anchor: 'middle' })}
  `);
  await sharp({ create: { width: W, height: H, channels: 4, background: paper } }).composite([{ input: content, top: 0, left: 0 }]).png().toFile(path.join(root, '05-多裂肌深层短肌-rick-v5-带字.png'));
}

async function main() {
  for (const source of [model, old01]) if (!fs.existsSync(source)) throw new Error(`Missing source: ${source}`);
  await render01();
  await render02();
  await render03();
  await render04();
  await render05();
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
