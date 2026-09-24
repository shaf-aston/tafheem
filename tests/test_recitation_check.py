"""Checking a recitation by sound: where a recording sits on a page, and whose
word each sureness belongs to. The ear itself is stood in for.

Run: python -m pytest tests/test_recitation_check.py
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.requests import Request

from backend.config import get_settings
from backend.main import app
from backend.routers import listen as listen_router
from backend.services import recitation
from backend.services.recitation import listen, place

client = TestClient(app)
# The first bytes of a browser's webm recording.
WEBM = bytes([0x1A, 0x45, 0xDF, 0xA3]) + bytes(8)


def test_nothing_places_without_two_words_in_a_row():
    assert place.reach(["قُلْ", "هُوَ", "اللَّهُ"], ["قل", "بعيد"]) is None
    assert place.reach(["قُلْ", "هُوَ"], []) is None


def test_the_stretch_grows_by_misheard_words_at_either_end_but_not_past_the_page():
    page = ["a", "قل", "هو", "الله", "احد", "b"]
    assert place.reach([w for w in page], ["x", "هو", "الله", "y"]) == (1, 5)
    assert place.reach(page[1:4], ["x", "x", "قل", "هو", "الله", "y", "y"]) == (0, 3)


def fake_check(monkeypatch, plain, sure=lambda audio, words: [0.5] * len(words)):
    asked = []
    monkeypatch.setattr(recitation, "_plain", lambda: plain)
    monkeypatch.setattr(listen, "sureness", lambda audio, words: asked.append(list(words)) or sure(audio, words))
    return asked


def test_each_sureness_goes_back_to_its_own_ayah_and_unreached_words_are_none(monkeypatch):
    plain = {"112:1": "قُلْ هُوَ اللَّهُ أَحَدٌ", "112:2": "اللَّهُ الصَّمَدُ", "112:3": "لَمْ يَلِدْ وَلَمْ يُولَدْ"}
    asked = fake_check(monkeypatch, plain, lambda audio, words: [round(0.1 * (i + 1), 1) for i in range(len(words))])
    out = recitation.check(b"sound", "أحد الله الصمد", ["112:1", "112:2", "112:3"])
    # الله appears in both ayahs; the stretch starts at 112:1's last word.
    assert out == {"112:1": [None, None, None, 0.1], "112:2": [0.2, 0.3], "112:3": [None, None, None, None]}
    assert len(asked) == 1 and len(asked[0]) == 3


def test_the_check_runs_on_to_the_end_of_the_ayah_the_transcript_stopped_in(monkeypatch):
    """The ear leaves out a word it doubts, often the last; that word is still checked."""
    plain = {"1:7": "غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ", "2:1": "الم"}
    fake_check(monkeypatch, plain)
    assert recitation.check(b"sound", "غير المغضوب عليهم ولا", ["1:7", "2:1"]) == {
        "1:7": [0.5, 0.5, 0.5, 0.5, 0.5], "2:1": [None]}


def test_a_recording_that_does_not_place_is_not_checked(monkeypatch):
    asked = fake_check(monkeypatch, {"1:1": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"})
    assert recitation.check(b"sound", "موسيقى", ["1:1"]) == {}
    assert asked == []


def test_more_words_than_one_recording_holds_is_not_checked(monkeypatch):
    long = " ".join(f"كَلِمَة{n}" for n in range(30))
    asked = fake_check(monkeypatch, {"2:282": long})
    monkeypatch.setattr(get_settings(), "recitation_sure_max_words", 10)
    heard = " ".join(f"كلمة{n}" for n in range(30))
    assert recitation.check(b"sound", heard, ["2:282"]) == {}
    assert asked == []


def test_an_ayah_the_text_does_not_have_is_skipped_not_crashed(monkeypatch):
    fake_check(monkeypatch, {"1:1": "بِسْمِ اللَّهِ"})
    assert recitation.check(b"sound", "بسم الله", ["1:1", "999:1"]) == {"1:1": [0.5, 0.5]}


def test_a_plain_undiacritised_heard_string_still_places(monkeypatch):
    """Groq writes no harakat at all; place.reach folds marks off both sides
    already, so a bare transcript must place exactly as a voweled one does."""
    fake_check(monkeypatch, {"1:2": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَالَمِينَ"})
    assert recitation.check(b"sound", "الحمد لله رب العالمين", ["1:2"]) == {"1:2": [0.5, 0.5, 0.5, 0.5]}


def test_heard_text_with_stray_punctuation_and_digits_still_places(monkeypatch):
    """Whisper's own numbering leaks into a long recitation's transcript, "114."
    among real words (see test_recitation.py); a digit-and-dot token must not
    stop the words after it from placing."""
    fake_check(monkeypatch, {"1:2": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَالَمِينَ"})
    assert recitation.check(b"sound", "114. الحمد لله رب العالمين", ["1:2"]) == {"1:2": [0.5, 0.5, 0.5, 0.5]}


def test_the_ayahs_to_check_are_validated_before_the_recording_is_read(monkeypatch):
    monkeypatch.setattr(recitation, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("read")))
    for bad in ("1:1,1:1", "1:1;1:2", "١:١", "1:1234", ",".join(f"2:{n}" for n in range(1, 62))):
        got = client.post(f"/api/listen/check?heard=x&check={bad}", files={"audio": ("r.webm", WEBM)})
        assert got.status_code == 422, bad


def test_an_oversize_heard_string_is_rejected(monkeypatch):
    monkeypatch.setattr(recitation, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("read")))
    too_long = "و" * (get_settings().recitation_check_heard_max_chars + 1)
    got = client.post(
        "/api/listen/check", params={"heard": too_long, "check": "1:1"}, files={"audio": ("r.webm", WEBM)},
    )
    assert got.status_code == 422


def test_sureness_comes_from_its_own_endpoint_not_the_words_one(monkeypatch):
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("قل هو", []))
    monkeypatch.setattr(recitation, "check", lambda audio, text, ayahs: {"112:1": [1.0, 1.0, None, None]})
    words = client.post("/api/listen?recite=true", files={"audio": ("r.webm", WEBM)}).json()
    assert "sure" not in words

    checked = client.post(
        "/api/listen/check", params={"heard": "قل هو", "check": "112:1"}, files={"audio": ("r.webm", WEBM)},
    ).json()
    assert checked == {"sure": {"112:1": [1.0, 1.0, None, None]}}


def test_a_check_with_no_ayahs_or_no_heard_text_answers_empty_without_scoring(monkeypatch):
    monkeypatch.setattr(recitation, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("scored")))
    assert client.post("/api/listen/check?heard=&check=112:1", files={"audio": ("r.webm", WEBM)}).json() == {"sure": {}}
    assert client.post("/api/listen/check?heard=x&check=", files={"audio": ("r.webm", WEBM)}).json() == {"sure": {}}


def test_a_zero_byte_audio_file_with_valid_answers_short_circuits_without_scoring(monkeypatch):
    monkeypatch.setattr(recitation, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check", params={"heard": "قل", "check": "112:1"}, files={"audio": ("r.webm", b"")},
    )
    assert resp.status_code == 200
    assert resp.json() == {"sure": {}}


def test_a_check_always_takes_the_turn(monkeypatch):
    """Scoring is always this machine's model, so it always shares the queue
    that protects this machine's CPU, whichever ear wrote the words down."""
    entered = []

    class _Track:
        async def __aenter__(self):
            entered.append(True)

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(listen_router, "_turn", _Track())
    monkeypatch.setattr(recitation, "check", lambda audio, text, ayahs: {"112:1": [1.0]})
    resp = client.post(
        "/api/listen/check", params={"heard": "قل", "check": "112:1"}, files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 200
    assert entered == [True]


def test_a_stale_check_is_dropped_when_the_page_has_given_up(monkeypatch):
    async def gone(self):
        return True

    monkeypatch.setattr(Request, "is_disconnected", gone)
    monkeypatch.setattr(recitation, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("scored")))
    resp = client.post(
        "/api/listen/check", params={"heard": "قل", "check": "112:1"}, files={"audio": ("r.webm", WEBM)},
    )
    assert resp.status_code == 200
    assert resp.json() == {"sure": {}}


