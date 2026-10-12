#!/usr/bin/env python3
"""Make the authorized adjusted second request for Day58 visual 04 only."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
root = here.parents[2]
request = json.loads((here / "request.json").read_text())
plan = json.loads((root / "runs/day58/image-prompts.json").read_text())
full_prompt = plan["commonPrompt"] + "\n\n" + request["prompt"]
target = root / "runs/day58/source/visual-04-progression.png"
generator = "/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py"
result = subprocess.run([
    sys.executable, generator, "--preset", "quality", "--background", "transparent",
    "--output-format", "png", "--prompt", full_prompt, "--output", str(target),
], capture_output=True, text=True)
record = dict(request)
record.update({
    "provider": "Lingzhi",
    "preset": "quality",
    "model": "gpt-image-2.5-sunburst",
    "requestedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    "fullPrompt": full_prompt,
    "returncode": result.returncode,
    "output": "runs/day58/source/visual-04-progression.png",
})
if result.returncode == 0 and target.is_file() and target.stat().st_size:
    record.update({"status": "generated-pending-quality-review", "bytes": target.stat().st_size,
                   "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
else:
    record.update({"status": "request-failed", "errorSummary": (result.stderr or result.stdout or "no usable local PNG").strip()[:1000]})
(here / "result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"file": request["file"], "attempt": request["attempt"], "status": record["status"]}, ensure_ascii=False))
