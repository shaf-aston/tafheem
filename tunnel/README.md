# tunnel

Puts the backend running on this PC onto the public internet, so the published
site can reach it. Nothing else in the project knows this folder exists.

## Using it

1. Start the backend as usual.
2. Double-click `go-live.cmd`.
3. It prints an address ending in `trycloudflare.com`. That is the backend's
   public address.

Closing the window takes it offline. Nothing is left running.

## Removing it

Delete this folder. That is the whole uninstall.

Nothing is installed into Windows: no service, no startup entry, no registry
key, no PATH change. `cloudflared.exe` is a single file that only runs while its
window is open, and it dials out rather than opening a port, so the router and
firewall are untouched either way.

## What it is coupled to

Two things, both one line each:

- `PORT` at the top of `go-live.cmd`, which must match the backend's port.
- The `/api` rewrite in `vercel.json` (repo root), which points the published site
  at the address this prints.

The address changes every time the tunnel restarts, because this is the
no-account version. A fixed address needs a free Cloudflare account, or the
Oracle machine in `deploy/`, which is the same backend with a permanent home.
