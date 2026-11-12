"""A name alone no longer opens an account (docs/plans/2026-11-11-security.md §5, option B).

Sign-up and log-in set a device token as an HttpOnly cookie, and hand back a recovery code once. What is
checked: a typed name opens nothing it does not hold the token for; the recovery code works once and moves the
account to another browser; accounts from before tokens keep working by name until the first log-in claims
them, are hidden from the ranking meanwhile, and are never claimable by name once claims close; logging out
ends one browser and "everywhere else" the others; nothing kept would open an account if the file leaked; and
another site's page cannot write.

Run: python -m pytest tests/learner/test_device_tokens.py
"""
from __future__ import annotations

import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.identity import cookie_name
from backend.main import app
from backend.scripts import recovery_code
from backend.services.core import audit
from backend.services.learner import journal, progress_db, tokens
from tests.learner import sign_in
from tests.learner.sign_in import as_

client = TestClient(app)


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_db, "data_path", lambda _name: target)
    progress_db.reset_connection()
    sign_in.forget_all()
    yield
    progress_db.reset_connection()


def signup(name):
    return sign_in.signup(client, name)


def login(name, code=None, **more):
    return sign_in.login(client, name, code, **more)


def bare(name):
    """What anyone can send: the name, and no cookie."""
    return as_(None, **{"X-Tafheem-Profile": name})


def account(headers):
    return client.get("/api/progress/account", headers=headers)


def old_account(name):
    """An account from before tokens: a row with no recovery code, and nobody holding a token."""
    db = progress_db.connection()
    with db:
        db.execute("INSERT INTO accounts (name) VALUES (?)", (name,))


def events(kind):
    try:
        with open(get_settings().security_log_path, encoding="utf-8") as handle:
            return [line for line in map(json.loads, handle) if line.get("kind") == kind]
    except FileNotFoundError:
        return []


# Sign-up

def test_sign_up_sets_a_cookie_no_script_can_read_and_shows_a_code_once():
    response = signup("Amina")
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{cookie_name()}=tft_") and cookie_name() == "__Host-tafheem"
    for part in ("HttpOnly", "Secure", "SameSite=strict", "Path=/"):
        assert part.lower() in cookie.lower(), part
    assert "domain" not in cookie.lower()  # __Host-: this host only
    body = response.json()
    assert len(body["recovery"]) == 19 and body["recovery"].count("-") == 3
    assert "tft_" not in response.text  # the token never reaches the page
    assert account(as_("Amina")).json()["proven"] is True


def test_a_typed_name_opens_nothing():
    signup("Amina")
    client.post("/api/progress/attempts", headers=as_("Amina"), json={"module": "quiz", "item": "a", "correct": True})
    for method, path in [("get", "/api/progress/account"), ("get", "/api/progress/summary"),
                         ("get", "/api/progress/overview"), ("post", "/api/progress/attempts"),
                         ("delete", "/api/progress"), ("delete", "/api/progress/account"),
                         ("get", "/api/progress/saved"), ("get", "/api/progress/circles")]:
        response = getattr(client, method)(path, headers=bare("amina"),
                                           **({"json": {"module": "quiz", "item": "b", "correct": True}}
                                              if method == "post" else {}))
        assert response.status_code == 401, path
        assert response.json()["detail"] == "Log in again on this device"
    assert account(as_("Amina")).json()["answers"] == 1  # nothing was wiped


def test_another_accounts_token_opens_nothing():
    signup("Amina"), signup("Bilal")
    borrowed = {"X-Tafheem-Profile": "amina", **sign_in.cookie("bilal")}
    assert account(borrowed).status_code == 401
    assert account({"X-Tafheem-Profile": "amina", "Cookie": f"{cookie_name()}=tft_made-up"}).status_code == 401


# Log-in and the recovery code

