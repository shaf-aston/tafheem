"""Who is asking: the username a request carries, for any router that needs it.

The page sends the username in the X-Tafheem-Profile header, percent-encoded
because a header cannot carry Arabic. Sign-up and log-in are by username only,
no password; that is agreed. No header is the shared guest record.

A FastAPI dependency, not middleware: only the routes that read or write one
learner's record ask for it, so the Qur'an, dictionary and the rest never pay
for a lookup. The spelling rules live in services/username.py, the accounts
table in services/progress_store.py; this file only joins them to a request.
"""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import Depends, Header, HTTPException

from backend.services import progress_store
from backend.services.username import GUEST, clean_name


def typed_name(x_tafheem_profile: str | None = Header(None)) -> str:
    """The cleaned name from the header, or the guest record when there is none."""
    if x_tafheem_profile is None:
        return GUEST
    try:
        return clean_name(unquote(x_tafheem_profile))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def typed(name: str = Depends(typed_name)) -> str:
    """`typed_name`, but the guest record is refused: sign-up and log-in need a name typed."""
    if name == GUEST:
        raise HTTPException(status_code=422, detail="Type a username")
    return name


def _signed_up(name: str) -> str:
    """Refused unless signed up, so a deleted account files nothing."""
    if not progress_store.has_account(name):
        raise HTTPException(status_code=401, detail="Log in again: no account with that username")
    return name


def current_user(name: str = Depends(typed_name)) -> str:
    """The guest record, or a signed-up name."""
    return name if name == GUEST else _signed_up(name)


def named(name: str = Depends(typed)) -> str:
    """A signed-up name, never the guest: for routes about one account."""
    return _signed_up(name)


USER = Depends(current_user)
TYPED = Depends(typed)
NAMED = Depends(named)
