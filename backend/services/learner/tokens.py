"""What proves a request comes from an account's owner: a device token, and a recovery code to get a new one.

Still no password (docs/plans/2026-11-11-security.md §5, option B). Signing up or logging in gives:

- a **device token**, one per browser, in an HttpOnly cookie the page's own scripts cannot read
  (backend/identity.py). Logging out on one phone ends that phone's and nobody else's. A token not used for
  ``progress_guest_days`` is swept with the idle guest records;
- a **recovery code**, shown once, which logs the account in on another device (or this one, once the browser
  has forgotten its cookie). It works once: using it hands that device its own token and shows a new code.

The token is 256 random bits, so a plain SHA-256 is the right thing to keep: a slow hash buys nothing against a
secret nobody chose. The recovery code is 80 bits, short enough to copy by hand, so it is kept as a salted
scrypt, as NIST SP 800-63B asks of a secret under 112 bits. A copy of progress.db opens no account.

Accounts made before tokens existed have no recovery code (``recovery IS NULL``): "unclaimed". The first log-in
to one claims it (trust on first use, logged as ``token_claimed``) while ``settings.account_claims_open`` holds;
until then it is kept out of the global ranking, the one list of names worth claiming.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from backend.services.learner.progress_db import connection

# Crockford's base32: no I, L, O or U, so a code read aloud or copied by hand has no look-alikes.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CODE_LENGTH = 16  # 80 bits
_LOOKALIKE = str.maketrans({"O": "0", "I": "1", "L": "1"})
# scrypt at 16 MiB: tens of milliseconds per log-in with a code, which the ACCOUNT limit already spaces out.
_SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1, "maxmem": 64 * 2 ** 20, "dklen": 32}
# Marks a device token wherever one could leak, so services/learner/journal.scrub can find and redact it.
TOKEN_PREFIX = "tft_"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def new_code() -> str:
    """A fresh recovery code, as it is shown: four groups of four."""
    code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
    return "-".join(code[i:i + 4] for i in range(0, _CODE_LENGTH, 4))


def _plain(typed: str) -> bytes:
    """A code however it was typed: any case, with or without dashes or spaces, O for 0, I or L for 1."""
    return "".join(typed.upper().split()).replace("-", "").translate(_LOOKALIKE).encode()


def _sealed(code: str) -> str:
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}${hashlib.scrypt(_plain(code), salt=salt, **_SCRYPT).hex()}"


def _opens(sealed: str, typed: str) -> bool:
    salt, _, digest = sealed.partition("$")
    try:
        tried = hashlib.scrypt(_plain(typed), salt=bytes.fromhex(salt), **_SCRYPT).hex()
    except ValueError:
        return False
    return hmac.compare_digest(tried, digest)


def _keep_token(db, name: str) -> str:
    token = new_token()
    db.execute("INSERT INTO tokens (hash, name) VALUES (?, ?)", (_hash(token), name))
    return token


def open_account(name: str) -> tuple[str, str] | None:
    """Make the account with its first token and recovery code, in one write: (token, code), or None when taken."""
    code = new_code()
    db = connection()
    with db:
        made = db.execute("INSERT OR IGNORE INTO accounts (name, recovery) VALUES (?, ?)", (name, _sealed(code)))
        if made.rowcount != 1:
            return None
        return _keep_token(db, name), code


def open_unclaimed(name: str) -> bool:
    """Make the account with no token or code yet, as accounts from before tokens were: for a page that would
    never show a code (models/progress.SignUpIn.shows_code). False when the name is taken."""
    db = connection()
    with db:
        return db.execute("INSERT OR IGNORE INTO accounts (name) VALUES (?)", (name,)).rowcount == 1


def claimed(name: str) -> bool:
    row = connection().execute("SELECT recovery FROM accounts WHERE name = ?", (name,)).fetchone()
    return row is not None and row["recovery"] is not None


def claim(name: str) -> tuple[str, str] | None:
    """Trust on first use: give an unclaimed account its first token and code. None when it is claimed already
    (or gone): only one device ever wins, however many ask at once."""
    code = new_code()
    db = connection()
    with db:
        won = db.execute("UPDATE accounts SET recovery = ? WHERE name = ? AND recovery IS NULL",
                         (_sealed(code), name))
        if won.rowcount != 1:
            return None
        return _keep_token(db, name), code


def recover(name: str, typed: str) -> tuple[str, str] | None:
    """Log in with the recovery code: (a token for this device, the next code), or None when the code is wrong.

    The code is spent as it is used: a compare-and-set on the stored seal, so the same code typed on two
    devices at once logs in one of them."""
    row = connection().execute("SELECT recovery FROM accounts WHERE name = ?", (name,)).fetchone()
    if row is None or row["recovery"] is None or not _opens(row["recovery"], typed):
        return None
    code = new_code()
    db = connection()
    with db:
        spent = db.execute("UPDATE accounts SET recovery = ? WHERE name = ? AND recovery = ?",
                           (_sealed(code), name, row["recovery"]))
        if spent.rowcount != 1:
            return None
        return _keep_token(db, name), code


def matches(name: str, typed: str) -> bool:
    """Whether `typed` is the account's current recovery code, without spending it."""
    row = connection().execute("SELECT recovery FROM accounts WHERE name = ?", (name,)).fetchone()
    return row is not None and row["recovery"] is not None and _opens(row["recovery"], typed)


def new_recovery(name: str) -> str:
    """Replace the account's recovery code (the old one stops working) and return the new one, to show once."""
    code = new_code()
    db = connection()
    with db:
        db.execute("UPDATE accounts SET recovery = ? WHERE name = ?", (_sealed(code), name))
    return code


def fresh(token: str, minutes: int) -> bool:
    """Whether this token was minted in the last `minutes`: a log-in just now, which may make a new recovery
    code without typing the old one (routers/progress.py new_recovery)."""
    row = connection().execute("SELECT at > datetime('now', ?) AS new FROM tokens WHERE hash = ?",
                               (f"-{minutes} minutes", _hash(token))).fetchone()
    return bool(row and row["new"])


def owner(token: str) -> str | None:
    """The account a token was minted for, or None for one never minted, revoked, or swept.

    A day's use is written down once, not per request, so the idle sweep knows which tokens are in use without
    costing every answer a write."""
    digest = _hash(token)
    row = connection().execute("SELECT name, used < datetime('now', '-1 day') AS stale FROM tokens WHERE hash = ?",
                               (digest,)).fetchone()
    if row is None:
        return None
    if row["stale"]:
        db = connection()
        with db:
            db.execute("UPDATE tokens SET used = datetime('now') WHERE hash = ?", (digest,))
    return row["name"]


def revoke(token: str) -> None:
    """Log this device out for good: its token opens nothing again."""
    db = connection()
    with db:
        db.execute("DELETE FROM tokens WHERE hash = ?", (_hash(token),))


def revoke_others(name: str, token: str) -> int:
    """Log out every other device of this account (a lost phone); returns how many."""
    db = connection()
    with db:
        return int(db.execute("DELETE FROM tokens WHERE name = ? AND hash != ?", (name, _hash(token))).rowcount)


def revoke_all(name: str) -> int:
    """Log out every device of this account (the owner's reset, scripts/recovery_code.py); returns how many."""
    db = connection()
    with db:
        return int(db.execute("DELETE FROM tokens WHERE name = ?", (name,)).rowcount)


def sweep(days: int) -> int:
    """Forget tokens nobody has used for `days`, as idle guest records are; returns how many went."""
    db = connection()
    with db:
        return int(db.execute("DELETE FROM tokens WHERE used < datetime('now', ?)", (f"-{days} days",)).rowcount)