def test_the_recovery_code_logs_in_once_and_hands_over_the_next():
    code = signup("Amina").json()["recovery"]
    sign_in.forget_all()  # another phone
    assert login("Amina").status_code == 403
    assert login("Amina").json()["detail"] == "Type this account's recovery code"
    assert login("Amina", "0000-0000-0000-0000").status_code == 403
    moved = login("Amina", code)
    assert moved.status_code == 200 and moved.json()["recovery"] not in (None, code)
    assert account(as_("Amina")).status_code == 200
    sign_in.forget_all()
    assert login("Amina", code).status_code == 403  # spent
    assert login("Amina", moved.json()["recovery"]).status_code == 200
    assert [e["user"] for e in events("login_refused")] == ["amina", "amina"]


def test_a_code_is_read_however_it_was_typed():
    code = signup("Amina").json()["recovery"]
    sign_in.forget_all()
    typed = code.lower().replace("-", " ").replace("0", "o").replace("1", "l")
    assert login("Amina", typed).status_code == 200


def test_a_browser_that_forgot_the_name_but_not_the_cookie_needs_no_code():
    signup("Amina")
    response = login("Amina")
    assert response.status_code == 200 and response.json()["recovery"] is None
    assert "set-cookie" not in response.headers  # the same token stays


def test_a_new_code_retires_the_old_one():
    first = signup("Amina").json()["recovery"]
    second = client.post("/api/progress/recovery", headers=as_("Amina")).json()["code"]
    sign_in.forget_all()
    assert login("Amina", first).status_code == 403
    assert login("Amina", second).status_code == 200
    assert client.post("/api/progress/recovery", headers=bare("amina")).status_code == 401


def test_a_spent_code_logs_in_nobody():
    code = signup("Amina").json()["recovery"]
    assert tokens.recover("amina", code) is not None
    assert tokens.recover("amina", code) is None


def test_two_devices_typing_one_code_at_once_log_in_one(monkeypatch):
    code = signup("Amina").json()["recovery"]
    # Every device checks the code before any of them spends it: only the compare-and-set can pick one.
    devices = 6
    together = threading.Barrier(devices)
    real = tokens._opens

    def checked_then_wait(sealed, typed):
        opened = real(sealed, typed)
        together.wait(timeout=10)
        return opened

    monkeypatch.setattr(tokens, "_opens", checked_then_wait)
    with ThreadPoolExecutor(devices) as pool:
        results = list(pool.map(lambda _: tokens.recover("amina", code), range(devices)))
    assert sum(result is not None for result in results) == 1
    assert progress_db.connection().execute("SELECT COUNT(*) FROM tokens").fetchone()[0] == 2  # sign-up's, the winner's


def test_an_old_session_makes_a_new_code_only_with_the_current_one():
    code = signup("Amina").json()["recovery"]
    db = progress_db.connection()
    with db:  # this browser logged in an hour ago: a script on the page could be the one asking
        db.execute("UPDATE tokens SET at = datetime('now', '-1 hour')")
    asked = client.post("/api/progress/recovery", headers=as_("Amina"))
    assert asked.status_code == 403 and asked.json()["detail"] == "Type your current recovery code to make a new one"
    wrong = client.post("/api/progress/recovery", headers=as_("Amina"), json={"code": "0000-0000-0000-0000"})
    assert wrong.status_code == 403 and [e["user"] for e in events("recovery_refused")] == ["amina"]
    new = client.post("/api/progress/recovery", headers=as_("Amina"), json={"code": code.lower()})
    assert new.status_code == 200 and new.json()["code"] != code
    assert [e["by"] for e in events("recovery_new")] == ["code"]
    sign_in.forget_all()
    assert login("Amina", code).status_code == 403
    assert login("Amina", new.json()["code"]).status_code == 200


# Logging out

def test_logging_out_ends_this_browser_and_only_this_one():
    code = signup("Amina").json()["recovery"]
    phone = as_("Amina")
    sign_in.forget_all()
    login("Amina", code)
    laptop = as_("Amina")
    response = client.delete("/api/progress/session", headers=phone)
    assert response.status_code == 200
    assert 'max-age=0' in response.headers["set-cookie"].lower() or "expires" in response.headers["set-cookie"].lower()
    assert account(phone).status_code == 401
    assert account(laptop).status_code == 200


