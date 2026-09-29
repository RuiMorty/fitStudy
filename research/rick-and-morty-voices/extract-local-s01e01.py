"""Extract short, unprocessed voice references from the user's local S01E01 file."""

import hashlib
import json
import subprocess
import wave
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/agiuser/Downloads/RKS01.蓝光版.6v电影 地址发布页 "
    "www.6v123.net 收藏不迷路/"
    "S01E01.1080p.BD中英双字[最新电影www.5266ys.com].mp4"
)
OUTPUT = ROOT / "samples-local-s01e01"
OFFSET = 5.06  # streaming timestamp = local-file timestamp + 5.06s

# Segment boundaries were first located in the streamed episode, checked
# against its transcript and scene frames, then aligned to this local copy.
CLIPS = [
    ("rick", "vehicle", 22.00, 27.40),
    ("rick", "bomb", 31.25, 36.25),
    ("rick", "reassure", 42.58, 47.00),
    ("rick", "plan", 49.44, 60.99),
    ("morty", "surprise", 27.63, 30.25),
    ("morty", "jessica", 47.40, 49.16),
    ("morty", "protest", 61.14, 66.25),
    ("morty", "take-wheel", 90.08, 92.10),
    ("morty", "take-charge", 93.02, 94.36),
    ("morty", "stop-bomb", 98.98, 102.58),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_reference(speaker: str, entries: list[dict]) -> dict:
    destination = OUTPUT / f"{speaker}-reference.wav"
    silence = array("h", [0]) * 16800  # 0.35s at 48 kHz
    fade_length = 480  # 10 ms; only the compiled reference receives fades
    with wave.open(str(destination), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(48000)
        selected = [entry for entry in entries if entry["speaker"] == speaker]
        for index, entry in enumerate(selected):
            with wave.open(entry["path"], "rb") as source:
                samples = array("h")
                samples.frombytes(source.readframes(source.getnframes()))
            for position in range(min(fade_length, len(samples) // 2)):
                gain = position / fade_length
                samples[position] = round(samples[position] * gain)
                samples[-1 - position] = round(samples[-1 - position] * gain)
            if index:
                out.writeframes(silence.tobytes())
            out.writeframes(samples.tobytes())
    with wave.open(str(destination), "rb") as file:
        duration = file.getnframes() / file.getframerate()
    return {
        "speaker": speaker,
        "path": str(destination),
        "duration_seconds": round(duration, 2),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "processing": "0.35s gaps and 10ms edge fades; individual clips unchanged",
    }


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing source: {SOURCE}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for speaker, label, stream_start, stream_end in CLIPS:
        start = round(stream_start - OFFSET, 2)
        end = round(stream_end - OFFSET, 2)
        destination = OUTPUT / f"{speaker}-{label}.wav"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-i", str(SOURCE), "-ss", f"{start:.2f}",
                "-t", f"{end - start:.2f}", "-map", "0:a:0",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le",
                "-y", str(destination),
            ],
            check=True,
        )
        entries.append(
            {
                "speaker": speaker,
                "label": label,
                "source_start_seconds": start,
                "source_end_seconds": end,
                "duration_seconds": round(end - start, 2),
                "path": str(destination),
                "size_bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )
    manifest = {
        "source": str(SOURCE),
        "source_size_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "episode": "Rick and Morty S01E01",
        "language": "English original audio, bilingual burned-in subtitles",
        "time_alignment": "streamed copy time = local copy time + 5.06s",
        "audio_format": "48 kHz, mono, 16-bit PCM WAV; no denoise or pitch processing",
        "clips": entries,
        "references": [make_reference(speaker, entries) for speaker in ("rick", "morty")],
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for entry in entries:
        print(f'{entry["speaker"]}: {entry["label"]} '
              f'{entry["source_start_seconds"]:.2f}–{entry["source_end_seconds"]:.2f}s '
              f'{entry["size_bytes"]} bytes')


if __name__ == "__main__":
    main()
