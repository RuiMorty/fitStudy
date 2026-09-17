const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { parseArgs } = require('node:util');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
const { ROOT, checkSlideLayout, launchOptions } = require('./lib/study-template');

async function main() {
  const { values } = parseArgs({ options: { out: { type: 'string' }, day: { type: 'string' } } });
  if ((!values.out && !values.day) || (values.out && values.day)) throw new Error('Usage: node scripts/verify-study-package.js --day N (or --out isolated-test-directory)');
  if (values.day && (!/^[1-9]\d{0,2}$/.test(values.day))) throw new Error('Invalid day');
  const site = Boolean(values.day), day = `day${String(values.day).padStart(2, '0')}`;
  const output = site ? ROOT : path.resolve(values.out);
  const shots = site ? path.join(ROOT, 'runs', day, 'verification') : path.join(output, 'verification');
  const manifest = JSON.parse(fs.readFileSync(path.join(output, site ? `xhs/${day}/manifest.json` : 'manifest.json'), 'utf8'));
  const courseFile = site ? manifest.paths.html : 'lesson.html';
  const socialFile = site ? `${manifest.paths.xhs}/index.html` : 'xhs/index.html';
  assert.equal(manifest.status, 'ready');
  for (const file of manifest.files) assert.ok(fs.statSync(path.join(output, file)).size > 0, file);
  fs.mkdirSync(shots, { recursive: true });
  const browser = await chromium.launch(launchOptions());
  const context = await browser.newContext({ reducedMotion: 'reduce', deviceScaleFactor: 1 });
  await context.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (url.protocol === 'file:') return route.continue();
    if (url.origin !== 'http://fitstudy.test') return route.abort();
    const filename = path.resolve(ROOT, `.${decodeURIComponent(url.pathname)}${url.pathname.endsWith('/') ? 'index.html' : ''}`);
    if (!filename.startsWith(`${ROOT}${path.sep}`) || !fs.existsSync(filename)) return route.fulfill({ status: 404, body: '' });
    const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json', '.md': 'text/plain', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
    return route.fulfill({ path: filename, contentType: types[path.extname(filename)] || 'application/octet-stream' });
  });
  const errors = [], results = [];
  try {
    const page = await context.newPage();
    page.on('pageerror', (error) => errors.push(error.message));
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(pathToFileURL(path.join(output, courseFile)).href);
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].filter((img) => img.getAttribute('src')).map((img) => img.decode())); });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `horizontal overflow at ${width}`);
      assert.equal(await page.locator('.cover-image').count(), 0, 'catalog cover must not appear in the lesson');
      assert.equal(await page.locator('.figure img').count(), 1, 'lesson has one detail image');
      if (site) assert.equal(await page.locator('img[src*="thumbs/"]').count(), 0);
      await page.screenshot({ path: path.join(shots, `course-${width}.png`), fullPage: width === 1440 });
      const first = page.locator('.kp details').first();
      await first.locator('summary').click();
      assert.equal(await first.getAttribute('open'), '');
      assert.ok(await first.locator('.kp-body').isVisible());
      const card = page.locator('.flip').first();
      await card.click();
      assert.equal(await card.getAttribute('aria-pressed'), 'true');
      assert.ok((await card.boundingBox()).height === 168);
      await card.click();
      for (const quiz of await page.locator('.question').all()) {
        await quiz.locator('.check').click();
        assert.match(await quiz.locator('.answer').innerText(), /请先选择/);
        const answers = JSON.parse(await quiz.getAttribute('data-answers'));
        for (const value of answers) await quiz.locator(`input[value="${value}"]`).check();
        await quiz.locator('.check').click();
        assert.equal(await quiz.getAttribute('data-result'), 'correct');
      }
      await page.locator('[data-zoom]').click();
      assert.equal(await page.locator('dialog').getAttribute('open'), '');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('dialog').getAttribute('open'), null);
      await page.evaluate(() => document.querySelectorAll('.kp details').forEach((element) => { element.open = true; }));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `expanded overflow at ${width}`);
      results.push(`course ${width}px: images, layout, disclosure, cards, quizzes, zoom passed`);
    }
    await page.setViewportSize({ width: 1080, height: 1440 });
    await page.goto(`${pathToFileURL(path.join(output, socialFile))}?export=1`);
    await checkSlideLayout(page);
    assert.equal(await page.locator('.slide').count(), manifest.slides);
    for (const file of manifest.files.filter((file) => /^(?:cover|slide-\d+)\.png$/.test(path.basename(file)))) {
      const bytes = fs.readFileSync(path.join(output, file));
      assert.equal(bytes.subarray(1, 4).toString(), 'PNG');
      assert.equal(bytes.readUInt32BE(16), 1080);
      assert.equal(bytes.readUInt32BE(20), 1440);
    }
    // Prove the overflow gate rejects a visibly broken page.
    await page.locator('.slide h1').first().evaluate((element) => { element.style.fontSize = '500px'; });
    await assert.rejects(() => checkSlideLayout(page), /overlap|overflow|outside/);
    for (const width of [320, 390, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      if (site) {
        await page.goto(pathToFileURL(path.join(output, socialFile)).href);
        await page.locator('.slide').first().waitFor();
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        await page.screenshot({ path: path.join(shots, `xhs-${width}.png`) });
        continue;
      }
      await page.goto(pathToFileURL(path.join(output, 'index.html')).href);
      await page.locator('[data-view="xhs/index.html"]').click();
      await page.frameLocator('iframe').locator('.slide').first().waitFor();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: path.join(shots, `preview-xhs-${width}.png`) });
      await page.locator('[data-view="lesson.html"]').click();
      await page.frameLocator('iframe').locator('.kp').waitFor();
    }
    if (site) {
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        await page.goto('http://fitstudy.test/library/');
        const card = page.locator(`.lesson-card[data-day="${manifest.day}"]`);
        await card.scrollIntoViewIfNeeded();
        assert.equal(await card.locator('.thumb img').getAttribute('src'), manifest.paths.thumbnail);
        await card.locator('.thumb img').evaluate((image) => image.decode());
        await page.screenshot({ path: path.join(shots, `catalog-${width}.png`) });
        for (const target of ['.thumb', 'h2', '.phase-line', '.card-action']) {
          await card.locator(target).click();
          await page.frameLocator('#modalBody iframe').locator('.kp').waitFor();
          assert.equal(await page.locator('#modalBody iframe').getAttribute('src'), manifest.paths.html);
          assert.equal(await page.frameLocator('#modalBody iframe').locator('.cover-image').count(), 0);
          await page.locator('#lessonModal button[data-close-modal]').click();
        }
      }
      results.push('catalog: thumbnail and all four card click targets reach the correct cover-free lesson');
    }
    assert.deepEqual(errors, []);
    results.push(`${manifest.slides} slides: layout and 1080x1440 PNG dimensions passed; broken-layout gate verified`);
    fs.writeFileSync(path.join(shots, 'report.json'), JSON.stringify({ status: 'passed', results }, null, 2));
    console.log(results.join('\n'));
  } finally { await context.close(); await browser.close(); }
}
main().catch((error) => { console.error(error.stack); process.exitCode = 1; });
