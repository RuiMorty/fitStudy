const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
const { launchOptions, checkSlideLayout } = require('../../../scripts/lib/study-template');

async function main() {
  const root = path.resolve(__dirname, '../../..');
  const lesson = JSON.parse(fs.readFileSync(path.join(root, 'runs/day43/lesson.json')));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'xhs/day43/manifest.json')));
  const hash = file => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex');
  const points = new Set(lesson.xhs.points.map(point => hash(point.image.src)));
  const overview = lesson.xhs.overview.items.map(item => hash(item.image.src));
  assert.equal(new Set(overview).size, 6);
  assert.ok(overview.every(value => !points.has(value)));
  const browser = await chromium.launch(launchOptions());
  const context = await browser.newContext({ viewport: { width: 1080, height: 1440 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
  await context.route('**/*', route => route.request().url().startsWith('file:') ? route.continue() : route.abort());
  try {
    const page = await context.newPage();
    await page.goto(pathToFileURL(path.join(root, 'xhs/day43/index.html')).href + '?export=1');
    await checkSlideLayout(page);
    assert.equal(await page.locator('.slide').count(), 11);
    assert.equal(await page.locator('.point .block').count(), 27);
    assert.equal(await page.locator('.point .block li').count(), 81);
    assert.equal(await page.locator('.overview-item').count(), 6);
    assert.doesNotMatch(await page.locator('body').innerText(), /FitnessStudy|健身学习/);
    const slots = await page.locator('.point .visual').evaluateAll(elements => elements.map(element => {
      const r = element.getBoundingClientRect();
      return { width: r.width, height: r.height, tag: element.tagName, fit: getComputedStyle(element).objectFit };
    }));
    assert.ok(slots.every(slot => slot.width === 936 && slot.height === 240 && slot.tag === 'IMG' && slot.fit === 'contain'));
    const flipReports = [];
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(pathToFileURL(path.join(root, manifest.paths.html)).href);
      await page.evaluate(() => document.fonts.ready);
      for (const card of await page.locator('.flip').all()) {
        for (const flipped of [false, true]) {
          if (flipped) await card.click();
          assert.equal(await card.getAttribute('aria-pressed'), String(flipped));
          const face = card.locator(flipped ? '.back' : '.front');
          if (flipped) {
            assert.equal(await face.getAttribute('aria-hidden'), 'false');
            assert.equal(await card.locator('.front').getAttribute('aria-hidden'), 'true');
          } else {
            assert.notEqual(await face.getAttribute('aria-hidden'), 'true');
          }
          const dimensions = await face.evaluate(element => ({ h: element.clientHeight, sh: element.scrollHeight, w: element.clientWidth, sw: element.scrollWidth }));
          assert.ok(dimensions.sh <= dimensions.h + 1 && dimensions.sw <= dimensions.w + 1, `flashcard overflow at ${width}: ${JSON.stringify(dimensions)}`);
        }
      }
      flipReports.push({ width, cards: 8, checkedFaces: 16, overflow: false });
      for (const question of await page.locator('.question').all()) {
        const answers = JSON.parse(await question.getAttribute('data-answers'));
        const inputs = question.locator('input');
        const count = await inputs.count();
        const wrong = Array.from({ length: count }, (_, i) => i).find(i => !answers.includes(i));
        await inputs.nth(wrong).check();
        await question.locator('.check').click();
        assert.equal(await question.getAttribute('data-result'), 'wrong');
      }
    }
    fs.writeFileSync(path.join(__dirname, 'final-validation.json'), JSON.stringify({
      status: 'passed', checkedAt: new Date().toISOString(), independentOverviewImages: 6,
      overviewAndKnowledgeImagesDisjoint: true, textCards: 27, bulletItems: 81,
      imageSlots: slots, flashcards: flipReports, incorrectQuizFeedback: 'passed at four widths',
      visibleBrandText: 'absent'
    }, null, 2) + '\n');
    console.log('Independent artwork, all text blocks, 936x240 slots, all flashcard faces and wrong-answer feedback passed.');
  } finally { await context.close(); await browser.close(); }
}
main().catch(error => { console.error(error.stack); process.exitCode = 1; });
