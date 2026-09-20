const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const lucide = require('lucide');
const { execFileSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '../..');
const TEMPLATE = path.join(ROOT, 'templates/study/v1');
const VERSION = 'study-day29-v1';
const LOGO = 'html/assets/fitness-study-logo-open-circle.svg';
const LOGO_CACHE_BUST = crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT, LOGO))).digest('hex').slice(0, 12);
const PUBLIC_ORIGIN = 'https://fitstudy.cn';
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const read = (name) => fs.readFileSync(path.join(TEMPLATE, name), 'utf8');
const number = (value) => String(value).padStart(2, '0');
const encodePath = (value) => value.split('/').map((part) => encodeURIComponent(part)).join('/');

function fail(field, message) { throw new Error(`${field}: ${message}`); }
function object(value, fields, field) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(field, 'must be an object');
  for (const key of Object.keys(value)) if (!fields.includes(key)) fail(`${field}.${key}`, 'unsupported field; per-lesson style overrides are forbidden');
}
function text(value, limit, field) {
  if (typeof value !== 'string' || !value.trim()) fail(field, 'must be non-empty text');
  if ([...value].length > limit) fail(field, `exceeds ${limit} characters; edit content, not CSS`);
}
function array(value, min, max, field) {
  if (!Array.isArray(value) || value.length < min || value.length > max) fail(field, `requires ${min}-${max} items`);
}
function texts(value, min, max, limit, field) {
  array(value, min, max, field);
  value.forEach((item, index) => text(item, limit, `${field}[${index}]`));
}
function image(value, field) {
  object(value, ['src', 'alt'], field);
  text(value.src, 260, `${field}.src`);
  text(value.alt, 120, `${field}.alt`);
  if (path.isAbsolute(value.src) || value.src.includes('..') || /[\\:]/.test(value.src) || !/\.(png|jpe?g|webp|svg)$/i.test(value.src)) fail(field, 'must reference a project-local image');
}

