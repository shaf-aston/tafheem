"""Test-wide setup: nothing here may write into the app's own real folders.

Autouse because the recite journal (services/learner/journal) is now wired into every
recitation request (backend/routers/listen.py), so any test that hits
/api/listen would otherwise create real files under logs/ as a side effect of
merely running the suite.
"""
from __future__ import annotations

import pytest

from backend.config import get_settings
from backend.services.nahw import iraab
from backend.services.learner import journal


@pytest.fixture(autouse=True)
def _journal_writes_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "journal_path", str(tmp_path / "journal.jsonl"))
    monkeypatch.setattr(journal, "_built_from", None)
    yield


@pytest.fixture(autouse=True)
def _analyze_unlimited(monkeypatch):
    """Suites that analyse hundreds of sentences from one client are not one hammering visitor."""
    monkeypatch.setattr(get_settings(), "analyze_per_minute", 10**9)


@pytest.fixture(autouse=True)
def _analyses_read_afresh():
    """A test that changes the book or a model reads its sentences again, not another test's answer."""
    iraab._kept.cache_clear()
