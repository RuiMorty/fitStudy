const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { ROOT, validateLesson, buildSlides, buildPackage, sitePaths, installPackage } = require('../scripts/lib/study-template');
const sample = () => JSON.parse(fs.readFileSync(path.join(ROOT, 'runs/day40/lesson.json'), 'utf8'));
function temporary(t) {
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-unit-'));
  t.after(() => fs.rmSync(output, { recursive: true, force: true }));
  return output;
}
function withExistingImages() {
  const lesson = sample();
  const src = 'html/thumbs/day29-training-adaptation-principles-thumbnail.png';
  for (const image of [lesson.cover, lesson.detailImage, ...lesson.xhs.points.map((point) => point.image)]) image.src = src;
  return lesson;
}
test('validate the complete course and preserve one point per slide', () => {
  const lesson = validateLesson(sample());
  const slides = buildSlides(lesson);
  assert.equal(slides.length, lesson.xhs.points.length + 2);
  assert.deepEqual(slides.slice(2).map(({ kind, ...point }) => point), lesson.xhs.points);
  assert.equal(slides[0].kind, 'cover');
  assert.equal(slides[1].kind, 'overview');
});
test('page count follows point count, not a hard-coded daily total', () => {
  const lesson = sample();
  lesson.xhs.points = lesson.xhs.points.slice(0, 4);
  assert.equal(buildSlides(validateLesson(lesson)).length, 6);
  delete lesson.xhs.overview;
  assert.equal(buildSlides(validateLesson(lesson)).length, 5);
});
test('reject per-day style overrides and invalid content', () => {
  for (const mutate of [
    (x) => { x.css = 'body{}'; },
    (x) => { x.xhs.points[0].fontSize = 12; },
    (x) => { x.knowledge[0].html = '<style></style>'; },
    (x) => { x.xhs.points[0].image.src = 'https://example.com/image.png'; },
    (x) => { x.cover.src = '../image.png'; },
    (x) => { x.quiz[0].answers = [8]; },
    (x) => { x.quiz[2].type = 'single'; },
    (x) => { x.day = 0; },
    (x) => { x.xhs.points[0].title = '字'.repeat(33); },
  ]) {
    const lesson = sample(); mutate(lesson);
    assert.throws(() => validateLesson(lesson));
  }
});
test('day changes only labels, never the layout, script or pagination', (t) => {
  const lesson = withExistingImages();
  const root = temporary(t), a = path.join(root, 'a'), b = path.join(root, 'b');
  buildPackage(lesson, a); lesson.day = 41; buildPackage(lesson, b);
  for (const file of ['lesson.html', 'xhs/index.html']) {
    assert.equal(fs.readFileSync(path.join(a, file), 'utf8').replaceAll('Day 40', 'Day 41'), fs.readFileSync(path.join(b, file), 'utf8'));
  }
});
test('preserve legacy website sections and use only the new brand image', (t) => {
  const output = temporary(t);
  const manifest = buildPackage(withExistingImages(), output);
  const html = fs.readFileSync(path.join(output, 'lesson.html'), 'utf8');
  assert.doesNotMatch(html, /cover-image/);
  assert.equal((html.match(/<figure\b/g) || []).length, 1);
  for (const heading of ['一句话总结', '核心要点', '常见误区', '记忆口诀', '翻转卡复习', '实操关联', '练习题']) assert.ok(html.includes(`<h2>${heading}</h2>`));
  assert.equal(manifest.status, 'html-ready');
  for (const file of ['lesson.html', 'xhs/index.html']) {
    const content = fs.readFileSync(path.join(output, file), 'utf8');
    assert.doesNotMatch(content, /FitnessStudy|Fitness<span>/i);
    assert.doesNotMatch(content, /class="brand"[^]*?<b>/);
    assert.doesNotMatch(content, /(?:src|href)="https?:/);
  }
});
test('escape text and never silently truncate content', (t) => {
  const lesson = withExistingImages(); lesson.title = '<script>& test';
  const output = temporary(t); buildPackage(lesson, output);
  const html = fs.readFileSync(path.join(output, 'lesson.html'), 'utf8');
  assert.ok(html.includes('&lt;script&gt;&amp; test'));
  assert.ok(html.includes(lesson.knowledge[0].details[0].body));
});
test('missing images fail before writing or changing output', (t) => {
  const lesson = withExistingImages(); lesson.cover.src = 'missing.png';
  const output = temporary(t);
  assert.throws(() => buildPackage(lesson, output), /missing missing.png/);
  assert.deepEqual(fs.readdirSync(output), []);
});
test('protect unrelated output and remove stale generated files on rebuild', (t) => {
  const output = temporary(t), note = path.join(output, 'notes.txt');
  fs.writeFileSync(note, 'keep');
  assert.throws(() => buildPackage(withExistingImages(), output), /empty directory/);
  fs.unlinkSync(note);
  buildPackage(withExistingImages(), output);
  fs.writeFileSync(path.join(output, 'xhs/slide-99.png'), 'stale');
  fs.writeFileSync(path.join(output, 'xhs.zip'), 'stale');
  fs.writeFileSync(note, 'keep');
  buildPackage(withExistingImages(), output);
  assert.ok(!fs.existsSync(path.join(output, 'xhs/slide-99.png')));
  assert.ok(!fs.existsSync(path.join(output, 'xhs.zip')));
  assert.equal(fs.readFileSync(note, 'utf8'), 'keep');
});

function stagedFixture(t) {
  const lesson = withExistingImages(), stage = temporary(t);
  const manifest = buildPackage(lesson, stage);
  const image = fs.readFileSync(path.join(ROOT, lesson.cover.src));
  for (let i = 0; i < manifest.slides; i += 1) fs.writeFileSync(path.join(stage, 'xhs', i ? `slide-${String(i).padStart(2, '0')}.png` : 'cover.png'), image);
  manifest.status = 'ready';
  fs.writeFileSync(path.join(stage, 'manifest.json'), JSON.stringify(manifest));
  return { lesson, stage };
}
test('canonical delivery separates the catalog cover, lesson image and XHS package', (t) => {
  const { lesson, stage } = stagedFixture(t), root = temporary(t);
  const manifest = installPackage(lesson, stage, root);
  assert.deepEqual(sitePaths(lesson), {
    html: 'html/day40-反馈与动作学习.html',
    thumbnail: 'html/thumbs/day40-feedback-motor-learning-thumbnail.png',
    detail: 'html/assets/阶段2训练科学/day40-反馈与动作学习.png',
    xhs: 'xhs/day40',
    archive: 'xhs/day40/day40-xhs.zip',
  });
  assert.equal(manifest.status, 'ready');
  for (const file of manifest.files) assert.ok(fs.existsSync(path.join(root, file)), file);
  const html = fs.readFileSync(path.join(root, manifest.paths.html), 'utf8');
  assert.match(html, /href="assets\/fitness-study-logo-open-circle\.svg\?v=[^"]+"/);
  assert.ok(html.includes('src="assets/阶段2训练科学/day40-反馈与动作学习.png"'));
  assert.doesNotMatch(html, /cover-image|thumbs\//);
  const social = fs.readFileSync(path.join(root, manifest.paths.xhs, 'index.html'), 'utf8');
  assert.match(social, /src="ai-visuals\/logo\.svg\?v=[^"]+"/);
  assert.match(social, /href="ai-visuals\/logo\.svg\?v=[^"]+"/);
  assert.doesNotMatch(social, /(?:src|href)="\.\.\//);
  assert.ok(fs.readFileSync(path.join(root, manifest.paths.xhs, 'cover.png')).equals(fs.readFileSync(path.join(stage, 'xhs/cover.png'))));
  assert.ok(!fs.existsSync(path.join(root, 'progress.json')));
});
test('canonical delivery refuses stale content or unknown existing lesson files', (t) => {
  const { lesson, stage } = stagedFixture(t), root = temporary(t);
  const changed = structuredClone(lesson); changed.xhs.points[0].lead += 'changed';
  assert.throws(() => installPackage(changed, stage, root), /content or template changed/);
  assert.deepEqual(fs.readdirSync(root), []);
  const file = path.join(root, sitePaths(lesson).html);
  fs.mkdirSync(path.dirname(file)); fs.writeFileSync(file, 'user content');
  assert.throws(() => installPackage(lesson, stage, root), /refusing to overwrite/);
  assert.equal(fs.readFileSync(file, 'utf8'), 'user content');
  assert.ok(!fs.existsSync(path.join(root, 'xhs')));
});

test('published HTML never uses the permanently cached unversioned logo URL', () => {
  const logoVersion = crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT, 'html/assets/fitness-study-logo-open-circle.svg'))).digest('hex').slice(0, 12);
  let references = 0;
  for (const directory of ['html', 'home', 'library']) {
    for (const filename of fs.readdirSync(path.join(ROOT, directory)).filter((name) => name.endsWith('.html'))) {
      const file = path.join(ROOT, directory, filename);
      const html = fs.readFileSync(file, 'utf8');
      for (const [, href] of html.matchAll(/(?:src|href)="([^"]*fitness-study-logo-open-circle\.svg[^"]*)"/g)) {
        assert.equal(new URL(href, 'https://fitstudy.test/').searchParams.get('v'), logoVersion, `${file}: stale logo URL`);
        references += 1;
      }
    }
  }
  assert.ok(references > 0);
});
