from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import sys

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('attempt',type=int)
parser.add_argument('prompt_file',type=Path)
args=parser.parse_args()
if not 2 <= args.attempt <= 6:
    parser.error('This image permits five retries after the initial request (attempts 2 through 6).')
record_file=root/f'attempt-{args.attempt:02d}.json'
if record_file.exists():
    parser.error('Attempt record already exists; do not duplicate a request.')
output=root/'rick-door-scene.png'
if output.exists():
    parser.error('Image already exists; inspect and use it instead of regenerating.')
prompt=args.prompt_file.read_text().strip()
prompt_file=root/f'prompt-{args.attempt:02d}.txt'
prompt_file.write_text(prompt+'\n')
record={
    'attempt':args.attempt,
    'retry':args.attempt-1,
    'max_retries':5,
    'started_at':datetime.now(timezone.utc).isoformat(),
    'model':'gpt-image-2.5-sunburst',
    'size':'1024x1024',
    'prompt_file':prompt_file.name,
    'status':'requesting',
}
record_file.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
command=[sys.executable,'/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py','--preset','quality','--size','1024x1024','--prompt',prompt,'--output',str(output)]
result=subprocess.run(command,capture_output=True,text=True)
record['finished_at']=datetime.now(timezone.utc).isoformat()
record['exit_code']=result.returncode
record['status']='success' if result.returncode==0 and output.is_file() and output.stat().st_size else 'failed'
if record['status']=='success':
    record['output']=str(output)
    record['bytes']=output.stat().st_size
else:
    record['error_summary']=result.stderr.strip()[:5000] or 'Image file was not created'
record_file.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
raise SystemExit((result.returncode or 1) if record['status']=='failed' else 0)
