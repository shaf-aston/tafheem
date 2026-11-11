"""What the security log says, as a short report. Reads files deploy/security-report.sh fetched.

The log is logs/security.jsonl (services/core/audit.py): one JSON line per refused or failed
answer and per account event. This answers the questions worth asking every morning:
who is being refused most, which accounts were deleted, which names were tried and not found,
and whether errors are bunching. Nothing here is sent anywhere.

    python deploy/security-report.py logs/security.jsonl [more files...] [--hours 24]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone

# Past these in the window, the line is marked so it stands out in a terminal or a mail.
LOUD = {"refused_per_ip": 200, "login_unknown_per_ip": 20, "errors": 20, "account_deleted": 5}


def read(paths: list[str], since: datetime) -> list[dict]:
    rows = []
    for path in paths:
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    row = json.loads(line)
                    if datetime.fromisoformat(row["at"]) >= since:
                        rows.append(row)
                except (ValueError, KeyError, TypeError):
                    continue
    return rows


def report(rows: list[dict], hours: int) -> list[str]:
    kinds = Counter(row["kind"] for row in rows)
    refused = Counter(row.get("ip", "") for row in rows if row["kind"] == "refused")
    statuses = Counter((row.get("status"), row.get("route")) for row in rows if row["kind"] in ("refused", "error"))
    unknown = Counter(row.get("ip", "") for row in rows if row["kind"] == "login_unknown")
    deleted = [row for row in rows if row["kind"] == "account_deleted"]

    def flag(count: int, limit: int) -> str:
        return "  <-- look" if count >= limit else ""

    def section(title: str, lines: list[str]) -> list[str]:
        return ["", title, *(lines or ["  none"])]

    out = [f"Security log, last {hours} h: {len(rows)} lines"]
    out += section("By kind:", [f"  {n:6}  {kind}" for kind, n in kinds.most_common()])
    out += section("Most refused visitors:",
                   [f"  {n:6}  {ip or '?'}{flag(n, LOUD['refused_per_ip'])}" for ip, n in refused.most_common(10)])
    out += section("Refusals and errors by answer and route:",
                   [f"  {n:6}  {status}  {route}" for (status, route), n in statuses.most_common(15)])
    out += section("Names tried that do not exist, by visitor (guessing?):",
                   [f"  {n:6}  {ip or '?'}{flag(n, LOUD['login_unknown_per_ip'])}" for ip, n in unknown.most_common(10)])
    out += ["", f"Accounts deleted: {len(deleted)}{flag(len(deleted), LOUD['account_deleted'])}"]
    out += [f"  {row['at']}  {row.get('user', '?')}  from {row.get('ip', '?')}  ({row.get('request_id', '')})" for row in deleted]
    out += ["", f"Server errors: {kinds['error']}{flag(kinds['error'], LOUD['errors'])}"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    print("\n".join(report(read(args.paths, since), args.hours)))


if __name__ == "__main__":
    main()