def test_a_recitation_skips_the_turn_when_the_hosted_ear_would_answer(monkeypatch):
    monkeypatch.setattr(recitation.ears, "would_answer_locally", lambda: False)
    monkeypatch.setattr(listen_router, "_turn", _NeverEnter())
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("hosted heard it", []))
    resp = client.post("/api/listen?recite=true", files={"audio": ("r.webm", WEBM)})
    assert resp.status_code == 200
    assert resp.json()["text"] == "hosted heard it"


def test_a_recitation_takes_the_turn_when_the_local_ear_would_answer(monkeypatch):
    entered = []

    class _Track:
        async def __aenter__(self):
            entered.append(True)

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(recitation.ears, "would_answer_locally", lambda: True)
    monkeypatch.setattr(listen_router, "_turn", _Track())
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("local heard it", []))
    resp = client.post("/api/listen?recite=true", files={"audio": ("r.webm", WEBM)})
    assert resp.status_code == 200
    assert entered == [True]


def test_only_a_sound_recording_is_listened_to(monkeypatch):
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("", []))
    for sound in (WEBM, b"OggS" + bytes(8), b"RIFF" + bytes(4) + b"WAVE", bytes(4) + b"ftypM4A ", b"ID3\x04", b"fLaC"):
        assert client.post("/api/listen", files={"audio": ("r", sound)}).status_code == 200, sound
    for other in (b"x", b"<html>", b"%PDF-1.7", b"RIFF" + bytes(4) + b"AVI "):
        assert client.post("/api/listen", files={"audio": ("r.webm", other)}).status_code == 415, other


def test_an_unexpected_failure_gives_the_new_detail_and_a_reading_id_header(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(recitation, "hear", boom)
    resp = client.post("/api/listen?recite=true", files={"audio": ("r.webm", WEBM)})
    assert resp.status_code == 500
    rid = resp.headers.get("X-Reading-Id")
    assert rid
    detail = resp.json()["detail"]
    assert rid in detail
    assert "Your recitation was not the problem" in detail


def test_the_pages_own_reading_id_is_echoed_back(monkeypatch):
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("", []))
    resp = client.post("/api/listen", files={"audio": ("r.webm", WEBM)}, headers={"X-Reading-Id": "my-own-id"})
    assert resp.headers["X-Reading-Id"] == "my-own-id"


class _NeverEnter:
    """Stands in for `_turn`, and fails the test the moment anything tries to
    enter it: proof a search request never even reaches for the recitation
    queue, rather than merely finding it free."""

    async def __aenter__(self):
        raise AssertionError("a search request must not take the recitation turn")

    async def __aexit__(self, *exc):
        return False


def test_a_search_request_never_takes_the_recitation_turn(monkeypatch):
    monkeypatch.setattr(listen_router, "_turn", _NeverEnter())
    monkeypatch.setattr(recitation, "hear", lambda *a, **k: ("mercy", []))
    resp = client.post("/api/listen", files={"audio": ("r.webm", WEBM)})
    assert resp.status_code == 200
    assert resp.json()["text"] == "mercy"
