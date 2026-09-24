#!/bin/bash
# Run once on a fresh Oracle Ubuntu machine, from /home/ubuntu/tafheem:
#   bash deploy/setup.sh tafheem.duckdns.org
set -e
HOST="${1:?Pass your duckdns name, for example: bash deploy/setup.sh tafheem.duckdns.org}"

sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential debian-keyring debian-archive-keyring apt-transport-https curl

python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/camel_data -i defaults

# Caddy, from its own package list.
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy

sed "s/tafheem.duckdns.org/$HOST/" deploy/Caddyfile | sudo tee /etc/caddy/Caddyfile >/dev/null
sudo systemctl restart caddy

# Oracle's Ubuntu image blocks every port but SSH in its own firewall.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save

sudo cp deploy/tafheem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tafheem

echo "Done. Check it: curl -s https://$HOST/api/health"
