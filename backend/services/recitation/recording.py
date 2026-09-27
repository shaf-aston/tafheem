"""What kind of sound file a recording is, told by its first bytes.

Not by the name or type it claims: the browser picks its own format (webm in
Chrome and Firefox, mp4 in Safari) and the page always calls it the same thing.
One place, so the route that refuses what is not a recording and the ear that
names a recording for Groq can never disagree about what one is.
"""
from __future__ import annotations


def kind_of(body: bytes) -> str | None:
    """"webm", "ogg", "flac", "mp3", "wav" or "mp4"; None when it is none of them."""
    if body.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if body.startswith(b"OggS"):
        return "ogg"
    if body.startswith(b"fLaC"):
        return "flac"
    if body.startswith(b"ID3") or (len(body) > 1 and body[0] == 0xFF and body[1] & 0xE0 == 0xE0):
        return "mp3"
    if body[:4] == b"RIFF" and body[8:12] == b"WAVE":
        return "wav"
    if body[4:8] == b"ftyp":
        return "mp4"
    return None
