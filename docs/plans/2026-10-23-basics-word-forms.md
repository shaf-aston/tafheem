# Basics, part 2: how small additions change a word

Date 2026-10-23 · `/lifecycle`. This follows `2026-10-23-basics-alif-lam.md`, where ال was the first skill.

## 1 · Requirements

**Who:** the Basics learner: new to Arabic, already met ال.

**Ask (user):** quiz the forms a word takes and what each one means:
- tense: past, present, future
- سَ on a verb
- command
- negation: which particle, and what it does to the verb
- gender and number
- translation of each form

Work out the full set of criteria, not just these examples. Reuse what exists, don't rebuild the data, and show the English parallel.

| # | Criterion | Check |
|---|---|---|
| F1 | Each skill teaches one **marker** (a prefix, suffix or particle) → its meaning → the English way of saying it | each marker's teach card shows the form, its English, the base form beside it and the rule |
| F2 | Questions both ways: "which one is 'she wrote'?" (3 Arabic options) and "what does كَتَبَتْ mean?" (3 English options) | both card types for every marker |
| F3 | **Wrong options are never also right.** An option is wrong only if no reading of it is the asked meaning (تَكْتُبُ = she writes *and* you write; لَمْ يَكْتُبْ = مَا كَتَبَ = he didn't write; سَيَكْتُبُ = سَوْفَ يَكْتُبُ) | property test over every verb, person and marker |
| F4 | Wrong options are the same word in its other forms, or the same word formed wrongly (*لَمْ كَتَبَ, *سَكَتَبَ, *الْكِتَابُهُ) | per-marker unit tests; every option contains the word's root letters |
| F5 | Verb Arabic comes from the app's own engine (`backend/services/sarf/conjugation.py`) and nothing is typed by hand | build script plus a freshness test: the shipped JSON equals a fresh build |
| F6 | The English is hand-checked per verb (write / wrote / writes); per-person wording comes from templates | data test: three forms for each verb |
| F7 | One Basics world with one path. The skills are interleaved with the ال words in a data-defined order; existing ال progress ids are unchanged | path test; ids of the existing 128 words unchanged |
| F8 | The marker is what is learned: the verb or noun on each card is drawn at random from the list, so the learner generalises instead of memorising | cards for one marker draw different verbs |
| F9 | No Qur'an text is altered or shown as Qur'an; a "wrong" form is never a valid spelling with the asked meaning | F3 plus the Arabic reviewer lane |
| F10 | Mutation score ≥ 90% on the new pure modules; full suite and lint green; axe 0 violations at 375 px | Stryker, vitest, eslint, Playwright |

## 2 · Research (two lanes; the full reports are kept in the session)

**Codebase lane**
- `conjugation.conjugate(root, form)` gives 14 persons × past, present, command and لا + jussive, plus passives. It is offline, deterministic, and has been checked live.
- There is no subjunctive column; لن is derived from the indicative or jussive. سَ, سَوْفَ, لَمْ and مَا are particles placed in front of an engine form.
- No gloss source can be templated from. Dictionary and words.json glosses are multi-sense or copied from one ayah, so the per-verb English must be hand-curated.
- The bab of each verb can be cross-checked against `verb_forms.babs_of`.
- Nothing generates noun forms; the attached-pronoun endings are in `nahw_rules/closed_words.json`.

**Web lane** (Madinah books 1–3, Understand Qur'an course 1, Duolingo, and the QAC corpus counted by the agent)
- Order: noun endings (possessive ـي ـهُ…, idafa, attached و/بِـ/لِـ, ة) → past persons → present persons → negation → command and prohibition → future → questions.
- Qur'an counts:

  | Form | Count |
  |---|---|
  | Past verbs | 9,150 |
  | Present verbs | 8,330 |
  | Command verbs | 1,876 |
  | Attached pronouns | 12,235 |
  | لا (not) | 1,364 |
  | مَا (not) | 704 |
  | لَمْ | 353 |
  | لا (don't!) | 327 |
  | لَنْ | 104 |
  | سَ | 119 |
  | سَوْفَ | 42 |
  | Duals | 237 |

  So future and the dual come late.
- Understand Qur'an: the six persons هو هم أنتَ أنتم أنا نحن cover 92.7% of past verbs, and adding هي covers 98.9%.
- Common errors, used as distractors:
  - masculine as the default (he for she);
  - ي for "she" in the present;
  - a particle with the wrong tense (*لَمْ كَتَبَ);
  - ال together with a possessive ending.
- Contrasts carried only by vowel marks are harder, so letter or particle contrasts come first.

### The full criteria list: every beginner form skill, tiered

**Tier 1 (beginner):**
1. ال (done)
2. Possessive endings
3. Idafa
4. Attached و فَ بِـ لِـ كَـ
5. Feminine ة
6. Past persons
7. Present persons
8. Command
9. Negation: لا, لم, لن, ما, prohibition
10. Future سَ / سَوْفَ
11. Question هَلْ / أَ
12. Sound plurals ـونَ / ـات

**Tier 2:** broken plural (recognise only), dual, nisba ـيّ, tanween as "a", يا, إنَّ, feminine and plural verb agreement, ليس.

**Tier 3:** verb forms II–X, participles, passive, mood endings, weak verbs.

**This build: possessive, past, present, negation, command and prohibition, future.** These are the user's examples, ranked by frequency, and all are generated from data that already exists. Deferred, with the reason for each:

| Skill | Why deferred |
|---|---|
| ة | needs a hand-made list of human-noun pairs |
| Idafa, attached و/بِـ/لِـ | sentence-level; needs case endings |
| Plurals | broken plurals need curation |
| Questions, ليس | different card shape |
| Dual | rare |

## 3 · Architecture

### Candidates

| | Speed | Quality | UX | Maintainable | Novelty | Σ |
|---|---|---|---|---|---|---|
| **A · One Basics path.** Items are ال words plus **marker items** (`past:she`, `neg:lam`, `mine:his`); a skill registry builds each item's cards; verbs come from a build-time JSON exported by the engine | 3 | 4: Arabic from the tested engine; one pure option picker that rules out ambiguity, mutation-tested | 4: one path, skills unlock in order, each a few markers | 4: a skill is one entry in the registry and one line of path data | 3: the learner tracks markers, not words | **18** |
| B · A Grow world per skill (Basics · Verbs, Basics · Negation…), each its own module | 3 | 3 | 2: Grow home grows by 6 tiles; Today must pick between them | 2: 6 hooks, and the pacing between worlds has no owner | 1 | 11 |
| C · Ask the live API for tables at lesson time | 2 | 3 | 2: needs the network; a slow first card | 3 | 1 | 11 |

**Pick A.**
- B loses because a beginner's path is one ordered thing; split across worlds, its order lives nowhere.
- C loses because it is offline-hostile and runs CAMeL/engine paths on every lesson. A build-time export gives the same Arabic every time, and the export can be reviewed as a whole file.

### Levels 1–2: unchanged
SPA → static `/grow/*.json` and the progress API.

### Level 3: components (★ = new)
```
★ backend/data/grow/basics_verbs.json    curated: root, bab, English {base, past, s3}
★ backend/scripts/grow/build_basics_verbs.py  engine → frontend/public/grow/basics-verbs.json (7 persons × past/present/subj/juss, command)
★ tests/sarf/test_basics_verbs.py             fresh build == shipped; bab == babs_of; shapes
★ lib/grow/wordForms.js (pure)                a verb's table and a noun's possessive table → entries {key, ar, en};
                                         readings; ambiguity-safe option pickers
★ lib/grow/basicsSkills.js (pure)             SKILLS: markers, teach/asks per skill; path → ordered items; basicsCards
  lib/grow/alifLam.js                         the 'al' skill (unchanged logic)
  lib/grow/useBasicsWorld.js                  loads both JSON files and builds the path
  TeachCard                              ★ optional `note` line (the marker's rule)
  public/grow/basics.json                ★ `path`
  worlds.json                            stages over every item
```

### Level 4: contracts
```js
// wordForms.js
PERSONS: [{id:'he', subj:'he', s3:true}, 'she', 'they', {id:'you', hint:'one man'}, 'you-all', 'I', 'we']
verbTable(verb): Entry[]            // Entry {key:'past:she', ar, en}; keys past|present|future|future-sawfa|not|not-past|not-past-ma|not-future (×7)
                                    // + command|prohibit (×you, you-all); malformed: wrong:sa-past|wrong:sa-apart|wrong:lam-past|wrong:lan-past (en null)
possessiveTable(word): Entry[]      // mine:my|your|his|her|our|your-all|their, + wrong:al|wrong:ta (ة kept); en null for wrong ones
                                    // no wrong:al:my unless the noun ends in ة (ال + ـِي can be a real word: الْجَارِي)
canPossess(word): boolean           // ends on a plain consonant or ة, no final shadda, no alif/hamza/weak letter
meanings(entries): Map<ar, Set<en>>
arabicOptions(entries, key, pool, random, n=2) -> [{id, text}]   // id 'right' plus the picked keys
englishOptions(entries, key, pool, random, n=2) -> [{id, text}]
// basicsSkills.js
SKILLS: {[skill]: {title, table:'verbs'|'nouns', markers:[{id, key, base, persons, rule, pool:[keys], toEnglish?:[keys]}]}}
                                    // toEnglish: the pool for the English direction when it differs (future: the bare present can say will)
pathItems(words, {verbs, path=[]}) -> Item[]   // ال words + marker items {id:`${skill}:${marker}`, skill, marker, words}
                                    // verbs null (file not loaded) → the verb skills are left out; the words always come
basicsCards(picked, random, intro) -> Card[]
```
- **Records:** `{module:'basics', item: item.id, context:{world:'basics', skill, direction, word: <the form asked>, from: <verb or noun id>, person?}}`.
- **Seam:** a new skill is one `SKILLS` entry plus one path line. Its Arabic comes from a table function, and the picker already rules out ambiguity.

### Gate
- Every L3 box maps to the SPA or the build.
- Every name used below is listed above. ✔

## 4 · Plan: vertical slices

| # | Slice | Check | Pre-mortem: "fails because…" |
|---|---|---|---|
| 1 | Curated verbs + build script + pytest | fresh == shipped; bab == babs_of; every cell vowelled | the engine's vowelling differs between verbs → sound Form I only, roots with no final ت/د/ط/ن/ث (assimilation) |
| 2 | `wordForms.js` tables + pickers | F3 property test over all verbs × keys | synonyms leak in as wrong options → meanings computed per Arabic string, not per key |
| 3 | `basicsSkills.js`: SKILLS + path + cards; hook and data | ids unchanged; path order; F8 | the ال intro or begunHere breaks → keep its tests as they are |
| 4 | TeachCard `note`, stages, copy | screen test: a marker lesson plays end to end | Today's "{fresh} new words" wording → reads "new steps" for Basics |
| 5 | Verify: Arabic reviewer, code reviewer, Stryker, Playwright + axe | findings fixed | — |

## 5 · Risks
- Vowel-only contrasts (كَتَبْتُ / كَتَبْتَ / كَتَبَتْ) are unavoidable in the past tense. Where a letter contrast exists it is preferred; the singular prohibition is never set against لا + present.
- لا + present in the Qur'an often means "will not". The card says "doesn't", the usual beginner gloss.
- Same shared guest record as before (Pick 0.1).
- A returning learner's service worker may hold an old `basics.json` with no `path`, or lack `basics-verbs.json` offline → `pathItems` defaults the path and skips skills with no data, so the 128 words always load.
- A lone vowel mark in a rule line (“the last ُ”) draws on a dotted circle → rules write marks on ـ (ـُ, ـْ); a test checks every rule.

## 6 · Verify results
- **Arabic reviewer:** all 20 verbs × 95 forms correct; no malformed distractor is a real word. Fixed: لا vs لن (لا can mean “won’t”, so not-future is never its distractor), the مَا rule, the command's اُ/اِ rule, ال + ـِي distractors (الْجَارِي), body nouns dropped from the possessives, the glosses for دخل (enter) and شكر (give thanks). Kept: “Hear!”, “Know!”.
- **Code reviewer:** no serious bugs. Fixed: robust load (above), the bare present offered as wrong for “will” (now only in the English direction), lone marks in rules, records without the verb/noun and person. Each fix has a test that fails without it.
- **Playwright + axe** at 375px, light and dark: 0 violations, no sideways scroll.
- **Tests:** vitest full suite, eslint, pytest (63) green; Stryker on wordForms.js + basicsSkills.js below.
