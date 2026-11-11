#!/bin/bash
# Who is using the backend and how much. Run from this machine:
#   bash deploy/usage.sh [ubuntu@132.145.17.56]
set -e
SERVER="${1:-ubuntu@132.145.17.56}"
T=$(mktemp)
trap 'rm -f "$T"' EXIT
# Caddy rolls access.log at 10 MB into access-<time>.log.gz (gzipped), so: access*.log* and zcat -f
# (which passes the live, uncompressed file through). cat access.log* read only the live file.
ssh -i ~/.ssh/tafheem_oci "$SERVER" "sudo sh -c 'zcat -f /var/log/caddy/access*.log*'; journalctl -u 'tafheem@*' --no-pager -o cat | grep api.groq.com || true" > "$T"
PY=$(command -v python3 || command -v python)
"$PY" "$(dirname "$0")/usage.py" "$T"
