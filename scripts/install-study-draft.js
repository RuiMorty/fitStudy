const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const { parseArgs } = require('node:util');
const { ROOT, installPackage } = require('./lib/study-template');

// Reuse the approved package installer in isolation, then install only draft artifacts.
function installDraft(lesson, stage, root = ROOT) {
  const isolated = fs.mkdtempSync(path.join(os.tmpdir(), 'fitstudy-draft-install-'));
  try {
    const manifest = installPackage(lesson, stage, isolated);
    const { html, thumbnail, detail, xhs, archive } = manifest.paths;
    const allowed = (file) => [html, thumbnail, detail].includes(file) || file.startsWith(`${xhs}/`);
    if (/完整学习页：https?:\/\//.test(lesson.xhs.caption)) throw new Error('A local draft caption must not advertise a public learning URL');
    fs.writeFileSync(path.join(isolated, xhs, 'caption.txt'), `${lesson.xhs.caption.trimEnd()}\n`);
    const archivePath = path.join(isolated, archive);
    fs.unlinkSync(archivePath);
    const zipFiles = manifest.files.filter(file => file.startsWith(`${xhs}/`) && file !== archive).map(file => path.posix.relative(xhs, file));
    execFileSync('zip', ['-q', archivePath, ...zipFiles], { cwd: path.join(isolated, xhs) });
    manifest.files = manifest.files.filter(allowed);
    manifest.deliveryMode = 'local-draft';
    manifest.publishApproved = false;
    manifest.publicLearningUrl = null;
    const relativeManifest = `${xhs}/manifest.json`;
    const previousPath = path.join(root, relativeManifest);
    const previous = fs.existsSync(previousPath) ? JSON.parse(fs.readFileSync(previousPath, 'utf8')) : null;
    if (previous && (previous.id !== manifest.id || previous.template !== manifest.template || previous.deliveryMode !== 'local-draft')) throw new Error('Destination belongs to another package');
    const owned = new Set(previous?.files || []);
    for (const file of manifest.files) {
      const target = path.join(root, file);
      if (fs.existsSync(target) && !owned.has(file) && !fs.readFileSync(target).equals(fs.readFileSync(path.join(isolated, file)))) throw new Error(`Refusing to overwrite ${file}`);
    }
    fs.mkdirSync(path.join(root, xhs), { recursive: true });
    fs.writeFileSync(previousPath, `${JSON.stringify({ ...manifest, status: 'installing' }, null, 2)}\n`);
    for (const file of manifest.files) {
      fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
      fs.copyFileSync(path.join(isolated, file), path.join(root, file));
    }
    fs.writeFileSync(previousPath, `${JSON.stringify(manifest, null, 2)}\n`);
    return manifest;
  } finally { fs.rmSync(isolated, { recursive: true, force: true }); }
}

if (require.main === module) {
  try {
    const { values } = parseArgs({ options: { input: { type: 'string' }, from: { type: 'string' } } });
    if (!values.input || !values.from) throw new Error('Usage: node scripts/install-study-draft.js --input lesson.json --from rendered-stage');
    console.log(JSON.stringify(installDraft(JSON.parse(fs.readFileSync(values.input, 'utf8')), path.resolve(values.from)), null, 2));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { installDraft };
