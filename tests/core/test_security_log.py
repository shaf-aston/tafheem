"""The security log (services/core/audit.py): what it writes, and what it must never write.

The risk is two-sided. A refused request that leaves no line cannot be investigated; a line
that carries what someone typed, a key, or a forged second line makes the log a liability.
"""
import json

from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.services.core import audit

client = TestClient(app)


def lines() -> list[dict]:
    path = get_settings().security_log_path
    try:
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]
    except FileNotFoundError:
        return []


def test_an_event_is_one_json_line_with_the_request_context():
    rid = audit.request_id.set("abc12345")
    ip = audit.client_ip.set("203.0.113.9")
    try:
        audit.event("signup", user="zayd")
    finally:
        audit.request_id.reset(rid)
        audit.client_ip.reset(ip)
    [line] = lines()
    assert line["kind"] == "signup" and line["user"] == "zayd"
    assert line["request_id"] == "abc12345" and line["ip"] == "203.0.113.9"
    assert line["at"].endswith("+00:00")


def test_a_newline_in_a_value_cannot_forge_a_second_line():
    audit.event("login", user='x\n{"kind": "forged"}')
    [line] = lines()
    assert line["kind"] == "login"
    assert line["user"] == "x?{\"kind\": \"forged\"}"  # one line; the break is not even kept as data


def test_keys_are_scrubbed_and_values_capped():
    audit.event("error", detail="Bearer sk-secret gsk_ABCdef123 " + "x" * 1000)
    [line] = lines()
    assert "sk-secret" not in line["detail"] and "gsk_ABCdef123" not in line["detail"]
    assert len(line["detail"]) <= 200


def test_a_log_that_cannot_be_written_never_breaks_the_caller(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "security_log_path", str(tmp_path))  # a folder, not a file
    monkeypatch.setattr(audit, "_built_from", None)
    audit.event("signup", user="zayd")  # no exception


def test_every_answer_carries_a_request_id():
    response = client.get("/api/sources")
    assert len(response.headers["x-request-id"]) == 32


def test_a_well_formed_inbound_request_id_is_kept_and_a_bad_one_replaced():
    assert client.get("/api/sources", headers={"X-Request-ID": "edge-1234abcd"}).headers["x-request-id"] == "edge-1234abcd"
    forged = client.get("/api/sources", headers={"X-Request-ID": "bad id\r\nx"}).headers["x-request-id"]
    assert forged != "bad id\r\nx" and len(forged) == 32


def test_a_fine_answer_writes_nothing():
    client.get("/api/sources")
    assert lines() == []


def test_a_refused_answer_is_logged_by_route_template_never_by_raw_path():
    response = client.get("/api/progress/summary?secret=typed-text", headers={"X-Tafheem-Guest": "not-a-device-id"})
    assert response.status_code == 422
    [line] = lines()
    assert line["kind"] == "refused" and line["status"] == 422 and line["method"] == "GET"
    assert line["route"] == "/api/progress/summary"
    assert line["request_id"] == response.headers["x-request-id"]
    assert "typed-text" not in json.dumps(line)


def test_after_logrotate_moves_the_file_the_next_line_starts_a_new_one():
    """Two server processes write this file, so rotation is logrotate's, outside Python
    (deploy/logrotate.conf). Each process must notice the move and write to the fresh file."""
    import os
    audit.event("login", user="before")
    path = get_settings().security_log_path
    os.rename(path, path + "-20990101")
    audit.event("login", user="after")
    assert [line["user"] for line in lines()] == ["after"]


def test_each_line_also_reaches_the_journal(capsys):
    """stderr is journald's under systemd: a copy the app's own user cannot rewrite."""
    audit.event("account_deleted", user="zayd")
    err = capsys.readouterr().err
    assert err.startswith("security {") and '"account_deleted"' in err


def test_a_crash_answer_still_carries_its_id_and_is_inert():
    """Starlette answers a crash from outside every middleware, so the id travels on the scope."""
    from backend.main import create_app
    crashing = create_app()

    @crashing.get("/api/boom")
    def boom():
        raise RuntimeError("boom")

    response = TestClient(crashing, raise_server_exceptions=False).get("/api/boom")
    assert response.status_code == 500
    assert response.headers["x-content-type-options"] == "nosniff"
    rid = response.headers["x-request-id"]
    assert [line["request_id"] for line in lines() if line["kind"] == "error"] == [rid]


def test_a_forged_address_cannot_put_control_characters_in_front_of_the_reader():
    audit.event("x", name="a\x1b[2Jb\x9bc")
    [line] = lines()
    assert line["name"] == "a?[2Jb?c"


def test_what_a_learner_searched_never_lands_in_the_server_log(caplog):
    """httpx logs each outbound address; the Qur'an search sends the learner's words as ?q=."""
    import httpx
    import logging

    import backend.main  # noqa: F401, installs the filter
    with caplog.at_level(logging.INFO, logger="httpx"):
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as http:
            http.get("https://api.quran.com/api/v4/search", params={"q": "رحمة", "size": 20})
            http.post("https://api.groq.com/openai/v1/chat/completions")
    lines = [r.getMessage() for r in caplog.records if r.name == "httpx"]
    assert len(lines) == 2
    assert "رحمة" not in lines[0] and "%D8" not in lines[0] and "api.quran.com/api/v4/search" in lines[0]
    assert "api.groq.com" in lines[1] and "/v1/" in lines[1] and " 200 " in lines[1]  # deploy/usage.py still counts it


def test_a_crash_is_logged_without_the_key_its_error_carried(caplog):
    from backend.main import create_app
    crashing = create_app()

    @crashing.get("/api/boom-key")
    def boom():
        raise RuntimeError("401 for Authorization: Bearer gsk_SECRETKEY123")

    with caplog.at_level("ERROR"):
        TestClient(crashing, raise_server_exceptions=False).get("/api/boom-key")
    assert "boom-key" in caplog.text and "SECRETKEY123" not in caplog.text


def test_an_api_path_no_route_owns_is_logged_but_a_missing_word_is_not():
    client.get("/api/no-such-thing")
    client.get("/api/hadith/zzzmissing/books/1")  # a route that answers 404 itself: ordinary
    assert [line["status"] for line in lines() if line["kind"] == "refused"] == [404]
