#!/bin/bash
# What the security log says (refusals, unknown names tried, deleted accounts, errors). Run from this machine:
#   bash deploy/security-report.sh [ubuntu@132.145.17.56] [hours, default 24]
# Or on the server itself: zcat -f logs/security.jsonl* > /tmp/s && python3 deploy/security-report.py /tmp/s
# (zcat -f: logrotate gzips days older than yesterday; plain cat would skip them without a word)
set -e
SERVER="${1:-ubuntu@132.145.17.56}"
HOURS="${2:-24}"
T=$(mktemp)
trap 'rm -f "$T"' EXIT
ssh -i ~/.ssh/tafheem_oci "$SERVER" "zcat -f /home/ubuntu/tafheem/logs/security.jsonl* 2>/dev/null || true" > "$T"
PY=$(command -v python3 || command -v python)
"$PY" "$(dirname "$0")/security-report.py" "$T" --hours "$HOURS"
