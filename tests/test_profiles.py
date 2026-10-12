"""Profiles: a learner signs up with a username and gets their own record.

No password, which is agreed. What is checked is that a username is signed up
once, that two names never mix, that one spelling is one person, and that
wiping or claiming touches only the name asking.

Run: python -m pytest tests/test_profiles.py
"""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import progress_store
from backend.services.username import clean_name

client = TestClient(app)


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


def as_(name):
    """The header the page sends: percent-encoded, since headers cannot carry Arabic."""
    return {"X-Tafheem-Profile": quote(name)} if name is not None else {}


def answer(name, item, correct=True):
    if name is not None:
        signup(name)  # a second sign-up of the same name is a harmless 409
    return client.post("/api/progress/attempts", headers=as_(name),
                       json={"module": "quiz", "item": item, "correct": correct})


def items(name):
    if name is not None:
        signup(name)
    response = client.get("/api/progress/summary", params={"module": "quiz"}, headers=as_(name))
    assert response.status_code == 200
    return [row["item"] for row in response.json()["items"]]


@pytest.mark.parametrize("raw, clean", [
    (" Amina ", "amina"),
    ("AMINA", "amina"),
    ("a  b", "a b"),
    ("عائشة", "عائشة"),
    ("عَائِشَة", "عَائِشَة"),          # tashkeel kept: a different spelling is a different name
    ("Amina-2_b.c", "amina-2_b.c"),
    ("x" * 40, "x" * 40),
    ("Straße", "strasse"),
    ("مهر\u200cناز", "مهر\u200cناز"),
])
def test_clean_name_folds_one_person_to_one_spelling(raw, clean):
    assert clean_name(raw) == clean


@pytest.mark.parametrize("raw", ["", "   ", "x" * 41, "ß" * 21, "<x>", "a/b", "local", " LOCAL ", "...", "-"])
def test_clean_name_refuses_what_is_not_a_name(raw):
    with pytest.raises(ValueError):
        clean_name(raw)


def test_two_names_keep_two_records():
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    assert items("Amina") == ["to-write"]
    assert items("bilal ") == ["to-read"]


def test_an_arabic_name_travels_and_is_its_own_record():
    answer("عائشة", "to-write")
    assert items("عائشة") == ["to-write"]
    assert items("Amina") == []


def test_no_name_is_the_old_shared_record():
    answer(None, "to-write")
    assert items(None) == ["to-write"]
    assert items("Amina") == []


@pytest.mark.parametrize("bad", ["<x>", "local", "x" * 41])
def test_a_bad_name_is_refused_not_filed(bad):
    assert answer(bad, "to-write").status_code == 422
    assert progress_store._db().execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_forget_wipes_only_the_name_asking():
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    response = client.delete("/api/progress", headers=as_("Amina"))
    assert response.json() == {"deleted": 1}
    assert items("Amina") == []
    assert items("Bilal") == ["to-read"]


def signup(name, keep=False):
    return client.post("/api/progress/signup", json={"keep": keep}, headers=as_(name))


def login(name):
    return client.post("/api/progress/login", headers=as_(name))


def test_signup_hands_back_the_one_spelling():
    body = signup("  Amina ").json()
    assert (body["name"], body["answers"]) == ("amina", 0)


def test_a_taken_username_cannot_sign_up_again():
    signup("Amina")
    response = signup("AMINA")
    assert response.status_code == 409
    assert response.json()["detail"] == "That username is taken"


def test_login_finds_a_signed_up_name_only():
    assert login("Amina").status_code == 404
    signup("Amina")
    assert login(" amina ").json()["name"] == "amina"


def test_names_used_before_signup_existed_can_log_in():
    progress_store.record(module="quiz", item="to-go", correct=True, user="bilal")  # from before accounts
    progress_store.leave_feedback(module="quiz", message="x", user="cyra")  # reported, never answered
    progress_store.reset_connection()  # a restart, where the old names become accounts
    assert login("Bilal").status_code == 200
    assert login("Cyra").status_code == 200
    assert signup("Bilal").status_code == 409


def test_a_name_without_an_account_cannot_read_or_write():
    """A deleted account in another tab must not keep filing answers."""
    body = {"module": "quiz", "item": "to-write", "correct": True}
    response = client.post("/api/progress/attempts", headers=as_("ghost"), json=body)
    assert response.status_code == 401
    assert response.json()["detail"] == "Log in again: no account with that username"
    assert client.get("/api/progress/summary", headers=as_("ghost")).status_code == 401


