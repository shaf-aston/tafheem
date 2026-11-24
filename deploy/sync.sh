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

# What this machine can carry, from /home/ubuntu/.sync.env (absent = the full set below).
# A 1 GB machine runs one copy (SYNC_PORTS=8000), takes its databases from copy-data.sh
# instead of building them (SYNC_BUILD_DATA=0), and leaves the site to Vercel (SYNC_SITE=0):
# it has no Node, and npm, a second backend or a hadith index build would not fit in its memory.
SYNC_PORTS="8001 8000"
SYNC_BUILD_DATA=1
SYNC_SITE=1
[ -f /home/ubuntu/.sync.env ] && . /home/ubuntu/.sync.env

wait_healthy() {
	local port=$1 tries=60  # health is 503 until the models load, ~40s on this machine
	while [ "$tries" -gt 0 ]; do
		curl -fsS "http://127.0.0.1:$port/api/health" >/dev/null 2>&1 && return 0
		tries=$((tries - 1))
		sleep 3
	done
	return 1
}
git fetch -q origin master
# The newest master commit whose CI passed: on a busy day a push lands every few
# minutes, so master's very tip is nearly always still in CI, and waiting on the tip
# kept the site hours behind. The rerun below (SYNC_FRESH) is already on the chosen commit.
# SYNC_SKIP_CI=1 by hand takes the tip as it is.
if [ -n "${SYNC_FRESH:-}" ]; then
	NEW=$(git rev-parse HEAD)
elif [ -n "${SYNC_SKIP_CI:-}" ]; then
	NEW=$(git rev-parse origin/master)
else
	GREEN=$(curl -fsS --max-time 20 "https://api.github.com/repos/shaf-aston/tafheem/actions/workflows/ci.yml/runs?branch=master&event=push&status=success&per_page=50" \
		| python3 -c 'import json,sys; print(" ".join(r["head_sha"] for r in json.load(sys.stdin)["workflow_runs"]))' 2>/dev/null || true)
	NEW=$(git rev-list --first-parent -n 100 origin/master | grep -m1 -xF -f <(tr ' ' '\n' <<<"$GREEN" | grep .) || true)
	if [ -z "$NEW" ]; then
		echo "not deploying: no recent master commit has passed CI (or GitHub can't be asked)"
		exit 0
	fi
fi
if [ "$NEW" = "$(cat /home/ubuntu/.deployed-sha 2>/dev/null || true)" ]; then
	echo "already on $NEW"
	exit 0
fi
git reset -q --hard "$NEW"
# The reset may have changed this very script; bash would finish the old one,
# so a change here would only apply a deploy late. Run the new copy once.
if [ -z "${SYNC_FRESH:-}" ]; then
	SYNC_FRESH=1 exec bash "$0" "$@"
fi
rsync -a --exclude data --exclude __pycache__ backend/ /home/ubuntu/tafheem/backend/
git ls-files -z backend/data | rsync -a --from0 --files-from=- ./ /home/ubuntu/tafheem/
rsync -a deploy/ /home/ubuntu/tafheem/deploy/
# rsync only adds and updates, so a file git deleted would live on here: a
# removed Colloquial unit then fails the whole tab. Remove what git removed
# since the last deploy; untracked databases are never in this list. --no-renames, or a moved
# file shows as renamed, not deleted, and its old copy lives on here.
OLD=$(cat /home/ubuntu/.deployed-sha 2>/dev/null || true)
if [ -n "$OLD" ] && git cat-file -e "$OLD^{commit}" 2>/dev/null; then
	git diff --no-renames --name-only --diff-filter=D -z "$OLD" "$NEW" -- backend/ deploy/ \
		| (cd /home/ubuntu/tafheem && xargs -0 -r rm -fv)
fi
# Colloquial lessons are all in git, so the server copy is mirrored exactly.
rsync -a --delete backend/data/colloquial/ /home/ubuntu/tafheem/backend/data/colloquial/
# The few frontend files the backend reads at runtime, kept at the same paths:
# the quiz's words for checked practice sentences (services/learner/sentence_check.py) and the Jazariyya poem
# (services/daleel/sources/jazariyya.py), and the voices' shared pace (services/speech.py). Without the words, Make one was a 500.
# word_audio.json and sentences.json: premake_speech.py lists the quiz lines from them.
# tests/core/test_deploy_files.py fails if the backend starts reading another.
rsync -aR frontend/public/words/words.json frontend/public/words/coverage.json \
	frontend/public/words/word_audio.json frontend/public/words/sentences.json \
	frontend/public/jazariyya/poem.json frontend/src/config/speak.json /home/ubuntu/tafheem/
