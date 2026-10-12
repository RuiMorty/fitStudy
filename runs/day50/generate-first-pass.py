#!/usr/bin/env python3
"""Generate Day50's still-unrequested assets once, retaining non-secret request evidence."""
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


def main() -> int:
    records: list[dict[str, object]] = []
    for asset in PLAN["assets"]:
        name = asset["file"]
        if name == "cover.png":
            continue
        output = HERE / "source" / name
        prompt = PLAN["commonPrompt"] + "\n\n" + asset["prompt"]
        result = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
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
            ],
            capture_output=True,
            text=True,
        )
        entry: dict[str, object] = {
            "file": name,
            "role": asset["role"],
            "attempt": 1,
            "startedAt": now(),
            "returncode": result.returncode,
            "output": str(output.relative_to(HERE.parent.parent)),
        }
        if result.returncode == 0 and output.is_file() and output.stat().st_size > 0:
            entry.update(
                {
                    "status": "generated-pending-quality-review",
                    "bytes": output.stat().st_size,
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                }
            )
        else:
            entry.update(
                {
                    "status": "request-failed",
                    "errorSummary": (result.stderr or result.stdout or "no usable local PNG").strip()[:1000],
                }
            )
        records.append(entry)
        RECORD.write_text(
            json.dumps(
                {
                    "provider": "Lingzhi",
                    "preset": "quality",
                    "model": "gpt-image-2.5-sunburst",
                    "authorization": "用户于2026-09-30授权：每张图片最多首次加5次重试；本文件只记录其余12张首轮。",
                    "updatedAt": now(),
                    "assets": records,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        print(json.dumps({"file": name, "status": entry["status"]}, ensure_ascii=False))
        if result.returncode != 0 and "API Key" in (result.stderr or ""):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
