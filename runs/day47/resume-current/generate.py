"""Make exactly the user-authorized single Day47 replacement image request."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
GENERATOR = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')

def now(): return datetime.now(timezone.utc).isoformat()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    authorization = json.loads((HERE / 'authorization.json').read_text())
    plan = json.loads((DAY / 'image-prompts.json').read_text())
    asset = next((item for item in plan['assets'] if item['file'] == authorization['asset']), None)
    if asset is None or asset['file'] != 'overview-04-cut.png':
        raise SystemExit('Only the explicitly authorized replacement asset may be generated.')
    output = DAY / 'source' / asset['file']
    if output.exists(): raise SystemExit('Refusing to overwrite an existing image.')
    record_path = HERE / 'generation.json'
    if record_path.exists(): raise SystemExit('A resume request was already recorded; refusing another paid request.')
    record = {'provider': plan['provider'], 'model': plan['model'], 'authorization': authorization, 'previousFailure': authorization['previousFailure'], 'status': 'requesting', 'attempts': [{'file': asset['file'], 'role': asset['role'], 'startedAt': now(), 'status': 'requested', 'prompt': authorization['revisedPrompt']}]}
    save(record_path, record)
    result = subprocess.run([sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent', '--prompt', plan['commonPrompt'] + '\n' + authorization['revisedPrompt'], '--output', str(output)], capture_output=True, text=True)
    attempt = record['attempts'][0]
    attempt.update({'completedAt': now(), 'returncode': result.returncode})
    if result.returncode or not output.is_file() or output.stat().st_size == 0:
        attempt['status'] = 'failed-no-retry'
        attempt['errorSummary'] = 'Lingzhi generator returned a non-zero status or no local output; no retry was sent.'
        record['status'] = 'failed-no-retry'
        save(record_path, record)
        print(json.dumps({'event': 'failed-no-retry', 'file': asset['file']}))
        return 1
    attempt.update({'status': 'generated', 'bytes': output.stat().st_size})
    record['status'] = 'generated'
    record['completedAt'] = now()
    save(record_path, record)
    print(json.dumps({'event': 'generated', 'file': asset['file'], 'bytes': output.stat().st_size}))

if __name__ == '__main__': raise SystemExit(main())
