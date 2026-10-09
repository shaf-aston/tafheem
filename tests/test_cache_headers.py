"""Which answers a browser may keep for a day, and that nothing else is.

The risk is one-sided: a fixed answer left uncached is only slower, but a
learner's progress or a live health check kept for a day is wrong. So the list
of cacheable paths is tested from both sides.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import CACHE_ONE_DAY, app, cacheable

client = TestClient(app)

ROOT = Path(__file__).resolve().parent.parent


def test_fixed_answer_is_cached_for_a_day():
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=86400" == CACHE_ONE_DAY


def test_health_is_never_cached():
    assert "cache-control" not in client.get("/api/health").headers


def test_a_missing_page_under_a_cached_prefix_is_not_cached():
    response = client.get("/api/dawah/no-such-thing")
    assert response.status_code == 404
    assert "cache-control" not in response.headers


def test_a_post_is_not_cached():
    assert "cache-control" not in client.post("/api/sources").headers


@pytest.mark.parametrize("path", [
    "/api/quran/surah/2",
    "/api/quran/surah/2/glosses",
    "/api/quran/editions/surah/2",
    "/api/hadith/collections",
    "/api/hadith/bukhari/books",
    "/api/hadith/bukhari/books/3",
    "/api/timelines",
    "/api/timelines/prophets/nuh/asbab",
    "/api/dawah",
    "/api/tamreen",
    "/api/notes",
    "/api/sources",
    "/api/grow/paths",
    "/api/tarkeeb/examples",
    "/api/daleel/books",
    "/api/colloquial",
    "/api/colloquial/egyptian/1",
])
def test_fixed_paths_are_cacheable(path):
    assert cacheable("GET", 200, path, None)


@pytest.mark.parametrize("path", [
    "/api/progress/summary",
    "/api/quran/editions",
    "/api/progress/review",
    "/api/progress",
    "/api/health",
    "/api/journal",
    "/api/listen",
    "/api/speak",
    "/api/analyze",
    "/api/hadith/search",
    "/api/quran/search",
    "/api/quran/similar/surah/2",
    "/api/quran/2/255",
    "/api/dictionary/search",
    "/api/daleel",
    "/api/rijal/narrators",
    "/api/dawah/extra",
    "/api/quran/surah/two",
    "/api/quran/surah/2/",
    "/api/sourcesX",
    "/x/api/sources",
])
def test_everything_else_is_not_cacheable(path):
    assert not cacheable("GET", 200, path, None)


def test_only_a_plain_successful_get_is_cached():
    assert not cacheable("POST", 200, "/api/sources", None)
    assert not cacheable("HEAD", 200, "/api/sources", None)
    assert not cacheable("GET", 404, "/api/sources", None)
    assert not cacheable("GET", 503, "/api/sources", None)


def test_a_route_that_set_its_own_cache_control_keeps_it():
    # /api/colloquial/image/... says a year; a day must not replace that.
    assert not cacheable("GET", 200, "/api/colloquial/image/a", "public, max-age=31536000, immutable")
    assert not cacheable("GET", 200, "/api/sources", "no-store")


def test_built_assets_are_cached_for_a_year():
    rules = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))["headers"]
    rule = next(r for r in rules if r["source"] == "/assets/(.*)")
    assert {h["key"]: h["value"] for h in rule["headers"]}["Cache-Control"] == "public, max-age=31536000, immutable"