function validateLesson(lesson) {
  object(lesson, ['schemaVersion', 'id', 'day', 'stage', 'title', 'subtitle', 'cert', 'chips', 'cover', 'detailImage', 'detailCaption', 'summary', 'knowledge', 'mistakes', 'mnemonic', 'flashcards', 'practice', 'quiz', 'sources', 'xhs'], 'lesson');
  if (lesson.schemaVersion !== 1) fail('schemaVersion', 'expected 1');
  if (!/^[a-z0-9][a-z0-9-]{1,70}$/.test(lesson.id || '')) fail('id', 'use a lowercase slug');
  if (!Number.isInteger(lesson.day) || lesson.day < 1 || lesson.day > 999) fail('day', 'must be 1-999');
  if (lesson.stage !== undefined && !/^[\p{L}\p{N} _-]{1,40}$/u.test(lesson.stage)) fail('stage', 'must be a safe stage directory name');
  for (const [key, limit] of Object.entries({ title: 36, subtitle: 130, cert: 10, detailCaption: 160, summary: 200, mnemonic: 120 })) text(lesson[key], limit, key);
  texts(lesson.chips, 1, 3, 24, 'chips');
  image(lesson.cover, 'cover');
  image(lesson.detailImage, 'detailImage');
  array(lesson.knowledge, 4, 12, 'knowledge');
  lesson.knowledge.forEach((point, i) => {
    const field = `knowledge[${i}]`;
    object(point, ['title', 'summary', 'details'], field);
    text(point.title, 40, `${field}.title`);
    text(point.summary, 150, `${field}.summary`);
    array(point.details, 2, 6, `${field}.details`);
    point.details.forEach((detail, j) => {
      object(detail, ['title', 'body'], `${field}.details[${j}]`);
      text(detail.title, 24, `${field}.details[${j}].title`);
      text(detail.body, 650, `${field}.details[${j}].body`);
    });
  });
  array(lesson.mistakes, 2, 5, 'mistakes');
  lesson.mistakes.forEach((item, i) => {
    object(item, ['wrong', 'right'], `mistakes[${i}]`);
    text(item.wrong, 100, `mistakes[${i}].wrong`);
    text(item.right, 220, `mistakes[${i}].right`);
  });
  array(lesson.flashcards, 6, 10, 'flashcards');
  lesson.flashcards.forEach((item, i) => {
    object(item, ['question', 'answer'], `flashcards[${i}]`);
    text(item.question, 50, `flashcards[${i}].question`);
    text(item.answer, 85, `flashcards[${i}].answer`);
  });
  texts(lesson.practice, 4, 6, 220, 'practice');
  array(lesson.quiz, 4, 8, 'quiz');
  lesson.quiz.forEach((quiz, i) => {
    const field = `quiz[${i}]`;
    object(quiz, ['type', 'question', 'options', 'answers', 'explanation'], field);
    if (!['single', 'multi', 'case'].includes(quiz.type)) fail(field, 'expected single, multi or case');
    text(quiz.question, 240, `${field}.question`);
    texts(quiz.options, 2, 5, 150, `${field}.options`);
    array(quiz.answers, 1, quiz.type === 'multi' ? quiz.options.length : 1, `${field}.answers`);
    if (new Set(quiz.answers).size !== quiz.answers.length || quiz.answers.some((value) => !Number.isInteger(value) || value < 0 || value >= quiz.options.length)) fail(field, 'invalid answer indexes');
    text(quiz.explanation, 650, `${field}.explanation`);
  });
  for (const type of ['single', 'multi', 'case']) if (!lesson.quiz.some((quiz) => quiz.type === type)) fail('quiz', `missing ${type} question`);
  texts(lesson.sources, 1, 8, 250, 'sources');
  const social = lesson.xhs;
  object(social, ['title', 'coverTitle', 'subtitle', 'chips', 'overview', 'points', 'caption', 'tags'], 'xhs');
  text(social.title, 20, 'xhs.title');
  text(social.coverTitle, 32, 'xhs.coverTitle');
  text(social.subtitle, 80, 'xhs.subtitle');
  texts(social.chips, 1, 3, 24, 'xhs.chips');
  if (social.overview) {
    object(social.overview, ['title', 'lead'], 'xhs.overview');
    text(social.overview.title, 30, 'xhs.overview.title');
    text(social.overview.lead, 100, 'xhs.overview.lead');
  }
  array(social.points, 1, 18, 'xhs.points');
  social.points.forEach((point, i) => {
    const field = `xhs.points[${i}]`;
    object(point, ['title', 'lead', 'image', 'blocks'], field);
    text(point.title, 32, `${field}.title`);
    text(point.lead, 110, `${field}.lead`);
    image(point.image, `${field}.image`);
    array(point.blocks, 2, 3, `${field}.blocks`);
    point.blocks.forEach((block, j) => {
      object(block, ['title', 'bullets'], `${field}.blocks[${j}]`);
      text(block.title, 24, `${field}.blocks[${j}].title`);
      texts(block.bullets, 1, 3, 100, `${field}.blocks[${j}].bullets`);
    });
  });
  text(social.caption, 950, 'xhs.caption');
  texts(social.tags, 1, 8, 20, 'xhs.tags');
  return lesson;
}