def test_signup_with_a_bad_name_says_why():
    response = signup("<x>")
    assert response.status_code == 422
    assert response.json()["detail"] == "Names use letters, numbers, spaces, - _ ."


def test_keep_moves_this_devices_old_answers_to_the_name():
    answer(None, "to-write")
    answer(None, "to-read", correct=False)
    answer("Bilal", "to-go")
    assert signup("Amina", keep=True).json()["answers"] == 2
    assert items("Amina") == ["to-read", "to-write"]
    assert items(None) == []
    assert items("Bilal") == ["to-go"]


def test_without_keep_old_answers_stay_unnamed():
    answer(None, "to-write")
    signup("Amina")
    assert items(None) == ["to-write"]


def test_keep_leaves_the_shared_ai_question_cache_alone():
    progress_store.keep_questions(module="meaning", sentence="s", source="ai",
                                  questions=[{"question": "q", "answer": "a"}])
    signup("Amina", keep=True)
    assert len(progress_store.kept_questions("meaning")) == 1


def test_signup_and_login_need_a_name():
    assert client.post("/api/progress/signup", json={}).status_code == 422
    assert client.post("/api/progress/login").status_code == 422


def test_the_account_says_who_since_when_and_how_many_answers():
    signup("Amina")
    answer("Amina", "to-write")
    answer("Amina", "to-read", correct=False)
    body = client.get("/api/progress/account", headers=as_("Amina")).json()
    assert (body["name"], body["answers"]) == ("amina", 2)
    assert body["joined"].endswith("+00:00")
    assert client.get("/api/progress/account", headers=as_("Bilal")).status_code == 401
    assert client.get("/api/progress/account").status_code == 422


def test_deleting_the_account_frees_the_name_and_wipes_only_its_answers():
    signup("Amina")
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    client.post("/api/progress/feedback", headers=as_("Amina"), json={"module": "quiz", "message": "typo"})
    assert client.delete("/api/progress/account", headers=as_("Amina")).json() == {"deleted": 1}
    progress_store.reset_connection()  # a restart must not bring the name back from its reports
    assert login("Amina").status_code == 404
    assert progress_store.summary("quiz", "amina") == []
    assert items("Bilal") == ["to-read"]
    assert signup("Amina").status_code == 200


def test_a_deleted_accounts_reports_go_to_nobody():
    """Kept, but not handed to whoever signs up next and keeps the guest's things."""
    signup("Amina")
    client.post("/api/progress/feedback", headers=as_("Amina"), json={"module": "quiz", "message": "typo"})
    client.delete("/api/progress/account", headers=as_("Amina"))
    signup("Bilal", keep=True)
    progress_store.reset_connection()
    users = [row[0] for row in progress_store._db().execute("SELECT user FROM feedback")]
    assert users == [""]
    assert client.get("/api/progress/accounts").json() == {"names": ["bilal"]}


def test_the_leaderboard_ranks_accounts_by_words_learnt_and_finds_you():
    db_answer = lambda name, item, days: progress_store._db().execute(  # noqa: E731
        "INSERT INTO attempts (user, module, item, correct, at) VALUES (?, 'quiz', ?, 1, datetime('now', ?))",
        (name, item, f"-{days} days"))
    for name in ("Amina", "Bilal", "Cyra"):
        signup(name)
    for item in ("a", "b"):  # right on two separate days: learnt
        db_answer("bilal", item, 3), db_answer("bilal", item, 2)
    db_answer("amina", "a", 3), db_answer("amina", "a", 2)
    progress_store._db().commit()
    answer(None, "a")  # the guest record is nobody's, so it is not ranked
    body = client.get("/api/progress/leaderboard", params={"module": "quiz"}, headers=as_("Cyra")).json()
    assert [(r["rank"], r["name"], r["learnt"]) for r in body["rows"]] == [
        (1, "bilal", 2), (2, "amina", 1), (3, "cyra", 0)]
    assert body["you"]["rank"] == 3
    assert client.get("/api/progress/leaderboard").json()["you"] is None


# The shelf: what the page keeps for one account (settings, Grow steps, favourites),
# saved whole on the server so it follows the name to another device.

def shelf(name, data=None):
    if data is None:
        return client.get("/api/progress/saved", headers=as_(name))
    return client.put("/api/progress/saved", headers=as_(name), json={"data": data})


