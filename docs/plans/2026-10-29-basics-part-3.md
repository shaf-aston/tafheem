# Basics, part 3: more of what a word can carry

Date 2026-10-29. Follows `2026-10-23-basics-word-forms.md` (its tier list) and the Basics audit of 2026-10-28.

## Why

The Basics path taught ال and six skills (my/his, past, present, not, do!/don't!, will), then 78 more ال words in a
row: one rule, drilled long after it was learnt. Tier 1 skills were still missing, and nothing taught a beginner what
the verb forms II–X *mean*: the Sarf world covers them as a classical book (Marāḥ al-Arwāḥ), not as "what does this
pattern add?". A live bug too: picking a misspelt verb (*لَمْ كَتَبَ) explained itself as "… undefined".

## What, in two PRs (same engine: markers on a table, asked both ways, wrong options never also right)

**3A · nouns** (this PR)

| Skill | Markers | Table, drawn on |
|---|---|---|
| `people` One and many | ة a woman · ـُونَ men · ـَات women | `peopleTable`, basics.json `people` (sound plurals only) |
| `joined` And, with, for, like | وَ · بِـ · لِـ (ال loses its ا: لِلْـ) · كَـ | `joinedTable`, things "with the …" fits |
| `this` This, that | هٰذَا/هٰذِهِ + word = this is a … · + ال word = this … · ذٰلِكَ/تِلْكَ the same | `pointingTable`, things whose gender the ة shows |

- Wrong forms: one-letter words written apart (*وَ الْكِتَاب), لِ keeping ال's ا (*لِالْكِتَاب), the wrong gender
  (*هٰذِهِ كِتَاب). Every misspelling, old ones included, has its own explanation.
- Path: 46 ال words woven between the skills, the rest left out (they stay in basics.json as the nouns the skills draw).
  Ids never change, so progress stays. 86 items; stages 10 · 25 · 45 · 65 · 86.

**3B · verbs** (next PR)

| Skill | Markers | Source |
|---|---|---|
| `object` Him, her, me | ـهُ ـهَا ـهُمْ ـنِي ـنَا ـكَ ـكُمْ on the past | basics-verbs.json, verbs that take a person |
| `patterns` Verb forms II–X | one meaning each: II do to someone / a lot, III with someone, IV make happen, V to yourself, VI each other, VII it got done, VIII for yourself, X ask for it | the conjugation engine, families curated in `backend/data/grow/basics_verbs.json` |

Each pattern is asked twice: what the pattern adds (its meaning), and what one real verb on it means beside its
Form I (عَلِمَ he knew → تَعَلَّمَ he learnt).

## Left for later, and why

- هُوَ/هِيَ/أَنَا as words, الَّذِي: whole sentences with agreement ("I am a teacher" is مُعَلِّم or مُعَلِّمَة), a new card shape.
- Idafa (كِتَابُ اللهِ), questions هَلْ/أَ, the dual, broken plurals: as in part 2's tier list.

## Checks

- Every marker, every word, 25 seeds: 3 options, one right, no wrong one that can mean what was asked (the part-2 test,
  now over every table).
- No explanation says "undefined"; every misspelling kind has its line.
- Data: people are sound plurals with a vowelled singular; pointed things have the gender their ة shows; no joined
  thing starts with ل (لِ + اللَّيْل is spelt differently).
- vitest, eslint green; the path's length is the last stage.
