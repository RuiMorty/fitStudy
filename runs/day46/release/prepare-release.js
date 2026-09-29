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
const releaseId = process.env.FITSTUDY_RELEASE_ID || `${new Date().toISOString().replace(/[-:.]/g, '')}-day46`;
const course = 'html/day46-软组织松解与关节活动度.html';
const thumbnail = 'html/thumbs/day46-soft-tissue-release-smr-thumbnail.png';
const thumbnailWebp = 'html/thumbs/day46-soft-tissue-release-smr-thumbnail.webp';
const detail = 'html/assets/阶段2训练科学/day46-软组织松解与关节活动度.png';
const shortlink = 'go/46/index.html';
const previous = {
  'app.js': '909088c0aa8e0e324fa9ff9f4509ee414efc25e8d0204e9b034ff6c35401732e',
  'library/index.html': 'ba943dacb3e87c54f32bf2a55304b5651b5a0fac960cb51bc60f9e9cc69ea562',
};

const html = read(course).toString();
assert.match(html, /Day 46 · 软组织松解与关节活动度/);
assert.match(html, /SMR在做什么：改变感觉，不是碾碎筋膜/);
assert.match(html, /筋膜球与按摩棒：小范围要更谨慎/);
assert.ok(html.includes('assets/阶段2训练科学/day46-软组织松解与关节活动度.png'));
assert.equal(read(thumbnail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
assert.equal(read(thumbnailWebp).subarray(0, 4).toString(), 'RIFF');
assert.equal(read(thumbnailWebp).subarray(8, 12).toString(), 'WEBP');
assert.equal(read(detail).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');

const baseApp = fs.readFileSync(path.join(release, 'server-before/app.js'));
assert.equal(sha(baseApp), previous['app.js'], 'remote app.js snapshot changed');
assert.ok(!baseApp.includes('publishedPages.set(46,'), 'Day46 already exists in remote app snapshot');
const publishedLine = baseApp.toString().split('\n').find((line) => line.startsWith('publishedPages.set(45,'));
assert.ok(publishedLine, 'Day45 entry is missing from remote app snapshot');
const encodedCourse = JSON.stringify(course).replace(/[\u0080-\uffff]/g, (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
let app = baseApp.toString().replace(publishedLine, `${publishedLine}\npublishedPages.set(46, ${encodedCourse});`);
const thumbnailLine = '  [45, "html/thumbs/day45-flexibility-stretching-pnf-thumbnail.png"],';
assert.ok(app.includes(thumbnailLine), 'Day45 thumbnail entry is missing from remote app snapshot');
app = app.replace(thumbnailLine, `${thumbnailLine}\n  [46, ${JSON.stringify(thumbnail)}],`);
assert.ok(app.includes('publishedPages.set(46,'), 'Day46 route missing');
assert.ok(app.includes('day46-soft-tissue-release-smr-thumbnail.png'), 'Day46 thumbnail missing');

const baseLibrary = fs.readFileSync(path.join(release, 'server-before/library-index.html'));
assert.equal(sha(baseLibrary), previous['library/index.html'], 'remote library snapshot changed');
const appScript = /app\.js\?v=[a-f0-9]+/g;
assert.equal([...baseLibrary.toString().matchAll(appScript)].length, 1, 'remote library must reference app.js exactly once');
const appHash = sha(Buffer.from(app));
const library = baseLibrary.toString().replace(appScript, `app.js?v=${appHash.slice(0, 12)}`);
assert.ok(library.includes(`app.js?v=${appHash.slice(0, 12)}`));

const target = `../../${encodeURI(course)}`;
const shortlinkHtml = `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="refresh" content="0; url=${target}" />
    <meta name="robots" content="noindex" />
    <title>正在前往 Day 46</title>
    <link rel="icon" type="image/svg+xml" href="../../html/assets/fitness-study-logo-open-circle.svg?v=a6d8e5caaa61" />
    <script>window.location.replace(${JSON.stringify(target)});</script>
  </head>
  <body>
    <p>正在前往 <a href="${target}">Day 46 课程页</a>。</p>
  </body>
</html>
`;

const staged = path.join(release, 'staged-site');
fs.mkdirSync(staged, { recursive: true });
fs.writeFileSync(path.join(staged, 'app.js'), app);
fs.writeFileSync(path.join(staged, 'library-index.html'), library);
fs.mkdirSync(path.join(staged, path.dirname(shortlink)), { recursive: true });
fs.writeFileSync(path.join(staged, shortlink), shortlinkHtml);
const inputs = new Map([
  [thumbnail, read(thumbnail)],
  [thumbnailWebp, read(thumbnailWebp)],
  [detail, read(detail)],
  [course, read(course)],
  [shortlink, Buffer.from(shortlinkHtml)],
  ['app.js', Buffer.from(app)],
  ['library/index.html', Buffer.from(library)],
]);
const manifest = {
  releaseId,
  day: 46,
  acceptedRevision: 'initial-smr-mobility-page04-mistake-removed',
  publicUrl: 'https://fitstudy.cn/go/46/',
  files: [...inputs].map(([name, bytes]) => ({ path: name, bytes: bytes.length, sha256: sha(bytes), previousSha256: previous[name] || null })),
};
assert.equal(manifest.files.length, 7);
fs.writeFileSync(path.join(release, 'release-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-day46-release-'));
try {
  fs.copyFileSync(path.join(release, 'release-manifest.json'), path.join(stage, 'release-manifest.json'));
  for (const record of manifest.files) {
    const destination = path.join(stage, record.path);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.writeFileSync(destination, inputs.get(record.path));
  }
  const archive = path.join(release, 'day46-site.tar.gz');
  execFileSync('tar', ['-czf', archive, '-C', stage, 'release-manifest.json', ...manifest.files.map((record) => record.path)], { env: { ...process.env, COPYFILE_DISABLE: '1' } });
  const members = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8' }).trim().split('\n');
  assert.deepEqual(new Set(members), new Set(['release-manifest.json', ...manifest.files.map((record) => record.path)]));
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}

console.log(`Prepared ${releaseId}: seven scoped Day46 files with validated remote base hashes.`);
