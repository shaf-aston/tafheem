"""A bad .env stops startup naming the key, never printing its value."""
import pytest

from backend.config import get_settings


def test_a_rejected_env_entry_is_named_and_its_value_is_not_printed(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("NOT_A_SETTING=planted_secret_one\nGROQ_API_KEY=planted secret #two\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(SystemExit) as stopped:
        get_settings.__wrapped__()
    message = str(stopped.value)
    assert "not_a_setting" in message and "groq_api_key" in message
    assert "planted" not in message
