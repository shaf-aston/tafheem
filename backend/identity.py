"""Who is asking: the username a request carries, for any router that needs it.

The page sends the username in the X-Tafheem-Profile header, percent-encoded
because a header cannot carry Arabic. The browser proves it with the device token sign-up or log-in set as
a cookie (services/learner/tokens.py; still no password, that is agreed): HttpOnly, so no script on the page
can read it, SameSite=Strict, so no other site's page can send it (and services/core/headers.SameOrigin
refuses a cross-site write besides), and __Host-, so only this host can set it. Not a token in localStorage:
one script-injection bug would hand every reader's token out, and Safari wipes script storage after a week
away (docs/plans/2026-11-11-security.md §5). A name with a missing or wrong token is a 401 that tells the page
to log in again.
Nobody logged in is the guest record of the device the page names in
X-Tafheem-Guest (docs/plans/2026-10-24-device-guest.md); no header at all is the old shared one.

A FastAPI dependency, not middleware: only the routes that read or write one
learner's record ask for it, so the Qur'an, dictionary and the rest never pay
for a lookup. This file is a thin adapter: it only pulls the two headers off the
request and turns a bad one into a 422. The whole guest-to-account lifecycle --
what a header means, the spelling rules, and sign-up's "keep" merge -- is owned
by services/learner/identity.py (see its docstring for the full picture).
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, Response

from backend.config import get_settings

from backend.services.learner.identity import NOT_PROVEN, refused, resolve_device, resolve_name
from backend.services.learner.username import GUEST, is_guest

PROFILE_HEADER = "X-Tafheem-Profile"
GUEST_HEADER = "X-Tafheem-Guest"
# A year: a reader who opens the app now and then is never logged out by the cookie running out. The token
# itself goes after progress_guest_days unused (tokens.sweep).
_COOKIE_DAYS = 365


def guest(sent: str | None = Header(None, alias=GUEST_HEADER)) -> str:
    """This device's guest record, or the shared one when the page names no device."""
    try:
        return resolve_device(sent)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def typed_name(sent: str | None = Header(None, alias=PROFILE_HEADER),
               device: str | None = Header(None, alias=GUEST_HEADER)) -> str:
    """The cleaned name from the header, or the device's guest record when there is none.
    A name wins, so the device id is not even read for someone logged in."""
    try:
        return resolve_name(sent, device)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def typed(name: str = Depends(typed_name)) -> str:
    """`typed_name`, but a guest record is refused: sign-up and log-in need a name typed."""
    if is_guest(name):
        raise HTTPException(status_code=422, detail="Type a username")
    return name


def _log_in_again(why: str) -> HTTPException:
    """The one answer that means "this browser is not logged in as that name": the page logs out on it."""
    return HTTPException(status_code=401, detail=why)


def cookie_name() -> str:
    """__Host- needs Secure, and a browser keeps no Secure cookie from plain http (a dev server on a LAN
    address), so a dev server with `cookie_secure` off uses the bare name."""
    return "__Host-tafheem" if get_settings().cookie_secure else "tafheem"


def device_token(request: Request) -> str | None:
    """This browser's device token, or None when it holds none."""
    return request.cookies.get(cookie_name()) or None


def give_token(response: Response, token: str) -> None:
    """Hand this browser its device token, where the page's scripts cannot reach it."""
    response.set_cookie(cookie_name(), token, max_age=_COOKIE_DAYS * 86400, path="/", httponly=True,
                        secure=get_settings().cookie_secure, samesite="strict")


def take_token(response: Response) -> None:
    """Make this browser forget its device token."""
    response.delete_cookie(cookie_name(), path="/", httponly=True, secure=get_settings().cookie_secure,
                           samesite="strict")


def _signed_up(name: str, token: str | None, strict: bool = False) -> str:
    """Refused unless signed up and proven, so a deleted account files nothing and a typed name opens nothing.
    (`strict` and the one exception for accounts from before tokens: services/learner/identity.refused.)"""
    if why := refused(name, token, strict):
        raise _log_in_again(why)
    return name


def current_user(name: str = Depends(typed_name), token: str | None = Depends(device_token)) -> str:
    """A guest record, or a signed-up name with its device's token."""
    return name if is_guest(name) else _signed_up(name, token)


def proven_user(name: str = Depends(typed_name), token: str | None = Depends(device_token)) -> str:
    """`current_user`, but a name always needs its token: for wiping a record."""
    return name if is_guest(name) else _signed_up(name, token, strict=True)


def own_record(user: str = Depends(current_user)) -> str:
    """`current_user`, but never the old shared record: XP and streak are one learner's, and that record is many."""
    if user == GUEST:
        raise HTTPException(status_code=422, detail="Not a device id")
    return user


def named(name: str = Depends(typed), token: str | None = Depends(device_token)) -> str:
    """A signed-up name, never the guest: for routes about one account."""
    return _signed_up(name, token)


def proven(name: str = Depends(typed), token: str | None = Depends(device_token)) -> str:
    """`named`, but always with its token: for changing or deleting the account, and for circles."""
    return _signed_up(name, token, strict=True)


def prove(name: str, token: str | None) -> str:
    """`proven` inside a route that needs it only sometimes (the leaderboard, when it is a circle's)."""
    return _signed_up(name, token, strict=True)


def session(name: str = Depends(proven), token: str | None = Depends(device_token)) -> tuple[str, str]:
    """The account and this device's own token: for logging this device out, the others out, or a new
    recovery code. (`proven` already refuses a name without one; this says so where the token is used.)"""
    if token is None:
        raise _log_in_again(NOT_PROVEN)
    return name, token


USER = Depends(current_user)
OWN = Depends(own_record)
DEVICE = Depends(guest)
TYPED = Depends(typed)
NAMED = Depends(named)
PROVEN_USER = Depends(proven_user)
PROVEN = Depends(proven)
SESSION = Depends(session)
TOKEN = Depends(device_token)
