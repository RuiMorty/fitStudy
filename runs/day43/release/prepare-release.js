const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '../../..');
const release = __dirname;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = name => fs.readFileSync(path.join(root, name));
const releaseId = process.env.FITSTUDY_RELEASE_ID || `${new Date().toISOString().replace(/[-:.]/g, '').replace('T', 'T').replace('Z', 'Z')}-day43`;

const previous = {
  'app.js': '8252518f0365273a471ee1e7a2dc5454a5b14c3445659d711c195cd401f77870',
  'library/index.html': '2a5d3f95b4bd6a7c14de57f10b0d23dbfa6fd6984bbc9725e20483dd48e4baed',
};
const files = [
  'html/thumbs/day43-dumbbell-kettlebell-machine-bodyweight-thumbnail.png',
  'html/thumbs/day43-dumbbell-kettlebell-machine-bodyweight-thumbnail.webp',
  'html/assets/阶段2训练科学/day43-哑铃、壶铃、固定器械与自重训练.png',
  'html/day43-哑铃、壶铃、固定器械与自重训练.html',
  'go/43/index.html',
  'app.js',
  'library/index.html',
];

const html = read('html/day43-哑铃、壶铃、固定器械与自重训练.html').toString();
assert.match(html, /Day 43 · 哑铃、壶铃、固定器械与自重训练/);
assert.match(html, /固定器械：先调设置，再选负荷/);
const app = read('app.js').toString();
assert.ok(app.includes('publishedPages.set(43,'));
assert.ok(app.includes('day43-dumbbell-kettlebell-machine-bodyweight-thumbnail.png'));
const appHash = sha(Buffer.from(app));
const library = read('library/index.html').toString();
assert.ok(library.includes(`app.js?v=${appHash.slice(0, 12)}`), 'library cache key must match app.js');
const png = read(files[0]);
assert.equal(png.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
const webp = read(files[1]);
assert.equal(webp.subarray(0, 4).toString(), 'RIFF');
assert.equal(webp.subarray(8, 12).toString(), 'WEBP');

const manifest = {
  releaseId,
  day: 43,
  acceptedRevision: 'revision-03',
  publicUrl: 'https://fitstudy.cn/go/43/',
  files: files.map(name => {
    const bytes = read(name);
    return { path: name, bytes: bytes.length, sha256: sha(bytes), previousSha256: previous[name] || null };
  }),
};
assert.equal(manifest.files.length, 7);
fs.writeFileSync(path.join(release, 'release-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-day43-release-'));
try {
  fs.copyFileSync(path.join(release, 'release-manifest.json'), path.join(stage, 'release-manifest.json'));
  for (const record of manifest.files) {
    const target = path.join(stage, record.path);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, record.path), target);
  }
  const archive = path.join(release, 'day43-site.tar.gz');
  fs.rmSync(archive, { force: true });
  execFileSync('tar', ['-czf', archive, '-C', stage, 'release-manifest.json', ...manifest.files.map(record => record.path)], {
    env: { ...process.env, COPYFILE_DISABLE: '1' },
  });
  const members = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8' }).trim().split('\n');
  assert.deepEqual(new Set(members), new Set(['release-manifest.json', ...manifest.files.map(record => record.path)]));
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}

console.log(`Prepared ${releaseId}: seven scoped Day43 files with validated hashes.`);
