#!/usr/bin/env python3
"""Add Lingzhi's documented multipart reference input to the installed skill.

The installed skill supplies argument parsing, Keychain authentication, model
selection, image extraction, and file output. Each job permits one POST only.
Public Lingzhi UI uses repeated `image` parts for multiple reference images.
No credentials or response image payloads are written to the request log.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import uuid

ROOT = Path(__file__).resolve().parent
SKILL = Path('/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('job')
    args = parser.parse_args()
    job = json.loads((ROOT / 'prompts' / f'{args.job}.json').read_text())
    output = ROOT / 'raw' / f'{args.job}.png'
    log_path = ROOT / 'logs' / f'{args.job}.json'
    if log_path.exists() or output.exists():
        raise SystemExit('Job already has an attempt/output; automatic retries are prohibited.')
    spec = importlib.util.spec_from_file_location('lingzhi_image_skill', SKILL)
    skill = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skill)
    references = [(ROOT / p).resolve() for p in job['references']]
    record = {
        'job': args.job, 'started_at': datetime.now(timezone.utc).isoformat(),
        'model': skill.MODEL_PRESETS['quality'], 'endpoint': '/v1/images/edits',
        'references': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in references],
        'status': 'prepared', 'post_count': 0,
    }

    def save():
        log_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')

    def post_with_references(endpoint, key, payload):
        boundary = '----FitStudyReference' + uuid.uuid4().hex
        data = bytearray()
        for name, value in payload.items():
            data.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        for index, path in enumerate(references):
            data.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="reference-{index+1}.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
            data.extend(path.read_bytes())
            data.extend(b'\r\n')
        data.extend(f'--{boundary}--\r\n'.encode())
        endpoint = endpoint.removesuffix('/images/generations') + '/images/edits'
        request = Request(endpoint, data=bytes(data), headers={
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
            raise RuntimeError(f'灵智接口返回 HTTP {error.code}: {detail}') from error
        except (URLError, TimeoutError, OSError) as error:
            record.update(status='failed', error=str(error).replace(key, '[REDACTED]'))
            save()
            raise RuntimeError(f'灵智请求失败，未重试: {record["error"]}') from error
        record.update(status='response-received')
        save()
        return result

    skill.post_generation = post_with_references
    sys.argv = [str(SKILL), '--preset', 'quality', '--prompt', job['prompt'],
                '--size', '1024x1536', '--output', str(output)]
    code = skill.main()
    if code == 0 and output.is_file() and output.stat().st_size > 0:
        record.update(status='succeeded', output=str(output), bytes=output.stat().st_size,
                      output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    elif record['status'] not in {'failed'}:
        record.update(status='failed-before-request' if record['post_count'] == 0 else 'failed-after-response')
    record['completed_at'] = datetime.now(timezone.utc).isoformat()
    save()
    return code


if __name__ == '__main__':
    raise SystemExit(main())
