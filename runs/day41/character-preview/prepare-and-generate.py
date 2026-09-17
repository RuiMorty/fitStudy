"""Generate the two explicitly authorized character style samples, once each."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys

ROOT = Path('/Users/agiuser/Documents/fit')
HERE = Path(__file__).resolve().parent
SKILL = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def main():
    prompts = json.loads((HERE / 'image-prompts.json').read_text())
    record_path = HERE / 'generation.json'
    if record_path.exists():
        raise SystemExit('Generation record already exists. Refusing duplicate requests.')
    (HERE / 'source').mkdir(parents=True, exist_ok=True)
    record = {'status': 'generating', 'startedAt': now(), 'model': prompts['model'], 'authorization': prompts['authorization'], 'attempts': []}
    save(record_path, record)
    for asset in prompts['assets']:
        output = HERE / 'source' / asset['file']
        if output.exists():
            raise SystemExit('Existing output. Refusing overwrite.')
        item = {'file': asset['file'], 'startedAt': now(), 'status': 'requested'}
        record['attempts'].append(item)
        save(record_path, record)
        print(json.dumps({'event': 'request-started', 'file': asset['file']}, ensure_ascii=False), flush=True)
        result = subprocess.run([sys.executable, str(SKILL), '--preset', 'quality', '--background', 'transparent', '--prompt', prompts['commonPrompt'] + '\n\n' + asset['prompt'], '--output', str(output)], capture_output=True, text=True)
        item.update({'completedAt': now(), 'returncode': result.returncode})
        if result.returncode != 0 or not output.is_file() or not output.stat().st_size:
            item['status'] = 'failed'
            record.update({'status': 'failed-no-retry', 'completedAt': now()})
            save(record_path, record)
            # Provider response is not echoed: it may include sensitive request metadata.
            print(json.dumps({'event': 'failed-no-retry', 'file': asset['file'], 'returncode': result.returncode}, ensure_ascii=False), flush=True)
            return 1
        item.update({'status': 'generated', 'bytes': output.stat().st_size})
        save(record_path, record)
        print(json.dumps({'event': 'generated', 'file': asset['file'], 'bytes': output.stat().st_size}, ensure_ascii=False), flush=True)
    record.update({'status': 'generated-awaiting-visual-review', 'completedAt': now()})
    save(record_path, record)
    return 0

if __name__ == '__main__':
    sys.exit(main())
