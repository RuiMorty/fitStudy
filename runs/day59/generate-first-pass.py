#!/usr/bin/env python3
"""Make one authorized first Lingzhi request per Day59 asset; this script never retries."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
plan = json.loads((here / "image-prompts.json").read_text())
record = here / "generation-first-pass.json"
generator = "/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py"
parser = argparse.ArgumentParser()
parser.add_argument("--file")
args = parser.parse_args()
files = {asset["file"] for asset in plan["assets"]}
if args.file and args.file not in files:
    raise SystemExit(f"Unknown asset: {args.file}")
previous = json.loads(record.read_text()) if record.exists() else {"assets": []}
rows = {row["file"]: row for row in previous.get("assets", [])}

def save_record():
    record.write_text(json.dumps({
        "provider": "Lingzhi",
        "preset": "quality",
        "model": "gpt-image-2.5-sunburst",
        "authorization": "用户于2026-09-30授权每张图片首次请求后最多5次经调整提示词重试；本脚本只执行Day59首轮，不执行重试。",
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "assets": list(rows.values()),
    }, ensure_ascii=False, indent=2) + "\n")

for asset in plan["assets"]:
    if args.file and asset["file"] != args.file:
        continue
    if asset["file"] in rows:
        print(json.dumps({"file": asset["file"], "status": "skipped-already-recorded-no-retry"}, ensure_ascii=False), flush=True)
        continue
    output = here / "source" / asset["file"]
    full_prompt = plan["commonPrompt"] + "\n\n" + asset["prompt"]
    if output.is_file() and output.stat().st_size:
        rows[asset["file"]] = {
            "file": asset["file"], "role": asset["role"], "attempt": 0,
            "prompt": full_prompt, "status": "existing-source-not-requested",
            "output": str(output.relative_to(here.parent.parent)),
            "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        }
        save_record()
        print(json.dumps({"file": asset["file"], "status": "existing-source-not-requested"}, ensure_ascii=False), flush=True)
        continue
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([
        sys.executable, generator, "--preset", "quality", "--background", "transparent",
        "--output-format", "png", "--prompt", full_prompt, "--output", str(output),
    ], capture_output=True, text=True)
    row = {
        "file": asset["file"], "role": asset["role"], "attempt": 1,
        "prompt": full_prompt, "returncode": result.returncode,
        "output": str(output.relative_to(here.parent.parent)),
    }
    if result.returncode == 0 and output.is_file() and output.stat().st_size:
        row.update({"status": "generated-pending-quality-review", "bytes": output.stat().st_size,
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    else:
        row.update({"status": "request-failed", "errorSummary": (result.stderr or result.stdout or "no usable local PNG").strip()[:1000]})
    rows[asset["file"]] = row
    save_record()
    print(json.dumps({"file": asset["file"], "status": row["status"]}, ensure_ascii=False), flush=True)
    if result.returncode and ("API Key" in (result.stderr or "") or "auth" in (result.stderr or "").lower()):
        break
