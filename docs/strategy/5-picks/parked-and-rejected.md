# Parked (good, not now) and rejected (not for us)

## Parked: with the trigger that un-parks each one

| ID | Idea | Why not now | Un-park when |
|---|---|---|---|
| I6 | Teacher mode: class, assign a surah's words, class confusion report | High business value, but unproven demand. Needs real accounts + privacy for minors | ~10 madrasah teacher interviews say "I'd pay for this". Pick 1's confusion data then makes the class report almost free |
| I7 | Tajweed rules on recitation / "error lattice" | XL size. Crowded field, **existing patents** (FTO check needed). Tarteel is there | The reviewer-marked clip set grows well beyond 1,950, *and* the phoneme checker beats its spike (45% letters caught at 12% false flags) |
| I14 | Hadith chain-continuity check + Mushkil tab | Novel-looking and cheap, but off the vocabulary focus | Any free week. It is a nice quick win and a good demo for hadith students |
| I9 | Offline PWA (service worker + an IndexedDB queue of attempts) | Useful for classrooms, but not the bottleneck | Teacher mode starts, or users report bad signal. **Never ship bulk data to the browser** (it would kill trade secret) |
| I10 | Payments + "upgrade moments" | Nothing to charge for until Picks 0–1 land | Coverage meter + diagnosis are live and retention is measured |
| I2 | n-best readings + arbitration | Already built in a better form (mask + teacher veto) | Published accuracy (Pick 0.5) shows ambiguity as the main error |

## Rejected

| ID | Idea | Why |
|---|---|---|
| I11 | Postgres + Redis + Kafka + OpenSearch + vector DB + LLM model router | It makes a 1-person app slower to build and run, with no speed gain. Our data is read-only and precomputed; SQLite lookups are already microseconds. See `../6-architecture/three-layers.md` |
| I5 (as its own system) | "Pedagogy router" choosing analogy, rule-first and so on | Vague, unmeasurable, crowded. The part that matters ("what next") is one deterministic rule inside Pick 1 |
| I12 (as its own system) | Teen safety policy engine | Already met by design: no open chat, no fatwa, AI only rephrases checked proofs. The never-say list in Pick 2 covers the rest |
| — | Patent filings now | £4–16k for claims likely to fail "inventive step". Spend it on a licence check and an IP attorney hour instead |
