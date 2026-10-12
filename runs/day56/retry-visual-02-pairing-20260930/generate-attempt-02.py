#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
request = json.loads((Path(__file__).resolve().parent / 'attempt-02-request.json').read_text())
plan = json.loads((root / 'runs/day56/image-prompts.json').read_text())
subprocess.run([sys.executable, '/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py', '--preset', 'quality', '--background', 'transparent', '--output-format', 'png', '--prompt', plan['commonPrompt'] + '\n\n' + request['adjustedPrompt'], '--output', str(root / request['output'])], check=True)
