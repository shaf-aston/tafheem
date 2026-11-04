"""Who is asking: the username a request carries, for any router that needs it.

The page sends the username in the X-Tafheem-Profile header, percent-encoded
because a header cannot carry Arabic. Sign-up and log-in are by username only,
no password; that is agreed. Nobody logged in is the guest record of the device the page names in
X-Tafheem-Guest (docs/plans/2026-10-24-device-guest.md); no header at all is the old shared one.

A FastAPI dependency, not middleware: only the routes that read or write one
learner's record ask for it, so the Qur'an, dictionary and the rest never pay
for a lookup. This file is a thin adapter: it only pulls the two headers off the
request and turns a bad one into a 422. The whole guest-to-account lifecycle --
what a header means, the spelling rules, and sign-up's "keep" merge -- is owned
by services/learner/identity.py (see its docstring for the full picture).
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from backend.services.learner.identity import has_account, resolve_device, resolve_name
from backend.services.learner.username import GUEST, is_guest

PROFILE_HEADER = "X-Tafheem-Profile"
GUEST_HEADER = "X-Tafheem-Guest"


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


def _signed_up(name: str) -> str:
    """Refused unless signed up, so a deleted account files nothing."""
    if not has_account(name):
        raise HTTPException(status_code=401, detail="Log in again: no account with that username")
    return name


def current_user(name: str = Depends(typed_name)) -> str:
    """A guest record, or a signed-up name."""
    return name if is_guest(name) else _signed_up(name)


def own_record(user: str = Depends(current_user)) -> str:
    """`current_user`, but never the old shared record: XP and streak are one learner's, and that record is many."""
    if user == GUEST:
        raise HTTPException(status_code=422, detail="Not a device id")
    return user


def named(name: str = Depends(typed)) -> str:
    """A signed-up name, never the guest: for routes about one account."""
    return _signed_up(name)


USER = Depends(current_user)
OWN = Depends(own_record)
DEVICE = Depends(guest)
TYPED = Depends(typed)
NAMED = Depends(named)
