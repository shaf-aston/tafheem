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


def test_a_circle_you_are_not_in_answers_like_one_that_does_not_exist():
    client = TestClient(create_app())
    for name in ("sara", "omar"):
        assert signup(client, name).status_code == 200
    made = client.post("/api/progress/circles", json={"name": "Class", "kind": "class"}, headers=as_("sara"))
    assert made.status_code == 200
    real = made.json()["id"]
    same = lambda call: [call(real).status_code, call(999999).status_code] == [404, 404] and call(real).json() == call(999999).json()  # noqa: E731
    omar = as_("omar")
    assert same(lambda i: client.get(f"/api/progress/circles/{i}", headers=omar))
    assert same(lambda i: client.get("/api/progress/leaderboard", params={"circle": i}, headers=omar))
    assert same(lambda i: client.delete(f"/api/progress/circles/{i}", headers=omar))
    assert same(lambda i: client.get(f"/api/progress/circles/{i}/members/sara/overview", headers=omar))
    # inside the circle, a real refusal stays one
    client.post(f"/api/progress/circles/{real}/members", json={"member": "omar", "role": "member"}, headers=as_("sara"))
    assert client.post(f"/api/progress/circles/{real}/accept", headers=omar).status_code == 200
    assert client.delete(f"/api/progress/circles/{real}", headers=omar).status_code == 403
