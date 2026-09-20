"""Execute explicitly authorized image requests once, recording progress per asset."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
SCRIPT = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')
def now(): return datetime.now(timezone.utc).isoformat()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--files', nargs='+', required=True); args=parser.parse_args()
    plan=json.loads((HERE/'image-prompts.json').read_text())
    record_path=HERE/'generation.json'
    record=json.loads(record_path.read_text()) if record_path.exists() else {'model':plan['model'],'startedAt':now(),'authorization':plan['authorization'],'attempts':[]}
    requested={x['file'] for x in record['attempts']}
    assets={x['file']:x for x in plan['assets']}
    if any(f in requested or f not in assets for f in args.files): raise SystemExit('Unknown or already requested asset; refusing repeat.')
    if any(x['status']=='failed' for x in record['attempts']): raise SystemExit('Prior failure; no automatic continuation or retry.')
    (HERE/'source').mkdir(exist_ok=True)
    for filename in args.files:
        item=assets[filename]; output=HERE/'source'/filename
        if output.exists(): raise SystemExit('Existing output; refusing overwrite.')
        attempt={'file':filename,'startedAt':now(),'status':'requested'}
        record['attempts'].append(attempt);record['status']='generating';save(record_path,record)
        print(json.dumps({'event':'started','file':filename}),flush=True)
        result=subprocess.run([sys.executable,str(SCRIPT),'--preset','quality','--background','transparent','--prompt',plan['commonPrompt']+'\n'+item['prompt'],'--output',str(output)],capture_output=True,text=True)
        attempt.update({'completedAt':now(),'returncode':result.returncode})
        if result.returncode or not output.is_file() or output.stat().st_size==0:
            attempt['status']='failed';record['status']='failed-no-retry';save(record_path,record)
            print(json.dumps({'event':'failed-no-retry','file':filename,'returncode':result.returncode}),flush=True);return 1
        attempt.update({'status':'generated','bytes':output.stat().st_size});save(record_path,record)
        print(json.dumps({'event':'generated','file':filename,'bytes':output.stat().st_size}),flush=True)
    record['status']='batch-complete';record['updatedAt']=now();save(record_path,record);return 0
if __name__=='__main__':sys.exit(main())
