# Grow → Ahkaam: PRD + architecture plan

Status: plan only. No code changes yet.
Scope: the **Prayer world** first, as the template for every later ahkaam world (Fasting, Zakat, Hajj, …).

---

## Part 1 — PRD

### 1.1 Problem
Today the Prayer world only teaches *what you say* in salah (phrases, surahs, a few postures).
That is the "how do I recite it" layer. It does not teach the **fiqh**:
what is fard, what is wajib, what is sunnah, what breaks the prayer, and why scholars differ.

Learners normally get this from a book read in order, e.g. Mukhtasar al-Quduri, then Hidaya, then comparative works.
→ Goal: walk that same road, in that same order, but structured, gamified, visual.

### 1.2 Users
- A Muslim who prays but never studied fiqh → wants the basics, trustworthy.
- A student who knows one madhhab → wants depth, then the differences.

### 1.3 The learning ladder (per topic, e.g. Salah)
Each level unlocks only when the one before it is learnt (same rule the map already has).

| Level | Name | What is learnt | Main source |
|---|---|---|---|
| 1 | Foundations | Conditions (shurut), pillars (arkan/fara'id), wajibat, sunan, what breaks it, what is disliked. One madhhab, plain. | Mukhtasar al-Quduri |
| 2 | Depth | Same headings, now with the reason + daleel, edge cases (forgetting, the traveller, catching up). | al-Hidaya (Marghinani) |
| 3 | The big differences | Where the four schools differ on the *fundamentals* (e.g. is Fatiha a pillar? raising hands? what counts as a pillar vs wajib). | Bidayat al-Mujtahid (Ibn Rushd) + one primer per school |
| 4 | Fine differences | Minute comparative points, each school's position + its evidence. | Bidayat al-Mujtahid, al-Mughni, school matns |

Recitation (today's world) stays: it becomes one **strand** that runs alongside the levels (the "what you say" track), not a separate world.

### 1.4 Shape: Russian dolls
```
Realm (Ahkaam)
 └ World (Prayer)            ← the "prayer world"; later Fasting, Zakat…
    └ Level (1 Foundations … 4 Fine differences)
       └ Unit  (Conditions, Pillars, Wajibat, Sunan, Breakers, …)
          └ Card (one ruling, quoted)
             └ Exercises made from that card
```

### 1.5 Exercises (gamified, short)
Made *from* the cards, not hand-written one by one:
- **Sort it** → drag "wiping the head" into Fard / Wajib / Sunnah / Makruh / Breaks.
- **Put in order** → the acts of salah, or of wudu.
- **True or false** → "Laughing out loud breaks wudu in prayer."
- **Which school?** (levels 3–4) → match a position to Hanafi / Maliki / Shafi'i / Hanbali.
- **Why?** (level 2+) → pick the daleel behind a ruling.
- **Say it** → the existing recitation check, unchanged.

Scoring stays honest (as today): a card counts as learnt only when answered right on 2 different days.

### 1.6 Visuals
- Each world/level/unit can have a **faded background**: image or short looping video.
- **Rule: no humans or animals.** Architecture, mihrabs, prayer mats, water, light, calligraphy, geometry, sky.
- Motion switch on / reduced motion → video becomes its still poster.
- The map stays a **graph map** (the vine today); levels shown as gates, units as nodes.

### 1.7 Non-negotiables
- Every ruling is a **quote** from a named book + chapter, checked by a test against the book text (this already exists for Quduri, `tests/test_grow.py`).
- No ruling is the app's own words. English is a translation, marked as such.
- For level 3–4, each school's position cites that school's own book.

### 1.8 Success
- A learner finishes Level 1 Salah → can name every fard / wajib / breaker.
- Adding a new unit = editing one data file, zero code.
- Adding a new world (Fasting) = one data folder + one `worlds.json` line.

### 1.9 Out of scope (for now)
Fatwa questions, user-asked rulings, AI-written rulings, other worlds before Salah is done.

---

## Part 2 — How it is built today (explored)

```
worlds.json ── kind ──► GrowPanel SCREENS
                         ├ "lessons" → LessonWorld + use*World hook (SRS, server "known")
                         └ "prayer"  → PrayerWorld → GrowMap (vine) → StepSheet → Practice
grow.json   → tiers (basics/intermediate/advanced), clean-days, vine shape
backend/data/grow/paths.json  (1 file, ~1000 lines, 8 paths)
   path { tier, groups[], steps[] }   step { kind?, arabic | ayahs | instruction, ruling(quote) }
backend/models/grow.py  → pydantic types (icon list is a Literal)
lib/grow.js     → pure rules: judge, clean days, tiers unlock, mapOf, upNext
lib/growKinds.js→ registry: phrase / ayahs / action → how to check
tests/test_grow.py → quote must exist in the Quduri file
```

Good already (keep):
- Pure rule file (`lib/grow.js`), tested.
- Kind **registry** (`growKinds.js`) → new kind = one entry.
- Tiers + proposed topics are data.
- Quote test.
- Scenes registry (`scenes/index.js`).

Pain points for growing big:
1. **One giant `paths.json`** → every new unit edits the same 1000-line file.
2. **Step = "something to say"** baked in (`arabic` xor `ayahs`, test enforces it). A ruling card with no recitation doesn't fit.
3. **Kinds only say how to *check* audio**, not how to *show* an exercise. Practice.jsx knows recitation by heart.
4. **Tiers are global** (`grow.json`), not per world. Prayer's Level 1 ≠ Fasting's Level 1.
5. **`PrayerWorld` is named after one world** but is really "a path-map world". Fasting would copy it.
6. **Icons are a closed Literal** in Python + a JSX file → new picture = edit 2 places.
7. Only Quduri text is in the quote test; Hidaya + Bidaya (Marghinani) files exist; no Maliki/Shafi'i/Hanbali/Ibn Rushd text yet.

---

## Part 3 — Target architecture

### 3.1 Principle
**Content is data, behaviour is registries.** Code knows *kinds* (of card, of exercise, of scene). Data says *which* ones and *what* they say. No `if world === 'prayer'` anywhere.

### 3.2 Content on disk (one folder per world, one file per unit)
```
backend/data/grow/
  sources.json                 ← every book once: id, title, author, madhhab, file path
  worlds/
    prayer/
      world.json               ← levels, strands, backdrop, order of units
      L1-foundations/
        conditions.json
        pillars.json
        wajibat.json
        sunan.json
        breakers.json
      L2-depth/ …
      L3-differences/ …
      L4-fine/ …
      recite/                  ← today's paths.json, split (wudu, salah, surahs…)
```
→ New unit = new file. New world = new folder. Nothing else.

### 3.3 The card (one shape for everything)
```jsonc
{
  "id": "salah-pillar-qiyam",
  "kind": "ruling",                 // registry key: ruling | recite | action | difference
  "title": "Standing",
  "category": "fard",               // fard | wajib | sunnah | mustahabb | makruh | breaks | condition
  "quote": { "source": "quduri", "where": "باب صفة الصلاة", "arabic": "…", "english": "…" },
  "why":   { "source": "hidaya", "arabic": "…", "english": "…" },     // level 2+
  "positions": [                                                       // level 3–4 ("difference")
    { "school": "hanafi",  "category": "wajib", "quote": { "source": "quduri", … } },
    { "school": "shafii",  "category": "fard",  "quote": { "source": "abu-shuja", … } }
  ],
  "order": 3                        // for "put in order" exercises, optional
}
```
- `source` is an id into `sources.json` → quote test finds the right book file automatically → test covers every book, not only Quduri.
- Recitation steps become `kind: "recite"` cards with `arabic | ayahs` (today's step, unchanged meaning).

### 3.4 Registries (front end)
```
lib/grow/cards/       one file per card kind: { validate?, exercisesFrom(card, unit) }
lib/grow/exercises/   one file per exercise: { Component, check(answer) → right?, needs }
components/grow/scenes/  backdrops + map scenes (exists; extend)
```
- `exercisesFrom` → a ruling card with `category` gives "Sort it"; a unit with `order` gives "Put in order"; a `difference` card gives "Which school?".
- New exercise type = 1 file in `exercises/` + its kind names it. Practice.jsx just looks it up.
- Existing `growKinds.js` (phrase/ayahs/action) folds into `cards/recite.js` + `cards/action.js`.

### 3.5 Rules (pure, stay in one place)
`lib/grow.js` stays the single rule file, generalised:
- `isLearnt(record, cardId)` → same "right on 2 days" rule, for any card (not only recitation).
- Tiers → **levels per world** read from `world.json`, same unlock logic (`unlocked`, `mapOf`, `upNext`).
- Record key stays card id → progress made today survives (ids of today's steps kept as-is).

### 3.6 Screens
```
GrowPanel SCREENS
  lessons → LessonWorld        (unchanged: Words, Quran, Hadith)
  path    → PathWorld          (renamed from PrayerWorld, world-agnostic)
              ├ Backdrop       (faded image/video from world/level/unit data)
              ├ GrowMap        (levels = gates, units = nodes; strands drawn alongside)
              └ CardSheet      (renamed StepSheet) → Practice → EXERCISES[kind]
```
`worlds.json` prayer entry → `"kind": "path"`. Fasting later → same kind, own folder.

### 3.7 Backend
- `routers/grow.py`: `/api/grow/worlds/{id}` → reads the world folder, returns world + levels + units + cards. Cached like today.
- `models/grow.py`: `Card` as a discriminated union on `kind`; `icon` becomes a plain string checked by a test against the icon registry (so new icon = 1 place).
- Old `/api/grow/paths` kept until the front end moves, then removed.

### 3.8 Visual assets
```
frontend/public/grow/backdrops/manifest.json
  { "id": "courtyard-dawn", "file": "…webp", "video": "…webm"?, "poster": "…",
    "subject": "architecture", "credit": "…", "licence": "…" }
```
- `subject` must be one of: architecture, nature-no-animals, objects, geometry, calligraphy, sky, water.
- Test: every backdrop named in data exists in the manifest; manifest has credit + licence.
- The no-humans/animals rule is checked by a person at review time (a test can't see pictures); the `subject` field makes that review explicit.
- CSS: one `.grow-backdrop` layer, low opacity, behind content; video only when motion is on.

### 3.9 Tests (keep the trust promise)
- Quote test → loops every card's `quote`/`why`/`positions[].quote`, opens `sources.json[source].file`, asserts the Arabic is in it.
- Schema test → every unit file loads into the pydantic model; ids unique across a world.
- Level test → every level 3–4 `difference` card has ≥ 2 schools, each citing a book of *that* school.
- Front end → `grow.test.js` extended: unlock per world, `exercisesFrom` per card kind.

---

## Part 4 — Steps (each one a small PR, app works after each)

1. **Split data, no behaviour change.** `paths.json` → `worlds/prayer/recite/*.json` + `sources.json`. Router merges them back into today's response. Tests green.
2. **Quote test via `sources.json`** (covers any book). Add Hidaya file to sources.
3. **Card model + `/worlds/{id}`** endpoint. Recite cards = today's steps.
4. **Front end: PrayerWorld → PathWorld**, StepSheet → CardSheet, growKinds → `cards/` registry. Levels per world. Same look.
5. **Exercises registry** + first new exercise: *Sort it*. First real unit: **L1 Pillars of Salah from Quduri**.
6. Rest of Level 1 (conditions, wajibat, sunan, breakers) + *Put in order*, *True/false*.
7. **Backdrops** (manifest, layer, reduced-motion poster).
8. Level 2 (Hidaya, *Why?* exercise).
9. Add school books (OpenITI): Risala of Ibn Abi Zayd (Maliki), Matn Abi Shuja' (Shafi'i), Zad al-Mustaqni' / Umdat al-Fiqh (Hanbali), Bidayat al-Mujtahid (comparative). Then Level 3 + *Which school?*.
10. Level 4.

## Open questions (decide before step 5)
- Base madhhab for Levels 1–2: **Hanafi (Quduri)** assumed, since the app already quotes it. Later a learner could pick their school → Level 1 swaps books, same units.
- Background media source: self-made / licensed stock (Unsplash-style licence) / generated. Needs credit + licence either way.
