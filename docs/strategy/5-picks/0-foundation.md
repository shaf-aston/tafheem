# Pick 0. Foundation: make learning measurable and sellable

Not IP. Not exciting. **Everything else is blocked without it.** Total size: S to M, about 1–2 weeks.

| # | Do | Why | Plugs into | Size |
|---|---|---|---|---|
| 0.1 | **One record per learner.** The server issues an anonymous signed device id (cookie); it replaces `LOCAL_USER = "local"` | Today every visitor shares one record, and "forget" wipes everyone. The code already says "this becomes an auth dependency and nothing below it changes" | `routers/progress.py:32`; the `user` column already exists in every table | S |
| 0.2 | **Log the wrong option picked**: `picked` plus *what kind of wrong option it was* | The diagnosis in Pick 1 is impossible without it | `QuizPanel.jsx:317`. `context` is free-form JSON already, so no schema change | S |
| 0.3 | **Record attempts from more tabs**: Memorise, Tamreen, Nahw practice | Today only Quiz, Grow and Colloquial write attempts | the same `recordAttempt` call | S each |
| 0.4 | **CI**: run the ~2,000 existing tests on every push | No CI today. Trust in the engine needs it | GitHub Actions | S |
| 0.5 | **Publish accuracy numbers**: run `score_iraab.py` on the held-out sets, write the result into a committed file, show it on the landing page | "Every answer has proof" needs a headline number: "x% of roles right on 258 blind sentences, y% shown as a gap, z% confident-wrong" | `backend/scripts/score_iraab.py`, `data/nahw_rules/*_sentences.json` | S |
| 0.6 | **Licence audit** (see decision D1) | Can't sell, raise money or claim database right on data we can't use commercially | `data/sources.json` already lists every source, so add a `commercial: yes/no/ask` field | S to do, ? to resolve |

## Done when

- Two browsers have two separate progress records.
- A wrong quiz answer is stored with its option and its probe kind.
- CI is green on the branch.
- An accuracy table is committed.
- Every source in `sources.json` has a commercial-use verdict.
