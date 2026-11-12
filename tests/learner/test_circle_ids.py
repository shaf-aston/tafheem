"""A circle id too big to exist is a 422 for a signed-in learner, not a 500 from the database."""
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services.learner import progress_db
from tests.learner.sign_in import as_, forget_all, signup

HUGE = 10**20


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_db, "data_path", lambda _name: target)
    progress_db.reset_connection()
    forget_all()
    yield
    progress_db.reset_connection()


def test_a_huge_circle_id_is_422_not_500():
    client = TestClient(create_app())
    assert signup(client, "sara").status_code == 200
    who = as_("sara")
    assert client.get(f"/api/progress/circles/{HUGE}", headers=who).status_code == 422
    assert client.get("/api/progress/leaderboard", params={"circle": HUGE}, headers=who).status_code == 422
    assert client.put("/api/progress/circles/1/parent", json={"parent": HUGE}, headers=who).status_code == 422
    assert client.post("/api/progress/circles", json={"name": "x", "kind": "class", "parent": HUGE}, headers=who).status_code == 422
