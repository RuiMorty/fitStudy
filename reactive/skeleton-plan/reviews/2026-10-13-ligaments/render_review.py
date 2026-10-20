from pathlib import Path
import json,html
P=Path(__file__).resolve().parent;data=json.loads((P/'完整核对结果.json').read_text());rows=data['objects'];summary=data['summary'];W=P.parents[2]/'skeleton-workbench';out=W/'qa/ligament-info-review-2026-10-13';out.mkdir(exist_ok=True)
md='''# 已接入韧带／骨间膜信息核对结果

日期：2026-10-13。**仅审查，未更改生产模型、中文名称、关联数据或网页代码。**

覆盖当前全部 **290 个对象、149 种源名称**。这是信息初核，不是 290 个模型的逐一几何或解剖验收。源对象存在性、导出节点、侧别标签、坐标半身、骨及关节 ID、分组和既往拆缝记录已逐条检查；精确足印尚未逐模型核查。

## 优先看这几项

| 项目 | 当前记录的问题 | 建议你二核的内容 |
|---|---|---|
| 左右颞下颌外侧韧带 | 左名模型位于右侧，右名模型位于左侧；原始源文件与导出一致 | 对照左右颞骨核对，决定交换侧别名称/映射；不要未经核对移动模型 |
| 尺豌豆韧带（源未标侧） | 名称无左右后缀，当前为 unknown | 源对象和导出均在右半身，对侧已有 .l；建议核对为右侧 |
| 双侧肋锁韧带 | 当前关联有胸骨、锁骨，漏第1肋 | 应涉及第1肋/肋软骨与锁骨，不能用胸锁关节父级替代附着关系 |
| 项韧带 | 当前骨列表遍及胸腰骶尾 | 限定颈后及枕骨相关范围；不要把整个脊柱目录当直接附着 |
| 双侧蝶下颌、翼棘韧带 | 当前关联缺蝶骨，混入颞下颌/舌骨区域骨 | 蝶下颌为蝶骨—下颌骨；翼棘两端在蝶骨范围内 |
| 喙肩韧带、肩胛横韧带、肱骨横韧带 | 区域骨列表不能表达同骨两点之间的连接 | 区分肩胛骨内连接、肱骨内连接与跨骨韧带 |
| 膝横韧带、半月板胫骨韧带、腘腓韧带等 | 当前只有骨/关节目录，缺明确软组织关系 | 分别记录半月板、腘肌腱等，不强行改成两骨起止 |
| 右肘尺侧副韧带 | 已有三向几何核查：范围延伸到桡骨头附近、三束不清 | 另核对源模型覆盖范围，不只改名字；本次未再次改形状 |
| 18 个拆缝候选 | 仅修过拓扑分叉，真实连续性未核对 | 结合源图谱逐个确认接缝、分组及形态，不按“可显示”验收 |

## 统计怎样理解

- P1：36 项优先复核，包括源侧别矛盾、关键关联缺失、右 UCL 既知形态问题及拆缝对象。
- P2：206 项需完善关联、分束、软组织关系或专门参考。
- P3：48 项当前未发现明显的基础信息冲突；**不等于已解剖验收**。
- 优先级不是错误数量；一个对象可以有多个问题。
- 290 项都能对应到本地源网格和导出对象，没有发现无效骨 ID 或源名后缀与记录侧别不一致。这里“对应”不表示源命名正确，颞下颌侧别就是反例。
- 56 项名称体现组合结构；18 项有拆缝记录；15 项的初核骨集合含当前目录遗漏的骨。后者还需要你结合变异、分束及软组织关系判断，不能全部视为已经证明错误。

## 哪些查到了什么程度

49 项有本次读取的 OpenStax 章节支持总体关系；121 项作了解剖关系初核；60 项仅进行名称所指骨对的语义初筛；另外 60 项需要组合结构或专门连接参考。本次没有把语义推断冒充逐页文献核查，也没有把所有模型都做过三维形态核查。

“当前关联骨”和“建议二核的解剖关系”在每行分别列出。当前 bone_ids 本来是区域目录，**不是数据库已经提供的起止点**。本轮主要发现它不能直接承担解剖起止信息；不会将所有额外区域骨都判成模型本身错误。

## 你的二次核对入口

- 逐项二次核对表.csv：290 行，包含当前值、发现、建议关系、依据限度，以及“你的二核结论”“你的备注与更改建议”两列。可在 Excel 中填写。
- 完整核对结果.json：完整 ID、当前骨 ID、坐标包围盒及审查状态。
- 网页版：skeleton-workbench/qa/ligament-info-review-2026-10-13/index.html。支持搜索、优先级/深度筛选、逐条备注及导出二核 JSON。备注仅保存在浏览器，不会修改项目模型。

建议先核对侧别问题、肋锁/项韧带/颅部关联，再看软组织连接和 18 个拆缝候选；细小腕足分束留到有专门图谱时确认。

## 本次直接读取的参考

- [OpenStax A&P 2e 9.6：典型滑膜关节](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-6-anatomy-of-selected-synovial-joints)：总体连接与稳定结构。
- [9.2：纤维关节](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-2-fibrous-joints)：骨间膜等。
- [7.3：脊柱](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-3-the-vertebral-column)：项韧带、棘上韧带、纵韧带、黄韧带。

参考页的读取状态、散列和文本保存在 references/。这些是总体参考，不能替代腕足等细小韧带的专门图谱、源模型边界和标本差异核查。

生产输入散列检查见 保护检查.json；本轮只新增独立审查文件。
'''
(P/'核对结果说明.md').write_text(md)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>韧带信息 · 二次核对</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f3f1;color:#252525;font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto;padding:28px 20px}h1{font-size:26px}h2{font-size:18px;margin:0}p{margin:10px 0}.muted{color:#666;font-size:13px}.tools{display:flex;gap:10px;flex-wrap:wrap;padding:16px 0;position:sticky;top:0;background:#f3f3f1;z-index:1}input,select,button,textarea{font:inherit;border:1px solid #bbb;border-radius:6px;padding:8px;background:white;color:inherit}input{flex:1;min-width:180px}button{cursor:pointer}article{padding:20px;background:#fff;border:1px solid #d7d7d4;border-radius:10px;margin:16px 0}.tag{font-size:12px;padding:3px 8px;background:#eee;border-radius:4px;margin-left:10px}details{margin:14px 0}summary{cursor:pointer}textarea{display:block;width:100%;min-height:70px;margin-top:8px}.review{border-top:1px solid #ddd;padding-top:14px}.label{font-weight:600}.sources{overflow-wrap:anywhere}#count{font-weight:600}#more{width:100%}a{color:inherit}button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid #777;outline-offset:2px}
</style><main><h1>韧带／骨间膜信息二次核对</h1><p>290 个对象 · 149 种源名称 · 仅审查，未更改模型或生产数据。</p><p>优先级表示复核顺序，不表示已经证明错误。P3 也不等于解剖验收。精确足印尚未逐模型核对。</p><p class="muted">建议先看左右颞下颌外侧韧带、尺豌豆韧带、肋锁韧带、项韧带及拆缝候选。填写后导出二核结果，用于后续更改。</p><div class="tools"><input id="search" type="search" aria-label="检索结构" placeholder="名称、ID、部位或问题"><select id="priority" aria-label="复核优先级"><option value="">全部优先级</option><option value="P1" selected>P1 优先复核</option><option>P2</option><option>P3</option></select><select id="depth" aria-label="核对深度"><option value="">全部核对深度</option><option value="A">A 章节总体依据</option><option value="B">B 解剖关系初核</option><option value="C">C 名称语义初筛</option><option value="D">D 需专门参考</option></select><button id="export">导出我的二核结果</button></div><p id="save" class="muted">二核备注仅保存在当前浏览器；不会更改模型。</p><p id="count" role="status"></p><div id="list"></div><button id="more">再显示 30 项</button><p class="muted">总体参考：<a href="https://openstax.org/books/anatomy-and-physiology-2e/pages/9-6-anatomy-of-selected-synovial-joints" target="_blank" rel="noreferrer">OpenStax 9.6</a>。具体每行的依据与限度见详情。</p></main><script>
const data=__DATA__,el=id=>document.getElementById(id),key='ligament-second-review-2026-10-13-v1';let answers={},limit=30;
try{answers=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
function node(tag,text,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n}
function save(id,field,value){answers[id]??={};answers[id][field]=value;try{localStorage.setItem(key,JSON.stringify(answers));el('save').textContent='已保存到当前浏览器，请导出文件后交回。'}catch{el('save').textContent='浏览器无法保存；请在关闭前导出结果。'}}
function render(){const q=el('search').value.trim().toLowerCase();const matches=data.objects.filter(r=>(!el('priority').value||r.priority===el('priority').value)&&(!el('depth').value||r.review_depth.startsWith(el('depth').value))&&(!q||[r.name_zh,r.source_object,r.id,r.region,...r.findings].join(' ').toLowerCase().includes(q)));el('count').textContent=`符合 ${matches.length} 项，显示 ${Math.min(limit,matches.length)} 项`;el('list').replaceChildren();for(const r of matches.slice(0,limit)){const card=node('article');card.dataset.id=r.id;const title=node('h2',r.name_zh);title.append(node('span',r.priority,'tag'));card.append(title,node('p',r.source_object+' · '+r.region+' · '+r.side,'muted'),node('p',r.review_depth,'muted'),node('p','建议二核的解剖关系','label'),node('p',r.expected_relation_for_second_review));const list=node('ul');for(const t of r.findings)list.append(node('li',t));card.append(list);const detail=node('details');detail.append(node('summary','查看当前记录、依据与核查范围'),node('p','ID：'+r.id,'sources'),node('p','当前关联骨：'+r.current_bones.join('、')),node('p','当前关联关节：'+r.current_connections.join('、')),node('p','依据与限度：'+r.basis),node('p','模型形态核查：'+r.geometry_review),node('p','精确足印：未逐模型核对；解剖验收：未通过。'));card.append(detail);const review=node('div',null,'review'),label=node('label','你的二核结论：'),sel=node('select');sel.setAttribute('aria-label',r.name_zh+'二核结论');for(const [value,text] of [['','未二核'],['usable','信息可用'],['change','需要修改'],['evidence','待补证据']]){const o=node('option',text);o.value=value;sel.append(o);}sel.value=answers[r.id]?.decision||'';sel.onchange=()=>save(r.id,'decision',sel.value);label.append(sel);const note=node('textarea');note.placeholder='写下确认结果、纠正信息或参考依据';note.setAttribute('aria-label',r.name_zh+'备注');note.value=answers[r.id]?.notes||'';note.oninput=()=>save(r.id,'notes',note.value);review.append(label,note);card.append(review);el('list').append(card);}el('more').hidden=matches.length<=limit;}
for(const id of ['search','priority','depth'])el(id).addEventListener(id==='search'?'input':'change',()=>{limit=30;render()});el('more').onclick=()=>{limit+=30;render()};el('export').onclick=()=>{const result={auditDate:'2026-10-13',exportedAt:new Date().toISOString(),productionInputs:data.input_sha256,reviews:data.objects.filter(r=>answers[r.id]?.decision||answers[r.id]?.notes).map(r=>({id:r.id,name:r.name_zh,...answers[r.id]}))};const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='韧带二次核对结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};render();
</script></html>'''
page=page.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c'));(out/'index.html').write_text(page);print(out/'index.html')
