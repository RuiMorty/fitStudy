const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const { ROOT, buildPackage, sitePaths } = require('../scripts/lib/study-template');
const { installDraft } = require('../scripts/install-study-draft');

function fixture(t) {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-draft-test-'));
  t.after(() => fs.rmSync(work, { recursive: true, force: true }));
  const lesson = JSON.parse(fs.readFileSync(path.join(ROOT, 'runs/day40/lesson.json')));
  lesson.xhs.caption = '本地学习草稿，尚未发布公开学习链接。';
  const stage = path.join(work, 'stage'), root = path.join(work, 'site');
  fs.mkdirSync(root);
  const manifest = buildPackage(lesson, stage);
  const image = fs.readFileSync(path.join(ROOT, lesson.cover.src));
  for (let i = 0; i < manifest.slides; i++) fs.writeFileSync(path.join(stage, 'xhs', i ? `slide-${String(i).padStart(2, '0')}.png` : 'cover.png'), image);
  manifest.status = 'ready';
  fs.writeFileSync(path.join(stage, 'manifest.json'), JSON.stringify(manifest));
  return { lesson, stage, root };
}

test('local draft strips the automatic public URL from text and archive and never installs shortlinks or site indexes', t => {
  const { lesson, stage, root } = fixture(t);
  fs.writeFileSync(path.join(root, 'progress.json'), '{"day":39}');
  const manifest = installDraft(lesson, stage, root);
  assert.equal(manifest.status, 'ready');
  assert.equal(manifest.deliveryMode, 'local-draft');
  assert.equal(manifest.publicLearningUrl, null);
  assert.equal(fs.readFileSync(path.join(root, 'progress.json'), 'utf8'), '{"day":39}');
  for (const forbidden of ['go', 'home', 'library', 'app.js', '.progress.json']) assert.ok(!fs.existsSync(path.join(root, forbidden)), forbidden);
  const caption = fs.readFileSync(path.join(root, manifest.paths.xhs, 'caption.txt'), 'utf8');
  assert.equal(caption, `${lesson.xhs.caption}\n`);
  assert.equal(execFileSync('unzip', ['-p', path.join(root, manifest.paths.archive), 'caption.txt'], { encoding: 'utf8' }), caption);
  assert.ok(manifest.files.every(file => !file.startsWith('go/')));
});

test('draft preflight refuses an unknown existing course before installing any package files', t => {
  const { lesson, stage, root } = fixture(t);
  const target = path.join(root, sitePaths(lesson).html);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, 'user-owned course');
  assert.throws(() => installDraft(lesson, stage, root), /Refusing to overwrite/);
  assert.equal(fs.readFileSync(target, 'utf8'), 'user-owned course');
  assert.ok(!fs.existsSync(path.join(root, 'xhs')));
});
