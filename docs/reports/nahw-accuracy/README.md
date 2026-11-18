# Nahw accuracy test: fresh sentences sent to the hosted app

One file per run date. Each says what was tested, what was wrong, and what got fixed, so a later run can show progress.

How a run works: send sentences to `POST /api/analyze {"sentence": ...}` on the live app, then compare each word's role and case with what a nahw teacher expects. Nothing in the code is changed during the test.

Rules for a fair run:
- Write the sentences fresh. Never tune the engine on them.
- Sort each miss: real mistake / unclear / my label was wrong. Only the first is a bug.
- A fix must be a grammar rule that also fixes a sibling sentence, never a fix for one sentence.

## Runs

| Date | File | Result | Open after the run |
|---|---|---|---|
| 2026-10-31 | [2026-10-31.md](2026-10-31.md) | 37/38 with vowels, 33/38 without | none of the 3 real mistakes (all fixed, PR 764) |
| 2026-11-14 | [2026-11-14.md](2026-11-14.md) | complex set, local, Sonnet blind key: 147/152 → 152/152 | card and tree findings in its section 4 |
| 2026-11-18 | [2026-11-18.md](2026-11-18.md) | near ties, 2 of 3 open gaps closed, bug hunt 149/149 + 10 probe faults fixed | فِعَال masdar gap (reverted) |
| 2026-11-18 | [2026-11-18-hadith.md](2026-11-18-hadith.md) | إنما hadith fixed; nested-sentence hunt: 9 faults fixed, every mutant killed | 8 sentences in its section 4 |

Related: [live-check](../live-check/README.md) (answer keys: Quran, hadith, blind set).
