"""Generate each approved Day44 asset at most once and preserve its request record."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
GENERATOR = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', nargs='+', required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / 'image-prompts.json').read_text())
    record_path = HERE / 'generation.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {
        'provider': plan['provider'], 'model': plan['model'], 'startedAt': now(),
        'authorization': plan['authorization'], 'attempts': []
    }
    assets = {item['file']: item for item in plan['assets']}
    requested = {item['file'] for item in record['attempts']}
    if any(name not in assets or name in requested for name in args.files):
        raise SystemExit('Unknown or previously requested asset; refusing to repeat a paid request.')
    if any(item.get('status') in ('requested', 'failed-no-retry') for item in record['attempts']):
        raise SystemExit('A prior request is unresolved or failed; automatic continuation is blocked.')
    source = HERE / 'source'
    source.mkdir(exist_ok=True)
    for name in args.files:
        item = assets[name]
        output = source / name
        if output.exists():
            raise SystemExit(f'Existing output for {name}; refusing overwrite.')
        attempt = {'file': name, 'role': item['role'], 'startedAt': now(), 'status': 'requested'}
        record['attempts'].append(attempt)
        record['status'] = 'generating'
        save(record_path, record)
        result = subprocess.run(
            [sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent',
             '--prompt', plan['commonPrompt'] + '\n' + item['prompt'], '--output', str(output)],
            capture_output=True, text=True
        )
        attempt.update({'completedAt': now(), 'returncode': result.returncode})
        if result.returncode or not output.is_file() or output.stat().st_size == 0:
            attempt['status'] = 'failed-no-retry'
            record['status'] = 'failed-no-retry'
            save(record_path, record)
            print(json.dumps({'event': 'failed-no-retry', 'file': name, 'returncode': result.returncode}), flush=True)
            return 1
        attempt.update({'status': 'generated', 'bytes': output.stat().st_size})
        save(record_path, record)
        print(json.dumps({'event': 'generated', 'file': name, 'bytes': output.stat().st_size}), flush=True)
    record['status'] = 'batch-complete'
    record['updatedAt'] = now()
    save(record_path, record)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())


