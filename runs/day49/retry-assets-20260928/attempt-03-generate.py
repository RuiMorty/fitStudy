"""Make the third bounded provider request for the two remaining Day49 visual QA corrections."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
DAY=HERE.parent
GENERATOR=Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')
ALLOWED={'visual-01-power-intent.png','visual-06-dosage-readiness.png'}
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--files',nargs='+',required=True); args=parser.parse_args()
 if any(name not in ALLOWED for name in args.files): raise SystemExit('Only the two remaining visual QA corrections are allowed.')
 plan=json.loads((DAY/'image-prompts.json').read_text()); prompts=json.loads((HERE/'attempt-03-prompts.json').read_text())
 record_path=HERE/'attempt-03-generation.json'
 if record_path.exists(): raise SystemExit('Attempt-03 record already exists; refusing duplicate provider request.')
 record={'provider':plan['provider'],'preset':'quality','model':plan['model'],'authorization':'runs/day49/retry-policy.json','visualReviews':['runs/day49/visual-quality-review-01.json','runs/day49/visual-quality-review-02.json'],'status':'generating','attempts':[]}; save(record_path,record)
 for name in args.files:
  item=next(a for a in plan['assets'] if a['file']==name); output=DAY/'source'/f'{Path(name).stem}-attempt-03{Path(name).suffix}'
  if output.exists(): raise SystemExit(f'Refusing to overwrite {output}')
  attempt={'file':name,'role':item['role'],'providerRequestNumberForAsset':3,'startedAt':now(),'status':'requested','output':str(output.relative_to(DAY.parent.parent))}; record['attempts'].append(attempt); save(record_path,record)
  result=subprocess.run([sys.executable,str(GENERATOR),'--preset','quality','--background','transparent','--output-format','png','--prompt',plan['commonPrompt']+'\n'+prompts[name],'--output',str(output)],capture_output=True,text=True)
  attempt.update({'completedAt':now(),'returncode':result.returncode})
  if result.returncode or not output.is_file() or not output.stat().st_size:
   attempt['status']='failed-no-local-output'; record['status']='failed-no-retry'; save(record_path,record); print(json.dumps({'event':'failed-no-local-output','file':name})); return 1
  with Image.open(output) as im: mode,size=im.mode,list(im.size); alpha=im.getchannel('A').getextrema() if mode=='RGBA' else None
  if mode!='RGBA' or alpha is None or alpha[0]!=0:
   attempt.update({'status':'failed-invalid-transparency','mode':mode,'size':size,'alphaRange':alpha}); record['status']='failed-no-retry'; save(record_path,record); print(json.dumps({'event':'failed-invalid-transparency','file':name})); return 1
  attempt.update({'status':'generated-pending-visual-quality','size':size,'alphaRange':alpha,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}); save(record_path,record); print(json.dumps({'event':'generated-pending-visual-quality','file':name,'size':size}))
 record['status']='awaiting-visual-quality';record['completedAt']=now();save(record_path,record)
if __name__=='__main__': raise SystemExit(main())
