"""Make one bounded revised provider request for each visually rejected Day49 asset."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
GENERATOR = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')


def now(): return datetime.now(timezone.utc).isoformat()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--files', nargs='+', required=True); args = parser.parse_args()
    plan = json.loads((DAY / 'image-prompts.json').read_text())
    prompts = json.loads((HERE / 'retry-prompts.json').read_text())
    if any(name not in prompts for name in args.files): raise SystemExit('Only visually rejected assets may be retried by this script.')
    record_path = HERE / 'generation.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {
        'provider': plan['provider'], 'preset': 'quality', 'model': plan['model'],
        'authorization': 'runs/day49/retry-policy.json', 'visualReview': 'runs/day49/visual-quality-review-01.json',
        'status': 'generating', 'attempts': []
    }
    seen = {item['file'] for item in record['attempts']}
    if any(name in seen for name in args.files): raise SystemExit('An asset already has a retry record; refusing duplicate request.')
    for name in args.files:
        original = next(item for item in plan['assets'] if item['file'] == name)
        output = DAY / 'source' / f'{Path(name).stem}-attempt-02{Path(name).suffix}'
        if output.exists(): raise SystemExit(f'Refusing to overwrite {output}')
        attempt = {'file': name, 'role': original['role'], 'providerRequestNumberForAsset': 2, 'startedAt': now(), 'status': 'requested', 'output': str(output.relative_to(DAY.parent.parent))}
        record['attempts'].append(attempt); save(record_path, record)
        result = subprocess.run([
            sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent', '--output-format', 'png',
            '--prompt', plan['commonPrompt'] + '\n' + prompts[name], '--output', str(output)
        ], capture_output=True, text=True)
        attempt.update({'completedAt': now(), 'returncode': result.returncode})
        if result.returncode or not output.is_file() or not output.stat().st_size:
            attempt.update({'status': 'failed-no-local-output', 'errorSummary': 'Provider retry returned no local PNG.'}); record['status'] = 'failed-no-retry'; save(record_path, record); print(json.dumps({'event':'failed-no-local-output','file':name})); return 1
        with Image.open(output) as image:
            mode, size = image.mode, list(image.size); alpha = image.getchannel('A').getextrema() if mode == 'RGBA' else None
        if mode != 'RGBA' or alpha is None or alpha[0] != 0:
            attempt.update({'status':'failed-invalid-transparency','mode':mode,'size':size,'alphaRange':alpha}); record['status']='failed-no-retry'; save(record_path, record); print(json.dumps({'event':'failed-invalid-transparency','file':name})); return 1
        attempt.update({'status':'generated-pending-visual-quality','size':size,'alphaRange':alpha,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}); save(record_path, record); print(json.dumps({'event':'generated-pending-visual-quality','file':name,'size':size}))
    record['status']='awaiting-visual-quality'; record['completedAt']=now(); save(record_path, record)


if __name__ == '__main__': raise SystemExit(main())
