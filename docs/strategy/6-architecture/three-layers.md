# The 3-layer architecture: fast data, fast AI, AI fenced in

The brainstorm's 3 layers were **edge → app + database → AI**. Those are *where code runs*. That
shape works for any app, so it gives nothing special.

Ours splits by **how much we trust each layer**. That gives speed and trust from one design.

```
          ┌────────────────────────────────────────────────────────────┐
LAYER 3   │ WORDS  (optional AI, fenced)                                │
          │ only rephrases or translates a proof it is handed;          │
          │ can never add a claim. Output checked, frozen, cached.      │
          └───────────────▲────────────────────────────────────────────┘
                          │ proof object (claims + sources)
          ┌───────────────┴────────────────────────────────────────────┐
LAYER 2   │ RULES  (deterministic engines, pure functions)              │
          │ i'raab walker · sarf + i'lal · diagnosis engine ·           │
          │ FSRS scheduler · coverage meter · proof checker             │
          └───────────────▲────────────────────────────────────────────┘
                          │ lookups (read-only)
          ┌───────────────┴────────────────────────────────────────────┐
LAYER 1   │ FACTS  (built ahead of time, read-only, every row sourced)  │
          │ corpus.db · word graph · atoms (rules, signs, notes) ·      │
          │ lexicons · rijal graph · recitation checks                  │
          └────────────────────────────────────────────────────────────┘
   Thread through all 3:  LEARNER STATE (one record per learner: attempts, picks, FSRS)
```

## Why this is fast

| What the brainstorm used | What we do instead | Why ours is faster for us |
|---|---|---|
| Postgres + Redis + Kafka | SQLite files built by scripts, opened read-only (`readonly_db.py`) | A lookup in a local file takes microseconds. No network hop, no cache to keep fresh, no servers to run |
| Vector DB for "AI" | Indexes on root, lemma and ayah:word, which already exist | The questions are exact ("every place this root occurs"), not fuzzy |
| Model router picking small or big LLMs at request time | **AI moved to build time.** Phrasings are made once per (proof, level, language), checked, stored | Request time = a lookup. The LLM is not on the hot path at all |
| Edge cache for everything | Facts are content-addressed (`hash of inputs → answer`). Static parts can go on a CDN later | The same answer is never computed twice |

**Rule of thumb:** a request should *look up* or *walk rules*. It should never *wait for a model*.
The only model kept on the live path is listening to recitation, where the input is new audio.

## Why this is trustworthy

1. **Facts** carry their source (already true: `services/provenance.py`).
2. **Rules** carry the rule id and book page (already true: walker → `naming_tree.json` page).
3. **Words** (AI) get a *proof object* and must return text whose every term is in that proof.
   A whitelist checker enforces it. A failed check falls back to the plain template. AI can make an
   answer *nicer*, never *different*.

→ "Deterministic AI": the AI's output is fixed (frozen at build time) and bounded (cannot leave the
proof), so the same question always gets the same answer.

## Where each pick lives

| Pick | Layer 1 (facts) | Layer 2 (rules) | Layer 3 (words) |
|---|---|---|---|
| 0 Foundation | licence-clean sources | learner record per person | — |
| 1 Diagnostic vocab engine | graph edges used as probes | probe builder, diagnosis, scheduler, coverage | optional friendly wording of a fix |
| 2 Proof-carrying answers | atoms with ids | proof builder + checker | the fenced phraser |
| 3 Word graph + senses | the graph itself | sense assignment rules + review queue | optional: propose a sense (marked "guessed" until a person approves it) |
