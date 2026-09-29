"""Make the fourth bounded provider request for the one remaining Day49 visual correction."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent; DAY=HERE.parent; GENERATOR=Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py'); OUTPUT=DAY/'source/visual-06-dosage-readiness-attempt-04.png'; RECORD=HERE/'attempt-04-generation.json'
def now(): return datetime.now(timezone.utc).isoformat()
def save(value): RECORD.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
 if OUTPUT.exists() or RECORD.exists(): raise SystemExit('Attempt-04 output or record already exists; refusing duplicate provider request.')
 plan=json.loads((DAY/'image-prompts.json').read_text()); item=next(a for a in plan['assets'] if a['file']=='visual-06-dosage-readiness.png'); prompt=(HERE/'attempt-04-prompt.txt').read_text()
 record={'provider':plan['provider'],'preset':'quality','model':plan['model'],'authorization':'runs/day49/retry-policy.json','visualReviews':['runs/day49/visual-quality-review-01.json','runs/day49/visual-quality-review-02.json','runs/day49/visual-quality-review-03.json'],'status':'requesting','attempt':{'file':item['file'],'role':item['role'],'providerRequestNumberForAsset':4,'startedAt':now(),'status':'requested','output':str(OUTPUT.relative_to(DAY.parent.parent))}}; save(record)
 result=subprocess.run([sys.executable,str(GENERATOR),'--preset','quality','--background','transparent','--output-format','png','--prompt',plan['commonPrompt']+'\n'+prompt,'--output',str(OUTPUT)],capture_output=True,text=True); attempt=record['attempt'];attempt.update({'completedAt':now(),'returncode':result.returncode})
 if result.returncode or not OUTPUT.is_file() or not OUTPUT.stat().st_size: attempt['status']='failed-no-local-output';record['status']='failed-no-retry';save(record);print(json.dumps({'event':'failed-no-local-output'}));return 1
 with Image.open(OUTPUT) as im: mode,size=im.mode,list(im.size);alpha=im.getchannel('A').getextrema() if mode=='RGBA' else None
 if mode!='RGBA' or alpha is None or alpha[0]!=0: attempt.update({'status':'failed-invalid-transparency','mode':mode,'size':size,'alphaRange':alpha});record['status']='failed-no-retry';save(record);print(json.dumps({'event':'failed-invalid-transparency'}));return 1
 attempt.update({'status':'generated-pending-visual-quality','size':size,'alphaRange':alpha,'bytes':OUTPUT.stat().st_size,'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()});record['status']='awaiting-visual-quality';record['completedAt']=now();save(record);print(json.dumps({'event':'generated-pending-visual-quality','size':size}))
if __name__=='__main__': raise SystemExit(main())
