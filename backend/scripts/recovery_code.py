"""The owner's way back into an account: a new recovery code for it, made on the server.

    sudo -u ubuntu .venv/bin/python -m backend.scripts.recovery_code NAME
    sudo -u ubuntu .venv/bin/python -m backend.scripts.recovery_code NAME --log-out-everywhere

For a learner who lost every device and the code with them, an account nobody claimed before
`account_claims_open` was turned off, or one claimed by the wrong person while it was open (the security
log's "token_claimed" line says by which address). Prints the code once; give it to the learner, who types it
in Log in. The old code stops working. `--log-out-everywhere` also ends every device's token: use it when the
account was taken, so whoever took it is logged out (docs/plans/2026-11-11-security.md §5 and §7).

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
    parser.add_argument("--log-out-everywhere", action="store_true", help="end every device's token as well")
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
    devices = tokens.revoke_all(name) if args.log_out_everywhere else 0
    audit.event("recovery_by_owner", user=name, devices_logged_out=devices)
    print(code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
