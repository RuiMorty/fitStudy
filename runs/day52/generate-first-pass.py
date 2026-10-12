#!/usr/bin/env python3
"""Generate each Day52 image once, retaining non-secret request evidence for QA."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "image-prompts.json").read_text())
GENERATOR = Path("/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py")
RECORD = HERE / "generation-first-pass.json"

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

records = []
for asset in PLAN["assets"]:
    output = HERE / "source" / asset["file"]
    result = subprocess.run([sys.executable, str(GENERATOR), "--preset", "quality", "--background", "transparent", "--output-format", "png", "--prompt", PLAN["commonPrompt"] + "\n\n" + asset["prompt"], "--output", str(output)], capture_output=True, text=True)
    entry = {"file": asset["file"], "role": asset["role"], "attempt": 1, "returncode": result.returncode, "output": str(output.relative_to(HERE.parent.parent))}
    if result.returncode == 0 and output.is_file() and output.stat().st_size:
        entry.update({"status": "generated-pending-quality-review", "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    else:
        entry.update({"status": "request-failed", "errorSummary": (result.stderr or result.stdout or "no usable local PNG").strip()[:1000]})
    records.append(entry)
    RECORD.write_text(json.dumps({"provider":"Lingzhi","preset":"quality","model":"gpt-image-2.5-sunburst","authorization":"用户于2026-09-30授权每图最多首次加5次重试；本记录仅为Day52首轮。","updatedAt":now(),"assets":records}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"file":asset["file"],"status":entry["status"]}, ensure_ascii=False))
    if result.returncode and "API Key" in (result.stderr or ""):
        break
