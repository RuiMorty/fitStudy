// Attachment evidence is curated independently of regional scene associations.
let catalog = {}, loadFailed = false;
try {
  const response = await fetch('data/ligament-attachments.json');
  if (!response.ok) throw new Error('附着资料读取失败');
  catalog = (await response.json()).structures;
} catch (error) { loadFailed = true; console.error(error); }
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
};
export function appendLigamentInfo(host, structure) {
  const name = structure.source_structure_id?.replace(/\.[rl]$/, '');
  const data = structure.origin ? {...structure, course: structure.shape} : catalog[name];
  const section = element('section', '', 'attachment-info');
  section.append(element('h3', '起止与附着区域'));
  if (!data) {
    section.append(element('p', loadFailed ? '附着资料未能读取，请刷新重试。' : '这一结构尚未补齐可直接核对的附着文献，不以区域分类代替起止点。', 'attachment-pending'));
  } else {
    const dl = element('dl');
    for (const [label, value] of [['起侧附着', data.origin], ['止侧附着', data.insertion], ['走行与组成', data.course]]) {
      dl.append(element('dt', label), element('dd', value));
    }
    section.append(dl);
    const status = data.evidence_status === 'reference_checked_geometry_pending' ? '文字关系已核对 · 几何足印待核准' : data.evidence_status === 'reference_checked' ? '文字依据已核对 · 等待二次核对' : '依据范围有限 · 待补证据';
    section.append(element('p', status, 'attachment-status'), element('p', data.limitations, 'attachment-limit'));
    for (const ref of (data.references || [])) {
      const a = element('a', ref.title, 'attachment-reference');
      a.href = ref.url; a.target = '_blank'; a.rel = 'noreferrer'; section.append(a);
      const details = element('details'); details.append(element('summary', '查看对应原文'), element('blockquote', ref.quote)); section.append(details);
    }
  }
  section.append(element('p', structure.geometry_revision ? '模型：当前为显示修形版；附着足印及完整穿插检查尚未验收。' : '模型：附着区域和分束尚未校准。', 'attachment-model-status'));
  host.append(section);
}
