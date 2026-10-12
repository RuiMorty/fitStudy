#!/usr/bin/env python3
"""Request one untouched Lingzhi image, optionally with a character reference."""

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = json.loads((ROOT / "generation/prompts.json").read_text())
SKILL_SCRIPT = Path("/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py")
REFERENCE = ROOT.parent / "branding/avatar-broccoli-pear-reference.png"
STYLE_REFERENCE = ROOT / "assets/body-style-reference.png"


def main() -> int:
    key_name = sys.argv[1]
    spec = PROMPTS[key_name]
    out = ROOT / "images" / (key_name + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    imported = importlib.util.spec_from_file_location("lingzhi_image", SKILL_SCRIPT)
    helper = importlib.util.module_from_spec(imported)
    imported.loader.exec_module(helper)
    key = helper.load_api_key()
    endpoint = "https://lingzhi.agibot.com/v1/images/"
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    if spec["mode"] == "reference-edit":
        boundary = "----fitstudy" + uuid.uuid4().hex
        parts = []
        for name, value in {"model": "gpt-image-2.5-sunburst", "prompt": spec["prompt"], "size": spec["size"], "n": "1"}.items():
            parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode())
        source = STYLE_REFERENCE if spec["mode"] == "style-reference" else REFERENCE
        parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"reference.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + source.read_bytes() + b"\r\n")
        parts.append((f"--{boundary}--\r\n").encode())
        data = b"".join(parts)
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        endpoint += "edits"
    else:
        data = json.dumps({"model": "gpt-image-2.5-sunburst", "prompt": spec["prompt"], "size": spec["size"], "n": 1}, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
        endpoint += "generations"
    try:
        with urlopen(Request(endpoint, data=data, headers=headers, method="POST"), timeout=180) as response:
            result = json.load(response)
        out.write_bytes(helper.extract_image_bytes(result))
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read(2000).decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except (URLError, OSError, RuntimeError) as error:
        print(f"Request failed: {error}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
