const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '../../..');
const release = __dirname;
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const read = (name) => fs.readFileSync(path.join(root, name));
const releaseId = process.env.FITSTUDY_RELEASE_ID || `${new Date().toISOString().replace(/[-:.]/g, '')}-day45`;
const course = 'html/day45-柔韧性分类与拉伸技术.html';
const thumbnail = 'html/thumbs/day45-flexibility-stretching-pnf-thumbnail.png';
const thumbnailWebp = 'html/thumbs/day45-flexibility-stretching-pnf-thumbnail.webp';
const detail = 'html/assets/阶段2训练科学/day45-柔韧性分类与拉伸技术.png';
const shortlink = 'go/45/index.html';
const previous = {
  'app.js': 'e5f2328ff3d8fc6708efff8923e0b084c8fd1bb46decbcca98e88acd3c5293ed',
  'library/index.html': '694a0a429116334da0a7e9d5a89e488321643622e6d446a04631585227c11dc0',
};

const html = read(course).toString();
assert.match(html, /Day 45 · 柔韧性分类与拉伸技术/);
assert.match(html, /PNF三法：CR、HR与CRAC/);
assert.match(html, /仰卧抬腿|仰卧抱大腿/);
assert.ok(html.includes('assets/阶段2训练科学/day45-柔韧性分类与拉伸技术.png'));
assert.equal(read(thumbnail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
assert.equal(read(thumbnailWebp).subarray(0, 4).toString(), 'RIFF');
assert.equal(read(thumbnailWebp).subarray(8, 12).toString(), 'WEBP');
assert.equal(read(detail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
assert.match(read(shortlink).toString(), /day45-%E6%9F%94%E9%9F%A7%E6%80%A7%E5%88%86%E7%B1%BB%E4%B8%8E%E6%8B%89%E4%BC%B8%E6%8A%80%E6%9C%AF\.html/);

const baseApp = fs.readFileSync(path.join(release, 'server-before/app.js'));
assert.equal(sha(baseApp), previous['app.js'], 'remote app.js snapshot changed');
assert.ok(!baseApp.includes('publishedPages.set(45,'), 'Day45 already exists in remote app snapshot');
const publishedLine = baseApp.toString().split('\n').find((line) => line.startsWith('publishedPages.set(44,'));
assert.ok(publishedLine, 'Day44 entry is missing from remote app snapshot');
const encodedCourse = JSON.stringify(course).replace(/[\u0080-\uffff]/g, (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
let app = baseApp.toString().replace(publishedLine, `${publishedLine}\npublishedPages.set(45, ${encodedCourse});`);
const thumbnailLine = '  [44, "html/thumbs/day44-core-training-pnf-diagonals-thumbnail.png"],';
assert.ok(app.includes(thumbnailLine), 'Day44 thumbnail entry is missing from remote app snapshot');
app = app.replace(thumbnailLine, `${thumbnailLine}\n  [45, ${JSON.stringify(thumbnail)}],`);
assert.ok(app.includes('publishedPages.set(45,'), 'Day45 route missing');
assert.ok(app.includes('day45-flexibility-stretching-pnf-thumbnail.png'), 'Day45 thumbnail missing');

const baseLibrary = fs.readFileSync(path.join(release, 'server-before/library-index.html'));
assert.equal(sha(baseLibrary), previous['library/index.html'], 'remote library snapshot changed');
const appScript = /app\.js\?v=[a-f0-9]+/g;
assert.equal([...baseLibrary.toString().matchAll(appScript)].length, 1, 'remote library must reference app.js exactly once');
const appHash = sha(Buffer.from(app));
const library = baseLibrary.toString().replace(appScript, `app.js?v=${appHash.slice(0, 12)}`);
assert.ok(library.includes(`app.js?v=${appHash.slice(0, 12)}`));

const staged = path.join(release, 'staged-site');
fs.mkdirSync(staged, { recursive: true });
fs.writeFileSync(path.join(staged, 'app.js'), app);
fs.writeFileSync(path.join(staged, 'library-index.html'), library);
const inputs = new Map([
  [thumbnail, read(thumbnail)],
  [thumbnailWebp, read(thumbnailWebp)],
  [detail, read(detail)],
  [course, read(course)],
  [shortlink, read(shortlink)],
  ['app.js', Buffer.from(app)],
  ['library/index.html', Buffer.from(library)],
]);
const manifest = {
  releaseId,
  day: 45,
  acceptedRevision: 'revision-01-visual-anatomy-and-action-examples',
  publicUrl: 'https://fitstudy.cn/go/45/',
  files: [...inputs].map(([name, bytes]) => ({ path: name, bytes: bytes.length, sha256: sha(bytes), previousSha256: previous[name] || null })),
};
assert.equal(manifest.files.length, 7);
fs.writeFileSync(path.join(release, 'release-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-day45-release-'));
try {
  fs.copyFileSync(path.join(release, 'release-manifest.json'), path.join(stage, 'release-manifest.json'));
  for (const record of manifest.files) {
    const target = path.join(stage, record.path);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, inputs.get(record.path));
  }
  const archive = path.join(release, 'day45-site.tar.gz');
  execFileSync('tar', ['-czf', archive, '-C', stage, 'release-manifest.json', ...manifest.files.map((record) => record.path)], { env: { ...process.env, COPYFILE_DISABLE: '1' } });
  const members = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8' }).trim().split('\n');
  assert.deepEqual(new Set(members), new Set(['release-manifest.json', ...manifest.files.map((record) => record.path)]));
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}

console.log(`Prepared ${releaseId}: seven scoped Day45 files with validated remote base hashes.`);
