const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

const root = __dirname;
const W = 1080;
const H = 1440;
const paper = '#F8F2E9';
const red = '#B44339';
const oldCover = path.join(root, '..', '2026-09-21-anatomy', '2026-09-21-错题复盘-封面.png');
const scene = path.join(root, 'cover-rick-door-raw.png');
const output = path.join(root, '2026-09-22-错题复盘-封面.png');

function svg(inner) {
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <style>.cn { font-family: 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif; }</style>
    ${inner}
  </svg>`);
}

async function makeLogo() {
  // The previous cover supplies the already-approved black brand mark. Its
  // background is the same paper color as this header, so no new logo is made.
  return sharp(oldCover).extract({ left: 76, top: 115, width: 92, height: 106 }).png().toBuffer();
}

async function main() {
  for (const file of [oldCover, scene]) {
    if (!fs.existsSync(file)) throw new Error(`Missing source asset: ${file}`);
  }

  const [logo, rickDoorScene] = await Promise.all([
    makeLogo(),
    sharp(scene).resize({ height: 1080, withoutEnlargement: false }).png().toBuffer(),
  ]);
  const base = svg(`
    <rect width="1080" height="1440" fill="${paper}"/>
    <text class="cn" x="540" y="265" text-anchor="middle" fill="${red}" font-size="140" font-weight="900">错题复盘</text>
    <rect x="0" y="360" width="1080" height="1080" fill="#F7EDE0"/>
    <path d="M0 360 H1080" stroke="#FFF9F0" stroke-width="6" opacity=".86"/>
    <path d="M355 360 V1440" stroke="#E0D2C3" stroke-width="3" opacity=".5"/>
  `);

  await sharp({ create: { width: W, height: H, channels: 4, background: paper } })
    .composite([
      { input: base, top: 0, left: 0 },
      { input: logo, top: 6, left: 54 },
      { input: rickDoorScene, top: 360, left: 360 },
    ])
    .png()
    .toFile(output);

  const meta = await sharp(output).metadata();
  if (meta.width !== W || meta.height !== H) throw new Error(`Unexpected output size: ${meta.width}x${meta.height}`);
  console.log(output);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
