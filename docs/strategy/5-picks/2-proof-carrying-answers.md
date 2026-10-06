# Pick 2. Proof-carrying answers (AI fenced in)

**Learner outcome:** every explanation, even a friendly one written by AI, can be traced to a book
page or a corpus record. If it can't, the learner never sees it.

**Business outcome:** "Tafheem never makes things up" becomes a claim we can *prove* and put a
number on. This is the trust gap the research found (AI tafsir chatbots fabricating, a fatwa against AI
tafsir). Trust is the brand.

**Better than the brainstorm's version:** it wanted "RAG + citations + refusal" at request time. We
flip it:
1. **The rules make the claims; AI only phrases them.**
2. **AI runs at build time, not request time.** Its output is checked, frozen and cached, so it is
   fast, deterministic and reviewable.

## 1. Flow

```
question (e.g. "why is this word mansub?")
 → Layer 2 rules build a PROOF OBJECT (claims + where each came from)      ← no AI
 → template renders it as plain text                                     ← always works
 → (optional) look up a frozen AI phrasing for hash(proof, level, lang)  ← instant
      missing? → queue it for the build-time phraser, show the template now
 → build-time phraser: LLM gets the proof object, returns text with [c1] markers
 → CHECKER (whitelist):
      every sentence carries ≥1 marker that exists in the proof
      every Arabic term, grammar name, root, ayah ref, number in the text ∈ proof's allowed set
      no term from the "never say" list (fatwa words, sectarian labels…)
   pass → store, badge "ai-checked" (a new key in sources.json)
   fail → drop it, the template stays; the failure is logged for review
```

## 2. The proof object

```json
{
  "id": "sha256 of the inputs",
  "about": {"ayah": "67:2", "word": 5},
  "claims": [
    {"c": "c1", "kind": "role",  "value": "مفعول به", "rule": "naming_tree#maful-bihi",
     "source": "tasheel-nahw", "where": "p.112"},
    {"c": "c2", "kind": "sign",  "value": "الفتحة", "rule": "teacher.signs#mansub-singular",
     "source": "tasheel-nahw", "where": "p.31"},
    {"c": "c3", "kind": "record","value": "OBJ", "source": "corpus", "where": "67:2:5"}
  ],
  "allowed_terms": ["مفعول به", "منصوب", "الفتحة", "…"],
  "confidence": "verified"
}
```

Most of this already exists in pieces:
- **role + page**: walker → `naming_tree.json`
- **sign**: `signs.py`
- **reasons**: `teacher.json`
- **source**: `provenance.py`

Pick 2 = give these pieces **stable ids** and gather them into one object.

## 3. Where it applies (in order)

| Use | Today | With Pick 2 |
|---|---|---|
| I'raab card "why" line | template from atoms ✅ | + level-aware phrasing (teen / adult / teacher) |
| Pick 1 fix cards | — | friendly wording, checked against the probe's proof |
| Sarf "meaning" (LLM today, "guessed") | unchecked | roots and patterns checked → upgraded to "ai-checked" or dropped |
| Maqayees → English (LLM, "~1 in 50 wrong") | only a line-count guard | terms checked against the Arabic entry's words + the dictionary |
| Open questions ("what does this ayah teach?") | not offered | **still not offered.** We stay out of open tafsir on purpose (see decision D4) |

## 4. Why it's fast

- The live request is a key lookup in a frozen table.
- The phraser runs as a nightly batch over the most-viewed proofs: the top N ayahs × 3 levels × 2–3 languages.
- A miss shows the template at once. Nothing waits on a model.

## 5. Build slices

| Slice | What | Size |
|---|---|---|
| 2a | Stable ids for atoms (rules, signs, reasons, note blocks) + a prerequisite link field | S–M |
| 2b | Proof object from the i'raab pipeline (gather what is already computed) | M |
| 2c | Whitelist checker + `ai-checked` source key + failure log | S–M |
| 2d | Build-time phraser script + frozen table + a review page in `/app?tab=kit` | M |
| 2e | Move the 3 existing LLM features behind the checker | S each |

## 6. What's protectable

- **Copyright**: the frozen, reviewed explanation library (original text).
- **Database right**: the proof-linked atom store.
- **Trade secret**: the checker rules and the never-say list.
- **Brand**: the published accuracy + "ai-checked" numbers (from Pick 0.5).
- **Patent**: the technique is crowded (ALCE, RARR). Don't file.