def test_logging_out_everywhere_else_keeps_this_browser():
    code = signup("Amina").json()["recovery"]
    phone = as_("Amina")
    sign_in.forget_all()
    login("Amina", code)
    laptop = as_("Amina")
    assert client.delete("/api/progress/sessions", headers=laptop).json() == {"deleted": 1}
    assert account(phone).status_code == 401
    assert account(laptop).status_code == 200


def test_reading_the_account_renews_the_cookie():
    signup("Amina")
    held = sign_in.cookie("amina")["Cookie"].split("=", 1)[1]
    renewed = account(as_("Amina"))
    assert renewed.json()["proven"] is True
    assert renewed.cookies.get(cookie_name()) == held and "Max-Age=31536000" in renewed.headers["set-cookie"]


def test_a_code_log_in_drops_the_token_this_browser_held_for_another_account():
    code = signup("Bilal").json()["recovery"]
    signup("Amina")
    amina = as_("Amina")
    moved = client.post("/api/progress/login", json={"code": code, "shows_code": True},
                        headers={"X-Tafheem-Profile": "bilal", **sign_in.cookie("amina")})
    assert moved.status_code == 200
    assert account(amina).status_code == 401


def test_on_plain_http_the_cookie_is_not_secure(monkeypatch):
    monkeypatch.setattr(get_settings(), "cookie_secure", False)
    response = client.post("/api/progress/signup", json={"shows_code": True}, headers={"X-Tafheem-Profile": "amina"})
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("tafheem=tft_") and "secure" not in cookie.lower() and "HttpOnly" in cookie
    token = response.cookies.get("tafheem")
    assert account({"X-Tafheem-Profile": "amina", "Cookie": f"tafheem={token}"}).json()["proven"] is True


def test_logging_in_as_someone_else_drops_the_old_token():
    signup("Amina")
    amina = as_("Amina")
    signup_as_bilal = client.post("/api/progress/signup", json={"keep": False, "shows_code": True},
                                  headers={"X-Tafheem-Profile": "bilal", **sign_in.cookie("amina")})
    assert signup_as_bilal.status_code == 200
    assert account(amina).status_code == 401  # one browser, one account: Amina's token went


def test_a_deleted_name_signed_up_again_starts_with_no_old_tokens():
    signup("Amina")
    old = as_("Amina")
    deleted = client.delete("/api/progress/account", headers=old)
    assert "Max-Age=0" in deleted.headers["set-cookie"]  # the browser's cookie goes with the account
    sign_in.forget_all()
    signup("Amina")
    assert account(old).status_code == 401
    assert progress_db.connection().execute("SELECT COUNT(*) FROM tokens").fetchone()[0] == 1


# Accounts from before tokens

def test_an_old_account_reads_by_name_until_its_first_log_in_claims_it():
    old_account("amina")
    assert account(bare("amina")).json()["proven"] is False  # the page then logs in, which claims it
    assert client.post("/api/progress/attempts", headers=bare("amina"),
                       json={"module": "quiz", "item": "a", "correct": True}).status_code == 200
    claimed = login("Amina", **{"User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) Chrome/150"})
    assert claimed.status_code == 200 and claimed.json()["recovery"]
    assert [(e["user"], e["device"]) for e in events("token_claimed")] == [("amina", "Android")]
    assert account(bare("amina")).status_code == 401
    assert account(as_("Amina")).json()["proven"] is True
    sign_in.forget_all()
    assert login("Amina").status_code == 403  # a second claimer needs the code


def test_wiping_deleting_and_circles_need_the_token_even_for_an_old_account():
    old_account("amina")
    for method, path in [("delete", "/api/progress"), ("delete", "/api/progress/account"),
                         ("get", "/api/progress/circles"), ("post", "/api/progress/recovery"),
                         ("delete", "/api/progress/session"), ("get", "/api/progress/saved")]:
        assert getattr(client, method)(path, headers=bare("amina")).status_code == 401, path
    assert client.put("/api/progress/saved", headers=bare("amina"), json={"data": {}}).status_code == 401
    assert client.put("/api/progress/account/public", headers=bare("amina"), json={"public": False}).status_code == 401


