"""Hearing a recording on Groq's machines, and what happens when that fails.

No network is touched here. The Groq client is stood in for, so what is tested
is the two things this side owns: that a recording goes to the right place with
the right question, and that every way of not getting an answer lands on the
engine on this machine instead of on the reader.

Run: python -m pytest tests/test_recitation_hosted.py
"""
from __future__ import annotations

import numpy as np
import pytest

from backend.config import get_settings
from backend.services import recitation
from backend.services.recitation import hosted, listen


@pytest.fixture(autouse=True)
def sound(monkeypatch):
    """Stand in for turning a file into sound.

    The recordings in this file are a few bytes of prose, not audio, because
    what is being tested is the rules above the engine and never the engine.
    Decoding is real work with its own test (an unreadable recording is refused,
    below), so here it is stood in for rather than fed something it cannot read.
    """
    import faster_whisper.audio

    handed = []
    monkeypatch.setattr(
        faster_whisper.audio, "decode_audio",
        lambda path: handed.append(path) or np.zeros(16000, dtype=np.float32),
    )
    # Stood in at the engine's own door rather than at ours, so the temporary
    # file a recording is written to is still really written and really
    # deleted, and a test can still prove none is left on the disk.
    listen._last = None
    yield handed
    listen._last = None


SOUND = b"pretend this is a recording"


class FakeGroq:
    """Stands in for the Groq client, and remembers how it was asked."""

    def __init__(self, replies, fail=None):
        self.replies = list(replies)
        self.fail = fail
        self.asked = []
        self.audio = self
        self.transcriptions = self

    def create(self, **how):
        self.asked.append(how)
        if self.fail:
            raise self.fail
        text, language = self.replies.pop(0)
        return type("Answer", (), {"text": text, "language": language})()


@pytest.fixture
def groq(monkeypatch):
    """Install a stand-in Groq, with a key present so hosted hearing is on."""
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "gsk_pretend")
    monkeypatch.setattr(settings, "recitation_hosted", True)

    def install(replies=(("قل هو الله أحد", "Arabic"),), fail=None):
        fake = FakeGroq(replies, fail)
        monkeypatch.setattr("groq.Groq", lambda **_: fake)
        # The real client is built once and kept; each stand-in must be the
        # one built, so the kept one is forgotten first.
        hosted._client.cache_clear()
        return fake

    return install


def test_a_spoken_word_goes_to_groq_with_no_language_named(groq):
    """Groq works the language out better than this machine can, so it is let to."""
    fake = groq([("Knowledge", "English")])
    assert hosted.transcribe(SOUND) == "Knowledge"
    assert "language" not in fake.asked[0]
    assert fake.asked[0]["response_format"] == "verbose_json"


def test_a_hint_is_sent_when_given_and_nothing_when_not(groq):
    fake = groq([("علم", "Arabic"), ("علم", "Arabic")])
    hosted.transcribe(SOUND, hint="register")
    assert fake.asked[0]["prompt"] == "register"
    hosted.transcribe(SOUND)
    assert "prompt" not in fake.asked[1]


def test_a_recitation_is_heard_on_groq_when_it_is_available_too(monkeypatch):
    """Words no longer need the ear here specially: checking sureness is a
    separate question now, asked of this machine's model directly (see
    services/recitation/__init__.py's `check`), so a recitation takes the
    normal ear order, quick one first, same as a search."""
    monkeypatch.setattr(hosted, "is_available", lambda: True)
    asked = []
    monkeypatch.setattr(hosted, "transcribe", lambda *a, **k: asked.append("groq") or "x")
    monkeypatch.setattr(listen, "transcribe", lambda *a, **k: asked.append("here") or "x")
    recitation.transcribe(SOUND, language="ar")
    recitation.transcribe(SOUND, language=None)
    assert asked == ["groq", "groq"]


def test_a_recitation_never_gets_the_register_hint(monkeypatch):
    """Measured: with the hint the Qur'an model rated every last word 0.90 and
    looped on invented words; without it every real word was 1.00."""
    fake = type("Ear", (), {"how": None})()
    def read(path, **how):
        fake.how = how
        return [], None
    monkeypatch.setattr(listen, "_engine", lambda name: type("M", (), {"transcribe": staticmethod(read)})())
    monkeypatch.setattr(hosted, "is_available", lambda: False)
    # The hint is Whisper's, so the Whisper ear is the one asked here.
    monkeypatch.setattr(get_settings(), "recitation_ears", "hosted,here")
    recitation.hear(SOUND, match_ayahs=False, recite=True, fusha=True)
    assert fake.how["initial_prompt"] is None


def test_reciting_without_looking_up_is_still_arabic(monkeypatch):
    asked = []
    monkeypatch.setattr(recitation, "transcribe", lambda audio, language=None, hint="": asked.append(language) or "x")
    recitation.hear(SOUND, match_ayahs=False, recite=True)
    assert asked == [get_settings().recitation_language]


