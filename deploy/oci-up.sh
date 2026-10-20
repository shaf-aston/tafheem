#!/bin/bash
# One-shot: build the free Oracle machine, send the backend, start it, test it.
# Run from the project root on this PC:   bash deploy/oci-up.sh
# Safe to run again: it reuses what already exists. Only Always Free shapes are used.
set -euo pipefail

T=ocid1.tenancy.oc1..aaaaaaaajaq5qozykqer7avg2t2c7w2trkatq3a3pvinvyoxd2sc22uhs47q
KEY=~/.ssh/tafheem_oci
SSH="ssh -i $KEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o ServerAliveInterval=30"
step() { printf '\n== %s\n' "$*"; }
fail() { printf 'FAILED: %s\n' "$*" >&2; exit 1; }
oci() { command oci "$@" | tr -d '\r'; }

[ -f .env ] || fail "run from the project root (no .env here)"
! grep -q '^RECITATION_GROQ_API_KEY' .env || fail ".env still has the old RECITATION_GROQ_API_KEY name"
grep -q '^LISTENING_GROQ_API_KEYS=.' .env || fail ".env has no LISTENING_GROQ_API_KEYS"

step "1/7 login key"
[ -f "$KEY" ] || ssh-keygen -t ed25519 -N "" -f "$KEY" -q

step "2/7 network (free)"
VCN=$(oci network vcn list -c $T --all --query 'data[?"display-name"==`tafheem-vcn`]|[0].id' --raw-output 2>/dev/null || true)
if [ -z "$VCN" ] || [ "$VCN" = null ]; then
  VCN=$(oci network vcn create -c $T --display-name tafheem-vcn --cidr-block 10.0.0.0/16 --wait-for-state AVAILABLE --query 'data.id' --raw-output)
  IGW=$(oci network internet-gateway create -c $T --vcn-id "$VCN" --is-enabled true --display-name tafheem-igw --wait-for-state AVAILABLE --query 'data.id' --raw-output)
  RT=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-route-table-id"' --raw-output)
  oci network route-table update --rt-id "$RT" --force \
    --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IGW\"}]" >/dev/null
  SL=$(oci network vcn get --vcn-id "$VCN" --query 'data."default-security-list-id"' --raw-output)
  tcp() { echo "{\"protocol\":\"6\",\"source\":\"0.0.0.0/0\",\"tcpOptions\":{\"destinationPortRange\":{\"min\":$1,\"max\":$1}}}"; }
  oci network security-list update --security-list-id "$SL" --force \
    --ingress-security-rules "[$(tcp 22),$(tcp 80),$(tcp 443)]" \
    --egress-security-rules '[{"protocol":"all","destination":"0.0.0.0/0"}]' >/dev/null
  oci network subnet create -c $T --vcn-id "$VCN" --cidr-block 10.0.0.0/24 --display-name tafheem-public \
    --wait-for-state AVAILABLE >/dev/null
fi
SUB=$(oci network subnet list -c $T --vcn-id "$VCN" --query 'data[0].id' --raw-output)

step "3/7 machine (Always Free Arm: 2 processors, 12 GB, 100 GB disk)"
INST=$(oci compute instance list -c $T --all --query 'data[?"display-name"==`tafheem`&&"lifecycle-state"!=`TERMINATED`]|[0].id' --raw-output 2>/dev/null || true)
if [ -z "$INST" ] || [ "$INST" = null ]; then
  IMG=$(oci compute image list -c $T --operating-system "Canonical Ubuntu" --operating-system-version 24.04 \
    --shape VM.Standard.A1.Flex --sort-by TIMECREATED --sort-order DESC --limit 10 \
    --query 'data[?!contains("display-name",`Minimal`)]|[0].id' --raw-output | tr -d '\r')
  ADS=$(oci iam availability-domain list --query 'data[].name' | tr -d '[]", ')
  for round in $(seq 1 30); do
    for AD in $ADS; do
      echo "trying $AD (round $round)"
      if INST=$(oci compute instance launch -c $T --availability-domain "$AD" --display-name tafheem \
          --shape VM.Standard.A1.Flex --shape-config '{"ocpus":2,"memoryInGBs":12}' \
          --image-id "$IMG" --subnet-id "$SUB" --assign-public-ip true \
          --boot-volume-size-in-gbs 100 --ssh-authorized-keys-file "$KEY.pub" \
          --wait-for-state RUNNING --query 'data.id' --raw-output 2>/tmp/oci-launch.err); then
        break 2
      fi
      grep -qi 'capacity' /tmp/oci-launch.err || { cat /tmp/oci-launch.err >&2; fail "launch refused"; }
    done
    echo "Oracle has no free Arm machine right now; waiting 2 minutes"
    sleep 120
  done
  [ -n "${INST:-}" ] || fail "no capacity after an hour; run this again later"
fi
IP=$(oci compute instance list-vnics --instance-id "$INST" --query 'data[0]."public-ip"' --raw-output | tr -d '\r')
HOST="$(echo "$IP" | tr . -).sslip.io"
echo "machine $IP  ->  https://$HOST"

step "4/7 wait for login"
for i in $(seq 1 40); do $SSH ubuntu@"$IP" true 2>/dev/null && break || sleep 10; done
$SSH ubuntu@"$IP" true || fail "cannot log in to $IP"

step "5/7 send the backend (about 2.4 GB, a while)"
$SSH ubuntu@"$IP" 'mkdir -p tafheem'
tar czf - --exclude='__pycache__' --exclude='backend/data/recitation_checks' \
  backend requirements.txt deploy | $SSH ubuntu@"$IP" 'tar xzf - -C tafheem'
scp -i "$KEY" .env ubuntu@"$IP":tafheem/.env
$SSH ubuntu@"$IP" 'chmod 600 tafheem/.env'

step "6/7 install and start (Python packages, Caddy, service)"
$SSH ubuntu@"$IP" 'sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables-persistent netfilter-persistent'
$SSH ubuntu@"$IP" "cd tafheem && bash deploy/setup.sh $HOST"

step "7/7 test"
ok=0
for i in $(seq 1 30); do
  if curl -fsS "https://$HOST/api/health" > /tmp/tafheem-health.json 2>/dev/null; then ok=1; break; fi
  sleep 10
done
[ $ok = 1 ] || { $SSH ubuntu@"$IP" 'sudo journalctl -u tafheem -n 40 --no-pager' || true; fail "no answer from https://$HOST/api/health"; }
grep -q listen_per_minute /tmp/tafheem-health.json || fail "health answered but has no listen_per_minute"
echo "health ok over HTTPS: $(sed -E 's/"[A-Za-z_]*(key|token)[A-Za-z_]*":"[^"]*"/"..":"hidden"/gI' /tmp/tafheem-health.json | head -c 400)"
curl -fsS -m 5 "http://$IP:8000/api/health" >/dev/null 2>&1 && fail "port 8000 is open to the internet" || echo "port 8000 closed to the internet: ok"
echo "rebooting to prove it restarts by itself"
$SSH ubuntu@"$IP" 'sudo reboot' || true
sleep 60
ok=0
for i in $(seq 1 30); do curl -fsS "https://$HOST/api/health" >/dev/null 2>&1 && { ok=1; break; } || sleep 10; done
[ $ok = 1 ] || fail "did not come back after reboot"

echo
echo "ALL CHECKS PASSED"
echo "address:  https://$HOST"
echo "login:    ssh -i $KEY ubuntu@$IP"
echo "update:   ssh -i $KEY ubuntu@$IP 'sudo systemctl restart tafheem'  (after re-running this script)"
