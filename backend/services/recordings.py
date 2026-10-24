"""A person's voice for the words no reciter says: the recording studio's store.

The studio page (frontend/record.html) shows a word, records someone saying it
and sends it here. It is kept in RECORDINGS as an MP3, trimmed of the quiet
before and after and given speech_lead_ms back on each side (the lead a phone
needs, as services/speech.py gives every made word). index.json maps the word,
exactly as words.json spells it, to its file.

Nothing here is played to learners directly: scripts/export_recordings.py
copies the store into frontend/public/words/voice/, where lib/speech/speak.js's
"person" voice finds it before every other voice, and the files ship with the
site like the reciter map does.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
from pathlib import Path

from backend.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
RECORDINGS = ROOT / "backend/data/recordings"
WORDS = ROOT / "frontend/public/words/words.json"
RECITED = ROOT / "frontend/public/words/word_audio.json"

_lock = threading.Lock()


def index() -> dict[str, str]:
    """Word -> file name, for every word recorded so far."""
    try:
        return json.loads((RECORDINGS / "index.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def file_for(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16] + ".mp3"


def todo(limit: int) -> tuple[list[dict], int]:
    """The next `limit` quiz words no person or reciter says yet, in words.json's order, and how many remain."""
    done = index().keys() | json.loads(RECITED.read_text(encoding="utf-8")).keys()
    seen: set[str] = set()
    left = []
    for word in json.loads(WORDS.read_text(encoding="utf-8"))["words"]:
        ar = word.get("ar")
        if ar and ar not in done and ar not in seen:
            seen.add(ar)
            left.append({"ar": ar, "en": word.get("en") or ""})
    return left[:limit], len(left)


def tidy(audio: bytes) -> bytes:
    """The recording as a small MP3: quiet cut from both ends, the phone's lead put back."""
    lead = get_settings().speech_lead_ms / 1000
    trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"
    cut = f"{trim},areverse,{trim},areverse,adelay={int(lead * 1000)},apad=pad_dur={lead}"
    done = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-af", cut, "-ac", "1", "-ar", "22050",
         "-b:a", "48k", "-f", "mp3", "pipe:1"],
        input=audio, capture_output=True, timeout=30, check=False,
    )
    if done.returncode or not done.stdout:
        raise ValueError(done.stderr.decode(errors="replace")[-200:] or "not a recording")
    return done.stdout


def keep(text: str, audio: bytes) -> str:
    """Store `audio` as the voice of `text`, replacing any earlier take. Returns the file name."""
    sound = tidy(audio)
    name = file_for(text)
    with _lock:
        RECORDINGS.mkdir(parents=True, exist_ok=True)
        (RECORDINGS / name).write_bytes(sound)
        kept = index() | {text: name}
        part = RECORDINGS / "index.json.part"
        part.write_text(json.dumps(kept, ensure_ascii=False, sort_keys=True, indent=0), encoding="utf-8")
        os.replace(part, RECORDINGS / "index.json")
    return name
