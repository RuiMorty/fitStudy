const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { launchOptions } = require('../../../scripts/lib/study-template');
const root = path.resolve(__dirname, '../../..');
const live = process.argv.includes('--live');
const origin = live ? 'https://fitstudy.cn' : 'http://fitstudy.test';
const mode = live ? 'live' : 'local';
const course = 'html/day42-自由重量-上肢杠铃技术.html';
const thumbnail = 'html/thumbs/day42-upper-body-barbell-technique-thumbnail.png';

(async () => {
  const browser = await chromium.launch(launchOptions());
  const context = await browser.newContext({ reducedMotion: 'reduce', deviceScaleFactor: 1 });
  if (!live) await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    const file = path.resolve(root, '.' + decodeURIComponent(url.pathname) + (url.pathname.endsWith('/') ? 'index.html' : ''));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) return route.fulfill({ status: 404, body: '' });
    const types = { '.html':'text/html', '.js':'application/javascript', '.css':'text/css', '.json':'application/json', '.md':'text/plain', '.svg':'image/svg+xml', '.png':'image/png', '.webp':'image/webp', '.jpg':'image/jpeg' };
    return route.fulfill({ path:file, contentType:types[path.extname(file)] || 'application/octet-stream' });
  });
  const errors = [], checks = [];
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', e => errors.push(e.message));
    await page.setViewportSize({ width:390, height:900 });
    await page.goto(origin + '/go/42/');
    await page.waitForURL(url => decodeURIComponent(url.pathname) === '/' + course);
    await page.locator('.kp').waitFor();
    const size = await page.locator('.figure img').evaluate(async img => { await img.decode(); return [img.naturalWidth, img.naturalHeight]; });
    assert.deepEqual(size, [3072, 2048]);
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
    await page.screenshot({ path:path.join(__dirname, `${mode}-course-390.png`) });
    checks.push('Shortlink reaches exact Day42 course; 3072x2048 detail, mobile layout, disclosure, flashcard, quizzes and zoom passed');
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height:1000 });
      await page.goto(origin + '/library/');
      const first = page.locator('.lesson-card').first();
      await first.waitFor();
      assert.equal(await first.getAttribute('data-day'), '42');
      const img = first.locator('.thumb img');
      assert.equal(await img.getAttribute('src'), thumbnail);
      const selected = await img.evaluate(async img => { await img.decode(); return {src:img.currentSrc, width:img.naturalWidth}; });
      assert.ok(selected.src.includes('day42-upper-body-barbell-technique-thumbnail.webp'));
      assert.equal(selected.width, 1600);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path:path.join(__dirname, `${mode}-catalog-${width}.png`) });
      await first.locator('.thumb').click();
      await page.frameLocator('#modalBody iframe').locator('.kp').waitFor();
      assert.equal(await page.locator('#modalBody iframe').getAttribute('src'), course);
      assert.equal(await page.frameLocator('#modalBody iframe').locator('.cover-image').count(), 0);
      await page.locator('#lessonModal button[data-close-modal]').click();
      checks.push(`Catalog ${width}px: Day42 first, WebP cover and course modal passed`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, `${mode}-browser-report.json`), JSON.stringify({status:'passed', checks, checkedAt:new Date().toISOString()}, null, 2) + '\n');
    console.log(checks.join('\n'));
  } finally { await context.close(); await browser.close(); }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
