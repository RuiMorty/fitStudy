#!/usr/bin/env python3
"""Generate exactly one Lingzhi image-edit request with two real reference images.

Reference 1 fixes the recurring presenter. Reference 2 fixes the card style.
Each job stores a non-secret request record and cannot be retried automatically.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT.parent
SKILL = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')
MODEL = Path('/Users/agiuser/Documents/fit/xhs-wrong-notebook/2026-09-22-joint-actions/00-rick-muscular-cartoon-model-v4.png')
STYLE = Path('/Users/agiuser/Documents/fit/xhs-wrong-notebook/2026-09-22-joint-actions/04-肩关节动作地图-修订.png')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('job', help='1-based card number, e.g. 01')
    parser.add_argument('--variant', default='reference-edits', help='subdirectory used for raw files and non-secret logs')
    parser.add_argument('--prompt-file', default='prompts.json', help='prompt JSON relative to the generation directory')
    args = parser.parse_args()
    prompt_data = json.loads((ROOT / args.prompt_file).read_text())
    number = int(args.job)
    card = prompt_data['cards'][number - 1]
    raw_dir = ROOT / args.variant / 'raw'
    logs_dir = ROOT / args.variant / 'logs'
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    output = raw_dir / f'{number:02d}-{card["id"]}.png'
    log_path = logs_dir / f'{number:02d}-{card["id"]}.json'
    if output.exists() or log_path.exists():
        raise SystemExit('This job already has an attempt/output; automatic retries are prohibited.')
    if not MODEL.is_file() or not STYLE.is_file():
        raise SystemExit('Required model/style reference is missing.')

    spec = importlib.util.spec_from_file_location('lingzhi_image_skill', SKILL)
    skill = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skill)
    references = [MODEL, STYLE]
    topic_prompt = card['nativeTextPrompt'] if 'nativeTextPrompt' in card else card['prompt']
    prompt = f"{prompt_data['referenceEditSharedPrompt']}\n\nTopic-specific composition: {topic_prompt}"
    record = {
        'job': f'{number:02d}-{card["id"]}',
        'variant': args.variant,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'provider': 'Lingzhi',
        'model': skill.MODEL_PRESETS['quality'],
        'endpoint': '/v1/images/edits',
        'references': [
            {'role': 'fixed-presenter-model', 'path': str(MODEL), 'sha256': hashlib.sha256(MODEL.read_bytes()).hexdigest()},
            {'role': 'card-style-reference', 'path': str(STYLE), 'sha256': hashlib.sha256(STYLE.read_bytes()).hexdigest()},
        ],
        'status': 'prepared',
        'post_count': 0,
        'output': str(output),
    }

    def save() -> None:
        log_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')

    def post_with_references(endpoint, key, payload):
        boundary = '----FitStudyReference' + uuid.uuid4().hex
        body = bytearray()
        for name, value in payload.items():
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        for index, ref in enumerate(references):
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="reference-{index + 1}.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
            body.extend(ref.read_bytes())
            body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode())
        request = Request(endpoint.removesuffix('/images/generations') + '/images/edits', data=bytes(body), headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Accept': 'application/json',
        }, method='POST')
        record.update(status='request-started', post_count=1)
        save()
        try:
            with urlopen(request, timeout=240) as response:
                result = json.load(response)
        except HTTPError as error:
            detail = error.read(8192).decode('utf-8', errors='replace').replace(key, '[REDACTED]')
            record.update(status='failed', http_status=error.code, error=detail)
            save()
            raise RuntimeError(f'Lingzhi HTTP {error.code}: {detail}') from error
        except (URLError, TimeoutError, OSError) as error:
            record.update(status='failed', error=str(error).replace(key, '[REDACTED]'))
            save()
            raise RuntimeError(f'Lingzhi request failed without retry: {record["error"]}') from error
        record.update(status='response-received')
        save()
        return result

    skill.post_generation = post_with_references
    sys.argv = [str(SKILL), '--preset', 'quality', '--prompt', prompt, '--size', prompt_data['size'], '--output', str(output)]
    code = skill.main()
    if code == 0 and output.is_file() and output.stat().st_size > 0:
        record.update(status='succeeded', bytes=output.stat().st_size, output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    elif record['status'] != 'failed':
        record.update(status='failed-before-request' if record['post_count'] == 0 else 'failed-after-response')
    record['completed_at'] = datetime.now(timezone.utc).isoformat()
    save()
    return code


if __name__ == '__main__':
    raise SystemExit(main())
