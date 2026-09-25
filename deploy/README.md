# Putting Tafheem online

The landing page goes on Vercel. The tool needs the backend, and the backend
needs 1.6 GB of databases, so it goes on a free Oracle machine.

## 1. The Oracle account

Sign up at <https://www.oracle.com/cloud/free/>. A card is required and is never
charged on the free parts.

**Choose the home region carefully. It cannot be changed afterwards.** The free
Arm machines run out in busy regions, and you are then stuck asking for one that
region has none of. Pick the least busy region near you rather than the default.

## 2. The machine

Create a compute instance:

- Image: Ubuntu 24.04
- Shape: `VM.Standard.A1.Flex`, 2 processors, 12 GB memory (the whole free allowance)
- Boot volume: 200 GB (also free, and the databases need the room)
- Save the SSH key it offers. Without it you cannot get back in.

If it says "out of capacity", that region has no free Arm machines right now.
Try again later or try another availability domain in the same region.

Then let the internet reach it: in the console, open Networking, the machine's
subnet, its security list, and add ingress rules for TCP 80 and 443 from
`0.0.0.0/0`.

## 3. A name for it

Register a free name at <https://www.duckdns.org> and point it at the machine's
public IP. HTTPS needs a name, not a number.

## 4. Set it up

From this machine:

```bash
ssh ubuntu@<the machine's IP>
git clone https://github.com/shaf-aston/tafheem.git
cd tafheem
bash deploy/setup.sh <your name>.duckdns.org
```

That installs Python, the packages, and Caddy, which fetches the HTTPS
certificate by itself. It takes a while; the Arabic morphology package alone
downloads about 200 MB.

## 5. Send the databases over

From this machine again, in the project folder:

```bash
bash deploy/copy-data.sh ubuntu@<the machine's IP>
```

About 1.6 GB, so it depends on your upload speed. Run it again if it drops out.

Check it answers:

```bash
curl https://<your name>.duckdns.org/api/health
```

## 6. Point the site at it

In `vercel.json` (repo root), add this above the `/app` line, with your own name in
it:

```json
{ "source": "/api/:path*", "destination": "https://<your name>.duckdns.org/api/:path*" }
```

Push, and Vercel rebuilds. The browser then calls the site's own address and
Vercel passes it back to the machine, so there is no cross-site problem to solve.

## Keeping the machine

Oracle may take back a machine that stays under 20% busy for 7 days. A free
uptime checker such as UptimeRobot, pointed at `/api/health` every 5 minutes,
keeps it awake and tells you if it ever stops answering.
