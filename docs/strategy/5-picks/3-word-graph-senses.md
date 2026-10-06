# Pick 3. The Qur'anic word graph, with senses

**Learner outcome:** tap any word → see *which meaning it has in this ayah*, its family, its
look-alikes and its false friends. That is one answer, not five tabs.

**Business / IP outcome:** this is **the deepest moat**. It is a curated, sourced, human-checked
dataset. That is exactly what UK database right protects, and it improves with every review.
Picks 1 and 2 grow more powerful on top of it.

## 1. What exists vs what's new

| Part | Exists? | Where |
|---|---|---|
| Word → lemma → root → POS, every one of the ~77k words | ✅ | `corpus.db segment` |
| Meaning of each word in its ayah (English, Urdu), as plain text | ✅ | `meanings.db` (Quran.com word-by-word) |
| Root origin sense | ✅ | Maqayees, 4,738 roots |
| Root → every occurrence | ✅ | `quran_corpus.occurrences_of_root` |
| Look-alike / sound-alike | ✅ | `soundalike.js` |
| Urdu cognate / false friend | ✅ (candidates + approved overrides) | `urdu_links*.json` |
| Twin verses | ✅ | `mutashabihat.json` |
| Noun patterns (awzan) | ❌ | new rule table in `data/sarf/` |
| **Sense inventory per lemma + which sense each word uses** | ❌ | **new, the hard part** |
| One store + one API joining all of it | ❌ | new `word_graph.db` + `services/word_graph.py` |

## 2. How to get senses *without* an AI guessing them

The trick: we already have a per-word, in-context gloss (`meanings.db`). Those glosses are human
translations, so the sense is *already chosen* by a person, word by word. We only need to **group
them**.

```
for each lemma:
  collect its contextual glosses across all occurrences       (e.g. ضَرَبَ: "strike", "set forth", "travel", "struck")
  normalise (lowercase, strip "he/they", stem)                 → rule-based
  group the glosses that match a dictionary sense of the lemma  → Wiktionary / Lane sense lists
  leftovers → their own group, flagged
  each group = a sense_id; each occurrence → its sense_id
  label every sense "derived"; a person approving it makes it "verified"
```

- **Deterministic**: the same input always gives the same groups.
- **Explainable**: "grouped because both glosses say *set forth*".
- **AI optional**: it may *propose* a merge, marked "guessed", that a person approves.
- **Scale**: only lemmas with ≥2 different gloss groups need review. Most of the 382 high-frequency
  words first: they cover about 80% of what learners meet.

## 3. Graph shape

Nodes:
- `token(s:a:w)`
- `lemma`
- `root`
- `pattern`
- `sense`

Edges, each with `source` + `confidence`:

| Edge | From → to | Feeds |
|---|---|---|
| `is_lemma`, `has_root`, `has_pattern` | token → lemma → root / pattern | everything |
| `means_here` | token → sense | P3 probes, the "this ayah" meaning |
| `same_root` | lemma ↔ lemma | P1 probes, root-family cards |
| `same_pattern` | lemma ↔ lemma | P2 probes, pattern cards |
| `looks_like` | lemma ↔ lemma (rasm / sound fold) | P4 probes |
| `urdu_false_friend` | lemma → Urdu sense | P5 probes |
| `near_synonym` | lemma ↔ lemma | P6 probes |
| `twin_verse` | ayah ↔ ayah | Memorise |

Stored as plain SQLite tables, read-only, the same pattern as `readonly_db.py`. No graph database is needed.

## 4. Build slices

| Slice | What | Size |
|---|---|---|
| 3a | `word_graph.db` built by one script that joins the existing stores (no senses yet) + `services/word_graph.py` | M |
| 3b | Noun pattern table + `has_pattern` edges | M |
| 3c | Sense grouping for the 382 high-frequency lemmas + a review queue in the kit page | L |
| 3d | Senses for the rest, review in order of frequency | ongoing |

## 5. Licence note

Senses grouped from Quran.com glosses inherit their licence. This needs checking (decision D1). Our
*grouping, review and arrangement* is our own investment, which is what database right protects.
