"""Who uses the backend and how much. Reads what deploy/usage.sh fetched.

Two kinds of line arrive mixed: Caddy's JSON access lines (one per request) and
the backend's own lines for each call it makes to Groq.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

people = defaultdict(lambda: {"n": 0, "ok": 0, "paths": Counter(), "first": None, "last": None})
days = Counter()
groq = Counter()

for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.strip()
    if line.startswith("{"):
        try:
            r = json.loads(line)
            q = r["request"]
        except (ValueError, KeyError):
            continue
        h = q.get("headers", {})
        who = (h.get("X-Vercel-Forwarded-For") or [q["remote_ip"]])[0]
        when = datetime.fromtimestamp(r["ts"], timezone.utc)
        p = people[who]
        p["n"] += 1
        p["ok"] += r["status"] < 400
        p["paths"][q["uri"].split("?")[0]] += 1
        p["first"] = min(p["first"] or when, when)
        p["last"] = max(p["last"] or when, when)
        days[when.strftime("%Y-%m-%d")] += 1
    elif "api.groq.com" in line:
        day = line[1:11]
        what = line.split("/v1/")[1].split(" ")[0] if "/v1/" in line else "?"
        groq[(day, what, "ok" if " 200 " in line else "FAILED")] += 1

print("REQUESTS PER DAY (UTC)")
for d, n in sorted(days.items()):
    print(f"  {d}  {n}")

print("\nWHO (real visitor address; 'scanner' = every request failed)")
for who, p in sorted(people.items(), key=lambda kv: -kv[1]["n"]):
    kind = "person" if p["ok"] else "scanner"
    top = ", ".join(f"{k} x{v}" for k, v in p["paths"].most_common(3))
    print(f"  {who:<18} {kind:<8} {p['n']:>5} req  {p['first']:%m-%d %H:%M} to {p['last']:%m-%d %H:%M}  {top}")

print("\nGROQ CALLS (what costs quota)")
for (day, what, ok), n in sorted(groq.items()):
    print(f"  {day}  {what:<22} {ok:<7} {n}")
if not groq:
    print("  none")
