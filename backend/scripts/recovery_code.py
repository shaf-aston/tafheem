"""The owner's way back into an account: a new recovery code for it, made on the server.

    sudo -u ubuntu .venv/bin/python -m backend.scripts.recovery_code NAME
    sudo -u ubuntu .venv/bin/python -m backend.scripts.recovery_code NAME --keep-devices

For a learner who lost every device and the code with them, an account nobody claimed before
`account_claims_open` was turned off, or one claimed by the wrong person while it was open (the security
log's "token_claimed" line says by which address). Prints the code once; give it to the learner, who types it
in Log in. The old code stops working, and every device's token ends too, so whoever took the account (or
holds the lost phone) is logged out and cannot make themselves a new code. `--keep-devices` leaves the devices
logged in: only when the learner is sure every one of them is theirs (docs/plans/2026-11-11-security.md §5, §7).

Run as the user the server runs as, from the repository, so it opens the same data/progress.db.
"""
from __future__ import annotations

import argparse
import sys

from backend.services.core import audit
from backend.services.learner import accounts, tokens
from backend.services.learner.username import clean_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="the username, as typed")
    parser.add_argument("--keep-devices", action="store_true",
                        help="leave every device logged in (default: log them all out)")
    args = parser.parse_args(argv)
    try:
        name = clean_name(args.name)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if not accounts.has_account(name):
        print(f"No account named {name!r}", file=sys.stderr)
        return 1
    code = tokens.new_recovery(name)
    devices = 0 if args.keep_devices else tokens.revoke_all(name)
    audit.event("recovery_by_owner", user=name, devices_logged_out=devices)
    print(code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