def test_a_circles_ranking_needs_the_token():
    signup("Amina")
    made = client.post("/api/progress/circles", headers=as_("Amina"), json={"name": "Class", "kind": "class"})
    assert made.status_code == 200, made.text
    ranking = f"/api/progress/leaderboard?module=quiz&circle={made.json()['id']}"
    assert client.get(ranking, headers=bare("amina")).status_code == 401
    assert client.get(ranking, headers=as_("Amina")).status_code == 200


def test_an_unclaimed_name_is_not_in_the_ranking():
    old_account("amina")
    signup("Bilal")
    names = lambda: [r["name"] for r in client.get("/api/progress/leaderboard", headers=as_("Bilal")).json()["rows"]]  # noqa: E731
    assert names() == ["bilal"]
    login("Amina")
    assert sorted(names()) == ["amina", "bilal"]


def test_once_claims_close_an_old_name_opens_nothing_until_the_owner_makes_a_code(monkeypatch, capsys):
    monkeypatch.setattr(get_settings(), "account_claims_open", False)
    old_account("amina")
    assert account(bare("amina")).status_code == 401
    assert login("Amina").status_code == 403
    assert recovery_code.main(["Amina"]) == 0
    code = capsys.readouterr().out.strip()
    assert login("Amina", code).status_code == 200
    assert [e["user"] for e in events("recovery_by_owner")] == ["amina"]


def test_the_owners_new_code_logs_every_device_out_unless_told_not_to(capsys):
    signup("Amina")
    taker = as_("Amina")
    assert recovery_code.main(["amina", "--keep-devices"]) == 0
    assert account(taker).status_code == 200
    assert recovery_code.main(["amina"]) == 0
    assert account(taker).status_code == 401  # nor can the taker make themselves a new code
    assert [e["devices_logged_out"] for e in events("recovery_by_owner")] == [0, 1]
    assert recovery_code.main(["nobody"]) == 1


# What is kept

def test_nothing_kept_would_open_an_account():
    response = signup("Amina")
    token, code = response.cookies.get(cookie_name()), response.json()["recovery"]
    dump = "\n".join(progress_db.connection().iterdump())
    assert token not in dump and code not in dump and code.replace("-", "") not in dump


def test_a_token_in_an_error_message_is_scrubbed():
    assert "tft_" not in journal.scrub("failed for tft_abcDEF-123_x")


def test_an_answer_to_a_browser_with_a_cookie_is_never_cached():
    response = client.get("/api/sources", headers={"Cookie": f"{cookie_name()}=tft_x"})
    assert response.headers["cache-control"] in ("private, no-store", "public, max-age=86400")
    response = client.get("/api/progress/summary", headers={"Cookie": f"{cookie_name()}=tft_x"})
    assert response.headers["cache-control"] == "private, no-store"


def test_idle_tokens_are_swept_with_idle_guests():
    signup("Amina")
    db = progress_db.connection()
    with db:
        db.execute("UPDATE tokens SET used = datetime('now', '-200 days')")
    assert tokens.sweep(180) == 1
    assert account(as_("Amina")).status_code == 401


def test_a_days_use_is_written_once():
    signup("Amina")
    db = progress_db.connection()
    with db:
        db.execute("UPDATE tokens SET used = datetime('now', '-3 days')")
    account(as_("Amina"))
    fresh = db.execute("SELECT used > datetime('now', '-1 hour') FROM tokens").fetchone()[0]
    assert fresh == 1


def test_an_old_file_gains_the_token_table_and_keeps_its_accounts(tmp_path):
    progress_db.reset_connection()
    path = progress_db.data_path("progress_db_path")
    path.unlink(missing_ok=True)
    old = sqlite3.connect(path)
    old.executescript(progress_db.SCHEMA)
    for step, script in enumerate(progress_db.MIGRATIONS[:3], start=1):
        old.executescript(f"BEGIN; {script} PRAGMA user_version = {step}; COMMIT;")
    old.execute("INSERT INTO accounts (name) VALUES ('amina')")
    old.commit()
    old.close()
    assert not tokens.claimed("amina")
    assert login("Amina").status_code == 200


# Another site's page

@pytest.mark.parametrize("site, status", [("cross-site", 403), ("Cross-Site", 403), ("same-site", 403),
                                          ("same-origin", 404), ("none", 404), (None, 404)])
