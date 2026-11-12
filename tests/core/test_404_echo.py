"""A 404 never echoes what the caller typed."""
from fastapi.testclient import TestClient

from backend.main import create_app

client = TestClient(create_app())


def test_a_404_does_not_echo_what_was_typed():
    for path in ("/api/hadith/zzzecho/books/1", "/api/timelines/zzzecho/yyyecho/asbab", "/api/usul/terms/zzzecho"):
        got = client.get(path)
        assert got.status_code == 404, path
        assert "zzzecho" not in got.text and "yyyecho" not in got.text
