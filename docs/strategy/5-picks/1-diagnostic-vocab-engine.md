# Pick 1. Diagnostic vocabulary engine (+ coverage meter)

**Learner outcome:** "I understand 62% of the words in Surah al-Mulk, up from 41% last month. And
when I get a word wrong, the app knows *why* and fixes exactly that."

**Better than the brainstorm's version:** it wanted an ML "misconception classifier" to guess *why*
an answer was wrong. We don't need to guess. **We build each wrong option on purpose to test one
specific confusion.** Then the option the learner picks *is* the diagnosis. That makes it
deterministic, explainable and testable, and it needs no AI.

## 1. The idea in one flow

```
pick a word to ask  →  build 3 wrong options, each a PROBE of one confusion
                    →  learner answers
right → FSRS "good"     wrong → the probe they fell for = the diagnosis
                    →  show the matching tiny FIX (10–20 s card, from stored atoms)
                    →  ask 1 RE-CHECK of the same confusion on a different word
                    →  update memory at word level, and move "confusion counters"
                    →  plan what comes next (due reviews + biggest coverage gain)
```

## 2. The probe kinds (the core know-how)

Each wrong option is chosen from one relation in our data. The relation **is** the label.

| Probe | Wrong option is… | Example (answer → probe) | Data it comes from (exists?) |
|---|---|---|---|
| **P1 same root** | another word from the same root | عِلْم *knowledge* → عَالِم *scholar* | corpus `segment.root` index ✅ |
| **P2 same pattern** | same mould, different root | مَكْتُوب → مَعْلُوم | verb forms ✅; noun patterns ❌ (Pick 3 adds them) |
| **P3 other sense** | same word, its meaning in a different ayah | *ḍaraba* "strike" vs "set forth (a parable)" | needs senses ❌ (Pick 3) |
| **P4 look-alike** | letters differ only by dots, or sound alike | نَصَرَ / نَظَرَ | `soundalike.js` groups ✅; a dot-skeleton (rasm) fold is new, small |
| **P5 Urdu false friend** | the meaning the word has in Urdu | آخَر *other* → "at last" (Urdu) | `urdu_links.json` verdicts ✅ (overrides approved) |
| **P6 near synonym** | a close word with a different shade | خَوْف / خَشْيَة | dictionary synonyms ✅, partial |
| **P7 job confusion** | a particle read as a noun or verb, or the reverse | مَا "what" vs مَا "not" | `particle_tree.json`, `closed_words.json` ✅ |
| **P0 filler** | the existing smart distractor (same type, same shape) | — | `lib/quiz.js:114` ✅ |

**P5 is a real edge for UK and South-Asian learners.** Urdu carries thousands of Arabic words with
shifted meanings. We found no app that targets this.

Rule: one question = 1 answer + up to 3 probes **of different kinds**. A thin bank falls back to P0;
the existing "ask a shorter question rather than pad" rule stays.

## 3. Fixes (micro-interventions), all from stored pieces

| Diagnosis | Fix card | Built from (exists?) |
|---|---|---|
| P1 | **Root family**: the root's origin sense + the 3 most frequent words from it in the Qur'an | Maqayees `core_meaning` ✅ + corpus counts ✅ |
| P2 | **Pattern card**: the mould and what it adds to a meaning, with 2 examples | `data/sarf/patterns.json` ✅ (verbs) |
| P3 | **Two ayahs side by side**, same word, two meanings, the clue word highlighted | needs senses (Pick 3) |
| P4 | **Dot/sound contrast** with audio of both | `SpeakButton` + word audio ✅ |
| P5 | "In Urdu **X**, in the Qur'an **Y**", one ayah | `urdu_links` ✅ |
| P6 | Contrast pair: two ayahs, one line on the difference | dictionary ✅ |
| P7 | The particle's job, from the particle tree | `particle_tree.json` ✅ |

Then **re-check**: 1 question with the *same probe kind* on a *different* word. If it passes, the
confusion is repaired. This is the measurable part: "repair rate per probe kind" tells us which fix
cards work.

## 4. Memory model (deterministic, small)

Stored per learner. Everything else is computed by replaying attempts, as `review_schedule.py` does today.

```
attempt  { user, item=lemma_key, correct, ms, context: { picked, probe, recheck_of? } }
```

Derived when needed:

| Thing | Rule |
|---|---|
| word known? | FSRS-6 retrievability ≥ threshold (exists: `is_known`) |
| confusion level `(user, probe)` | count of falls for that probe, halved every N days without a fall |
| root familiarity | share of that root's Qur'an occurrences whose lemma is known |
| **transfer bonus** | the first time a word is asked whose root family is ≥ 50% known, start it one FSRS step ahead (config knob) |

## 5. Coverage meter (the outcome metric)

```
coverage(surah) = Σ occurrences of known lemmas in surah ÷ total words in surah
```

- The data exists: corpus occurrences + FSRS "known".
- Show it per surah, per juz, and for the whole Qur'an.
- Tie it to Grow's surah paths (Mulk, Kursi, Amma), so learners see words *of the surah they are memorising*.

**What to ask next = due reviews first, then the unknown lemma with the biggest coverage gain in the
learner's chosen surah.** That one line *is* the "pedagogy router" from the brainstorm, without the
hand-waving.

## 6. Build slices

| Slice | What | Size |
|---|---|---|
| 1a | Coverage meter on the quiz page (needs Pick 0.1) | S |
| 1b | Probe-tagged options P1, P4, P5, P7 + log `picked` and `probe` (needs 0.2) | M |
| 1c | Fix cards P1, P4, P5, P7 + re-check question | M |
| 1d | Insights: "your top confusion is look-alike letters" (extend `lib/insights.js`) | S |
| 1e | P2, P3, P6 once Pick 3 gives patterns and senses | M |

## 7. How we know it works

- **Repair rate**: the share of re-checks passed, per probe kind.
- **Falls on the same probe kind over 30 days**: should go down.
- **Coverage growth per week of use.**
- Run as an A/B test: probes + fixes vs today's quiz, on retention at 7 days.

## 8. What's protectable

- **Trade secret**: the probe taxonomy, the build rules, the fix-card mapping, the thresholds.
- **Database right**: the probe-labelled item bank + the repair statistics we collect.
- **Patent**: unlikely to survive "inventive step" in the UK (teaching method). Not worth the money now.
- **The real moat is the data loop**: every wrong answer makes the repair statistics better, and a
  copier starts from zero.
