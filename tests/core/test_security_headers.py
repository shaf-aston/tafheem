"""Every /api answer is inert in a browser, and only our pages may call it cross-site, without credentials.

Paired with tests/core/test_cache_headers.py: that file guards what may be kept, this one what may run.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import CORS_HEADERS, app
from backend.services.core.headers import API_HEADERS

client = TestClient(app)
DEV = "http://localhost:5173"


@pytest.mark.parametrize("path", ["/api/sources", "/api/health", "/api/no-such-route"])
def test_every_api_answer_is_inert(path):
    headers = client.get(path).headers
    assert headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert headers["referrer-policy"] == "no-referrer"


def test_an_error_answer_is_inert_too():
    response = client.get("/api/progress/summary", headers={"X-Tafheem-Guest": "bad"})
    assert response.status_code == 422
    assert response.headers["x-content-type-options"] == "nosniff"


def test_each_header_is_sent_once():
    raw = [name.lower() for name, _ in client.get("/api/sources").headers.multi_items()]
    for name, _ in API_HEADERS:
        assert raw.count(name.decode()) == 1


def test_the_docs_page_keeps_its_own_scripts():
    assert "content-security-policy" not in client.get("/docs").headers


def test_a_dev_page_may_call_with_our_headers_but_no_credentials():
    response = client.options("/api/progress/summary", headers={
        "Origin": DEV, "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "x-tafheem-profile,x-tafheem-guest",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DEV
    assert "access-control-allow-credentials" not in response.headers


def test_a_stranger_site_is_not_allowed():
    response = client.get("/api/sources", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_a_header_the_page_never_sends_is_refused_in_preflight():
    response = client.options("/api/sources", headers={
        "Origin": DEV, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "x-something-else",
    })
    assert response.status_code == 400


def test_the_page_can_read_the_request_id():
    response = client.get("/api/sources", headers={"Origin": DEV})
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


def test_every_header_the_frontend_sends_is_allowed():
    """A header added to the page but not to CORS_HEADERS works live (same origin) and breaks only on a dev
    server, where nobody would think to look. So the page's own source is the list."""
    import re
    from pathlib import Path
    src = Path(__file__).resolve().parents[2] / "frontend" / "src"
    sent = set()
    for path in src.rglob("*.js*"):
        if ".test." in path.name:
            continue
        sent |= set(re.findall(r"['\"](X-[A-Za-z-]+)['\"]", path.read_text(encoding="utf-8")))
    assert sent, "found no headers: the search is broken"
    assert {h.lower() for h in sent} <= {h.lower() for h in CORS_HEADERS}


def test_an_answer_about_a_learner_is_never_kept_by_a_shared_cache():
    response = client.get("/api/progress/summary", headers={"X-Tafheem-Guest": "0" * 32})
    assert response.headers["cache-control"] == "private, no-store"


def test_a_fixed_answer_keeps_its_day_long_cache_even_when_a_learner_asks():
    response = client.get("/api/sources", headers={"X-Tafheem-Guest": "0" * 32})
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_an_anonymous_answer_is_left_as_it_was():
    assert "cache-control" not in client.get("/api/health").headers
