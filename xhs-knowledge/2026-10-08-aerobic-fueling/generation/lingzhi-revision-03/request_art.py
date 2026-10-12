#!/usr/bin/env python3
"""Submit exactly one Lingzhi image request and record the attempt without credentials."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILL_SCRIPT = Path("/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py")
CONFIG = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CONFIG["assets"]:
        print(f"Usage: {Path(sys.argv[0]).name} <{'|'.join(CONFIG['assets'])}>")
        return 2
    name = sys.argv[1]
    prompt = CONFIG["common"] + "\n\nSubject: " + CONFIG["assets"][name]
    raw = HERE / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    output = raw / f"{name}.png"
    if output.exists():
        print(f"Already exists; no new request sent: {output}")
        return 0
    command = [
        sys.executable,
        str(SKILL_SCRIPT),
        "--preset",
        "quality",
        "--background",
        "transparent",
        "--output-format",
        "png",
        "--prompt",
        prompt,
        "--output",
        str(output),
    ]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    success = result.returncode == 0 and output.exists() and output.stat().st_size > 0
    record = {
        "asset": name,
        "model": CONFIG["model"],
        "requestedAt": started,
        "prompt": prompt,
        "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output": str(output.relative_to(ROOT)),
        "status": "generated" if success else "failed",
        "returncode": result.returncode,
    }
    if success:
        record["bytes"] = output.stat().st_size
        record["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    else:
        summary = (result.stderr or result.stdout).strip()[:1000]
        summary = re.sub(r"(?i)(bearer\s+)\S+", r"\1[redacted]", summary)
        summary = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", summary)
        record["errorSummary"] = summary
    attempts = HERE / "attempts.jsonl"
    with attempts.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{name}: {record['status']} ({record['returncode']})")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
