"""Publish a compact production inventory; this is not an anatomical acceptance report."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1]
W=P.parents[1]/'skeleton-workbench/z-anatomy-candidate'
a=json.loads((P/'剩余资源处置台账.json').read_text())
names={r['id']:r['name_zh'] for name in ['joints','connections','ligament-library','repaired-disc','nuclei'] for r in json.loads((W/(name+'.json')).read_text())['objects']}
records=[{k:r[k] for k in ['id','name_zh','region','decision','reason']} for r in a['records']]
for r,source in zip(records,a['records']):
 r['name_zh']=names.get(r['id'],r['name_zh'])
 r['model_ids']=[x['model_id'] for x in source.get('evidence',[]) if 'model_id' in x]
(W/'coverage.json').write_text(json.dumps({'records':records},ensure_ascii=False,indent=2)+'\n')
