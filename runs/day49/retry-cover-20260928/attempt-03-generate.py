"""Send the first billable Day49 cover request using the available host Keychain credential."""
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
OUTPUT = HERE / 'cover-attempt-03.png'
RECORD = HERE / 'attempt-03-generation.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def save(value):
    RECORD.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    if OUTPUT.exists() or RECORD.exists():
        raise SystemExit('Attempt-03 output or record already exists; refusing duplicate provider request.')
    prompt = (HERE / 'attempt-03-prompt.txt').read_text()
    record = {
        'provider': 'Lingzhi', 'preset': 'quality', 'model': 'gpt-image-2.5-sunburst',
        'authorization': 'runs/day49/retry-policy.json',
        'hostCredentialCheck': 'keychain-available-without-disclosing-secret',
        'previousFailures': ['runs/day49/failure.json', 'runs/day49/retry-cover-20260928/failure-attempt-02.json'],
        'providerRequestNumberForCover': 1,
        'status': 'requesting',
        'attempt': {'file': 'cover-attempt-03.png', 'role': 'cover-revision', 'startedAt': now(), 'status': 'requested', 'output': 'runs/day49/retry-cover-20260928/cover-attempt-03.png'}
    }
    save(record)
    result = subprocess.run([
        sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent', '--output-format', 'png',
        '--prompt', prompt, '--output', str(OUTPUT)
    ], capture_output=True, text=True)
    record['attempt'].update({'completedAt': now(), 'returncode': result.returncode})
    if result.returncode or not OUTPUT.is_file() or not OUTPUT.stat().st_size:
        record['attempt'].update({'status': 'failed-no-retry', 'errorSummary': 'Provider request returned no usable local PNG; do not retry without a revised prompt.'})
        record['status'] = 'failed-no-retry'
        save(record)
        print(json.dumps({'event': 'failed-no-retry', 'providerRequestNumberForCover': 1}))
        return 1
    with Image.open(OUTPUT) as image:
        mode, size = image.mode, list(image.size)
        alpha = image.getchannel('A').getextrema() if mode == 'RGBA' else None
    if mode != 'RGBA' or alpha is None or alpha[0] != 0:
        record['attempt'].update({'status': 'failed-invalid-transparency', 'mode': mode, 'size': size, 'alphaRange': alpha, 'errorSummary': 'Provider output lacks real transparent background; do not retry without a revised prompt.'})
        record['status'] = 'failed-no-retry'
        save(record)
        print(json.dumps({'event': 'failed-invalid-transparency', 'mode': mode, 'alphaRange': alpha}))
        return 1
    record['attempt'].update({'status': 'generated-pending-visual-quality', 'size': size, 'bytes': OUTPUT.stat().st_size, 'alphaRange': alpha, 'sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest()})
    record['status'] = 'awaiting-visual-quality'
    record['completedAt'] = now()
    save(record)
    print(json.dumps({'event': 'generated-pending-visual-quality', 'size': size, 'bytes': OUTPUT.stat().st_size}))


if __name__ == '__main__':
    raise SystemExit(main())
