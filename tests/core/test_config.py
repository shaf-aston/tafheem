"""Settings that must never be zero or negative: a limit of 0 does not mean
"no limit", it silently rejects every request the field was meant to cap.

Run: python -m pytest tests/core/test_config.py
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.config import Settings


@pytest.mark.parametrize("field", [
    "recitation_max_mb", "recitation_check_ayahs_max", "recitation_check_heard_max_chars",
    "search_max_query_chars", "quran_search_limit", "daleel_result_limit", "hadith_result_limit", "recitation_threads",
    "username_max", "leaderboard_size", "progress_busy_timeout_ms",
])
def test_a_positive_only_field_rejects_zero(field, monkeypatch):
    monkeypatch.delenv(field.upper(), raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: 0})
