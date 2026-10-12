#!/usr/bin/env python3
"""Request exactly one reviewed-candidate study image from Lingzhi.

This is deliberately a request runner, not a batch generator: each invocation
handles one named asset and waits for that request to finish before returning.
It never writes into runs/dayNN/source/, so approving/copying a reviewed
candidate into source remains a separate, explicit QA step.
"""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterator


LINGZHI_GENERATOR = Path(
    "/Users/agiuser/.codex/skills/lingzhi-image/scripts/generate_image.py"
)
MAX_REQUESTS_PER_ASSET = 6  # Initial request plus at most five adjusted retries.
REDACTION_PATTERNS = (
    re.compile(
        r"(?i)\b(api[ _-]?key|authorization|bearer|token|password|secret)\b"
        r"\s*([:=])\s*(?:bearer\s+)?[^\s,;]+"
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


class RunnerError(RuntimeError):
    """A safe-to-display request-runner error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_sensitive(value: str) -> str:
    """Keep request records useful without retaining credential-like values."""
    result = value
    for pattern in REDACTION_PATTERNS:
        if pattern.pattern.startswith("(?i)"):
            result = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED]", result)
    return result


def error_summary(stdout: str, stderr: str, fallback: str) -> str:
    raw = stderr.strip() or stdout.strip() or fallback
    return " ".join(redact_sensitive(raw).split())[:1600]


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError as exc:
        raise RunnerError(f"Path is outside the FitStudy project: {path}") from exc


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically replace the record while the caller owns the global lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextlib.contextmanager
def request_lock(path: Path) -> Iterator[None]:
    """Serialize every generic runner request, including the billable subprocess."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RunnerError(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RunnerError(f"{label} must contain a JSON object: {path}")
    return payload


def validate_input_path(path: Path) -> tuple[Path, Path, Path]:
    """Return project root, runs directory, and day directory for image-prompts."""
    if path.name != "image-prompts.json":
        raise RunnerError("Input must be a runs/dayNN/image-prompts.json file.")
    day_dir = path.parent
    runs_dir = day_dir.parent
    if runs_dir.name != "runs" or not re.fullmatch(r"day\d+", day_dir.name):
        raise RunnerError("Input must live directly in runs/dayNN/.")
    root = runs_dir.parent
    relative_to_root(path, root)
    return root, runs_dir, day_dir


def plan_asset(plan: dict[str, Any], file_name: str) -> dict[str, Any]:
    assets = plan.get("assets")
    if not isinstance(assets, list):
        raise RunnerError('image-prompts.json requires an "assets" array.')
    matches = [asset for asset in assets if isinstance(asset, dict) and asset.get("file") == file_name]
    if not matches:
        raise RunnerError(f"Unknown asset in image-prompts.json: {file_name}")
    if len(matches) != 1:
        raise RunnerError(f"Asset is duplicated in image-prompts.json: {file_name}")
    asset = matches[0]
    if not isinstance(asset.get("prompt"), str) or not asset["prompt"].strip():
        raise RunnerError(f'Asset "{file_name}" needs a non-empty prompt.')
    asset_path = Path(file_name)
    if (
        asset_path.name != file_name
        or asset_path.suffix.lower() != ".png"
        or file_name in {".", ".."}
    ):
        raise RunnerError("Asset file must be a plain .png filename without directories.")
    return asset


def full_prompt(plan: dict[str, Any], asset_prompt: str) -> str:
    common_prompt = plan.get("commonPrompt", "")
    if not isinstance(common_prompt, str):
        raise RunnerError('"commonPrompt" must be a string when present.')
    parts = [part.strip() for part in (common_prompt, asset_prompt) if part.strip()]
    return "\n\n".join(parts)


def output_path(day_dir: Path, file_name: str, attempt: int) -> Path:
    """Use immutable attempt folders; source/ is never an output destination."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(file_name).stem).strip(".-") or "asset"
    file_hash = hashlib.sha256(file_name.encode("utf-8")).hexdigest()[:10]
    return (
        day_dir
        / "image-requests"
        / f"{stem}-{file_hash}"
        / f"attempt-{attempt:02d}"
        / file_name
    )


def source_metadata(source: Path, root: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "path": relative_to_root(source, root),
        "exists": source.exists(),
    }
    if source.exists():
        metadata["isFile"] = source.is_file()
        if source.is_file():
            metadata["bytes"] = source.stat().st_size
            metadata["sha256"] = sha256_file(source)
    return metadata


def candidate_metadata(candidate: Path) -> dict[str, Any]:
    if not candidate.is_file():
        return {"outputExists": candidate.exists(), "usablePng": False}
    size = candidate.stat().st_size
    metadata: dict[str, Any] = {
        "outputExists": True,
        "bytes": size,
        "usablePng": size > 0,
    }
    if size > 0:
        metadata["sha256"] = sha256_file(candidate)
    return metadata


def load_record(record_path: Path) -> dict[str, Any]:
    if not record_path.exists():
        return {"schemaVersion": 1, "assets": []}
    record = read_json(record_path, "Image request record")
    if not isinstance(record.get("assets"), list):
        raise RunnerError(f'Image request record has no valid "assets" list: {record_path}')
    return record


def get_asset_record(
    record: dict[str, Any], file_name: str, role: str, source: dict[str, Any]
) -> dict[str, Any]:
    assets = record["assets"]
    matches = [
        item for item in assets if isinstance(item, dict) and item.get("file") == file_name
    ]
    if len(matches) > 1:
        raise RunnerError(f"Image request record has duplicate entries for {file_name}.")
    if matches:
        item = matches[0]
        if not isinstance(item.get("attempts", []), list):
            raise RunnerError(f"Image request record has invalid attempts for {file_name}.")
        item.setdefault("attempts", [])
    else:
        item = {"file": file_name, "role": role, "attempts": []}
        assets.append(item)
    item["role"] = role
    item["source"] = source
    return item


def request_attempts(asset_record: dict[str, Any], file_name: str) -> list[dict[str, Any]]:
    attempts = asset_record["attempts"]
    numbers: list[int] = []
    for row in attempts:
        if not isinstance(row, dict) or not isinstance(row.get("attempt"), int):
            raise RunnerError(f"Image request record has a malformed attempt for {file_name}.")
        number = row["attempt"]
        if number < 1 or number > MAX_REQUESTS_PER_ASSET:
            raise RunnerError(f"Image request record has an invalid attempt number for {file_name}.")
        numbers.append(number)
    if len(numbers) != len(set(numbers)):
        raise RunnerError(f"Image request record has duplicate attempt numbers for {file_name}.")
    if any(row.get("status") == "requesting" for row in attempts):
        raise RunnerError(
            f"{file_name} has an unfinished recorded request; reconcile it before another request."
        )
    return attempts


def update_record_metadata(
    record: dict[str, Any], plan_path: Path, root: Path
) -> None:
    record.update(
        {
            "schemaVersion": 1,
            "provider": "Lingzhi",
            "preset": "quality",
            "model": "gpt-image-2.5-sunburst",
            "input": relative_to_root(plan_path, root),
            "updatedAt": utc_now(),
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Request exactly one Lingzhi candidate from runs/dayNN/image-prompts.json. "
            "The runner holds a cross-day lock through the single request and never "
            "writes into source/."
        ),
        epilog=(
            "Examples:\n"
            "  python3 scripts/request-study-image.py --input runs/day59/image-prompts.json "
            "--file visual-04-integrate.png --initial\n"
            "  python3 scripts/request-study-image.py --input runs/day59/image-prompts.json "
            '--file visual-04-integrate.png --retry-prompt "Adjusted asset-specific prompt"\n\n'
            "Each invocation sends at most one request. Retry prompts must be different "
            "from earlier prompts; at most six total requests (initial plus five adjusted "
            "retries) are allowed. Candidates and the audit log are saved under runs/dayNN/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Absolute or project-relative runs/dayNN/image-prompts.json path.",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Exactly one asset filename from the input plan, for example cover.png.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--initial",
        action="store_true",
        help="Make the first request only when no source asset or prior request exists.",
    )
    mode.add_argument(
        "--retry-prompt",
        metavar="TEXT",
        help="Explicitly make one adjusted-prompt retry after an earlier request.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan_path = Path(args.input).expanduser().resolve()
    root, runs_dir, day_dir = validate_input_path(plan_path)
    plan = read_json(plan_path, "Image prompt plan")
    asset = plan_asset(plan, args.file)
    role = str(asset.get("role", "unspecified"))
    source = day_dir / "source" / args.file
    record_path = day_dir / "image-request-log.json"

    # A repository-wide lock prevents two calls for different days from becoming
    # concurrent billable generation requests. It also protects every JSON write.
    with request_lock(runs_dir / ".study-image-request-runner.lock"):
        record = load_record(record_path)
        update_record_metadata(record, plan_path, root)
        source_info = source_metadata(source, root)
        asset_record = get_asset_record(record, args.file, role, source_info)
        attempts = request_attempts(asset_record, args.file)

        if args.initial:
            if source.exists():
                asset_record["lastStatus"] = "source-exists-not-requested"
                update_record_metadata(record, plan_path, root)
                atomic_write_json(record_path, record)
                print(
                    json.dumps(
                        {
                            "file": args.file,
                            "status": asset_record["lastStatus"],
                            "record": relative_to_root(record_path, root),
                        },
                        ensure_ascii=False,
                    )
                )
                return 0
            if attempts:
                raise RunnerError(
                    f"{args.file} already has a request record; use --retry-prompt for an "
                    "explicit adjusted retry instead."
                )
            attempt_number = 1
            request_kind = "initial"
            asset_specific_prompt = asset["prompt"]
        else:
            retry_prompt = args.retry_prompt.strip() if args.retry_prompt else ""
            if not retry_prompt:
                raise RunnerError("--retry-prompt must contain an adjusted asset-specific prompt.")
            if not attempts:
                raise RunnerError(
                    f"{args.file} has no prior request; begin with --initial instead."
                )
            attempt_number = max(row["attempt"] for row in attempts) + 1
            if attempt_number > MAX_REQUESTS_PER_ASSET:
                raise RunnerError(
                    f"{args.file} already used all {MAX_REQUESTS_PER_ASSET} allowed requests."
                )
            request_kind = "adjusted-retry"
            asset_specific_prompt = retry_prompt

        request_prompt = full_prompt(plan, asset_specific_prompt)
        prompt_digest = hashlib.sha256(request_prompt.encode("utf-8")).hexdigest()
        if args.retry_prompt and any(
            row.get("promptSha256") == prompt_digest for row in attempts
        ):
            raise RunnerError(
                "Adjusted retry prompt matches an earlier request; revise it before retrying."
            )

        candidate = output_path(day_dir, args.file, attempt_number)
        if candidate.exists():
            raise RunnerError(
                f"Refusing to overwrite preserved attempt output: {relative_to_root(candidate, root)}"
            )
        if not LINGZHI_GENERATOR.is_file():
            raise RunnerError(f"Lingzhi generator is unavailable: {LINGZHI_GENERATOR}")

        candidate.parent.mkdir(parents=True, exist_ok=True)
        attempt: dict[str, Any] = {
            "attempt": attempt_number,
            "kind": request_kind,
            "explicitInvocation": True,
            "requestedAt": utc_now(),
            "prompt": redact_sensitive(request_prompt),
            "promptSha256": prompt_digest,
            "assetPrompt": redact_sensitive(asset_specific_prompt),
            "output": relative_to_root(candidate, root),
            "status": "requesting",
        }
        attempts.append(attempt)
        asset_record["lastStatus"] = "requesting"
        update_record_metadata(record, plan_path, root)
        atomic_write_json(record_path, record)

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINGZHI_GENERATOR),
                    "--preset",
                    "quality",
                    "--background",
                    "transparent",
                    "--output-format",
                    "png",
                    "--prompt",
                    request_prompt,
                    "--output",
                    str(candidate),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return_code: int | None = result.returncode
            summary = error_summary(
                result.stdout,
                result.stderr,
                "Lingzhi returned no usable local PNG.",
            )
        except OSError as exc:
            return_code = None
            summary = error_summary("", str(exc), "Unable to start Lingzhi image generation.")

        candidate_info = candidate_metadata(candidate)
        attempt.update(
            {
                "completedAt": utc_now(),
                "returncode": return_code,
                **candidate_info,
            }
        )
        if return_code == 0 and candidate_info["usablePng"]:
            attempt["status"] = "generated-pending-quality-review"
            attempt.pop("errorSummary", None)
        else:
            attempt["status"] = "request-failed"
            attempt["errorSummary"] = summary
        asset_record["lastStatus"] = attempt["status"]
        update_record_metadata(record, plan_path, root)
        atomic_write_json(record_path, record)
        print(
            json.dumps(
                {
                    "file": args.file,
                    "attempt": attempt_number,
                    "status": attempt["status"],
                    "output": attempt["output"],
                    "record": relative_to_root(record_path, root),
                },
                ensure_ascii=False,
            )
        )
        return 0 if attempt["status"] == "generated-pending-quality-review" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as exc:
        print(f"error: {redact_sensitive(str(exc))}", file=sys.stderr)
        raise SystemExit(2)
