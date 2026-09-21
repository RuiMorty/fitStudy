const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const { launchOptions } = require('../../../scripts/lib/study-template');

const root = path.resolve(__dirname, '../../..');
const release = __dirname;
const live = process.argv.includes('--live');
const origin = live ? 'https://fitstudy.cn' : 'http://fitstudy.test';
const mode = live ? 'live' : 'local';
const course = 'html/day44-核心训练技术应用与PNF对角线.html';
const thumbnail = 'html/thumbs/day44-core-training-pnf-diagonals-thumbnail.png';

function localFile(url) {
  if (url.pathname === '/app.js') return path.join(release, 'staged-site/app.js');
  if (url.pathname === '/library/' || url.pathname === '/library/index.html') return path.join(release, 'staged-site/library-index.html');
  return path.resolve(root, `.${decodeURIComponent(url.pathname)}${url.pathname.endsWith('/') ? 'index.html' : ''}`);
}

(async () => {
  const browser = await chromium.launch(launchOptions());
  const context = await browser.newContext({ reducedMotion: 'reduce', deviceScaleFactor: 1 });
  if (!live) await context.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    const file = localFile(url);
    if (!file.startsWith(`${root}${path.sep}`) || !fs.existsSync(file)) return route.fulfill({ status: 404, body: '' });
    const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.md': 'text/plain', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
    return route.fulfill({ path: file, contentType: types[path.extname(file)] || 'application/octet-stream' });
  });
  const errors = [], checks = [];
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', (error) => errors.push(error.message));
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(`${origin}/go/44/`);
    await page.waitForURL((url) => decodeURIComponent(url.pathname) === `/${course}`);
    await page.locator('.kp').waitFor();
    const detailSize = await page.locator('.figure img').evaluate(async (image) => { await image.decode(); return [image.naturalWidth, image.naturalHeight]; });
    assert.deepEqual(detailSize, [3072, 2048]);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    const disclosure = page.locator('.kp details').first();
    await disclosure.locator('summary').click();
    assert.equal(await disclosure.getAttribute('open'), '');
    await page.locator('.flip').first().click();
    assert.equal(await page.locator('.flip').first().getAttribute('aria-pressed'), 'true');
    for (const quiz of await page.locator('.question').all()) {
      const answers = JSON.parse(await quiz.getAttribute('data-answers'));
      for (const answer of answers) await quiz.locator(`input[value="${answer}"]`).check();
      await quiz.locator('.check').click();
      assert.equal(await quiz.getAttribute('data-result'), 'correct');
    }
    await page.locator('[data-zoom]').click();
    assert.equal(await page.locator('dialog').getAttribute('open'), '');
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('dialog').getAttribute('open'), null);
    await page.screenshot({ path: path.join(release, `${mode}-course-390.png`) });
    checks.push('Shortlink reaches exact Day44 course; 3072x2048 detail, mobile layout, disclosure, flashcard, quizzes and zoom passed');
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(`${origin}/library/`);
      const first = page.locator('.lesson-card').first();
      await first.waitFor();
      assert.equal(await first.getAttribute('data-day'), '44');
      const image = first.locator('.thumb img');
      assert.equal(await image.getAttribute('src'), thumbnail);
      await page.waitForFunction((selector) => {
        const element = document.querySelector(selector);
        return Boolean(element && element.complete);
      }, '.lesson-card:first-child .thumb img');
      const selected = await image.evaluate(async (element) => {
        await element.decode();
        return { src: element.currentSrc, width: element.naturalWidth };
      });
      assert.ok(selected.src.includes('day44-core-training-pnf-diagonals-thumbnail.webp'), JSON.stringify(selected));
      assert.equal(selected.width, 1600);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: path.join(release, `${mode}-catalog-${width}.png`) });
      await first.locator('.thumb').click();
      await page.frameLocator('#modalBody iframe').locator('.kp').waitFor();
      assert.equal(await page.locator('#modalBody iframe').getAttribute('src'), course);
      assert.equal(await page.frameLocator('#modalBody iframe').locator('.cover-image').count(), 0);
      await page.locator('#lessonModal button[data-close-modal]').click();
      checks.push(`Catalog ${width}px: Day44 first, WebP cover and course modal passed`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(release, `${mode}-browser-report.json`), `${JSON.stringify({ status: 'passed', checks, checkedAt: new Date().toISOString() }, null, 2)}\n`);
    console.log(checks.join('\n'));
  } finally {
    await context.close();
    await browser.close();
  }
})().catch((error) => { console.error(error.stack); process.exitCode = 1; });
