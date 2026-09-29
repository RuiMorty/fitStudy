const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

const root = path.resolve(__dirname, '..');
const rawDir = path.join(__dirname, 'reference-edits', 'raw');
const outDir = path.join(root, 'images');
const W = 1024;
const H = 1536;
const paper = '#F8F2E9';
const red = '#B44339';
const ink = '#152B3A';
const navy = '#294D68';
const border = '#D5BFB0';
const font = "'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif";

const cards = [
  {
    source: '01-01-deep-back-muscles.png',
    output: '01-背部深层肌.png',
    title: '背部深层肌',
    tip: '深层贴脊柱，重点在椎间稳定。',
    titleSize: 58,
    overlays: [
      label(54, 674, 258, '表层：斜方肌 / 背阔肌', { size: 24, fill: '#FFFDF9' }),
      label(70, 1138, 244, '多裂肌：深层短肌束', { size: 27, fill: '#FFF4EE', stroke: red })
    ]
  },
  {
    source: '02-02-adductor-magnus-fixed-end.png',
    output: '02-大收肌-固定端决定谁动.png',
    title: '大收肌：固定端决定谁动',
    tip: '近固定看大腿；骨盆动作先看股骨是否固定。',
    titleSize: 45,
    overlays: [
      label(74, 430, 260, '近固定：骨盆固定', { size: 29, fill: '#FFFDF9', stroke: red }),
      label(564, 430, 260, '远固定：股骨固定', { size: 29, fill: '#FFFDF9', stroke: red }),
      label(70, 1228, 310, '主看：大腿内收', { size: 30, fill: '#FFF4EE', stroke: red }),
      label(548, 1228, 330, '双侧：骨盆前倾', { size: 30, fill: '#FFF4EE', stroke: red })
    ]
  },
  {
    source: '03-03-upper-limb-location-map.png',
    output: '03-上肢定位地图.png',
    title: '上肢定位地图',
    tip: '长头腱看横肱韧带；旋前圆肌屈肘只是辅助。',
    titleSize: 56,
    overlays: [
      label(72, 464, 360, '横肱韧带：固定长头腱', { size: 26, fill: '#FFF4EE', stroke: red }),
      label(72, 852, 380, '旋前圆肌：主旋前，助屈肘', { size: 25, fill: '#FFFDF9' }),
      label(72, 1214, 366, '桡腕 / 腕骨间 / 腕中', { size: 26, fill: '#FFFDF9', stroke: red })
    ]
  },
  {
    source: '04-04-leg-compartments-gastrocnemius.png',
    output: '04-小腿三群与腓肠肌.png',
    title: '小腿三群与腓肠肌',
    tip: '前群背屈、外侧群外翻、后群跖屈；腓肠肌还屈膝。',
    titleSize: 48,
    overlays: [
      label(56, 248, 204, '前群：背屈', { size: 27, fill: '#FFF4EE', stroke: red }),
      label(317, 248, 204, '外侧：外翻', { size: 27, fill: '#EEF4F5', stroke: navy }),
      label(576, 248, 206, '后群：跖屈', { size: 27, fill: '#FFF7E9', stroke: '#B4873E' }),
      label(548, 1106, 318, '腓肠肌：屈膝 + 跖屈', { size: 25, fill: '#FFFDF9', stroke: red })
    ]
  },
  {
    source: '05-05-bone-membranes-cells.png',
    output: '05-骨膜-骨内膜与骨细胞.png',
    title: '骨膜、骨内膜与骨细胞',
    tip: '骨原细胞→成骨细胞；破骨细胞不是同一来源。',
    titleSize: 44,
    overlays: [
      label(58, 364, 180, '骨膜（外）', { size: 27, fill: '#FFF4EE', stroke: red }),
      label(62, 1048, 180, '骨内膜（内）', { size: 27, fill: '#FFFDF9', stroke: navy }),
      label(388, 456, 352, '骨原细胞 → 成骨细胞 → 骨细胞', { size: 22, fill: '#FFFDF9', stroke: navy }),
      label(404, 830, 264, '破骨细胞：骨吸收', { size: 25, fill: '#FFF4EE', stroke: red })
    ]
  },
  {
    source: '06-06-pennate-muscles.png',
    output: '06-羽状肌.png',
    title: '羽状肌',
    tip: '肌束斜接肌腱，常以力量优势换取位移范围。',
    titleSize: 58,
    overlays: [
      label(40, 1134, 174, '平行肌', { size: 30, fill: '#FFFDF9', stroke: navy }),
      label(267, 1134, 174, '单羽肌', { size: 30, fill: '#FFF4EE', stroke: red }),
      label(493, 1134, 174, '双羽肌', { size: 30, fill: '#FFF4EE', stroke: red }),
      label(720, 1134, 174, '多羽肌', { size: 30, fill: '#FFF4EE', stroke: red }),
      label(314, 1224, 390, '羽状：肌束与肌腱成斜角', { size: 27, fill: '#FFFDF9', stroke: red })
    ]
  },
  {
    source: '07-07-respiratory-and-bone-connections.png',
    output: '07-呼吸系统与骨连结.png',
    title: '呼吸系统与骨连结',
    tip: '呼吸道＋肺；直接连结 → 半关节 → 关节。',
    titleSize: 45,
    overlays: [
      label(594, 194, 230, '呼吸道 + 肺', { size: 32, fill: '#FFF4EE', stroke: red }),
      label(54, 1116, 220, '直接连结（无腔）', { size: 23, fill: '#FFFDF9', stroke: navy }),
      label(390, 1116, 172, '半关节', { size: 27, fill: '#FFF4EE', stroke: red }),
      label(668, 1116, 238, '关节（有关节腔）', { size: 23, fill: '#FFFDF9', stroke: navy })
    ]
  }
];

