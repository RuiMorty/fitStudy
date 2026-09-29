"""Send exactly one authorized Day49 image request and retain non-secret evidence."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
GENERATOR = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / 'image-prompts.json').read_text())
    assets = {item['file']: item for item in plan['assets']}
    if args.file not in assets:
        raise SystemExit('Unknown image-plan asset.')
    record_path = HERE / 'generation.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {
        'provider': plan['provider'], 'preset': 'quality', 'model': plan['model'],
        'authorization': plan['authorization'], 'startedAt': now(), 'attempts': []
    }
    if any(item['file'] == args.file for item in record['attempts']):
        raise SystemExit('This paid asset was already requested; refusing repeat.')
    if any(item.get('status', '').startswith('failed') or item.get('status') == 'requested' for item in record['attempts']):
        raise SystemExit('A prior request is unresolved or failed; automatic continuation is blocked.')
    output = HERE / 'source' / args.file
    if output.exists():
        raise SystemExit('Destination already exists; refusing overwrite.')
    output.parent.mkdir(parents=True, exist_ok=True)
    asset = assets[args.file]
    attempt = {'file': args.file, 'role': asset['role'], 'startedAt': now(), 'status': 'requested', 'output': str(output.relative_to(HERE.parent.parent))}
    record['attempts'].append(attempt)
    record['status'] = 'generating'
    save(record_path, record)
    result = subprocess.run([
        sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent',
        '--output-format', 'png', '--prompt', plan['commonPrompt'] + '\n' + asset['prompt'], '--output', str(output)
    ], capture_output=True, text=True)
    attempt.update({'completedAt': now(), 'returncode': result.returncode})
    if result.returncode or not output.is_file() or output.stat().st_size == 0:
        attempt['status'] = 'failed-no-retry'
        attempt['errorSummary'] = 'The authorized Lingzhi request returned no usable local PNG; no retry was sent.'
        record['status'] = 'failed-no-retry'
        save(record_path, record)
        print(json.dumps({'event': 'failed-no-retry', 'file': args.file}))
        return 1
    with Image.open(output) as image:
        mode, size = image.mode, list(image.size)
        alpha = image.getchannel('A').getextrema() if mode == 'RGBA' else None
    if mode != 'RGBA' or alpha is None or alpha[0] != 0:
        attempt.update({'status': 'failed-invalid-transparency', 'mode': mode, 'size': size, 'alphaRange': alpha, 'errorSummary': 'Output lacks a real transparent background; no retry was sent.'})
        record['status'] = 'failed-no-retry'
        save(record_path, record)
        print(json.dumps({'event': 'failed-invalid-transparency', 'file': args.file, 'mode': mode, 'alphaRange': alpha}))
        return 1
    attempt.update({'status': 'generated-pending-visual-quality', 'bytes': output.stat().st_size, 'size': size, 'alphaRange': alpha, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
    record['status'] = 'awaiting-visual-quality'
    record['updatedAt'] = now()
    save(record_path, record)
    print(json.dumps({'event': 'generated-pending-visual-quality', 'file': args.file, 'size': size, 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    raise SystemExit(main())
