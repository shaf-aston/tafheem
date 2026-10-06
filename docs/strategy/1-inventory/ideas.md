# Step 1. Every idea, written down once

Source: an outside AI's brainstorm (3-layer "fast data + fast AI", "IP novelties", "deep tech",
"vocabulary mastery engine"). Its many lists repeat each other. This file merges them into one list
with one ID per idea, plus 3 ideas the code audit surfaced (marked **ours**).

Flow: brainstorm (≈40 bullets) → merge duplicates → 16 ideas → assessed in `../3-assessment/`.

## A. Plumbing (generic architecture, not new)

| ID | Idea | Merged from |
|---|---|---|
| I11 | Generic stack: API gateway/BFF, Postgres, Redis, OpenSearch/Meilisearch, Kafka/SQS, Pinecone/pgvector, model router (tiny/medium/large model) | Layer 1–3 "obvious" architecture |
| I9 | Offline-first "learning state capsule": compact learner state on device, synced by deltas, open app → continue in <1 s | Layer 1 novelty, edge cache, IndexedDB |
| I10 | Accounts → payments → "upgrade trigger map": learning moments (plateau, repeated confusion) mapped to premium prompts | Novelty 6 |

## B. Trust (answers you can check)

| ID | Idea | Merged from |
|---|---|---|
| I1 | Verified generation: every claim tied to an approved source, refuse if it can't be cited, per-claim confidence, structured JSON output | "Trust-by-Sources", "V-Gen", "SGVG", "truth layer", "VOG" |
| I8 | Explanation atoms: tiny stored pieces (definition, rule, exception, example, misconception fix) put together per level, so AI composes instead of inventing | "Explanation atoms", "precompute + assemble" |
| I12 | Teen safety policy engine: age mode, no fatwa, no sectarian debate, audit log | Novelty 7 |

## C. Language engines

| ID | Idea | Merged from |
|---|---|---|
| I2 | Hybrid rules + small model for Arabic morphology/syntax: rules first, model only when rules tie | "HAMP", "multi-layer morphology engine" |
| I3 | Word Identity Graph: token → lemma → root → pattern → POS → **sense in this ayah**, with edges (same root, confused-with, occurs-in) | "Micro-index", "WIG", "SCD", knowledge graph |

## D. Learning engines

| ID | Idea | Merged from |
|---|---|---|
| I4 | Diagnostic vocabulary engine: wrong answer → *why* wrong (root / pattern / sense / POS / synonym confusion) → smallest fix → 1-question check → mastery at sense, lemma, root level → plan next exposure | "VME", "misconception model", "MC", "MIL", "EP" |
| I5 | Pedagogy router: picks teaching *strategy* (analogy, rule-first, example-first, quiz-first) by learner state | Novelty 3 |
| I6 | Teacher lesson compiler: teacher writes a short intent → app builds screens, quizzes with provable answer keys, hints, class report | "LCAG", "Teacher Mode Compiler" |
| I7 | Recitation feedback as an "error lattice" with tajweed rules and beginner-first priority | Novelty 5 |

## E. Ours (found by the code audit, not in the brainstorm)

| ID | Idea | Why it came up |
|---|---|---|
| I13 | **Learner identity**: one record per learner, not one shared `'local'` record for every visitor | `backend/routers/progress.py:32`. Today all visitors share one progress record. Every learning idea above needs this first |
| I14 | **Hadith chain check**: does every teacher→student link in an isnad exist in the narrator graph? Plus a tab for al-Tahawi's *Mushkil* (hadith that seem to clash, and how he reconciles them) | The `tie` + `mention.ord` tables make this computable; Mushkil data is built and no tab reads it |
| I15 | **Qur'an coverage meter**: "you know 41% of the words in Surah al-Mulk" = known lemmas × how often each occurs | The corpus has every occurrence and FSRS already knows which words are known. This is an outcome a learner can feel |