def test_another_sites_page_cannot_write(site, status):
    """same-site too: the server's sslip.io name is not a public suffix, so any x.sslip.io is "the same site"."""
    headers = {"Sec-Fetch-Site": site} if site else {}
    headers["X-Tafheem-Profile"] = "nobody"
    assert client.post("/api/progress/login", headers=headers).status_code == status
    assert len(events("cross_site_write")) == (status == 403)


def test_another_sites_page_can_still_read():
    assert client.get("/api/sources", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200


@pytest.mark.parametrize("agent, kind", [
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1", "iPhone"),
    ("Mozilla/5.0 (Linux; Android 15; SM-S928B) AppleWebKit/537.36 Chrome/150 Mobile Safari/537.36", "Android"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/150 Safari/537.36", "Windows"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/19.0 Safari/605.1.15", "Mac"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0", "Linux"),
    ("curl/8.9.1", "other"), (None, "other"),
])
def test_a_claim_records_the_device_family_only(agent, kind):
    assert audit.device_kind(agent) == kind


# A page from before codes (auditor round 10): it never shows a code, so none is made for it

def test_an_old_page_signs_up_an_account_its_browser_holds_and_the_new_page_makes_its_first_code():
    old = sign_in.signup(client, "Amina", shows_code=False)
    assert old.status_code == 200 and old.json()["recovery"] is None  # no code that nobody would see
    held = as_("Amina")  # but the browser holds the account: nobody else can claim it (auditor round 11)
    assert tokens.claimed("amina") and not tokens.has_code("amina")
    sign_in.forget_all()
    assert login("Amina").status_code == 403  # another browser, even a new page, needs a code that does not exist
    assert account(bare("amina")).status_code == 401  # and no name-only access either
    seen = account(held).json()
    assert seen["proven"] is True and seen["has_code"] is False  # the new page, on its next load here
    first = client.post("/api/progress/recovery", headers=held).json()["code"]  # any age of token: none existed
    assert tokens.has_code("amina") and account(held).json()["has_code"] is True
    assert client.post("/api/progress/recovery", headers=held).status_code == 200  # minted moments ago: fresh
    assert login("Amina", code=first).status_code == 403  # and the first code was replaced by that one


def test_an_old_pages_account_needs_the_current_code_once_it_has_one():
    sign_in.signup(client, "Amina", shows_code=False)
    held = as_("Amina")
    db = progress_db.connection()
    with db:
        db.execute("UPDATE tokens SET at = datetime('now', '-1 hour')")
    assert client.post("/api/progress/recovery", headers=held).status_code == 200  # the first, without
    assert client.post("/api/progress/recovery", headers=held).status_code == 403  # the next, only with it


def test_an_old_page_in_a_browser_holding_another_account_drops_that_token():
    signup("Alpha")
    alpha = as_("Alpha")
    old_account("beta")
    old = client.post("/api/progress/login", json={}, headers={"X-Tafheem-Profile": "beta", **sign_in.cookie("alpha")})
    assert old.status_code == 200 and "Max-Age=0" in old.headers["set-cookie"]
    assert account(alpha).status_code == 401  # one browser, one account


def test_log_in_counts_names_asked_without_a_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "names_per_minute", 2)
    from backend.services.core import ratelimit
    monkeypatch.setattr(ratelimit.NAMELESS, "asked", {})
    monkeypatch.setattr(ratelimit.NAMELESS, "all", {})
    codes = [sign_in.login(client, n, shows_code=False).status_code for n in ("a1", "a2", "a3")]
    assert codes == [404, 404, 429]


def test_an_old_page_logging_in_to_an_unclaimed_account_claims_nothing():
    old_account("amina")
    old = sign_in.login(client, "Amina", shows_code=False)
    assert old.status_code == 200 and old.json()["recovery"] is None and cookie_name() not in old.cookies
    assert not tokens.claimed("amina")
    assert [e["by"] for e in events("login")] == ["name"]


def test_an_old_page_still_needs_the_code_for_a_claimed_account():
    signup("Amina")
    sign_in.forget_all()
    assert sign_in.login(client, "Amina", shows_code=False).status_code == 403


def test_with_claims_closed_an_old_page_still_makes_no_code_nobody_sees(monkeypatch):
    monkeypatch.setattr(get_settings(), "account_claims_open", False)
    old = sign_in.signup(client, "Amina", shows_code=False)
    assert old.json()["recovery"] is None and tokens.claimed("amina") and not tokens.has_code("amina")
    assert account(as_("Amina")).json()["has_code"] is False  # the new page makes and shows the first


def test_only_the_first_tab_makes_the_first_code_the_others_do_not_replace_it():
    sign_in.signup(client, "Amina", shows_code=False)
    tab = as_("Amina")
    first = client.post("/api/progress/recovery", json={"first": True}, headers=tab)
    again = client.post("/api/progress/recovery", json={"first": True}, headers=tab)
    assert first.status_code == 200 and again.status_code == 409
    sign_in.forget_all()
    assert login("Amina", code=first.json()["code"]).status_code == 200  # the one shown still works


# Asking about many names without a token: which exist, which can be claimed

def test_one_visitor_may_name_only_a_few_usernames_a_minute_without_a_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "names_per_minute", 3)
    from backend.services.core import ratelimit
    monkeypatch.setattr(ratelimit.NAMELESS, "asked", {})
    monkeypatch.setattr(ratelimit.NAMELESS, "all", {})
    old_account("amina")
    assert all(account(bare("amina")).status_code == 200 for _ in range(10))  # one name, however often
    assert [account(bare(n)).status_code for n in ("nobody1", "nobody2", "nobody3")] == [401, 401, 429]
    signup("Bilal")
    assert account(as_("Bilal")).status_code == 200  # a browser with its cookie is not counted


