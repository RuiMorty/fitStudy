#!/usr/bin/env python3
import datetime as dt, hashlib, json, subprocess, sys
from pathlib import Path
here=Path(__file__).resolve().parent; plan=json.loads((here/'image-prompts.json').read_text()); record=here/'generation-first-pass.json'; generator='/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py'; rows=[]
for asset in plan['assets']:
    output=here/'source'/asset['file']; result=subprocess.run([sys.executable,generator,'--preset','quality','--background','transparent','--output-format','png','--prompt',plan['commonPrompt']+'\n\n'+asset['prompt'],'--output',str(output)],capture_output=True,text=True)
    row={'file':asset['file'],'role':asset['role'],'attempt':1,'returncode':result.returncode,'output':str(output.relative_to(here.parent.parent))}
    if result.returncode==0 and output.is_file() and output.stat().st_size: row.update({'status':'generated-pending-quality-review','bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
    else: row.update({'status':'request-failed','errorSummary':(result.stderr or result.stdout or 'no usable local PNG').strip()[:1000]})
    rows.append(row); record.write_text(json.dumps({'provider':'Lingzhi','preset':'quality','model':'gpt-image-2.5-sunburst','authorization':'用户于2026-09-30授权每图最多首次加5次重试；本记录仅为Day53首轮。','updatedAt':dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z'),'assets':rows},ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'file':asset['file'],'status':row['status']},ensure_ascii=False))
    if result.returncode and 'API Key' in (result.stderr or ''): break
