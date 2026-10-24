"""Who is asking: the username a request carries, for any router that needs it.

The page sends the username in the X-Tafheem-Profile header, percent-encoded
because a header cannot carry Arabic. Sign-up and log-in are by username only,
no password; that is agreed. Nobody logged in is the guest record of the device the page names in
X-Tafheem-Guest (docs/plans/2026-10-24-device-guest.md); no header at all is the old shared one.

A FastAPI dependency, not middleware: only the routes that read or write one
learner's record ask for it, so the Qur'an, dictionary and the rest never pay
for a lookup. The spelling rules live in services/learner/username.py, the accounts
table in services/learner/progress_store.py; this file only joins them to a request.
"""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import Depends, Header, HTTPException

from backend.services.learner import progress_store
from backend.services.learner.username import GUEST, clean_name, device_key, is_guest

PROFILE_HEADER = "X-Tafheem-Profile"
GUEST_HEADER = "X-Tafheem-Guest"


def _device(sent: str | None) -> str:
    if sent is None:
        return GUEST
    try:
        return device_key(sent)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def guest(sent: str | None = Header(None, alias=GUEST_HEADER)) -> str:
    """This device's guest record, or the shared one when the page names no device."""
    return _device(sent)


def typed_name(sent: str | None = Header(None, alias=PROFILE_HEADER),
               device: str | None = Header(None, alias=GUEST_HEADER)) -> str:
    """The cleaned name from the header, or the device's guest record when there is none.
    A name wins, so the device id is not even read for someone logged in."""
    if sent is None:
        return _device(device)
    try:
        return clean_name(unquote(sent))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def typed(name: str = Depends(typed_name)) -> str:
    """`typed_name`, but a guest record is refused: sign-up and log-in need a name typed."""
    if is_guest(name):
        raise HTTPException(status_code=422, detail="Type a username")
    return name


def _signed_up(name: str) -> str:
    """Refused unless signed up, so a deleted account files nothing."""
    if not progress_store.has_account(name):
        raise HTTPException(status_code=401, detail="Log in again: no account with that username")
    return name


def current_user(name: str = Depends(typed_name)) -> str:
    """A guest record, or a signed-up name."""
    return name if is_guest(name) else _signed_up(name)


def named(name: str = Depends(typed)) -> str:
    """A signed-up name, never the guest: for routes about one account."""
    return _signed_up(name)


USER = Depends(current_user)
DEVICE = Depends(guest)
TYPED = Depends(typed)
NAMED = Depends(named)
