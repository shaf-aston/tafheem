"""POST /api/analyze: a visitor past analyze_per_minute is refused with 429, and the limit is per visitor."""
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
