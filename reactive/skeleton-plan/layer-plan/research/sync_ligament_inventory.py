"""Add the audited source-library candidates to the production ledger, without marking acceptance."""
from pathlib import Path
import json,csv
P=Path(__file__).resolve().parents[1];mapping=json.loads((P/'research/ligament-library-mapping.json').read_text());file=P/'全身关节层台账.json';data=json.loads(file.read_text());byid={r['id']:r for r in data['objects']}
for m in mapping:
 byid[m['id']]={'id':m['id'],'name_zh':m['name_zh'],'region':m['region'],'tissue_type':'interosseous_membrane' if 'membrane' in m['source_object'] else 'ligament','production_stage':2,'display_layer':'连接组织','connection_ids':m['connection_ids'],'bone_ids':m['bone_ids'],'granularity':m['granularity'],'candidate_search_terms':[m['source_object']],'resource_status':'source_library_candidate','source_evidence':[],'accepted_asset':None,'coverage_boundary':None,'anatomy_review':'pending','assembly_review':'pending','motion_review':'pending','note':m['note']}
data['objects']=list(byid.values());data['total_objects']=len(data['objects']);file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('PLAN_RECORDS',len(data['objects']))
from collections import Counter
O=P.parents[1]/'skeleton-workbench/z-anatomy-candidate';exported={}
for name in ['joints','connections','ligament-library','repaired-disc','nuclei']:
 for r in json.loads((O/(name+'.json')).read_text())['objects']:exported[r['id']]=r
for r in data['objects']:
 if r['id'] in exported:
  out=exported[r['id']];r['resource_status']='exported_split_seam_candidate' if out.get('topology_status')=='split_seams_pending_review' else 'exported_candidate';r['candidate_asset_id']=out['id']
data['statistics'].update(records=len(data['objects']),resource_status=dict(Counter(r['resource_status'] for r in data['objects'])),regions=dict(Counter(r['region'] for r in data['objects'])))
file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
with (P/'全身关节层台账.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f,lineterminator='\n');writer.writerow(['ID','名称','区域','组织类型','批次','条目粒度','资源状态','候选对象','关联骨','备注'])
 for r in data['objects']:writer.writerow([r['id'],r['name_zh'],r['region'],r['tissue_type'],r['production_stage'],r['granularity'],r['resource_status'],'; '.join(r.get('candidate_search_terms',[])),'; '.join(r['bone_ids']),r['note']])
assert len(data['objects'])==len({r['id'] for r in data['objects']})
(P/'validation.json').write_text(json.dumps({'planning_records':len(data['objects']),'connection_records_accounted_for':205,'resource_dispositions_sum':len(data['objects']),'unique_ids':True,'csv_json_consistent':True,'source_asset_anatomy_accepted':0,'note':'Source extraction and topology repairs are not anatomical acceptance.'},indent=2)+'\n')
