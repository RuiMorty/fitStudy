"""Generate the remaining Day49 assets using the host Keychain, with bounded per-asset retries."""
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
MAX_PROVIDER_REQUESTS = 6


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def revised_prompt(common, original, attempt):
    refinements = [
        "Keep the composition simple and sparse; include only the requested objects and two characters; preserve every requested limb, foot and equipment item.",
        "Use a wider safety margin and one clear focal action; verify no unrelated objects, people, text, markers, frames, floor or background are present.",
        "Make the action mechanically conservative, stable and teachable; keep all equipment connections physically continuous and complete."
    ]
    return common + '\n' + original + '\n' + refinements[min(attempt - 2, len(refinements) - 1)]


def verify_png(output):
    if not output.is_file() or not output.stat().st_size:
        return None, 'no-local-output'
    try:
        with Image.open(output) as image:
            mode, size = image.mode, list(image.size)
            alpha = image.getchannel('A').getextrema() if mode == 'RGBA' else None
    except Exception:
        return None, 'unreadable-output'
    if mode != 'RGBA' or alpha is None or alpha[0] != 0:
        return {'mode': mode, 'size': size, 'alphaRange': alpha}, 'invalid-transparency'
    return {'mode': mode, 'size': size, 'alphaRange': alpha, 'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', nargs='+', required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / 'image-prompts.json').read_text())
    assets = {asset['file']: asset for asset in plan['assets']}
    requested = args.files
    if any(name not in assets or name == 'cover.png' for name in requested):
        raise SystemExit('Only still-unrequested non-cover plan assets are permitted.')
    manifest_path = HERE / 'authorized-generation.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'provider': plan['provider'], 'preset': 'quality', 'model': plan['model'],
        'authorization': 'runs/day49/retry-policy.json', 'hostCredentialCheck': 'keychain-available-without-disclosing-secret',
        'startedAt': now(), 'assets': [], 'status': 'generating'
    }
    seen = {item['file'] for item in manifest['assets']}
    if any(name in seen for name in requested):
        raise SystemExit('At least one requested asset already has a record; refusing duplicate work.')
    source = HERE / 'source'
    source.mkdir(exist_ok=True)
    for name in requested:
        asset = assets[name]
        asset_record = {'file': name, 'role': asset['role'], 'status': 'generating', 'attempts': []}
        manifest['assets'].append(asset_record)
        save(manifest_path, manifest)
        success = False
        for provider_attempt in range(1, MAX_PROVIDER_REQUESTS + 1):
            output = source / (name if provider_attempt == 1 else f'{Path(name).stem}-attempt-{provider_attempt}{Path(name).suffix}')
            if output.exists():
                raise SystemExit(f'Refusing to overwrite {output}')
            attempt = {
                'providerRequestNumberForAsset': provider_attempt,
                'output': str(output.relative_to(HERE.parent.parent)),
                'startedAt': now(), 'status': 'requested'
            }
            asset_record['attempts'].append(attempt)
            save(manifest_path, manifest)
            prompt = revised_prompt(plan['commonPrompt'], asset['prompt'], provider_attempt)
            result = subprocess.run([
                sys.executable, str(GENERATOR), '--preset', 'quality', '--background', 'transparent', '--output-format', 'png',
                '--prompt', prompt, '--output', str(output)
            ], capture_output=True, text=True)
            attempt.update({'completedAt': now(), 'returncode': result.returncode})
            quality, problem = verify_png(output)
            if result.returncode or problem:
                attempt.update({'status': f'failed-{problem or "provider"}', 'quality': quality})
                asset_record['status'] = 'failed'
                save(manifest_path, manifest)
                if provider_attempt == MAX_PROVIDER_REQUESTS:
                    manifest['status'] = 'failed-no-retry-budget'
                    save(manifest_path, manifest)
                    print(json.dumps({'event': 'failed-no-retry-budget', 'file': name, 'attempts': provider_attempt}))
                    return 1
                continue
            attempt.update({'status': 'generated-pending-visual-quality', 'quality': quality})
            asset_record['status'] = 'generated-pending-visual-quality'
            asset_record['acceptedCandidate'] = attempt['output']
            save(manifest_path, manifest)
            print(json.dumps({'event': 'generated-pending-visual-quality', 'file': name, 'attempt': provider_attempt, 'size': quality['size']}))
            success = True
            break
        if not success:
            return 1
    manifest['status'] = 'awaiting-visual-quality'
    manifest['completedAt'] = now()
    save(manifest_path, manifest)


if __name__ == '__main__':
    raise SystemExit(main())