def test_the_shelf_is_kept_per_account_and_replaced_whole():
    signup("Amina"), signup("Bilal")
    assert shelf("Amina").json() == {"data": {}}
    assert shelf("Amina", {"settings": '{"size":"large"}', "progress:grow": "{}"}).status_code == 200
    shelf("Bilal", {"settings": '{"size":"small"}'})
    shelf("Amina", {"settings": '{"size":"medium"}'})
    assert shelf("Amina").json() == {"data": {"settings": '{"size":"medium"}'}}
    assert shelf("Bilal").json() == {"data": {"settings": '{"size":"small"}'}}


def test_the_guest_and_strangers_have_no_shelf():
    assert shelf(None).status_code == 422
    assert shelf(None, {"k": "v"}).status_code == 422
    assert shelf("Nobody").status_code == 401


def test_a_shelf_too_big_is_refused(monkeypatch):
    from backend.config import get_settings
    monkeypatch.setattr(get_settings(), "saved_max_bytes", 50)
    signup("Amina")
    assert shelf("Amina", {"k": "x" * 100}).status_code == 413
    assert shelf("Amina").json() == {"data": {}}


def test_start_over_and_delete_empty_the_shelf():
    signup("Amina")
    shelf("Amina", {"k": "v"})
    client.delete("/api/progress", headers=as_("Amina"))
    assert shelf("Amina").json() == {"data": {}}
    shelf("Amina", {"k": "v"})
    client.delete("/api/progress/account", headers=as_("Amina"))
    signup("Amina")
    assert shelf("Amina").json() == {"data": {}}


# Beta: the log-in box lists every username, so testers can pick one.

def test_while_in_beta_every_username_is_listed(monkeypatch):
    from backend.config import get_settings
    signup("Bilal"), signup("Amina")
    assert client.get("/api/progress/accounts").json() == {"names": ["amina", "bilal"]}
    monkeypatch.setattr(get_settings(), "beta_list_accounts", False)
    assert client.get("/api/progress/accounts").status_code == 404


# Circles: invited people are invisible until they accept; what a viewer may see of a member follows the roles.

def make(name, circle="Crew", kind="team", parent=None):
    """Sign `name` up if needed and have it create a circle; returns the response."""
    signup(name)
    return client.post("/api/progress/circles", headers=as_(name),
                       json={"name": circle, "kind": kind, **({"parent": parent} if parent else {})})


def invite(admin, cid, member, role="member"):
    signup(member)
    return client.post(f"/api/progress/circles/{cid}/members", headers=as_(admin),
                       json={"member": member, "role": role})


def join(admin, cid, member, role="member"):
    assert invite(admin, cid, member, role).status_code == 200
    assert client.post(f"/api/progress/circles/{cid}/accept", headers=as_(member)).status_code == 200


def detail(who, cid):
    return client.get(f"/api/progress/circles/{cid}", headers=as_(who))


def seen_overview(viewer, cid, member):
    return client.get(f"/api/progress/circles/{cid}/members/{quote(member)}/overview", headers=as_(viewer))


def ranked(who, cid):
    response = client.get("/api/progress/leaderboard", params={"module": "quiz", "circle": cid}, headers=as_(who))
    return response.status_code, [row["name"] for row in response.json().get("rows", [])]


def test_an_invite_shows_nothing_until_accepted():
    cid = make("Amina").json()["id"]
    join("Amina", cid, "Cyra")
    invite("Amina", cid, "Bilal")
    pending = client.get("/api/progress/circles", headers=as_("Bilal")).json()["circles"]
    assert [(c["id"], c["status"], c["invitedBy"]) for c in pending] == [(cid, "invited", "amina")]
    assert detail("Bilal", cid).status_code == 403
    assert ranked("Bilal", cid)[0] == 403
    assert ranked("Cyra", cid) == (200, ["amina", "cyra"])
    assert [m["name"] for m in detail("Cyra", cid).json()["members"]] == ["amina", "cyra"]
    members = detail("Amina", cid).json()["members"]
    assert [(m["name"], m["status"]) for m in members] == [("amina", "joined"), ("bilal", "invited"), ("cyra", "joined")]
    client.post(f"/api/progress/circles/{cid}/accept", headers=as_("Bilal"))
    assert ranked("Cyra", cid) == (200, ["amina", "bilal", "cyra"])


