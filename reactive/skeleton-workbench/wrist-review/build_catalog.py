import json,re
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
rows=json.loads((W/'z-anatomy-candidate/wrist-ligaments-refined.json').read_text())['objects']
attachments=json.loads((W/'data/ligament-attachments.json').read_text())['structures']
# Explicit display context; never use broad region bone_ids as attachment evidence.
contexts={
'Capitohamate interosseous ligament':['Capitate','Hamate'],
'Dorsal intercarpal ligaments':['Triquetrum','Scaphoid','Trapezoid','Capitate'],
'Dorsal radio-ulnar ligament':['Radius','Ulna'],
'Dorsal radiocarpal ligament':['Radius','Triquetrum','Lunate'],
'Dorsal scaphotriquetral ligament':['Scaphoid','Triquetrum'],
'Dorsal ulnocarpal ligament':['Ulna','Triquetrum'],
'Lunotriquetral interosseous ligament':['Lunate','Triquetrum'],
'Palmar capitohamate ligament':['Capitate','Hamate'],
'Palmar lunotriquetral ligament':['Lunate','Triquetrum'],
'Palmar radio-ulnar ligament':['Radius','Ulna'],
'Palmar scaphotriquetral ligament':['Scaphoid','Triquetrum','Pisiform'],
'Palmar trapezoideocapitate ligament':['Trapezoid','Capitate'],
'Pisohamate ligament':['Pisiform','Hamate'],
'Pisometacarpal ligament':['Pisiform','Metacarpal5'],
'Pisotriquetral ligament':['Pisiform','Triquetrum'],
'Radial collateral ligament of wrist joint':['Radius','Scaphoid'],
'Radiate carpal ligament':['Capitate','Scaphoid','Lunate','Triquetrum'],
'Radiocapitate ligament':['Radius','Scaphoid','Capitate'],
'Radioscaphocapitate ligament':['Radius','Scaphoid','Capitate'],
'Scaphocapitate ligament':['Scaphoid','Capitate'],
'Scapholunate interosseous ligament':['Scaphoid','Lunate'],
'Scaphotrapeziotrapezoidal ligament':['Scaphoid','Trapezium','Trapezoid'],
'Trapeziotrapezoidal interosseous ligament':['Trapezium','Trapezoid'],
'Trapezoideocapitate interosseous ligament':['Trapezoid','Capitate'],
'Triquetrocapitate ligament':['Triquetrum','Capitate'],
'Triquetrohamate ligament':['Triquetrum','Hamate'],
'Ulnar collateral ligament of wrist joint':['Ulna','Triquetrum','Pisiform'],
'Ulnolunate ligament':['Ulna','Lunate'],
'Ulnotriquetral ligament':['Ulna','Triquetrum'],
'Ulnocapitate ligament':['Ulna','Capitate'],
'Ulnopisiform ligament':['Ulna','Pisiform']}
landmarks={'Radius':['桡骨茎突','尺切迹'],'Ulna':['尺骨茎突'],'Scaphoid':['舟骨结节'],'Trapezium':['大多角骨结节'],'Hamate':['钩骨钩']}
result=[]
for r in rows:
 key=r['source_structure_id'].rsplit('.',1)[0];a=attachments.get(key,{});bones=contexts[key]
 group='intrinsic'
 if 'radio-ulnar' in key:group='druj'
 elif 'collateral' in key:group='collateral'
 elif key.startswith('Dorsal'):group='dorsal'
 elif key.startswith(('Radio','Ulno')):group='palmar_extrinsic'
 elif key.startswith('Piso'):group='pisiform'
 r={**r,'group':group,'context_bones':bones,'landmark_names':sum((landmarks.get(b,[]) for b in bones),[]),'origin':a.get('origin','尚未找到支持该源对象精确附着的已核对资料。'),'insertion':a.get('insertion','待核对；不根据名称或最近骨面自动填入。'),'shape':a.get('course','保留现有源派生形状；分束、厚度与走行待核对。'),'comparison':'沿用现有腕部修形 v2，本次只接入审核，不因模型已贴骨就认定附着正确。','limitations':a.get('limitations','当前仅有源对象及区域目录；画布参考骨为观察上下文，不是经过核准的附着骨清单。'),'evidence_status':a.get('evidence_status','missing'),'references':a.get('references',[]),'anatomy_review':'pending'}
 if key in ['Dorsal intercarpal ligaments','Dorsal scaphotriquetral ligament','Radiocapitate ligament','Radioscaphocapitate ligament']:r['limitations']+=' 与相近名称对象的范围是否重叠尚待核对，不应直接重复计作独立束。'
 if key=='Ulnopisiform ligament':r['limitations']+=' 本轮导出清单仅左侧；未自动镜像生成右侧。'
 result.append(r)
if (P/'local-overrides.json').exists():
 overrides=json.loads((P/'local-overrides.json').read_text())
 for r in result:r.update(overrides.get(r['id'],{}))
gaps=['61 个现有对象、31 个名称类别；尺豌豆韧带仅左侧，不等于完整双侧解剖清单。','TFCC 的关节盘、尺骨凹/茎突深浅附着及与尺腕韧带的连续关系尚未一起接入校准；不能把桡尺韧带直接等同于完整 TFCC。','掌侧长/短桡月韧带等名称映射及遗漏需继续核查；未用相似名称模型自动代替。','背侧腕骨间/舟三角韧带、桡头状/桡舟头状韧带的范围可能重叠，需核对后再计数或拆分。','显示参考骨来自明确的观察上下文映射；原文件的 bone_ids 是区域目录，不作为起止点证据。','本轮沿用已有修形 v2，未批量吸附或拉长韧带。各组精确附着及关节运动仍未验收。']
(P/'catalog.json').write_text(json.dumps({'scope':'wrist_ligaments','type_count':31,'source_object_count':61,'structures':result,'gaps':gaps},ensure_ascii=False,indent=2)+'\n')
(P/'source-inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
counts={}
for r in result:counts[r['group']]=counts.get(r['group'],0)+1
missing=[r['name_zh'] for r in result if not r['references']]
(P/'inventory-summary.json').write_text(json.dumps({'groups':counts,'objects_without_references':missing,'missing_reference_count':len(missing),'asymmetry':'Ulnopisiform ligament: L only'},ensure_ascii=False,indent=2)+'\n')
print(counts,'missing references',len(missing))
