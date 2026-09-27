"""What kind of sound file a recording is, told by its first bytes.

Run: python -m pytest tests/test_recitation_recording.py
"""
from __future__ import annotations

import pytest

from backend.routers.listen import is_audio
from backend.services.recitation.recording import kind_of


@pytest.mark.parametrize("head, kind", [
    (b"\x1a\x45\xdf\xa3" + bytes(8), "webm"),
    (b"OggS" + bytes(8), "ogg"),
    (b"fLaC" + bytes(8), "flac"),
    (b"ID3\x04" + bytes(8), "mp3"),
    (b"\xff\xfb\x90\x00" + bytes(8), "mp3"),
    (b"RIFF\x24\x00\x00\x00WAVEfmt ", "wav"),
    (b"\x00\x00\x00\x20ftypM4A " + bytes(4), "mp4"),
])
def test_each_format_a_browser_or_a_person_sends_is_told_apart(head, kind):
    assert kind_of(head) == kind
    assert is_audio(head)


@pytest.mark.parametrize("body", [b"", b"x", b"<html>not sound</html>", b"RIFF\x00\x00\x00\x00AVI LIST"])
def test_what_is_not_a_recording_is_not_one(body):
    assert kind_of(body) is None
    assert not is_audio(body)
