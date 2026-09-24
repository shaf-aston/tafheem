#!/bin/bash
# Bring the server up to date with the code. Run from this machine:
#   bash deploy/update.sh ubuntu@123.45.67.89
# Databases are not touched: they are not in git, see copy-data.sh.
set -e
SERVER="${1:?Pass the server, for example: bash deploy/update.sh ubuntu@123.45.67.89}"
ssh "$SERVER" 'cd tafheem && git pull --ff-only && venv/bin/pip install -q -r requirements.txt && sudo systemctl restart tafheem'
echo "Updated. Check: ssh $SERVER 'curl -s localhost:8000/api/health'"
