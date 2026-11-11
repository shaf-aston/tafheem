"""Being a logged-in learner in a test: the name header plus the device-token cookie a sign-up or log-in set.

The cookie is Secure and the test client talks plain http, so it would never send it back by itself; and one
client plays several learners at once. So each name's token is kept here and sent by hand (`as_`).
"""
from __future__ import annotations

from urllib.parse import quote

from backend.identity import cookie_name
from backend.services.learner.username import clean_name

_held: dict[str, str] = {}


def forget_all() -> None:
    """A fresh database: nobody holds a token."""
    _held.clear()


def keep(name: str, response) -> None:
    """Hold whatever token this answer set, under the name it was for (the server's spelling)."""
    if response.status_code == 200 and (token := response.cookies.get(cookie_name())):
        _held[response.json()["name"]] = token


def cookie(name: str) -> dict[str, str]:
    try:
        token = _held.get(clean_name(name))
    except ValueError:  # not a name: the test is about the refusal
        token = None
    return {"Cookie": f"{cookie_name()}={token}"} if token else {}


def as_(name: str | None, **more: str) -> dict[str, str]:
    """The headers the page sends for `name`, its cookie included once it signed up or logged in here."""
    if name is None:
        return dict(more)
    return {"X-Tafheem-Profile": quote(name), **cookie(name), **more}


def signup(client, name: str, keep_answers: bool = False, **more: str):
    response = client.post("/api/progress/signup", json={"keep": keep_answers}, headers=as_(name, **more))
    keep(name, response)
    return response


def login(client, name: str, code: str | None = None, **more: str):
    body = {"code": code} if code else {}
    response = client.post("/api/progress/login", json=body, headers=as_(name, **more))
    keep(name, response)
    return response
