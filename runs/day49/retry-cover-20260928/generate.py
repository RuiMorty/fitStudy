"""Make exactly one user-authorized Day49 cover revision without overwriting evidence."""
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


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    authorization = json.loads((HERE / 'authorization.json').read_text())
    output = DAY.parent.parent / authorization['output']
    record_path = HERE / 'generation.json'
    if output.exists() or record_path.exists():
        raise SystemExit('A revision output or record already exists; refusing another paid request.')
    prompt = (HERE / 'prompt.txt').read_text()
    record = {
        'provider': 'Lingzhi', 'preset': 'quality', 'model': 'gpt-image-2.5-sunburst',
        'authorization': 'runs/day49/retry-cover-20260928/authorization.json',
        'previousFailure': authorization['previousFailure'], 'status': 'requesting',
        'attempts': [{'file': 'cover-attempt-02.png', 'role': 'cover-revision', 'startedAt': now(), 'status': 'requested', 'output': authorization['output']}]
    }
    save(record_path, record)
    result = subprocess.run([
        sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent', '--output-format', 'png',
        '--prompt', prompt, '--output', str(output)
    ], capture_output=True, text=True)
    attempt = record['attempts'][0]
    attempt.update({'completedAt': now(), 'returncode': result.returncode})
    if result.returncode or not output.is_file() or not output.stat().st_size:
        attempt.update({'status': 'failed-no-retry', 'errorSummary': 'The single authorized revision returned no usable local PNG; no further request was sent.'})
        record['status'] = 'failed-no-retry'
        save(record_path, record)
        print(json.dumps({'event': 'failed-no-retry', 'file': attempt['file']}))
        return 1
    with Image.open(output) as image:
        mode, size = image.mode, list(image.size)
        alpha = image.getchannel('A').getextrema() if mode == 'RGBA' else None
    if mode != 'RGBA' or alpha is None or alpha[0] != 0:
        attempt.update({'status': 'failed-invalid-transparency', 'mode': mode, 'size': size, 'alphaRange': alpha, 'errorSummary': 'The output lacks a real transparent background; no further request was sent.'})
        record['status'] = 'failed-no-retry'
        save(record_path, record)
        print(json.dumps({'event': 'failed-invalid-transparency', 'file': attempt['file'], 'mode': mode, 'alphaRange': alpha}))
        return 1
    attempt.update({'status': 'generated-pending-visual-quality', 'size': size, 'bytes': output.stat().st_size, 'alphaRange': alpha, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
    record['status'] = 'awaiting-visual-quality'
    record['completedAt'] = now()
    save(record_path, record)
    print(json.dumps({'event': 'generated-pending-visual-quality', 'file': attempt['file'], 'size': size, 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    raise SystemExit(main())