def test_declining_an_invite_deletes_it_and_a_stranger_cannot_invite():
    cid = make("Amina").json()["id"]
    invite("Amina", cid, "Bilal")
    assert client.post(f"/api/progress/circles/{cid}/decline", headers=as_("Bilal")).status_code == 200
    assert client.get("/api/progress/circles", headers=as_("Bilal")).json()["circles"] == []
    assert invite("Bilal", cid, "Cyra").status_code == 403


def test_an_admin_sees_a_joined_members_overview_but_a_plain_member_does_not():
    cid = make("Amina").json()["id"]
    join("Amina", cid, "Bilal")
    join("Amina", cid, "Cyra")
    invite("Amina", cid, "Dana")
    answer("Bilal", "a")
    assert seen_overview("Amina", cid, "Bilal").json()["attempts"] == 1
    assert seen_overview("Bilal", cid, "Bilal").status_code == 200       # your own
    assert seen_overview("Cyra", cid, "Bilal").status_code == 403         # a team shows no details
    assert seen_overview("Amina", cid, "Dana").status_code == 403         # invited, not joined


def test_in_a_friends_circle_every_member_sees_every_overview():
    cid = make("Amina", kind="friends").json()["id"]
    join("Amina", cid, "Bilal")
    join("Amina", cid, "Cyra")
    answer("Bilal", "a")
    assert seen_overview("Cyra", cid, "Bilal").json()["attempts"] == 1


def test_an_ancestor_circles_admin_sees_down_and_only_an_admin_may_nest():
    top = make("Dana", "School", "class").json()["id"]
    join("Dana", top, "Eli")                                              # a plain member of the parent
    assert make("Eli", "Room", "class", parent=top).status_code == 403
    assert make("Amina", "Room", "class", parent=top).status_code == 403  # not in the parent at all
    child = make("Dana", "Room 1", "class", parent=top).json()["id"]
    join("Dana", child, "Bilal")
    answer("Bilal", "a")
    assert seen_overview("Dana", child, "Bilal").status_code == 200
    assert seen_overview("Eli", child, "Bilal").status_code == 403
    assert detail("Eli", child).status_code == 403
    client.delete(f"/api/progress/circles/{top}", headers=as_("Dana"))
    assert detail("Dana", child).json()["parent"] is None                 # children lose their parent


def move(who, cid, parent):
    return client.put(f"/api/progress/circles/{cid}/parent", headers=as_(who), json={"parent": parent})


def test_moving_a_circle_inside_another_lets_that_circles_admin_see_it_and_moving_out_takes_it_back():
    top = make("Dana", "School", "class").json()["id"]
    join("Dana", top, "Amina", "admin")
    room = make("Amina", "Room", "class").json()["id"]
    join("Amina", room, "Bilal")
    answer("Bilal", "a")
    assert seen_overview("Dana", room, "Bilal").status_code == 403         # apart, so unseen
    moved = move("Amina", room, top)
    assert moved.status_code == 200 and moved.json()["parent"] == top
    assert move("Amina", room, top).status_code == 200                     # same parent: no-op
    assert seen_overview("Dana", room, "Bilal").json()["attempts"] == 1
    assert [c["id"] for c in detail("Dana", top).json()["inside"]] == [room]
    out = move("Amina", room, None)
    assert out.status_code == 200 and out.json()["parent"] is None
    assert seen_overview("Dana", room, "Bilal").status_code == 403
    assert detail("Dana", top).json()["inside"] == []


def test_a_circle_cannot_go_inside_itself_or_a_circle_inside_it():
    top = make("Dana", "School", "class").json()["id"]
    mid = make("Dana", "Wing", "class", parent=top).json()["id"]
    low = make("Dana", "Room", "class", parent=mid).json()["id"]
    for target in (top, mid, low):
        assert move("Dana", top, target).status_code == 422
    assert move("Dana", mid, low).status_code == 422
    assert [detail("Dana", c).json()["parent"] for c in (top, mid, low)] == [None, top, mid]


def test_only_an_admin_of_both_circles_may_move_one():
    top = make("Dana", "School", "class").json()["id"]
    join("Dana", top, "Eli")                                               # a plain member of the target
    room = make("Amina", "Room", "class").json()["id"]
    join("Amina", room, "Eli", "admin")
    assert move("Amina", room, top).status_code == 403                     # not in the target
    assert move("Eli", room, top).status_code == 403                       # member, not admin, of the target
    assert move("Dana", room, top).status_code == 403                      # admin of the target only
    assert detail("Amina", room).json()["parent"] is None


