#!/bin/bash
# Every note left from the site (the footer's "Spotted a mistake?" and each panel's
# "Report a problem"), newest first, then the emails that asked for updates.
#   bash deploy/feedback.sh [ubuntu@132.145.17.56] [how many notes, default 50]
set -e
SERVER="${1:-ubuntu@132.145.17.56}"
N="${2:-50}"
ssh -i ~/.ssh/tafheem_oci "$SERVER" "cd ~/tafheem && venv/bin/python - $N" <<'PY'
import sqlite3, sys
db = sqlite3.connect("data/progress.db")
cols = {row[1] for row in db.execute("PRAGMA table_info(feedback)")}
mail = "email, updates" if "email" in cols else "NULL, 0"
print("NOTES, newest first")
for at, module, item, message, email, updates in db.execute(
        f"SELECT at, module, item, message, {mail} FROM feedback WHERE message != '' ORDER BY id DESC LIMIT ?",
        (int(sys.argv[1]),)):
    print(f"  {at}  {module}{'/' + item if item else ''}{'  <' + email + '>' if email else ''}")
    print(f"    {message}")
if "email" in cols:
    emails = [row[0] for row in db.execute(
        "SELECT email FROM feedback WHERE updates = 1 GROUP BY lower(email) ORDER BY MIN(id)")]
    print(f"\nASKED FOR UPDATES ({len(emails)})")
    print("  " + ", ".join(emails) if emails else "  none yet")
PY
