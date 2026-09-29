"""Transcribe the locally captured reference audio with word time stamps."""

import json
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parent
model = WhisperModel("base.en", device="cpu", compute_type="int8", download_root="/private/tmp/rick-whisper-model")
segments, info = model.transcribe(
    str(ROOT / "dialogue-first-180s.wav"),
    language="en",
    beam_size=5,
    vad_filter=False,
    word_timestamps=True,
)
output = {
    "source": "dialogue-first-180s.wav",
    "language": info.language,
    "segments": [
        {
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text.strip(),
            "words": [
                {"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word}
                for w in (s.words or [])
            ],
        }
        for s in segments
    ],
}
(ROOT / "transcript-first-180s.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
)
for segment in output["segments"]:
    print(f'{segment["start"]:6.2f}-{segment["end"]:6.2f} {segment["text"]}')