function esc(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[char]);
}

function label(x, y, width, text, options = {}) {
  const {
    size = 26,
    fill = '#FFFDF9',
    stroke = border,
    color = ink,
    height = 62
  } = options;
  return `<g>
    <rect x="${x}" y="${y}" width="${width}" height="${height}" rx="17" fill="${fill}" fill-opacity="0.96" stroke="${stroke}" stroke-width="3"/>
    <text x="${x + width / 2}" y="${y + height / 2 + size * 0.34}" text-anchor="middle" font-family="${font}" font-size="${size}" font-weight="750" fill="${color}">${esc(text)}</text>
  </g>`;
}

function overlay(card) {
  const titleX = 60;
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect x="0" y="0" width="${W}" height="174" fill="${paper}"/>
    <rect x="0" y="1320" width="${W}" height="216" fill="${paper}"/>
    <text x="${titleX}" y="100" font-family="${font}" font-size="${card.titleSize}" font-weight="850" fill="${red}">${esc(card.title)}</text>
    <path d="M60 138 H962" stroke="${red}" stroke-width="5" opacity="0.82" stroke-linecap="round"/>
    <path d="M60 146 H770" stroke="${red}" stroke-width="3" opacity="0.35" stroke-linecap="round"/>
    ${card.overlays.join('')}
    <rect x="38" y="1372" width="948" height="116" rx="26" fill="${red}"/>
    <text x="76" y="1417" font-family="${font}" font-size="24" font-weight="850" fill="#FFFFFF">TIP</text>
    <path d="M76 1431 H142" stroke="#FFFFFF" stroke-width="3" opacity="0.8"/>
    <text x="164" y="1447" font-family="${font}" font-size="29" font-weight="800" fill="#FFFFFF">${esc(card.tip)}</text>
  </svg>`);
}

async function renderCard(card) {
  const source = path.join(rawDir, card.source);
  if (!fs.existsSync(source)) throw new Error(`Missing base image: ${source}`);
  const output = path.join(outDir, card.output);
  await sharp(source)
    .composite([
      { input: overlay(card), top: 0, left: 0 }
    ])
    .png()
    .toFile(output);
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const readyCards = cards.filter((card) => fs.existsSync(path.join(rawDir, card.source)));
  if (readyCards.length === 0) throw new Error('No successful reference-edit images are available to render.');
  for (const card of readyCards) await renderCard(card);
  const skipped = cards.filter((card) => !readyCards.includes(card));
  if (skipped.length) console.error(`Skipped failed reference-edit cards: ${skipped.map((card) => card.output).join(', ')}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
