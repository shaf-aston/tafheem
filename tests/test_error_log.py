"""An unexpected server error is logged with where it happened and whose record.

The access log already has the path and the status; this adds the profile, so a
crash one learner reports can be found. The body is never logged.

Run: python -m pytest tests/test_error_log.py
"""
from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import progress_store


def test_a_crash_is_logged_with_path_and_profile_not_body(monkeypatch, caplog):
    def broken(*_args, **_kwargs):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(progress_store, "record", broken)
    monkeypatch.setattr(progress_store, "has_account", lambda _name: True)
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="backend.main"):
        response = client.post("/api/progress/attempts", headers={"X-Tafheem-Profile": "amina"},
                               json={"module": "quiz", "item": "secret-item", "correct": True})
    assert response.status_code == 500
    line = next(r.getMessage() for r in caplog.records if r.name == "backend.main")
    assert "/api/progress/attempts" in line and "amina" in line and "disk on fire" in line
    assert "secret-item" not in line
