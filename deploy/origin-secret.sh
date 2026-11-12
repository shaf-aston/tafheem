#!/usr/bin/env bash
# Writes /etc/caddy/origin-secret.caddy, the origin_gate snippet the Caddyfile imports: /api answers only a
# request carrying X-Origin-Secret, which Vercel adds (ORIGIN_SECRET in the project's env, vercel.json "routes").
# The secret comes on stdin, never as an argument (arguments show in ps):
#   openssl rand -hex 32 > s; bash deploy/origin-secret.sh < s; vercel env add ORIGIN_SECRET production --sensitive < s
# Then sudo systemctl reload caddy. Refuses anything but 64 hex characters, so a gate can never match "".
set -euo pipefail
read -r secret || true
if ! [[ $secret =~ ^[0-9a-f]{64}$ ]]; then
  echo "origin-secret.sh: expected 64 lowercase hex characters on stdin" >&2
  exit 1
fi
printf '(origin_gate) {\n\t@not_vercel not header X-Origin-Secret "%s"\n\trespond @not_vercel 403\n}\n' "$secret" |
  sudo install -m 640 -o root -g caddy /dev/stdin /etc/caddy/origin-secret.caddy
