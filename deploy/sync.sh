#!/bin/bash
# Makes the server match GitHub master: backend code, the website copy, then a
# rolling backend restart. Run by tafheem-sync.timer every 5 minutes, or by hand.
# backend/data holds both: databases that are not in git, never touched here,
# and small tracked files (the Sarf rules, Nahw notes, Colloquial lessons) that
# the code reads and must change with it. Only the files git tracks are copied,
# so a database the server has and git does not is left alone.
#
# Two backend copies run behind Caddy (tafheem@8000, tafheem@8001). Restarted
# one at a time so the other keeps answering requests throughout — visitors
# never see a dropped request during a deploy. If the first restarted copy
# never comes back healthy, the second is left alone on the old code rather
# than restarting it too: one working copy always stays up.
set -euo pipefail
cd /home/ubuntu/repo

wait_healthy() {
	local port=$1 tries=30
	while [ "$tries" -gt 0 ]; do
		curl -fsS "http://127.0.0.1:$port/api/health" >/dev/null 2>&1 && return 0
		tries=$((tries - 1))
		sleep 3
	done
	return 1
}
git fetch -q origin master
NEW=$(git rev-parse origin/master)
if [ "$NEW" = "$(cat /home/ubuntu/.deployed-sha 2>/dev/null || true)" ]; then
	echo "already on $NEW"
	exit 0
fi
git reset -q --hard origin/master
rsync -a --exclude data --exclude __pycache__ backend/ /home/ubuntu/tafheem/backend/
git ls-files -z backend/data | rsync -a --from0 --files-from=- ./ /home/ubuntu/tafheem/
rsync -a deploy/ /home/ubuntu/tafheem/deploy/
cp requirements.txt requirements-nodeps.txt /home/ubuntu/tafheem/
/home/ubuntu/tafheem/venv/bin/pip install -q -r requirements.txt
/home/ubuntu/tafheem/venv/bin/pip install -q --no-deps -r requirements-nodeps.txt
# The hadith collections are fetched here from the public CDN and indexed here,
# never copied from anyone's machine. Each step reruns only when its input is
# newer than its output, so a quiet sync costs nothing.
H=/home/ubuntu/tafheem
HD=$H/backend/data/hadith
for key in $("$H/venv/bin/python" -c "import json;print(' '.join(k for k in json.load(open('$HD/collections.json')) if not k.startswith('_')))"); do
	if [ ! -f "$HD/$key.json" ] || [ "$H/backend/scripts/fetch_hadith_collections.py" -nt "$HD/$key.json" ]; then
		(cd "$H" && venv/bin/python backend/scripts/fetch_hadith_collections.py "$key") || echo "hadith: fetching $key failed, kept the old copy"
	fi
done
if [ ! -f "$H/backend/data/hadith.db" ] || [ -n "$(find "$HD" "$H/backend/scripts/build_hadith_index.py" -newer "$H/backend/data/hadith.db" -print -quit)" ]; then
	(cd "$H" && venv/bin/python backend/scripts/build_hadith_index.py)
fi
(cd frontend && npm ci --silent && npm run build)
rm -rf /home/ubuntu/site.new
cp -r frontend/dist /home/ubuntu/site.new
rm -rf /home/ubuntu/site
mv /home/ubuntu/site.new /home/ubuntu/site

sudo systemctl restart tafheem@8001
if wait_healthy 8001; then
	sudo systemctl restart tafheem@8000
	wait_healthy 8000 || echo "warning: tafheem@8000 did not come back healthy after restart" >&2
else
	echo "warning: tafheem@8001 did not come back healthy, left tafheem@8000 on the old code" >&2
	exit 1
fi

echo "$NEW" > /home/ubuntu/.deployed-sha
echo "deployed $NEW"
