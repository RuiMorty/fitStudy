"""Generate each approved Day43 asset at most once and preserve its request record."""
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
    parser.add_argument('--resume-authorization', type=Path)
    args = parser.parse_args()
    plan = json.loads((HERE / 'image-prompts.json').read_text())
    record_path = HERE / 'generation.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {
        'provider': plan['provider'], 'model': plan['model'], 'startedAt': now(),
        'authorization': plan['authorization'], 'attempts': []
    }
    assets = {item['file']: item for item in plan['assets']}
    authorization = json.loads(args.resume_authorization.read_text()) if args.resume_authorization else None
    if authorization and any(name not in authorization['files'] for name in args.files):
        raise SystemExit('Asset is outside the explicit resume authorization.')
    prior_attempts = record['attempts']
    if any(item.get('status') == 'requested' for item in prior_attempts):
        raise SystemExit('An unresolved request exists; check its result before continuing.')
    current_attempts = [item for item in prior_attempts if not authorization or item.get('authorizationId') == authorization['id']]
    requested = {item['file'] for item in current_attempts}
    requested.update(item['file'] for item in prior_attempts if item.get('status') == 'generated')
    if any(name not in assets or name in requested for name in args.files):
        raise SystemExit('Unknown or previously requested asset; refusing to repeat a paid request.')
    if any(item.get('status') == 'failed-no-retry' for item in current_attempts):
        raise SystemExit('A prior asset failed; automatic continuation is blocked pending review.')
    source = HERE / 'source'
    source.mkdir(exist_ok=True)
    for name in args.files:
        item = assets[name]
        output = source / name
        if output.exists():
            raise SystemExit(f'Existing output for {name}; refusing overwrite.')
        attempt = {'file': name, 'role': item['role'], 'startedAt': now(), 'status': 'requested'}
        if authorization:
            attempt['authorizationId'] = authorization['id']
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
