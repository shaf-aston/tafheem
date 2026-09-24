#!/bin/bash
# Copy the databases onto the server. They are far too large for GitHub, so the
# clone up there arrives without them. About 1.6 GB in all.
#
# Run from the project root, on this machine:
#   bash deploy/copy-data.sh ubuntu@123.45.67.89
#
# Safe to run again: a file already up there at the same size is skipped, so a
# transfer that drops out only costs you the file it was on.
set -e
SERVER="${1:?Pass the server, for example: bash deploy/copy-data.sh ubuntu@123.45.67.89}"
REMOTE=tafheem

FILES="
backend/data/daleel.db
backend/data/daleel_index.db
backend/data/lexicons.db
backend/data/lexicon.db
backend/data/openiti.db
backend/data/books/openiti.db
backend/data/parser/encoder.onnx
backend/data/quran/library.db
backend/data/quran/corpus.db
backend/data/quran/meanings.db
backend/data/quran/search.db
backend/data/maqayees/roots.json
"

for f in $FILES; do
  [ -e "$f" ] || { echo "not on this machine, skipping: $f"; continue; }
  here=$(stat -c %s "$f")
  there=$(ssh "$SERVER" "stat -c %s '$REMOTE/$f' 2>/dev/null || echo 0")
  if [ "$here" = "$there" ]; then echo "already there: $f"; continue; fi
  ssh "$SERVER" "mkdir -p '$REMOTE/$(dirname "$f")'"
  echo "copying $f"
  scp "$f" "$SERVER:$REMOTE/$f"
done

echo "Done. Now restart the backend:  ssh $SERVER 'sudo systemctl restart tafheem'"
