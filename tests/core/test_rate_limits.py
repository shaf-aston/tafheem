"""Every per-visitor limit refuses with 429 past its count, only that visitor, and each has a ceiling for everyone
(services/core/ratelimit.Limit). The model budget is tested in test_ai_guard.py."""
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import create_app
from backend.services.core.ratelimit import ANALYZE, READ


def test_past_the_limit_is_429_for_that_visitor_only(monkeypatch):
    ANALYZE.each.asks.clear()
    monkeypatch.setattr(get_settings(), "analyze_per_minute", 2)
    app = TestClient(create_app())
    ask = lambda who: app.post("/api/analyze", json={"sentence": "hello"}, headers={"x-forwarded-for": who}).status_code  # noqa: E731
    assert [ask("1.1.1.1"), ask("1.1.1.1")] == [422, 422]  # not Arabic: refused after the limit check, without the parser
    assert ask("1.1.1.1") == 429
    assert ask("2.2.2.2") == 422


def test_forging_a_new_address_each_time_still_meets_the_ceiling(monkeypatch):
    ANALYZE.each.asks.clear()
    ANALYZE.everyone.asks.clear()
    monkeypatch.setattr(get_settings(), "analyze_all_per_minute", 2)
    app = TestClient(create_app())
    codes = [app.post("/api/analyze", json={"sentence": "hello"}, headers={"x-real-ip": f"198.51.100.{n}"}).status_code
             for n in range(3)]
    assert codes == [422, 422, 429]
    ANALYZE.everyone.asks.clear()


def test_a_sentences_meaning_and_practice_share_a_parser_count(monkeypatch):
    """Both run the parser over up to 160 words; neither had a limit once the AI budget moved to the call."""
    READ.each.asks.clear()
    monkeypatch.setattr(get_settings(), "sentence_per_minute", 2)
    app = TestClient(create_app())
    who = {"x-real-ip": "203.0.113.20"}
    assert app.get("/api/dictionary/sentence", params={"q": "hello"}, headers=who).status_code == 422
    assert app.post("/api/practice", json={"sentence": "hello"}, headers=who).status_code == 422
    assert app.get("/api/dictionary/sentence", params={"q": "hello"}, headers=who).status_code == 429
    assert app.post("/api/practice", json={"sentence": "hello"}, headers=who).status_code == 429
    assert app.post("/api/practice", json={"sentence": "hello"}, headers={"x-real-ip": "203.0.113.21"}).status_code == 422
    READ.each.asks.clear()


def test_signing_up_and_logging_in_share_a_small_count(monkeypatch):
    from backend.services.core.ratelimit import ACCOUNT
    ACCOUNT.each.asks.clear()
    monkeypatch.setattr(get_settings(), "account_per_minute", 2)
    app = TestClient(create_app())
    who = {"x-real-ip": "203.0.113.30", "X-Tafheem-Profile": "nobody-here"}
    assert app.post("/api/progress/login", headers=who).status_code == 404
    assert app.post("/api/progress/login", headers=who).status_code == 404
    assert app.post("/api/progress/signup", json={"keep": False}, headers=who).status_code == 429
    ACCOUNT.each.asks.clear()


def test_recordings_have_a_count_of_their_own(monkeypatch):
    from backend.services.core.ratelimit import RECORDING
    RECORDING.each.asks.clear()
    monkeypatch.setattr(get_settings(), "recording_per_minute", 1)
    app = TestClient(create_app())
    who = {"x-real-ip": "203.0.113.31"}
    first = app.post("/api/listen/check", params={"heard": "x"}, files={"audio": ("a.webm", b"x", "audio/webm")}, headers=who)
    assert first.status_code != 429
    again = app.post("/api/listen", files={"audio": ("a.webm", b"x", "audio/webm")}, headers=who)
    assert again.status_code == 429
    RECORDING.each.asks.clear()


def test_journal_reports_are_429_past_the_limit(monkeypatch):
    from backend.services.core.ratelimit import JOURNAL
    JOURNAL.each.asks.clear()
    monkeypatch.setattr(get_settings(), "journal_per_minute", 2)
    app = TestClient(create_app())
    ask = lambda who: app.post("/api/journal", json={"events": []}, headers={"x-real-ip": who}).status_code  # noqa: E731
    first = [ask("203.0.113.40"), ask("203.0.113.40")]
    assert 429 not in first
    assert ask("203.0.113.40") == 429
    assert ask("203.0.113.41") != 429
    JOURNAL.each.asks.clear()
