"""Who is asking: the username a request carries, for any router that needs it.

The page sends the username in the X-Tafheem-Profile header, percent-encoded
because a header cannot carry Arabic. Sign-up and log-in are by username only,
no password; that is agreed. No header is the shared guest record.

A FastAPI dependency, not middleware: only the routes that read or write one
learner's record ask for it, so the Qur'an, dictionary and the rest never pay
for a lookup. The spelling rules live in services/profile.py, the accounts table
in services/progress_store.py; this file only joins them to a request.
"""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import Depends, Header, HTTPException

from backend.services import progress_store
from backend.services.profile import clean_name

GUEST = "local"


def typed_name(x_tafheem_profile: str | None = Header(None)) -> str:
    """The cleaned name from the header, or the guest record when there is none."""
    if x_tafheem_profile is None:
        return GUEST
    try:
        return clean_name(unquote(x_tafheem_profile))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def current_user(name: str = Depends(typed_name)) -> str:
    """`typed_name`, refused unless it was signed up, so a deleted account files nothing."""
    if name != GUEST and not progress_store.has_account(name):
        raise HTTPException(status_code=401, detail="Log in again: no account with that username")
    return name


def named(name: str = Depends(current_user)) -> str:
    """`current_user`, but the guest record is refused: for routes about one account."""
    if name == GUEST:
        raise HTTPException(status_code=422, detail="Type a username")
    return name


USER = Depends(current_user)
TYPED = Depends(typed_name)
NAMED = Depends(named)