# The page reader's Tesseract is a system package, installed by setup.sh, never from here: sync runs from
# master and must not hold apt rights. Without it pictures go to the vision model alone; /api/health says which.
tesseract --list-langs 2>/dev/null | grep -qx ara || echo "sync: no tesseract-ocr-ara; run: sudo apt-get install tesseract-ocr tesseract-ocr-ara"
cp requirements-torch.txt requirements.txt requirements-nodeps.txt /home/ubuntu/tafheem/
/home/ubuntu/tafheem/venv/bin/pip install -q -r requirements-torch.txt
/home/ubuntu/tafheem/venv/bin/pip install -q -r requirements.txt
/home/ubuntu/tafheem/venv/bin/pip install -q --no-deps -r requirements-nodeps.txt
if [ "$SYNC_BUILD_DATA" = 1 ]; then
# The hadith collections are fetched here from the public CDN and indexed here,
# never copied from anyone's machine. Each step reruns only when its input is
# newer than its output, so a quiet sync costs nothing. The index also reads
# the chain rule (data/hadith/chain.json, inside $HD) and the word helpers it imports.
H=/home/ubuntu/tafheem
HD=$H/backend/data/hadith
for key in $("$H/venv/bin/python" -c "import json;print(' '.join(k for k in json.load(open('$HD/collections.json')) if not k.startswith('_')))"); do
	if [ ! -f "$HD/$key.json" ] || [ "$H/backend/scripts/hadith/fetch_hadith_collections.py" -nt "$HD/$key.json" ]; then
		(cd "$H" && venv/bin/python backend/scripts/hadith/fetch_hadith_collections.py "$key") || echo "hadith: fetching $key failed, kept the old copy"
	fi
done
if [ ! -f "$H/backend/data/hadith.db" ] || [ -n "$(find "$HD" "$H/backend/scripts/hadith/build_hadith_index.py" "$H"/backend/services/hadith/{chain,words,lemma}.py -newer "$H/backend/data/hadith.db" -print -quit)" ]; then
	(cd "$H" && venv/bin/python backend/scripts/hadith/build_hadith_index.py)
fi
# Meaning vectors: the build itself knows what changed (text, model, length), re-encodes only
# that, and takes seconds when nothing did. Low priority, so the live site stays quick.
(cd "$H" && nice -n 19 venv/bin/python backend/scripts/hadith/build_hadith_meaning.py) || echo "hadith: meaning build failed, search runs on words alone"
# CAMeL's BERT disambiguator as ONNX (the parser then loads no torch), built here from CAMeL's
# own weights once, and again when the build script changes. Until it is built, or if the
# build fails, the parser loads CAMeL's torch copy, which ranks the same readings.
if [ ! -f "$H/backend/data/disambig/model.onnx" ] || [ "$H/backend/scripts/nahw/build_disambig_onnx.py" -nt "$H/backend/data/disambig/model.onnx" ]; then
	(cd "$H" && nice -n 19 venv/bin/python -m backend.scripts.nahw.build_disambig_onnx) || echo "disambig: ONNX build failed, the parser keeps CAMeL's torch copy"
fi
fi
if [ "$SYNC_SITE" = 1 ]; then
	(cd frontend && npm ci --silent && npm run build)
	rm -rf /home/ubuntu/site.new
	cp -r frontend/dist /home/ubuntu/site.new
	rm -rf /home/ubuntu/site
	mv /home/ubuntu/site.new /home/ubuntu/site
fi

# One copy at a time; the first that fails to come back stops the rest, so with two
# copies the other keeps answering on the old code. With one, the API pauses ~40s.
for port in $SYNC_PORTS; do
	sudo systemctl restart "tafheem@$port"
	if ! wait_healthy "$port"; then
		echo "warning: tafheem@$port did not come back healthy; stopped the restarts there" >&2
		exit 1
	fi
done

echo "$NEW" > /home/ubuntu/.deployed-sha
echo "deployed $NEW"
