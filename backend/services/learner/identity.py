"""Who this learner's answers are filed under, start to finish.

The one module that owns the guest -> account lifecycle end to end, so answering
"what happens to my guest answers when I sign up" never needs identity.py,
username.py, progress_store.py and routers/progress.py read together.

Three kinds of "who" a request can be about:

- The shared legacy guest (``GUEST``, ``"local"``): a request with no device header
  at all, from a page cached before devices had ids. It is everyone's and nobody's
  record, mixing many guests' answers together, so it never merges, never earns
  XP, and is never swept.
- A per-device guest (``services.learner.username.DEVICE`` + 32 lowercase hex, e.g.
  ``"guest:<id>"``): one record per device, made the moment a page sends its own
  ``X-Tafheem-Guest`` header. Isolated from every other device and from the legacy
  record. Idle ones are cleaned up by ``progress_store.sweep_guests``.
- A real signed-up account: a ``clean_name``'d username with a row in ``accounts``.

The lifecycle's one seam is sign-up's "keep" (``merge``): it moves a device's own
guest answers and feedback onto the account just created, and nothing else -- never
another device's, and never the legacy record's, since that record holds many
guests' answers mixed together and no single signer could honestly claim them.

``backend/identity.py`` is a thin FastAPI adapter: it only pulls the two headers
(``X-Tafheem-Profile``, ``X-Tafheem-Guest``) off the request and hands them to
``resolve_device``/``resolve_name`` here, turning a ``ValueError`` into a 422.
Everything that decides what those headers *mean* lives here, in
``services/learner/username.py`` (the spelling and shape rules: ``clean_name``,
``device_key``, ``is_guest``, ``GUEST``, ``DEVICE``) and in
``services/learner/progress_store.py`` (the rows themselves: ``claim_guest``,
``sweep_guests``, ``has_account``).
"""
from __future__ import annotations

from urllib.parse import unquote

from backend.services.learner import progress_store
from backend.services.learner.username import GUEST, clean_name, device_key, is_guest

__all__ = ["GUEST", "is_guest", "resolve_device", "resolve_name", "has_account", "merge"]


def resolve_device(sent: str | None) -> str:
    """This device's guest record key, or the legacy shared record when the page names no device.

    Raises ValueError when `sent` is not 32 lowercase hex.
    """
    return GUEST if sent is None else device_key(sent)


def resolve_name(sent: str | None, device: str | None) -> str:
    """The cleaned name from the profile header, or `resolve_device(device)` when there is none.

    A name wins, so a malformed device id never blocks someone logged in: the device
    header is not even read once a name is sent.
    """
    return resolve_device(device) if sent is None else clean_name(unquote(sent))


def has_account(name: str) -> bool:
    """Whether `name` is a signed-up account. False for the legacy guest and any device record too."""
    return progress_store.has_account(name)


def merge(device: str, account: str) -> None:
    """Sign-up's "keep": move `device`'s guest answers and feedback onto the account just made.

    A no-op when `device` is the legacy shared record (no header was sent): it holds
    many guests' answers mixed together, not this signer's own, so "keep" from a page
    that names no device takes nothing.
    """
    if device != GUEST:
        progress_store.claim_guest(account, device)
