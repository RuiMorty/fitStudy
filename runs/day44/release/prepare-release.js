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
const releaseId = process.env.FITSTUDY_RELEASE_ID || `${new Date().toISOString().replace(/[-:.]/g, '').replace('T', 'T').replace('Z', 'Z')}-day44`;
const course = 'html/day44-核心训练技术应用与PNF对角线.html';
const thumbnail = 'html/thumbs/day44-core-training-pnf-diagonals-thumbnail.png';
const thumbnailWebp = 'html/thumbs/day44-core-training-pnf-diagonals-thumbnail.webp';
const detail = 'html/assets/阶段2训练科学/day44-核心训练技术应用与PNF对角线.png';
const shortlink = 'go/44/index.html';
const previous = {
  'app.js': '032f10cab9ae1063fe9a504a2e1cf24cec4d787dafe89923b2b7a006c9767263',
  'library/index.html': 'e90c7d87664a18be51493cff751776c4f502ca5375c57167f43958b53b5619ca',
};

const html = read(course).toString();
assert.match(html, /Day 44 · 核心训练技术应用与PNF对角线/);
assert.match(html, /核心训练不等于反复卷腹/);
assert.ok(html.includes('assets/阶段2训练科学/day44-核心训练技术应用与PNF对角线.png'));
assert.equal(read(thumbnail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
assert.equal(read(thumbnailWebp).subarray(0, 4).toString(), 'RIFF');
assert.equal(read(thumbnailWebp).subarray(8, 12).toString(), 'WEBP');
assert.equal(read(detail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
assert.match(read(shortlink).toString(), /day44-%E6%A0%B8%E5%BF%83%E8%AE%AD%E7%BB%83%E6%8A%80%E6%9C%AF%E5%BA%94%E7%94%A8%E4%B8%8EPNF%E5%AF%B9%E8%A7%92%E7%BA%BF\.html/);

const baseApp = fs.readFileSync(path.join(release, 'server-before/app.js'));
assert.equal(sha(baseApp), previous['app.js'], 'remote app.js snapshot changed');
assert.ok(!baseApp.includes('publishedPages.set(44,'), 'Day44 already exists in remote app snapshot');
const publishedLine = baseApp.toString().split('\n').find((line) => line.startsWith('publishedPages.set(43,'));
assert.ok(publishedLine, 'Day43 entry is missing from remote app snapshot');
const encodedCourse = JSON.stringify(course).replace(/[\u0080-\uffff]/g, (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
let app = baseApp.toString().replace(publishedLine, `${publishedLine}\npublishedPages.set(44, ${encodedCourse});`);
const thumbnailLine = '  [43, "html/thumbs/day43-dumbbell-kettlebell-machine-bodyweight-thumbnail.png"],';
assert.ok(app.includes(thumbnailLine), 'Day43 thumbnail entry is missing from remote app snapshot');
app = app.replace(thumbnailLine, `${thumbnailLine}\n  [44, ${JSON.stringify(thumbnail)}],`);
assert.ok(app.includes('publishedPages.set(44,'));
assert.ok(app.includes('day44-core-training-pnf-diagonals-thumbnail.png'));

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
  day: 44,
  acceptedRevision: 'revision-09-distributed-inline-emphases',
  publicUrl: 'https://fitstudy.cn/go/44/',
  files: [...inputs].map(([name, bytes]) => ({ path: name, bytes: bytes.length, sha256: sha(bytes), previousSha256: previous[name] || null })),
};
assert.equal(manifest.files.length, 7);
fs.writeFileSync(path.join(release, 'release-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-day44-release-'));
try {
  fs.copyFileSync(path.join(release, 'release-manifest.json'), path.join(stage, 'release-manifest.json'));
  for (const record of manifest.files) {
    const target = path.join(stage, record.path);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, inputs.get(record.path));
  }
  const archive = path.join(release, 'day44-site.tar.gz');
  fs.rmSync(archive, { force: true });
  execFileSync('tar', ['-czf', archive, '-C', stage, 'release-manifest.json', ...manifest.files.map((record) => record.path)], { env: { ...process.env, COPYFILE_DISABLE: '1' } });
  const members = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8' }).trim().split('\n');
  assert.deepEqual(new Set(members), new Set(['release-manifest.json', ...manifest.files.map((record) => record.path)]));
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}

console.log(`Prepared ${releaseId}: seven scoped Day44 files with validated remote base hashes.`);