def test_the_fusha_switch_decides_the_hint(monkeypatch):
    hints = []
    monkeypatch.setattr(recitation, "transcribe", lambda audio, language=None, hint="": hints.append(hint) or "علم")
    recitation.hear(SOUND, match_ayahs=False, fusha=True)
    recitation.hear(SOUND, match_ayahs=False, fusha=False)
    assert hints == [get_settings().recitation_fusha_hint, ""]
    assert hints[0]


def test_a_recitation_is_named_as_arabic(groq):
    fake = groq([("قل هو الله أحد", "Arabic")])
    assert hosted.transcribe(SOUND, language="ar") == "قل هو الله أحد"
    assert fake.asked[0]["language"] == "ar"


def test_an_answer_in_neither_language_is_asked_again_as_arabic(groq):
    """The nearest case nobody asks for: one word heard as Urdu, in Urdu letters.

    Groq's model is much bigger than the one here and wanders far less, but
    "much less often" is not "never", and this app is Arabic and English only.
    """
    fake = groq([("نالج", "Urdu"), ("علم", "Arabic")])
    assert hosted.transcribe(SOUND) == "علم"
    assert [how.get("language") for how in fake.asked] == [None, "ar"]


def test_a_language_it_did_get_right_is_not_asked_twice(groq):
    fake = groq([("Knowledge", "English")])
    hosted.transcribe(SOUND)
    assert len(fake.asked) == 1


def test_no_internet_falls_back_to_this_machine(groq, monkeypatch):
    """The one that matters: a dead cloud must never reach the reader."""
    groq(fail=ConnectionError("getaddrinfo failed"))
    monkeypatch.setattr(listen, "transcribe", lambda audio, language=None, hint="": "heard here")
    assert recitation.transcribe(SOUND) == "heard here"


def test_a_retired_key_or_a_spent_allowance_falls_back_too(groq, monkeypatch):
    """Both have happened on this key. Neither is news the reader can act on."""
    for failure in (PermissionError("401 invalid api key"), RuntimeError("429 rate limit")):
        groq(fail=failure)
        monkeypatch.setattr(listen, "transcribe", lambda audio, language=None, hint="": "heard here")
        assert recitation.transcribe(SOUND) == "heard here"


def test_with_no_key_nothing_is_sent_anywhere(monkeypatch):
    """Neither key, so there is nothing to send with and nothing is sent."""
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "recitation_groq_api_key", "")
    assert not hosted.is_available()


def test_listening_spends_its_own_key(monkeypatch):
    """The whole point of the second key: an hour of reciting must not spend
    the allowance the grammar explanations run on."""
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "gsk_explanations")
    monkeypatch.setattr(settings, "recitation_groq_api_key", "gsk_listening")
    assert settings.listening_key == "gsk_listening"


def test_without_its_own_key_listening_falls_back_to_the_shared_one(monkeypatch):
    """A machine that never set a second key listens exactly as it did before."""
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "gsk_explanations")
    monkeypatch.setattr(settings, "recitation_groq_api_key", "")
    assert settings.listening_key == "gsk_explanations"
    assert hosted.is_available()


def test_switching_it_off_keeps_every_recording_on_this_machine(monkeypatch):
    """The privacy switch: off means no sound leaves, key or no key."""
    settings = get_settings()
    monkeypatch.setattr(settings, "recitation_groq_api_key", "gsk_pretend")
    monkeypatch.setattr(settings, "recitation_hosted", False)
    assert not hosted.is_available()


def test_an_empty_recording_is_never_sent(groq, monkeypatch):
    """Nothing recorded is answered here, before any machine is troubled."""
    fake = groq()
    monkeypatch.setattr(listen, "transcribe", lambda audio, language=None, hint="": "")
    assert recitation.transcribe(b"") == ""
    assert fake.asked == []


def test_a_recitation_is_heard_as_arabic_and_a_search_in_either(monkeypatch):
    """The rule that decides the language, tested without a server in the way."""
    asked = []
    monkeypatch.setattr(recitation, "transcribe", lambda audio, language=None, hint="": asked.append(language) or "علم")
    monkeypatch.setattr(recitation, "find", lambda text, limit: [])
    recitation.hear(SOUND, match_ayahs=True)
    recitation.hear(SOUND, match_ayahs=False)
    assert asked == [get_settings().recitation_language, None]


def test_nothing_heard_is_not_matched(monkeypatch):
    monkeypatch.setattr(recitation, "transcribe", lambda audio, language=None, hint="": "")
    monkeypatch.setattr(recitation, "find", lambda text, limit: pytest.fail("matched silence"))
    assert recitation.hear(SOUND, match_ayahs=True) == ("", [])
