"""Test-wide setup: nothing here may write into the app's own real folders.

Autouse because the recite journal (services/journal) is now wired into every
recitation request (backend/routers/listen.py), so any test that hits
/api/listen would otherwise create real files under logs/ as a side effect of
merely running the suite.
"""
from __future__ import annotations

import pytest

from backend.config import get_settings
from backend.services import journal


@pytest.fixture(autouse=True)
def _journal_writes_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_path", str(tmp_path / "journal.jsonl"))
    monkeypatch.setattr(journal, "_built_from", None)
    yield
