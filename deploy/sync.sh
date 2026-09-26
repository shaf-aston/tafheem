#!/bin/bash
# Makes the server match GitHub master: backend code, the website copy, then a
# backend restart. Run by tafheem-sync.timer every 5 minutes, or by hand.
# Databases in backend/data are never touched, they are not in git.
set -euo pipefail
cd /home/ubuntu/repo
git fetch -q origin master
NEW=$(git rev-parse origin/master)
if [ "$NEW" = "$(cat /home/ubuntu/.deployed-sha 2>/dev/null || true)" ]; then
	echo "already on $NEW"
	exit 0
fi
git reset -q --hard origin/master
rsync -a --exclude data --exclude __pycache__ backend/ /home/ubuntu/tafheem/backend/
rsync -a deploy/ /home/ubuntu/tafheem/deploy/
cp requirements.txt /home/ubuntu/tafheem/requirements.txt
/home/ubuntu/tafheem/venv/bin/pip install -q -r requirements.txt
(cd frontend && npm ci --silent && npm run build)
rm -rf /home/ubuntu/site.new
cp -r frontend/dist /home/ubuntu/site.new
rm -rf /home/ubuntu/site
mv /home/ubuntu/site.new /home/ubuntu/site
sudo systemctl restart tafheem
echo "$NEW" > /home/ubuntu/.deployed-sha
echo "deployed $NEW"
