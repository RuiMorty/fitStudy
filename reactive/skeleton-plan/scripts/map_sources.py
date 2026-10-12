import json,csv,re
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];A=R/'source-audit'
parts={}
for l in (A/'upstream/parts_list_e.txt').read_text().splitlines():
 p=l.split('\t')
 if len(p)==2 and re.match(r'^(FMA|BP)\d+$',p[0]):parts[p[1].strip().lower()]=p[0]
composite=defaultdict(list);labels={}
for row in csv.DictReader((A/'upstream/composite_parts.txt').open(),delimiter='\t'):
 composite[row['composite id']].append(row['primitive id']);labels[row['primitive id']]=row['primitive name']
ordinals=['','first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth']
records=[]
for b in json.loads((R/'data/bones-206.json').read_text())['bones']:
 key=b['id'][5:-2];side={'L':'left','R':'right','M':''}[b['side']];label=b['name_en'].lower()
 if key.startswith('vertebra_'):
  tag=key.split('_')[1];label='atlas' if tag=='C1' else 'axis' if tag=='C2' else ordinals[int(tag[1:])]+' '+{'C':'cervical','T':'thoracic','L':'lumbar'}[tag[0]]+' vertebra'
 elif key.startswith('rib_'):label=side+' '+ordinals[int(key.split('_')[-1])]+' rib'
 elif key.startswith(('metacarpal_','metatarsal_')):label=side+' '+ordinals[int(key.split('_')[1])]+' '+key.split('_')[0]+' bone'
 elif '_phalanx_' in key:
  region,_,digit,seg=key.split('_');digit=int(digit);name=(['thumb','index finger','middle finger','ring finger','little finger'] if region=='hand' else ['big toe','second toe','third toe','fourth toe','little toe'])[digit-1];label=f'{seg} phalanx of {side} {name}'
 elif key=='navicular':label=f'navicular bone of {side} foot'
 else:
  label={'ethmoid':'ethmoid','hyoid':'hyoid bone','triquetrum':'triquetral','scaphoid':'scaphoid','lunate':'lunate','pisiform':'pisiform','trapezium':'trapezium','trapezoid':'trapezoid','capitate':'capitate','hamate':'hamate','cuboid':'cuboid bone','medial_cuneiform':'medial cuneiform bone','intermediate_cuneiform':'intermediate cuneiform bone','lateral_cuneiform':'lateral cuneiform bone'}.get(key,label)
  if side:label=side+' '+label
 sid=parts.get(label);primitives=sorted(set(composite.get(sid,[sid]))) if sid else []
 records.append(dict(id=b['id'],name_zh=b['name_zh'],region=b['region'],side=b['side'],lookup_label=label,source_id=sid,source_label=label if sid else None,primitive_ids=primitives,primitive_labels=[labels.get(x) for x in primitives],mapping_status=('composite_index_match' if sid in composite else 'single_index_match') if sid else 'not_found_in_release_index',file_status='not_checked',assembly_status='not_reviewed',anatomy_status='not_reviewed'))
extra=[]
for b in json.loads((R/'data/extension-bones.json').read_text())['planned']:
 side={'L':'left','R':'right'}[b['id'][-1]];label=f'sesamoid bone of {side} foot' if 'hallux' in b['id'] else None;sid=parts.get(label)
 extra.append(dict(id=b['id'],name_zh=b['name_zh'],source_group_id=sid,primitive_ids=sorted(set(composite.get(sid,[sid]))) if sid else [],status='foot_group_requires_geometry_split_or_identification' if sid else 'not_found_in_release_index',anatomy_status='not_reviewed'))
report=dict(commit='f0eeb6e843380cfe6b83797cf8c3e1af74de5e61',scope='Exact release label mapping with explicit ordinal/anatomical synonym rules; model files and geometry checked separately.',core=records,extensions=extra)
(A/'mapping.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(Counter(x['mapping_status'] for x in records))
print('Unmatched',[(x['name_zh'],x['lookup_label']) for x in records if not x['source_id']])
print('Composites',[(x['name_zh'],x['source_id'],x['primitive_ids'],x['primitive_labels']) for x in records if x['mapping_status']=='composite_index_match'])
print('Unique raw meshes:',len({i for r in records+extra for i in r['primitive_ids']}))