function buildSlides(lesson) {
  return [{ kind: 'cover' }, ...(lesson.xhs.overview ? [{ kind: 'overview', ...lesson.xhs.overview }] : []), ...lesson.xhs.points.map((point) => ({ kind: 'point', ...point }))];
}
function icon(name) {
  return `<svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${lucide[name].map(([tag, attributes]) => `<${tag} ${Object.entries(attributes).map(([key, value]) => `${key}="${escapeHtml(value)}"`).join(' ')} />`).join('')}</svg>`;
}
function imagePaths(lesson) { return [...new Set([LOGO, lesson.cover.src, lesson.detailImage.src, ...lesson.xhs.points.map((point) => point.image.src)])]; }
function createAssets(lesson, output) {
  const assets = new Map();
  fs.mkdirSync(path.join(output, 'assets'), { recursive: true });
  for (const source of imagePaths(lesson)) {
    const bytes = fs.readFileSync(path.join(ROOT, source));
    const name = crypto.createHash('sha256').update(bytes).digest('hex').slice(0, 16) + path.extname(source).toLowerCase();
    fs.writeFileSync(path.join(output, 'assets', name), bytes);
    assets.set(source, `assets/${name}`);
  }
  return assets;
}
function picture(value, assets, className = '', prefix = '') { return `<img class="${className}" src="${prefix}${assets.get(value.src)}" alt="${escapeHtml(value.alt)}">`; }
function brand(lesson, assets, prefix = '') { return `<div class="brand"><img src="${prefix}${logoHref(assets.get(LOGO))}" alt="Logo"><span>${escapeHtml(lesson.cert)}</span></div>`; }
function logoHref(logo) { return logo && /(?:fitness-study-logo-open-circle|logo)\.svg$/.test(logo) ? `${logo}?v=${LOGO_CACHE_BUST}` : logo; }
function publicShortlink(lesson) { return `${PUBLIC_ORIGIN}/go/${lesson.day}/`; }
function captionText(lesson) {
  const caption = lesson.xhs.caption.trimEnd();
  return /完整学习页：https?:\/\//.test(caption) ? caption : `${caption}\n\n完整学习页：${publicShortlink(lesson)}`;
}
function shortlinkHtml(lesson, htmlPath) {
  const target = encodePath(path.posix.relative(`go/${lesson.day}`, htmlPath));
  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="refresh" content="0; url=${target}" />
    <meta name="robots" content="noindex" />
    <title>正在前往 Day ${lesson.day}</title>
    <link rel="icon" type="image/svg+xml" href="../../${LOGO}?v=${LOGO_CACHE_BUST}" />
    <script>window.location.replace("${target}");</script>
  </head>
  <body>
    <p>正在前往 <a href="${target}">Day ${lesson.day} 课程页</a>。</p>
  </body>
</html>
`;
}
function documentHtml(title, styles, body, script = '', logo = '') {
  return `<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(title)}</title><link rel="icon" type="image/svg+xml" href="${escapeHtml(logoHref(logo))}"><style>${read('tokens.css')}\n${styles}</style></head><body>${body}${script ? `<script>${script}</script>` : ''}</body></html>\n`;
}
function courseHtml(lesson, assets) {
  const knowledge = lesson.knowledge.map((point) => `<li><details><summary><span class="term">${escapeHtml(point.title)}</span>：${escapeHtml(point.summary)}</summary><div class="kp-body">${point.details.map((detail) => `<section class="detail-block"><h4>${escapeHtml(detail.title)}</h4><p>${escapeHtml(detail.body)}</p></section>`).join('')}</div></details></li>`).join('');
  const cards = lesson.flashcards.map((card) => `<button class="flip" aria-pressed="false"><span class="flip-in"><span class="face front">${escapeHtml(card.question)}</span><span class="face back" aria-hidden="true">${escapeHtml(card.answer)}</span></span></button>`).join('');
  const labels = { single: '单选', multi: '多选', case: '案例' };
  const quizzes = lesson.quiz.map((quiz, index) => `<section class="question" data-answers="${escapeHtml(JSON.stringify(quiz.answers))}" data-explanation="${escapeHtml(quiz.explanation)}"><h3>${index + 1}. ${labels[quiz.type]}：${escapeHtml(quiz.question)}</h3><div class="options">${quiz.options.map((option, i) => `<label class="option"><input type="${quiz.type === 'multi' ? 'checkbox' : 'radio'}" name="question-${index}" value="${i}"><span>${String.fromCharCode(65 + i)}. ${escapeHtml(option)}</span></label>`).join('')}</div><button class="check">查看解析</button><div class="answer" role="status" hidden></div></section>`).join('');
  const body = `<main><header class="header"><h1>Day ${lesson.day} · ${escapeHtml(lesson.title)}</h1><p class="sub">${escapeHtml(lesson.subtitle)}</p><div class="meta">${lesson.chips.map((chip) => `<span class="chip">${escapeHtml(chip)}</span>`).join('')}</div></header><section class="panel green"><h2>一句话总结</h2><p class="takeaway">${escapeHtml(lesson.summary)}</p></section><figure class="figure"><button data-zoom aria-label="放大详情图">${picture(lesson.detailImage, assets)}<span class="icon-button">${icon('Expand')}</span></button><figcaption class="caption">${escapeHtml(lesson.detailCaption)}</figcaption></figure><section class="panel"><h2>核心要点</h2><ul class="kp">${knowledge}</ul></section><section class="warn"><h2>常见误区</h2>${lesson.mistakes.map((mistake) => `<p><strong class="misconception">误区：${escapeHtml(mistake.wrong)}</strong><br>辨析：${escapeHtml(mistake.right)}</p>`).join('')}</section><section class="mnemonic"><h2>记忆口诀</h2><p><strong>${escapeHtml(lesson.mnemonic)}</strong></p></section><section class="panel"><h2>翻转卡复习</h2><div class="cards">${cards}</div></section><section class="panel orange"><h2>实操关联</h2><ul class="practice">${lesson.practice.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section><section class="panel blue"><h2>练习题</h2>${quizzes}</section><footer>Day ${lesson.day}/112 · ${escapeHtml(lesson.cert)}<ul>${lesson.sources.map((source) => `<li>${escapeHtml(source)}</li>`).join('')}</ul></footer></main><dialog aria-label="详情大图"><button class="icon-button" aria-label="关闭大图" title="关闭大图">${icon('X')}</button><img alt=""></dialog>`;
  return documentHtml(`Day ${lesson.day} · ${lesson.title}`, read('course.css'), body, read('course.js'), assets.get(LOGO));
}
function slideHtml(slide, index, total, lesson, assets) {
  let body;
  if (slide.kind === 'cover') {
    body = `${picture(lesson.cover, assets, 'cover-image')}<div class="cover-copy"><div class="daymark">Day ${lesson.day}</div><h1>${escapeHtml(lesson.xhs.coverTitle)}</h1><p class="subtitle">${escapeHtml(lesson.xhs.subtitle)}</p><div class="chips">${lesson.xhs.chips.map((chip) => `<span>${escapeHtml(chip)}</span>`).join('')}</div></div>`;
  } else {
    body = `<div class="rule"></div><div class="eyebrow">${number(index)}</div><h1>${escapeHtml(slide.title)}</h1><p class="lead">${escapeHtml(slide.lead)}</p>`;
    body += slide.kind === 'overview' ? picture(lesson.detailImage, assets, 'overview-image') : `${picture(slide.image, assets, 'visual')}<ul class="blocks">${slide.blocks.map((block) => `<li class="block"><h2>${escapeHtml(block.title)}</h2><ul>${block.bullets.map((bullet) => `<li>${escapeHtml(bullet)}</li>`).join('')}</ul></li>`).join('')}</ul>`;
  }
  return `<article class="slide ${slide.kind === 'cover' ? 'cover' : `content ${slide.kind}`}" data-slide="${index + 1}">${brand(lesson, assets)}<div class="slide-body">${body}</div><footer class="footer"><span>Day ${lesson.day}/112</span><span>${number(index + 1)} / ${number(total)}</span></footer></article>`;
}
function slidesHtml(lesson, assets, slides) {
  const body = `<main class="slide-deck">${slides.map((slide, i) => `<div class="slide-frame">${slideHtml(slide, i, slides.length, lesson, assets)}</div>`).join('')}</main>`;
  const script = `if (new URLSearchParams(location.search).has('export')) document.documentElement.classList.add('export'); else document.querySelectorAll('.slide-frame').forEach(frame => { const resize = () => frame.style.setProperty('--slide-scale', frame.clientWidth / 1080); new ResizeObserver(resize).observe(frame); resize(); });`;
  return documentHtml(lesson.xhs.coverTitle, read('slides.css'), body, script, assets.get(LOGO));
}
function previewHtml(lesson, assets) {
  const body = `<header><img src="${logoHref(assets.get(LOGO))}" alt="Logo"><span>Day ${lesson.day}</span><nav aria-label="预览格式"><button aria-pressed="true" data-view="lesson.html">网站 HTML</button><button aria-pressed="false" data-view="xhs/index.html">小红书</button></nav><a href="xhs.zip" download title="下载小红书包" aria-label="下载小红书包">${icon('Download')}</a></header><iframe title="网站 HTML 预览" src="lesson.html"></iframe>`;
  const css = `body{height:100dvh;display:flex;flex-direction:column;background:white}header{display:flex;align-items:center;gap:16px;padding:10px 20px;border-bottom:1px solid var(--line);min-height:64px}header>img{width:40px;height:40px;object-fit:contain}header>span{font-size:14px;color:var(--muted)}nav{display:flex;gap:20px;margin-left:auto}nav button{background:none;border:0;border-bottom:2px solid transparent;padding:10px 0;color:var(--muted);font-size:14px}nav button[aria-pressed=true]{color:var(--accent);border-color:var(--accent)}header a{color:var(--ink);display:grid;place-items:center;width:36px;height:36px}iframe{width:100%;flex:1;min-height:0;border:0}@media(max-width:420px){header{gap:10px;padding:8px 12px}nav{gap:12px}header>span{display:none}}`;
  const script = `document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{document.querySelector('iframe').src=button.dataset.view;document.querySelector('iframe').title=button.textContent+'预览';document.querySelectorAll('[data-view]').forEach(tab=>tab.setAttribute('aria-pressed',String(tab===button)));}));`;
  return documentHtml(`Day ${lesson.day} 样稿`, css, body, script, assets.get(LOGO));
}
function buildPackage(lesson, output) {
  validateLesson(lesson);
  for (const source of imagePaths(lesson)) if (!fs.existsSync(path.join(ROOT, source))) fail('image', `missing ${source}`);
  if (fs.existsSync(output) && fs.readdirSync(output).length) {
    const manifestPath = path.join(output, 'manifest.json');
    const previous = fs.existsSync(manifestPath) && JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    if (!previous || previous.template !== VERSION || previous.id !== lesson.id) fail('output', 'use an empty directory or the same lesson output');
    if (fs.existsSync(path.join(output, 'xhs.zip'))) fs.unlinkSync(path.join(output, 'xhs.zip'));
    const xhs = path.join(output, 'xhs');
    if (fs.existsSync(xhs)) for (const name of fs.readdirSync(xhs)) if (/^(cover|slide-\d+)\.png$/.test(name)) fs.unlinkSync(path.join(xhs, name));
  }
  const assets = createAssets(lesson, output);
  const slides = buildSlides(lesson);
  fs.mkdirSync(path.join(output, 'xhs'), { recursive: true });
  fs.writeFileSync(path.join(output, 'lesson.html'), courseHtml(lesson, assets));
  fs.writeFileSync(path.join(output, 'index.html'), previewHtml(lesson, assets));
  fs.writeFileSync(path.join(output, 'xhs/index.html'), slidesHtml(lesson, new Map([...assets].map(([source, target]) => [source, `../${target}`])), slides));
  for (const field of ['title', 'caption', 'tags']) fs.writeFileSync(path.join(output, `xhs/${field}.txt`), `${field === 'tags' ? lesson.xhs.tags.map((tag) => `#${tag.replace(/^#/, '')}`).join(' ') : field === 'caption' ? captionText(lesson) : lesson.xhs[field]}\n`);
  const manifest = { template: VERSION, id: lesson.id, day: lesson.day, status: 'html-ready', slides: slides.length, dimensions: [1080, 1440], files: ['lesson.html', 'index.html', 'xhs/index.html', 'xhs/title.txt', 'xhs/caption.txt', 'xhs/tags.txt'], assets: Object.fromEntries(assets) };
  fs.writeFileSync(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

function sitePaths(lesson) {
  validateLesson(lesson);
  if (!lesson.stage) fail('stage', 'required for the project asset directory');
  const day = `day${number(lesson.day)}`;
  const title = lesson.title.replace(/[\\/:*?"<>|]/g, '-');
  const slug = lesson.id.replace(/^day\d+-/, '');
  return {
    html: `html/${day}-${title}.html`,
    thumbnail: `html/thumbs/${day}-${slug}-thumbnail.png`,
    detail: `html/assets/${lesson.stage}/${day}-${title}.png`,
    xhs: `xhs/${day}`,
    archive: `xhs/${day}/${day}-xhs.zip`,
  };
}

function installPackage(lesson, stagedOutput, root = ROOT) {
  const paths = sitePaths(lesson);
  const staged = JSON.parse(fs.readFileSync(path.join(stagedOutput, 'manifest.json'), 'utf8'));
  if (staged.status !== 'ready' || staged.template !== VERSION || staged.id !== lesson.id || staged.day !== lesson.day || staged.slides !== buildSlides(lesson).length) fail('package', 'a complete matching rendered package is required');
  const stagedSocialAssets = new Map(Object.entries(staged.assets).map(([source, target]) => [source, `../${target}`]));
  if (fs.readFileSync(path.join(stagedOutput, 'xhs/index.html'), 'utf8') !== slidesHtml(lesson, stagedSocialAssets, buildSlides(lesson))) fail('package', 'XHS content or template changed; render again before installing');
  const writes = new Map();
  const sourceBytes = (source) => {
    const relative = staged.assets[source];
    if (!relative || !/^assets\/[a-f0-9]+\.(png|jpe?g|webp|svg)$/i.test(relative)) fail('package', `missing asset ${source}`);
    const bytes = fs.readFileSync(path.join(stagedOutput, relative));
    if (source !== LOGO && bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') fail('image', 'project delivery requires PNG source images');
    return bytes;
  };
  const courseAssets = new Map([
    [LOGO, path.posix.relative('html', LOGO)],
    [lesson.detailImage.src, path.posix.relative('html', paths.detail)],
  ]);
  writes.set(LOGO, sourceBytes(LOGO));
  writes.set(paths.thumbnail, sourceBytes(lesson.cover.src));
  writes.set(paths.detail, sourceBytes(lesson.detailImage.src));
  writes.set(`go/${lesson.day}/index.html`, Buffer.from(shortlinkHtml(lesson, paths.html)));
  const socialAssets = new Map();
  const addSocialAsset = (source, filename) => {
    const relative = `ai-visuals/${filename}`;
    writes.set(`${paths.xhs}/${relative}`, sourceBytes(source));
    socialAssets.set(source, relative);
  };
  addSocialAsset(LOGO, 'logo.svg');
  addSocialAsset(lesson.cover.src, 'visual-00-cover.png');
  addSocialAsset(lesson.detailImage.src, 'visual-01-overview.png');
  lesson.xhs.points.forEach((point, index) => {
    const suffix = path.basename(point.image.src, path.extname(point.image.src)).replace(/^visual-\d+-/, '');
    addSocialAsset(point.image.src, `visual-${number(index + 2)}-${suffix}.png`);
  });
  writes.set(paths.html, Buffer.from(courseHtml(lesson, courseAssets)));
  writes.set(`${paths.xhs}/index.html`, Buffer.from(slidesHtml(lesson, socialAssets, buildSlides(lesson))));
  for (const filename of ['title.txt', 'caption.txt', 'tags.txt', ...Array.from({ length: staged.slides }, (_, i) => `${i === 0 ? 'cover' : `slide-${number(i)}`}.png`)]) {
    const bytes = filename === 'caption.txt' ? Buffer.from(`${captionText(lesson)}\n`) : fs.readFileSync(path.join(stagedOutput, 'xhs', filename));
    if (!bytes.length) fail('package', `empty ${filename}`);
    writes.set(`${paths.xhs}/${filename}`, bytes);
  }

  const manifestFile = `${paths.xhs}/manifest.json`;
  const previousPath = path.join(root, manifestFile);
  const previous = fs.existsSync(previousPath) ? JSON.parse(fs.readFileSync(previousPath, 'utf8')) : null;
  if (previous && (previous.layout !== 'site' || previous.id !== lesson.id || previous.template !== VERSION)) fail('output', 'destination belongs to another package');
  const owned = new Set(previous?.files || []);
  // Preflight the whole write set before changing any existing lesson or asset.
  for (const [relative, bytes] of writes) {
    const target = path.join(root, relative);
    if (fs.existsSync(target) && (relative === LOGO || !owned.has(relative)) && !fs.readFileSync(target).equals(bytes)) fail('output', `refusing to overwrite ${relative}`);
  }
  if (fs.existsSync(path.join(root, paths.archive)) && !owned.has(paths.archive)) fail('output', `refusing to overwrite ${paths.archive}`);
  fs.mkdirSync(path.join(root, paths.xhs), { recursive: true });
  const manifest = { template: VERSION, layout: 'site', id: lesson.id, day: lesson.day, status: 'installing', slides: staged.slides, dimensions: staged.dimensions, paths, files: [...writes.keys(), paths.archive] };
  fs.writeFileSync(previousPath, `${JSON.stringify(manifest, null, 2)}\n`);
  try {
    for (const [relative, bytes] of writes) {
      const target = path.join(root, relative);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, bytes);
    }
    for (const relative of owned) {
      if (relative.startsWith(`${paths.xhs}/`) && !writes.has(relative) && relative !== paths.archive && fs.existsSync(path.join(root, relative))) fs.unlinkSync(path.join(root, relative));
    }
    const archive = path.join(root, paths.archive);
    if (fs.existsSync(archive)) fs.unlinkSync(archive);
    const zipFiles = [...writes.keys()].filter((file) => file.startsWith(`${paths.xhs}/`)).map((file) => path.posix.relative(paths.xhs, file));
    execFileSync('zip', ['-q', archive, ...zipFiles], { cwd: path.join(root, paths.xhs) });
    manifest.status = 'ready';
  } catch (error) {
    manifest.status = 'failed';
    manifest.error = error.message;
    throw error;
  } finally { fs.writeFileSync(previousPath, `${JSON.stringify(manifest, null, 2)}\n`); }
  return manifest;
}
async function checkSlideLayout(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map((image) => image.decode()));
  });
  const errors = await page.evaluate(() => {
    const errors = [];
    document.querySelectorAll('.slide').forEach((slide) => {
      const label = `slide ${slide.dataset.slide}`;
      const footer = slide.querySelector('.footer').getBoundingClientRect();
      const rect = slide.getBoundingClientRect();
      slide.querySelectorAll('.slide-body h1,.slide-body h2,.slide-body p,.slide-body li,.slide-body img,.chips').forEach((element) => {
        const box = element.getBoundingClientRect();
        if (box.bottom > footer.top - 16 || box.left < rect.left || box.right > rect.right) errors.push(`${label}: ${element.className || element.tagName} overlaps footer or leaves page`);
        if (element.scrollWidth > element.clientWidth + 2) errors.push(`${label}: horizontal text overflow`);
      });
      slide.querySelectorAll('.block').forEach((block) => {
        const box = block.getBoundingClientRect();
        block.querySelectorAll('h2,li').forEach((element) => {
          const range = document.createRange(); range.selectNodeContents(element);
          const text = range.getBoundingClientRect();
          if (text.bottom > box.bottom || text.right > box.right) errors.push(`${label}: text outside block`);
        });
      });
      if (slide.classList.contains('overview') && slide.querySelector('.lead').getBoundingClientRect().bottom + 16 > slide.querySelector('.overview-image').getBoundingClientRect().top) errors.push(`${label}: overview heading overlaps image`);
    });
    return errors;
  });
  if (errors.length) throw new Error(errors.join('\n'));
}
async function exportSlides(output, manifest, browser) {
  const { pathToFileURL } = require('node:url');
  const context = await browser.newContext({ viewport: { width: 1080, height: 1440 }, deviceScaleFactor: 1 });
  await context.route('**/*', (route) => route.request().url().startsWith('file:') ? route.continue() : route.abort());
  try {
    const page = await context.newPage();
    await page.goto(`${pathToFileURL(path.join(output, 'xhs/index.html'))}?export=1`);
    await checkSlideLayout(page);
    for (let i = 0; i < manifest.slides; i += 1) {
      const file = `xhs/${i === 0 ? 'cover' : `slide-${number(i)}`}.png`;
      await page.locator('.slide').nth(i).screenshot({ path: path.join(output, file) });
      manifest.files.push(file);
    }
    execFileSync('zip', ['-q', '-r', path.join(output, 'xhs.zip'), 'xhs', 'assets'], { cwd: output });
    manifest.files.push('xhs.zip');
    manifest.status = 'ready';
    fs.writeFileSync(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  } catch (error) {
    manifest.status = 'failed';
    manifest.error = error.message;
    fs.writeFileSync(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
    throw error;
  } finally { await context.close(); }
}
function launchOptions() {
  if (process.env.CHROME_EXECUTABLE) return { executablePath: process.env.CHROME_EXECUTABLE, headless: true };
  const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  return fs.existsSync(chrome) ? { executablePath: chrome, headless: true } : { headless: true };
}
module.exports = { ROOT, VERSION, validateLesson, buildSlides, buildPackage, sitePaths, installPackage, checkSlideLayout, exportSlides, launchOptions };