def test_a_cross_site_refusal_logs_the_area_not_the_path():
    client.post("/api/progress/circles/1/members/somechild", headers={"Sec-Fetch-Site": "cross-site"})
    [line] = events("cross_site_write")
    assert line["area"] == "/api/progress" and "somechild" not in json.dumps(line)


def test_the_name_limit_has_a_ceiling_a_forged_address_does_not_pass(monkeypatch):
    monkeypatch.setattr(get_settings(), "names_all_per_minute", 3)
    from backend.services.core import ratelimit
    monkeypatch.setattr(ratelimit.NAMELESS, "asked", {})
    monkeypatch.setattr(ratelimit.NAMELESS, "all", {})
    codes = [account({"X-Tafheem-Profile": f"n{i}", "X-Real-IP": f"203.0.113.{i}"}).status_code for i in range(5)]
    assert codes == [401, 401, 401, 429, 429]


def test_a_flood_of_addresses_evicts_the_oldest_and_resets_nobody(monkeypatch):
    from backend.services.core import ratelimit
    names = ratelimit.Names("names_per_minute", "names_all_per_minute")
    monkeypatch.setattr(get_settings(), "names_per_minute", 1)
    assert not names.too_many("victim-probe", "x") and names.too_many("victim-probe", "y")
    for i in range(10_001):
        names.too_many(f"a{i}", "z")
    assert "victim-probe" not in names.asked and len(names.asked) <= 10_001  # evicted, oldest first
    names.too_many("prober", "p")
    assert names.too_many("prober", "q")  # still counted after the flood


def test_a_flood_of_addresses_does_not_reset_the_ceiling(monkeypatch):
    from backend.services.core import ratelimit
    names = ratelimit.Names("names_per_minute", "names_all_per_minute")
    monkeypatch.setattr(get_settings(), "names_all_per_minute", 2)
    assert not names.too_many("a", "x") and not names.too_many("b", "y") and names.too_many("c", "z")
    for i in range(10_002):
        names.too_many(f"f{i}", "w")  # refused, but each forged address is a visitor entry
    assert names.too_many("d", "v")  # the ceiling is still full


def test_the_name_limit_holds_under_threads(monkeypatch):
    from backend.services.core import ratelimit
    names = ratelimit.Names("names_per_minute", "names_all_per_minute")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda i: [names.too_many("one", f"{i}-{j}") for j in range(300)], range(8)))  # no RuntimeError
