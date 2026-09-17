'use strict';
const { inventory, statistics } = window.AUDIT_DATA;
const groups = inventory.groups;
const labels = { 'html-cover':'HTML 无字封面', 'html-detail':'HTML 中文详情', 'xhs-cover':'小红书封面成图', 'xhs-export':'小红书全部成图（含封面）', 'xhs-source':'小红书原图（含备选）', 'day41-source':'Day41 新源图' };
const el = id => document.getElementById(id);
const originalUrl = file => '../../' + file.split('/').map(encodeURIComponent).join('/');
const itemLabel = item => `Day${String(item.day).padStart(2,'0')} · ${item.file.split('/').pop()} · ${item.size.join('×')}`;
const describe = item => `${itemLabel(item)}${item.kind === 'html-detail' && !item.active ? ' · 存储文件，当前正文未引用' : ''}${item.kind === 'xhs-source' ? ' · 原图不等于最终采用版本' : ''}${item.day === 41 ? ' · 源图，图片审核未通过' : ''}\n${item.file}`;
const options = (select, items) => { select.replaceChildren(...items.map(({value,text}) => { const o = document.createElement('option'); o.value = value; o.textContent = text; return o; })); };

for (const key of Object.keys(groups)) {
  const s = statistics[key];
  const tr = document.createElement('tr');
  [labels[key], s.count, s.distinctSizes, `${s.sizes[0].width}×${s.sizes[0].height}（${s.sizes[0].count} 张）`].forEach(value => { const td = document.createElement('td'); td.textContent = value; tr.append(td); });
  el('stats').append(tr);
}

const day41 = groups['day41-source'];
const collections = {
  cover: [...groups['html-cover'], ...day41.filter(i => i.file.endsWith('/cover-source.png'))],
  detail: [...groups['html-detail'], ...day41.filter(i => i.file.endsWith('/detail.png'))],
  knowledge: [...groups['xhs-source'], ...day41.filter(i => i.file.split('/').pop().startsWith('visual-'))],
  export: groups['xhs-export']
};
const defaults = {
  cover: ['html/thumbs/day17-biomechanical-movement-patterns-thumbnail.png', 'runs/day41/source-assets/cover-source.png'],
  detail: ['html/assets/阶段1基础科学/day12-主要肌群-核心肌群与McGill核心功能分类.png', 'runs/day41/source-assets/detail.png'],
  knowledge: ['xhs/day17/ai-visuals/visual-07-lower-body-patterns.png', 'runs/day41/source-assets/visual-02-high-bar.png'],
  export: ['xhs/day29/slide-02.png', 'xhs/day40/slide-02.png']
};
const notes = {
  cover:'历史也有真实人物；重点看人物与解剖、动作、受力关系如何结合，以及 Day41 器械场景的视觉分量。',
  detail:'比较黑色／蓝色标题、色块重量、线条和图文关系。历史详情图比例也不统一，不能直接把任一旧课当作唯一标准。',
  knowledge:'源图目录含备选和拼图。两图在同一查看框中完整显示；实际成品还会受源图留白、主体大小和页面图片区影响。',
  export:'这是实际历史小红书 PNG。Day41 没有最终成图。旧图中的历史文字品牌仅供追溯；新模板继续使用现有 SVG。'
};
function showSide(side) {
  const item = collections[el('compare-kind').value].find(i => i.file === el(side + '-select').value);
  el(side + '-image').src = originalUrl(item.file);
  el(side + '-image').alt = itemLabel(item);
  el(side + '-link').href = originalUrl(item.file);
  el(side + '-meta').textContent = describe(item);
}
function setComparison(kind) {
  el('compare-kind').value = kind;
  const list = collections[kind].map(i => ({value:i.file,text:itemLabel(i)}));
  ['left','right'].forEach((side,index) => { options(el(side + '-select'), list); el(side + '-select').value = defaults[kind][index]; showSide(side); });
  document.querySelector('.compare-grid').classList.toggle('portrait', kind === 'export');
  document.querySelectorAll('[data-preset]').forEach(b => b.classList.toggle('active', b.dataset.preset === kind));
  el('compare-note').textContent = notes[kind];
}
el('compare-kind').addEventListener('change', e => setComparison(e.target.value));
['left','right'].forEach(side => el(side + '-select').addEventListener('change', () => showSide(side)));
document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => setComparison(button.dataset.preset)));
setComparison('cover');

options(el('gallery-kind'), Object.keys(groups).map(k => ({value:k,text:labels[k]})));
let page = 0;
const pageSize = 20;
function setDays() {
  options(el('gallery-day'), [{value:'all',text:'全部课程'}, ...Array.from(new Set(groups[el('gallery-kind').value].map(i => i.day))).sort((a,b) => a-b).map(day => ({value:String(day),text:'Day' + String(day).padStart(2,'0')}))]);
}
function renderGallery() {
  const query = el('gallery-query').value.trim().toLocaleLowerCase();
  const items = groups[el('gallery-kind').value].filter(i => (el('gallery-day').value === 'all' || i.day === Number(el('gallery-day').value)) && i.file.toLocaleLowerCase().includes(query));
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  page = Math.min(page, pages - 1);
  el('gallery-items').replaceChildren();
  items.slice(page*pageSize,(page+1)*pageSize).forEach(item => {
    const card = document.createElement('article'); card.className = 'gallery-card';
    const a = document.createElement('a'); a.href = originalUrl(item.file); a.target = '_blank'; a.rel = 'noopener';
    const img = document.createElement('img'); img.src = originalUrl(item.file); img.alt = itemLabel(item); img.loading = 'lazy'; a.append(img);
    const heading = document.createElement('h3'); heading.textContent = `Day${String(item.day).padStart(2,'0')} · ${item.size.join('×')}`;
    const desc = document.createElement('p'); desc.textContent = describe(item);
    card.append(a,heading,desc); el('gallery-items').append(card);
  });
  el('gallery-count').textContent = `筛选结果 ${items.length} 张 · ${labels[el('gallery-kind').value]}`;
  el('page-label').textContent = `${page+1} / ${pages}`;
  el('prev-page').disabled = page === 0; el('next-page').disabled = page === pages-1;
}
el('gallery-kind').addEventListener('change', () => { page = 0; setDays(); renderGallery(); });
el('gallery-day').addEventListener('change', () => { page = 0; renderGallery(); });
el('gallery-query').addEventListener('input', () => { page = 0; renderGallery(); });
el('prev-page').addEventListener('click', () => { page--; renderGallery(); });
el('next-page').addEventListener('click', () => { page++; renderGallery(); });
setDays(); renderGallery();

options(el('sheet-select'), inventory.contactSheets.map((sheet,index) => ({value:String(index),text:`${labels[sheet.kind]} · ${sheet.range.join('–')} · ${sheet.file}`})));
function showSheet() {
  const sheet = inventory.contactSheets[Number(el('sheet-select').value)];
  el('sheet-image').src = sheet.file;
  el('sheet-image').alt = `${labels[sheet.kind]}，第 ${sheet.range.join('–')} 张`;
  el('sheet-link').href = sheet.file;
  el('sheet-description').textContent = `${labels[sheet.kind]} · ${sheet.range.join('–')} / ${groups[sheet.kind].length} · ${sheet.items.length} 张原图`;
}
el('sheet-select').addEventListener('change', showSheet);
showSheet();
