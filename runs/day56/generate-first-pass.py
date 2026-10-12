#!/usr/bin/env python3
"""One authorized first Lingzhi request per Day56 asset; retry handling stays explicit."""
import datetime as dt
import hashlib
import json
import subprocess
import sys
import argparse
from pathlib import Path

here = Path(__file__).resolve().parent
plan = json.loads((here / 'image-prompts.json').read_text())
record = here / 'generation-first-pass.json'
generator = '/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py'
parser = argparse.ArgumentParser()
parser.add_argument('--file')
args = parser.parse_args()
if args.file and args.file not in {asset['file'] for asset in plan['assets']}:
    raise SystemExit(f'Unknown asset: {args.file}')
previous = json.loads(record.read_text()) if record.exists() else {'assets': []}
rows = {row['file']: row for row in previous.get('assets', [])}
for asset in plan['assets']:
    if args.file and asset['file'] != args.file:
        continue
    output = here / 'source' / asset['file']
    if output.is_file() and output.stat().st_size:
        continue
    result = subprocess.run([
        sys.executable, generator, '--preset', 'quality', '--background', 'transparent',
        '--output-format', 'png', '--prompt', plan['commonPrompt'] + '\n\n' + asset['prompt'],
        '--output', str(output),
    ], capture_output=True, text=True)
    row = {
        'file': asset['file'], 'role': asset['role'], 'attempt': 1,
        'returncode': result.returncode, 'output': str(output.relative_to(here.parent.parent)),
    }
    if result.returncode == 0 and output.is_file() and output.stat().st_size:
        row.update({
            'status': 'generated-pending-quality-review', 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        })
    else:
        row.update({'status': 'request-failed', 'errorSummary': (result.stderr or result.stdout or 'no usable local PNG').strip()[:1000]})
    rows[asset['file']] = row
    record.write_text(json.dumps({
        'provider': 'Lingzhi', 'preset': 'quality', 'model': 'gpt-image-2.5-sunburst',
        'authorization': '用户于2026-09-30授权每张图片首次请求后最多5次经调整提示词重试；本记录仅为Day56首轮。',
        'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'assets': list(rows.values()),
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'file': asset['file'], 'status': row['status']}, ensure_ascii=False), flush=True)
    if result.returncode and ('API Key' in (result.stderr or '') or 'auth' in (result.stderr or '').lower()):
        break
