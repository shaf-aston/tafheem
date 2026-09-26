#!/bin/bash
# Put the committed website on the server, so its address matches Vercel.
# Builds from git HEAD (what Vercel builds), not from unsaved local edits.
#   bash deploy/site.sh [ubuntu@132.145.17.56]
set -eo pipefail
SERVER="${1:-ubuntu@132.145.17.56}"
W=$(mktemp -d)
trap 'git worktree remove --force "$W" 2>/dev/null || true' EXIT
git worktree add -q --detach "$W" HEAD
(cd "$W/frontend" && npm ci --silent && npm run build)
tar czf - -C "$W/frontend/dist" . | ssh -i ~/.ssh/tafheem_oci "$SERVER" 'rm -rf site.new && mkdir site.new && tar xzf - -C site.new && rm -rf site && mv site.new site'
