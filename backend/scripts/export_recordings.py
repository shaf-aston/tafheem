"""Copy the studio's recordings into the site: frontend/public/words/voice/.

    python backend/scripts/export_recordings.py

services/recitation/recordings.py keeps each take on the server. This puts them where
lib/speech/speak.js's "person" voice looks (speak.json voices.person): one MP3 per
word, and voice_audio.json mapping the word to its file. Run it, then commit
the folder; files for words no longer recorded are removed.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.recitation import recordings

OUT = recordings.ROOT / "frontend/public/words/voice"
MAP = recordings.ROOT / "frontend/public/words/voice_audio.json"


def export() -> int:
    kept = recordings.index()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in kept.values():
        shutil.copyfile(recordings.RECORDINGS / name, OUT / name)
    for old in OUT.glob("*.mp3"):
        if old.name not in kept.values():
            old.unlink()
    MAP.write_text(json.dumps(kept, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return len(kept)


if __name__ == "__main__":
    print(f"{export()} words exported to {OUT.relative_to(recordings.ROOT)}")
