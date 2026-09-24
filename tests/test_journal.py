"""The recite journal: one JSON line per event, server side and page side both.

Every test points journal_path at its own tmp_path file (the module-wide
conftest.py fixture already does this for the whole suite; here it is done
again per test so a test can also set journal_max_kb / journal_keep / the page
limits without disturbing any other test).

Run: python -m pytest tests/test_journal.py
"""
from __future__ import annotations

import json
import threading

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.services import journal

client = TestClient(app)


@pytest.fixture
def journal_file(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    monkeypatch.setattr(get_settings(), "journal_path", str(path))
    monkeypatch.setattr(journal, "_built_from", None)
    return path


def lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_a_server_line_is_valid_json_with_the_expected_fields(journal_file):
    journal.note("reading.received", bytes=123, recite=True, session="s1", reading="r1")
    row = lines(journal_file)[0]
    assert row["side"] == "server"
    assert row["kind"] == "reading.received"
    assert row["bytes"] == 123
    assert row["recite"] is True
    assert row["session"] == "s1"
    assert row["reading"] == "r1"
    assert "at" in row


def test_a_page_line_is_written_exactly_as_sent(journal_file):
    journal.note_page({"at": "2026-09-16T10:00:00.000Z", "kind": "mic.gate", "reading": "r1"})
    assert lines(journal_file)[0] == {
        "at": "2026-09-16T10:00:00.000Z", "side": "page", "kind": "mic.gate", "reading": "r1",
    }


def test_blank_fields_are_left_out_rather_than_written(journal_file):
    journal.note("reading.done", ms=12, status=200, session="", reading=None)
    row = lines(journal_file)[0]
    assert "session" not in row
    assert "reading" not in row


def test_the_reading_id_is_filled_from_the_contextvar_when_not_named(journal_file):
    token = journal.reading_id.set("abc123")
    try:
        journal.note("ear.failed", ear="hosted", error="ConnectionError", message="no internet")
    finally:
        journal.reading_id.reset(token)
    assert lines(journal_file)[0]["reading"] == "abc123"


def test_rotation_happens_past_the_configured_size(journal_file, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_max_kb", 1)  # 1024 bytes: tiny, on purpose
    monkeypatch.setattr(get_settings(), "journal_keep", 2)
    monkeypatch.setattr(journal, "_built_from", None)
    for i in range(80):
        journal.note("reading.done", ms=i, status=200, reading=f"r{i}")
    assert journal_file.exists()
    assert journal_file.with_name(journal_file.name + ".1").exists(), "past the cap, a backup file must appear"


def test_an_exact_duplicate_event_in_one_batch_is_written_as_sent_both_lines(journal_file):
    """The page may legitimately repeat an event (a retry, a duplicate mic-gate
    close); deciding which repeat is the "real" one is not this file's job, so
    nothing here deduplicates."""
    batch = {"events": [
        {"at": 1000, "kind": "mic.gate", "reading": "r1"},
        {"at": 1000, "kind": "mic.gate", "reading": "r1"},
    ]}
    resp = client.post("/api/journal", json=batch)
    assert resp.status_code == 204
    rows = lines(journal_file)
    assert len(rows) == 2
    assert rows[0] == rows[1]


def test_a_bad_kind_is_rejected(journal_file):
    resp = client.post("/api/journal", json={"events": [{"at": 1, "kind": "Not Ok!"}]})
    assert resp.status_code == 422
    assert lines(journal_file) == []


def test_too_many_events_is_rejected(journal_file):
    limit = get_settings().journal_page_events_max
    events = [{"at": i, "kind": "mic.gate"} for i in range(limit + 1)]
    resp = client.post("/api/journal", json={"events": events})
    assert resp.status_code == 422
    assert lines(journal_file) == []


def test_an_oversize_body_is_rejected(journal_file, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_page_bytes_max", 200)
    events = [{"at": 1, "kind": "mic.gate", "detail": {"note": "x" * 500}}]
    resp = client.post("/api/journal", json={"events": events})
    assert resp.status_code == 413
    assert lines(journal_file) == []


def test_an_oversize_detail_is_truncated_with_a_marker(journal_file):
    big = {"note": "x" * 5000}
    resp = client.post("/api/journal", json={"events": [{"at": 1, "kind": "mic.gate", "detail": big}]})
    assert resp.status_code == 204
    assert lines(journal_file)[0]["detail"] == {"truncated": True}


def test_journal_settings_reject_zero_or_negative(journal_file, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_max_kb", 0)
    monkeypatch.setattr(journal, "_built_from", None)
    with pytest.raises(journal.JournalConfigError):
        journal.note("reading.done", ms=1, status=200)


def test_note_from_several_threads_on_a_fresh_config_adds_one_handler_and_n_lines(journal_file):
    """Two worker threads can both see the handler as unbuilt at once; without
    the lock in _ensure_configured both add one, doubling every line after."""
    threads = [threading.Thread(target=journal.note, args=("t.event",), kwargs={"i": i}) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(journal._journal.handlers) == 1
    assert len(lines(journal_file)) == 20


def test_rotation_with_keep_two_never_leaves_a_dot_three_file(journal_file, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_max_kb", 1)
    monkeypatch.setattr(get_settings(), "journal_keep", 2)
    monkeypatch.setattr(journal, "_built_from", None)
    for i in range(200):
        journal.note("reading.done", ms=i, status=200, reading=f"r{i}")
    assert not journal_file.with_name(journal_file.name + ".3").exists()


def test_a_batch_with_one_valid_and_one_invalid_event_writes_nothing(journal_file):
    """Batches are validated and written atomically, on purpose: one bad event
    must not half-write a page's batch. This never trips a real page, because
    the page omits an event's id rather than sending a blank one."""
    batch = {"events": [
        {"at": 1, "kind": "mic.gate", "reading": "r1"},
        {"at": 2, "kind": "Not Ok!"},
    ]}
    resp = client.post("/api/journal", json=batch)
    assert resp.status_code == 422
    assert lines(journal_file) == []


def test_a_streamed_body_without_content_length_over_the_limit_is_rejected(journal_file, monkeypatch):
    """No Content-Length header (a chunked/streamed body): the cap must still
    be enforced by what is actually read, not skipped for lack of a header."""
    monkeypatch.setattr(get_settings(), "journal_page_bytes_max", 200)
    big = json.dumps({"events": [{"at": 1, "kind": "mic.gate", "detail": {"note": "x" * 500}}]}).encode()

    def stream():
        for i in range(0, len(big), 50):
            yield big[i:i + 50]

    resp = client.post("/api/journal", content=stream())
    assert resp.status_code == 413
    assert lines(journal_file) == []


def test_scrub_removes_a_bearer_token_and_a_gsk_key():
    out = journal.scrub("call failed: Authorization: Bearer gsk_abc123XYZ, retry")
    assert "gsk_abc123XYZ" not in out
    assert "Bearer" not in out
    assert "[redacted]" in out


# How the two listening routes file a request: under the page's id, with how it
# ended. Both go through one helper in routers/listen.py, so each is checked.
WEBM = bytes([0x1A, 0x45, 0xDF, 0xA3]) + bytes(8)


def route_lines(path, prefix):
    return [row for row in lines(path) if row["kind"].startswith(prefix)]


def test_a_rejected_check_is_filed_as_failed_then_done_under_the_page_id(journal_file):
    resp = client.post(
        "/api/listen/check", params={"heard": "x", "check": "not-an-ayah"},
        files={"audio": ("a.webm", WEBM, "audio/webm")}, headers={"X-Reading-Id": "page-7-1"},
    )
    assert resp.status_code == 422
    assert resp.headers["X-Reading-Id"] == "page-7-1"
    rows = route_lines(journal_file, "check.")
    assert [row["kind"] for row in rows] == ["check.failed", "check.done"]
    assert rows[0]["stage"] == "validate"
    assert rows[1]["status"] == 422
    assert {row["reading"] for row in rows} == {"page-7-1"}


def test_a_rejected_reading_is_filed_the_same_way_under_its_own_name(journal_file):
    resp = client.post(
        "/api/listen", params={"recite": "true"},
        files={"audio": ("a.webm", b"not sound at all", "audio/webm")}, headers={"X-Reading-Id": "page-7-2"},
    )
    assert resp.status_code == 415
    assert resp.headers["X-Reading-Id"] == "page-7-2"
    kinds = [row["kind"] for row in route_lines(journal_file, "reading.")]
    assert kinds == ["reading.received", "reading.failed", "reading.done"]
    assert route_lines(journal_file, "reading.done")[0]["status"] == 415


def test_an_empty_reading_is_done_not_failed(journal_file):
    resp = client.post("/api/listen", files={"audio": ("a.webm", b"", "audio/webm")})
    assert resp.status_code == 200
    assert [row["kind"] for row in route_lines(journal_file, "reading.")] == ["reading.received", "reading.done"]


def test_a_badly_shaped_page_id_is_replaced_and_the_new_one_used_throughout(journal_file):
    resp = client.post(
        "/api/listen/check", params={"heard": "x", "check": "bad"},
        files={"audio": ("a.webm", WEBM, "audio/webm")}, headers={"X-Reading-Id": "has spaces/and slashes"},
    )
    made = resp.headers["X-Reading-Id"]
    assert made != "has spaces/and slashes"
    assert {row["reading"] for row in route_lines(journal_file, "check.")} == {made}
