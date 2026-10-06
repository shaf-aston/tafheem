# Strategy: what to build next, and why

Status: **for review. No code has changed.** Written 2026-10-06 from an outside AI's brainstorm,
a code audit of this repo, and web research.

## The logic flow (one folder per step)

```
1-inventory/        every idea written once (16 IDs)
      ↓
2-where-we-are/     business position + usefulness to a learner + what's already built
      ↓
3-assessment/       impact against complexity: scores, chart, risks
      ↓
4-research/         competitors, prior art, UK IP reality, price anchors
      ↓
5-picks/            the chosen few, each in detail + what's parked or rejected
      ↓
6-architecture/     the 3-layer design they all sit in
```

Evidence files (long, raw, with file:line and URLs):
- `2-where-we-are/audit-evidence.md`
- `4-research/market-prior-art-ip.md`

## The answer in 30 seconds

**Where we are:** the best engine in the market for *understanding* an ayah (rules not AI, proof on
every answer). But the product **can't remember a learner, can't show progress, can't take money**,
and some data licences may block selling.

**The gap for a learner:** not "understand". It is **"remember + see that I'm growing"**.

**The picks, in build order:**

| # | Pick | Learner gets | Moat | Size |
|---|---|---|---|---|
| 0 | [Foundation](5-picks/0-foundation.md): one record per learner, log the wrong option picked, CI, published accuracy, licence audit | progress that is theirs | trust numbers | S–M |
| 1 | [Diagnostic vocabulary engine + coverage meter](5-picks/1-diagnostic-vocab-engine.md) | "I know 62% of Surah Mulk's words" + the app fixes *why* they got a word wrong | the probe taxonomy (trade secret) + repair data loop | M |
| 2 | [Proof-carrying answers](5-picks/2-proof-carrying-answers.md): AI only rephrases a checked proof, at build time | friendly explanations that are never made up | brand + reviewed explanation library | M |
| 3 | [Word graph with senses](5-picks/3-word-graph-senses.md) | "this word means *this* here" + family, look-alikes, false friends | **database right** on a curated, human-checked dataset | L, sliced |

Parked with triggers: teacher mode, tajweed, hadith chain check, offline PWA, payments →
[parked-and-rejected.md](5-picks/parked-and-rejected.md).

**The novel core:** wrong options are **built on purpose as probes**, so the learner's wrong pick
*is* the diagnosis. That is deterministic, explainable and needs no AI. Add a Qur'an-specific word
graph (with an **Urdu false-friend** probe nobody else has), and AI is fenced to phrasing checked
proofs at build time.

**Architecture** ([three-layers.md](6-architecture/three-layers.md)): **Facts → Rules → Words(AI)**,
layered by *trust*, not by server. Requests look things up; they never wait for a model. The
Postgres + Redis + Kafka + vector-DB stack from the brainstorm is rejected as slower for us.

## Decisions for you to review

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | Licences: Quranic Arabic Corpus ("non-commercial" note beside GPL), sunnah.com scrape, Bayna Yadayk decks, "80% words" book, Quran.com glosses | (a) ask each owner for commercial permission, (b) replace the risky sources, (c) stay free/non-profit | **(a) now**, with (b) as the fallback. Email the corpus team first: all grammar data depends on it |
| **D2** | Who is the first paying customer? | (a) adult self-learner subscription, (b) madrasah / teacher B2B, (c) stay free, donations | **(a) first** (needs only Picks 0–1). Run ~10 teacher interviews in parallel to test (b) |
| **D3** | Learner identity | (a) anonymous device id, (b) email accounts, (c) Google/Apple sign-in | **(a) now** (no personal data, no minors' privacy load). (b)/(c) when payments or teachers arrive |
| **D4** | Open-ended AI Q&A ("what does this ayah teach?") | (a) never, (b) later, behind the proof checker and tafsir citations only | **(a) for now**. Staying out is part of the trust story |
| **D5** | Patents | (a) file now, (b) pay for one IP-attorney hour + rely on database right / trade secret | **(b)**. Keep a dated build log of the probe taxonomy and sense grouping as evidence of investment |
| **D6** | Build order | 0 → 1 → 2 → 3, or 0 → 3 → 1 → 2 (data first) | **0 → 1a/1b/1c → 3a → 2 → 3b/3c → 1e**. Each step ships something a learner feels |

## Not covered (gaps to know about)

- US law (Alice) and a full patent search were not researched. Do a freedom-to-operate check before any tajweed work.
- Market size has no reliable figure; only price anchors.
- Accuracy numbers could not be run in the audit sandbox (Pick 0.5 fixes that).