def test_a_hidden_account_is_absent_from_the_global_ranking_but_sees_its_own_row():
    answer("Amina", "a")
    answer("Bilal", "b")
    assert client.put("/api/progress/account/public", json={"public": False}, headers=as_("Bilal")).status_code == 200
    board = lambda who: client.get(  # noqa: E731
        "/api/progress/leaderboard", params={"module": "quiz"}, headers=as_(who)).json()
    assert [row["name"] for row in board("Amina")["rows"]] == ["amina"]
    assert board("Bilal")["you"]["name"] == "bilal"
    assert "bilal" not in [row["name"] for row in board("Bilal")["rows"]]


def test_the_old_teams_become_circles_with_their_members_invited(tmp_path):
    import sqlite3
    old = sqlite3.connect(tmp_path / "progress.db")
    old.executescript("""
        CREATE TABLE accounts (name TEXT PRIMARY KEY, at TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE teams (team TEXT NOT NULL, member TEXT NOT NULL, at TEXT NOT NULL DEFAULT (datetime('now')),
                            PRIMARY KEY (team, member));
        INSERT INTO accounts (name) VALUES ('coach'), ('amina');
        INSERT INTO teams (team, member) VALUES ('coach', 'amina');
    """)
    old.commit(), old.close()
    progress_store.reset_connection()
    mine = progress_store.my_circles("amina")
    assert [(c["name"], c["kind"], c["role"], c["status"]) for c in mine] == [("coach", "team", "member", "invited")]
    coach = progress_store.my_circles("coach")
    assert [(c["role"], c["status"]) for c in coach] == [("admin", "joined")]
    assert not progress_store._db().execute("SELECT 1 FROM sqlite_master WHERE name = 'teams'").fetchone()


def test_the_last_admin_cannot_leave_while_others_are_in_the_circle():
    cid = make("Amina").json()["id"]
    join("Amina", cid, "Bilal")
    leave = lambda who: client.post(f"/api/progress/circles/{cid}/leave", headers=as_(who))  # noqa: E731
    assert leave("Amina").status_code == 422
    client.put(f"/api/progress/circles/{cid}/members/bilal", json={"role": "admin"}, headers=as_("Amina"))
    assert leave("Amina").status_code == 200
    assert leave("Bilal").status_code == 200                              # alone now: the circle goes with them
    assert detail("Bilal", cid).status_code == 404


def test_the_password_columns_go_from_a_fresh_file_and_from_one_already_at_step_two():
    accounts = lambda: [r[1] for r in progress_store._db().execute("PRAGMA table_info(accounts)")]  # noqa: E731
    assert accounts() == ["name", "at", "public"]                                   # fresh file
    progress_store.reset_connection()
    path = progress_store.data_path("progress_db_path")
    path.unlink()
    for suffix in ("-wal", "-shm"):
        path.with_name(path.name + suffix).unlink(missing_ok=True)
    old = sqlite3.connect(path)
    old.executescript(progress_store.SCHEMA)
    for step, script in enumerate(progress_store.MIGRATIONS[:2], start=1):
        old.executescript(f"BEGIN; {script} PRAGMA user_version = {step}; COMMIT;")
    old.execute("INSERT INTO accounts (name, pass, key) VALUES ('amina', 'p', 'k')")
    old.commit()
    old.close()
    assert progress_store.has_account("amina")                                      # opens, migrates, keeps the row
    assert accounts() == ["name", "at", "public"]


def test_the_overview_counts_every_module_and_the_days_in_a_row():
    signup("Amina")
    db = progress_store._db()
    with db:
        for module, correct, days in [("quiz", 1, 0), ("quiz", 0, 1), ("quiz:ur", 1, 1), ("quiz", 1, 3)]:
            db.execute("INSERT INTO attempts (user, module, item, correct, at) VALUES ('amina', ?, 'a', ?, "
                       "datetime('now', ?))", (module, correct, f"-{days} days"))
    body = client.get("/api/progress/overview", headers=as_("Amina")).json()
    assert [(m["module"], m["attempts"], m["correct"]) for m in body["modules"]] == [("quiz", 3, 2), ("quiz:ur", 1, 1)]
    assert (body["attempts"], body["correct"], body["streak"]) == (4, 3, 2)  # today and yesterday; day 3 is past a gap
    assert client.get("/api/progress/overview").json()["streak"] == 0
