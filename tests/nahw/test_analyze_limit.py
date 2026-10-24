"""POST /api/analyze: a visitor past analyze_per_minute is refused with 429, and the limit is per visitor."""
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import create_app
from backend.routers import analyze as analyze_route


def test_past_the_limit_is_429_for_that_visitor_only(monkeypatch):
    analyze_route._limit.asks.clear()
    monkeypatch.setattr(get_settings(), "analyze_per_minute", 2)
    app = TestClient(create_app())
    ask = lambda who: app.post("/api/analyze", json={"sentence": "hello"}, headers={"x-forwarded-for": who}).status_code  # noqa: E731
    assert [ask("1.1.1.1"), ask("1.1.1.1")] == [422, 422]  # not Arabic: refused after the limit check, without the parser
    assert ask("1.1.1.1") == 429
    assert ask("2.2.2.2") == 422
