const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { parseArgs } = require('node:util');
const { buildPackage, exportSlides, installPackage, launchOptions } = require('./lib/study-template');

async function main() {
  const { values } = parseArgs({ options: { input: { type: 'string' }, out: { type: 'string' }, 'html-only': { type: 'boolean', default: false } } });
  if (!values.input) throw new Error('Usage: node scripts/render-study-package.js --input lesson.json [--out isolated-test-directory] [--html-only]');
  if (values['html-only'] && !values.out) throw new Error('--html-only requires an isolated --out directory; incomplete packages are not installed');
  const lesson = JSON.parse(fs.readFileSync(values.input, 'utf8'));
  const output = values.out ? path.resolve(values.out) : fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-render-'));
  try {
    const manifest = buildPackage(lesson, output);
    if (!values['html-only']) {
      const { chromium } = require('playwright');
      const browser = await chromium.launch(launchOptions());
      try { await exportSlides(output, manifest, browser); } finally { await browser.close(); }
    }
    console.log(JSON.stringify(values.out ? { output, ...manifest } : installPackage(lesson, output), null, 2));
  } finally { if (!values.out) fs.rmSync(output, { recursive: true, force: true }); }
}

main().catch((error) => { console.error(error.message); process.exitCode = 1; });
