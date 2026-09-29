"""Grow: its paths, the scholar's words it quotes, and checking a phrase that
is not an ayah. The ear itself is stood in for.

The one test here that matters most is the quote test: Grow promises that no
ruling on the page is the app's own, and that is only true while every ruling
is a sentence that is actually in the book it names.

Run: python -m pytest tests/test_grow.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.routers import grow
from backend.services import recitation
from backend.services.recitation import listen
from backend.services.recitation.spelling import as_heard

client = TestClient(app)
WEBM = bytes([0x1A, 0x45, 0xDF, 0xA3]) + bytes(8)
QUDURI = Path(__file__).resolve().parent.parent / "backend" / "data/books/openiti/0428AbuHusaynQuduri.Mukhtasar.Sham19Y0124336-ara1"
GROW_CONFIG = Path(__file__).resolve().parent.parent / "frontend" / "src" / "grow.json"
AYAH_KEY = re.compile(r"(\d{1,3}):(\d{1,3})")


def _as_read(text: str) -> str:
    """The book's text with its file markup gone: line marks, page and
    manuscript markers, and line breaks inside a sentence."""
    text = re.sub(r"PageV\d+P\d+|ms\d+", " ", text)
    text = re.sub(r"^(#+ ?(\|+ )?|~~)", " ", text, flags=re.M)
    return " ".join(text.split())


def test_every_path_loads_and_every_step_has_something_to_say():
    paths = client.get("/api/grow/paths").json()
    assert [p["id"] for p in paths] == ["salah", "surahs"]
    for path in paths:
        ids = [step["id"] for step in path["steps"]]
        assert len(ids) == len(set(ids)), path["id"]
        for step in path["steps"]:
            if step["kind"] == "action":
                assert step["instruction"] and not step["arabic"] and not step["ayahs"], step["id"]
            else:
                assert bool(step["arabic"]) != bool(step["ayahs"]), step["id"]


def test_step_ids_are_unique_across_every_path():
    """One record holds every step by id, so two paths sharing one would share progress."""
    ids = [step.id for path in grow.paths() for step in path.steps]
    assert len(ids) == len(set(ids))


def test_every_ayahs_step_is_one_surah():
    """The card loads one surah's text for a step, so a step may not span two."""
    for path in grow.paths():
        for step in path.steps:
            assert len({key.split(":")[0] for key in step.ayahs}) <= 1, step.id


def test_every_path_names_a_tier_and_every_step_sits_in_one_group():
    tiers = {t["id"] for t in json.loads(GROW_CONFIG.read_text(encoding="utf-8"))["tiers"]}
    for path in grow.paths():
        assert path.tier in tiers, path.id
        grouped = [step for group in path.groups for step in group.steps]
        assert sorted(grouped) == sorted(step.id for step in path.steps), path.id


def test_every_posture_is_an_action_that_quotes_its_source():
    """A posture cannot be heard, so it is tapped Done; and since it is a ruling
    on how to pray, it carries al-Quduri's own sentence (held to the book above)."""
    actions = [step for path in grow.paths() for step in path.steps if step.kind == "action"]
    assert [step.id for step in actions] == ["stand-up", "fold-hands", "bow-down", "prostrate-down", "sit-down"]
    for step in actions:
        assert step.ruling and step.ruling.known_as == "al-Quduri", step.id


def test_every_ruling_says_who_it_is_by():
    for path in grow.paths():
        for step in path.steps:
            if step.ruling:
                assert step.ruling.known_as, step.id


def test_every_ruling_is_the_books_own_sentence():
    book = _as_read(QUDURI.read_text(encoding="utf-8"))
    for path in grow.paths():
        for step in path.steps:
            if step.ruling:
                quoted = " ".join(step.ruling.arabic.split())
                assert quoted in book, f"{step.id}: not in al-Quduri as written"


def test_every_ayah_is_a_real_one():
    for path in grow.paths():
        for step in path.steps:
            for key in step.ayahs:
                surah, ayah = map(int, AYAH_KEY.fullmatch(key).groups())
                assert 1 <= surah <= 114 and ayah >= 1, key
    fatiha = next(step for step in grow.paths()[0].steps if step.id == "fatiha")
    assert len(fatiha.ayahs) <= get_settings().recitation_check_ayahs_max


def test_every_phrase_is_one_ear_word_per_written_word():
    """The page marks words as written and the ear scores words as it spells
    them; the two lists must be the same length or the marks land on the
    wrong words."""
    for path in grow.paths():
        for step in path.steps:
            if step.arabic:
                assert len(as_heard(step.arabic)) == len(step.arabic.split()), step.id


def test_a_phrase_is_scored_whole(monkeypatch):
    asked = []
    monkeypatch.setattr(listen, "sureness", lambda audio, words: asked.append(words) or [0.91234] * len(words))
    assert recitation.check_text(b"x", "سبحان ربي", "سُبْحَانَ رَبِّيَ الْعَظِيمِ") == [0.912] * 3
    assert len(asked[0]) == 3


def test_nothing_heard_or_too_long_is_not_scored(monkeypatch):
    monkeypatch.setattr(listen, "sureness", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    assert recitation.check_text(b"x", "  ", "اللَّهُ أَكْبَرُ") == []
    monkeypatch.setattr(get_settings(), "recitation_sure_max_words", 1)
    assert recitation.check_text(b"x", "الله اكبر", "اللَّهُ أَكْبَرُ") == []


def test_check_text_route_answers_per_word(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda audio, heard, expected: [1.0, 0.4])
    resp = client.post(
        "/api/listen/check-text", params={"heard": "الله اكبر", "expected": "اللَّهُ أَكْبَرُ"},
        files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 200
    assert resp.json() == {"sure": [1.0, 0.4]}


def test_check_text_route_refuses_what_is_not_a_recording(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check-text", params={"heard": "الله", "expected": "اللَّهُ"},
        files={"audio": ("r.webm", b"not a recording at all")},
    )
    assert resp.status_code == 415


def test_check_text_route_with_nothing_heard_answers_empty(monkeypatch):
    monkeypatch.setattr(recitation, "check_text", lambda *a: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check-text", params={"heard": "", "expected": "اللَّهُ"}, files={"audio": ("r.webm", WEBM)},
    )
    assert resp.json() == {"sure": []}


def test_check_text_route_refuses_an_oversize_phrase(monkeypatch):
    monkeypatch.setattr(get_settings(), "recitation_check_heard_max_chars", 5)
    resp = client.post(
        "/api/listen/check-text", params={"heard": "x", "expected": "اللَّهُ أَكْبَرُ"},
        files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 422
