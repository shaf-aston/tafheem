# Basics: a beginner's way in, starting with ال ("the")

Date 2026-10-23 · `/lifecycle` stages 1–4, then built in the same run.

## 1 · Requirements (assumed, testable)

Who: someone brand new to Arabic. They may read the letters slowly, or barely. Today Home's first visit sends everyone to the Qur'an tab.

| # | Criterion | Check |
|---|---|---|
| R1 | A newcomer can say so on their first visit, and is taken to beginner lessons | Home's first visit offers "New to Arabic" next to the existing first lesson; ≤ 3 taps from opening the app to the first question |
| R2 | First beginner skill: ال means "the". Asked both ways (English → Arabic and Arabic → English) | both card types in every new word's asks |
| R3 | Wrong options are built only from the item's own word, each one a real beginner mistake | every distractor contains the word's own letters; per-type unit tests |
| R4 | Exactly one right option; options unique; never a correct spelling posing as wrong | property test over the whole word list |
| R5 | Every answer, right or wrong, shows the correct form and why | the `choose` kind's `why` is set on every card |
| R6 | Progress, review and stages reuse the existing engine (server FSRS record, requeue, XP) | no new scheduler; `useLessonWorld` config only |
| R7 | No Qur'an or hadith text passes through this | words come only from `public/grow/basics.json` |
| R8 | Logic proven by mutation testing | Stryker on `lib/grow/alifLam.js`: score ≥ 80% |
| R9 | Fits 375 px wide; axe shows no serious or critical issues; works RTL | Playwright + axe on Home's first visit and on a lesson |

## 2 · Research (summary; sources in the two research reports)

**Other apps**
- **Kalaam (Quranic).** Placement test first ("% of the Qur'an you understand"). Self-graded recall with 3 cards per word. No multiple choice.
- **Duolingo.** "Start from scratch" or a placement test. The Arabic course starts with the alphabet. Weak words are ranked by a half-life model; Birdbrain predicts whether you'll get an exercise right.
- **Quranic.** "Word strength" and spaced repetition.
- **Busuu.** Start from scratch or a placement test.

**Textbooks**
- **Alif Baa** teaches ال in Unit 8, after the letters, vowels, shadda and ة. Its exercises: make a word definite, and decide definite or not.
- **Madinah** teaches ال in Lesson 3. Rule: never ال and tanween together.

**Writing the questions**
- 3 options is the best number (Haladyna 2002, Rodriguez 2005).
- Distractors should be real student errors.
- Feedback stops learners keeping a wrong option as a "fact" (Butler & Roediger 2008).

**This codebase**
- **The engine already exists:** `useLessonWorld` → `lessonItems`/`weave`/`requeue`, server FSRS-6 `summary`, `recordAttempt`.
- **The `choose` kind** already draws Arabic options (`card.arabic`) and an Arabic stem (`card.ar`).
- **`buildQuestion` can't be reused:** its sense rule merges "the book" with "a book".
- **No onboarding exists.** `HomePanel`'s `first` (no journey yet) is the hook.
- **Word data:** `words.json` glosses can't be trusted for "a/the" (Qur'an-cut glosses come from one ayah: "a Book", "gates"). So a curated, checked list is needed.

## 3 · Architecture

### Candidates (scored 0–4 on the five criteria)

| | Speed (to value) | Quality | UX | Maintainable | Novelty | Σ |
|---|---|---|---|---|---|---|
| **A · "Basics" lessons world in Grow + a fork on Home's first visit**: pure `lib/grow/alifLam.js` builds the cards, the existing engine runs them | 4 | 4: pure generator, mutation-tested | 3: reuses Grow's look; own colour, emblem, teach cards | 4: one config hook + one pure module | 2 | **17** |
| B · Its own "Beginner" tab, with its own runner and a Leitner box in localStorage | 1 | 3 | 4: a fully separate feel; guest record kept on the device | 1: a second lesson engine, scheduler and XP path | 3 | 12 |
| C · A `book` world of hand-written choose cards | 3: no code | 2: distractors typed by hand per word, drift | 3 | 2: 2 × N cards to keep in sync | 0 | 10 |

**Pick A.** Every number that changes lives in data, and the logic is one pure, testable module.

**Loser B, recorded.** Its one real advantage is that a guest's record stays separate. Today every guest shares one server record (`USER == GUEST`), across all worlds. That is a pre-existing gap (strategy Pick 0.1), out of scope here, and listed under risks.

### Level 1 · Context
```
Newcomer ──(first visit)──▶ Tafheem app ──(answers)──▶ Tafheem API (progress store, FSRS)
```
### Level 2 · Containers (unchanged)
```
Browser SPA (React) ──GET /grow/basics.json (static)──▶ Vercel static
                    ──POST /api/progress/attempts, GET /summary?module=basics──▶ FastAPI on the Oracle VM
```
### Level 3 · Components (new = ★)
```
HomePanel ──first visit──▶ ★ BeginnerFork ──onGo('grow','basics/lesson')──▶ GrowPanel
GrowPanel ── lessons.basics = ★ useBasicsWorld(world) ──▶ useLessonWorld (existing)
★ useBasicsWorld ── load: fetch /grow/basics.json ; cards: ★ alifLam.basicsCards
★ alifLam (pure) ── definite / forms / distractors / card builders
LessonRunner + KINDS.choose / KINDS.teach / KINDS.rule (existing) ── recordAttempt(module 'basics')
GrowHome.Today ── ★ a Basics line while it isn't finished
worlds.json ★ entry · theme.json ★ world colour · Emblem ★ art 'basics' · public/grow/basics.json ★ words
```
Every ★ maps up to one Level 2 box (the SPA). There are no new containers.

### Level 4 · Contracts (`frontend/src/lib/grow/alifLam.js`, pure, no React)

```js
SUN_LETTERS: Set<string>                 // ت ث د ذ ر ز س ش ص ض ط ظ ل ن
isSun(bare): boolean                      // first base letter in SUN_LETTERS
plain(bare): string                       // tanween off (ٌ ٍ ً and the alif after ً), NFC
definite(bare): string                    // sun → 'ال' + letter + shadda + rest; moon → 'الْ' + bare
article(word): 'a' | 'an'                 // word.a ?? /^[aeiou]/ test
english(word, isDefinite): string         // 'the book' | 'a book'
FORMS: { [type]: (bare) => string | null } // wrong forms; null when the type doesn't apply
   bare      كِتَاب          forgot ال
   tanween   الْكِتَابٌ       ال with tanween (never together)
   apart     ال كِتَاب       ال written as its own word
   heard     اشَّمْس         spelt as said: sun letters except ل (الَّيْل is the Qur'an's own script), the silent ل dropped
wrongForms(bare, random): string[2]       // 'bare' always + one of (heard if it applies, else tanween|apart)
toArabicCard(word, isNew, random): choose card   // ask 'the book' → 3 Arabic options
toEnglishCard(word, isNew, random): choose card  // ar = definite or bare (random) → 'the book' | 'a book'
basicsCards(picked, random, intro): Card[] // weave: teach(definite + 'the book'), then the two asks; INTRO first when `intro`
keyOfBasic(word): string                  // word.id
MODULE = 'basics'
```
- **Card record:** `{ module: 'basics', item: word.id, context: { world: 'basics', direction: 'to-arabic' | 'to-english', word: bare } }`.
- **Begun, per device:** `useBasicsWorld` keeps `basics-begun` (a remembered flag, on a signed-in learner's shelf too) and passes `intro = !begunHere`; GrowPanel calls `began()` once a Basics lesson is on screen. Today reads `begunHere`, never the shared record (see risks).
- **Hand-off:** a tap elsewhere hands Grow `handed: true` (useTabNavigation → TabPane), so "Start the basics" opens the lesson at once; the tab reopened on its saved place still lands on home with the lesson offered.
- **Seam:** `useBasicsWorld` is the only place that knows the data file. A later skill, such as sun/moon or ة, is a sibling builder plus one entry in a `SKILLS` list. The world doesn't change.
- **Knobs (data):** `worlds.json` `lesson {new, most-new, size}` and `stages`; the word list and its order are in `basics.json`.

### Gate (stage 3)
- Every L3 box maps to the SPA.
- Every L2 arrow is a real call: the static fetch, `recordAttempt`, `fetchSummary`.
- Every slice below names only identifiers listed here. ✔

## 4 · Plan: vertical slices

| # | Slice | Component | Check | Pre-mortem: "fails because…" |
|---|---|---|---|---|
| 0 | Walking skeleton: worlds entry + hook + GrowPanel line, one hard-coded word → a lesson plays end to end | useBasicsWorld | vitest screen test: lesson renders a choose card | the hook isn't in GrowPanel's `lessons` map → world page blank |
| 1 | `alifLam.js` forms + cards, with property tests over the list | alifLam | unit + property tests; Stryker ≥ 80% | combining-mark order (shadda/fatha) makes equal strings compare unequal → NFC everywhere |
| 2 | Curated `basics.json` + its checker test | data | test enforces every rule; second agent verifies the Arabic | a gloss isn't countable ("a rice") → reviewer lane plus an explicit rule |
| 3 | Home fork on the first visit | BeginnerFork | screen test: two leads; tapping "New to Arabic" calls onGo('grow','basics/lesson') | the fork stays after the first visit → keyed on the same `first` |
| 4 | Look: colour, emblem, Today line | theme/Emblem/GrowHome | Playwright at 375 px + axe | Today hard-codes worlds → an explicit Basics line |
| 5 | Verify: fresh-context lanes (code review, Arabic accuracy, UX), mutation run, full suite | — | every finding classified | — |

## 5 · Risks / known unknowns
- **Shared guest record (pre-existing).** A guest's "learnt" mixes with other guests'. Mitigated here: whether Basics has begun (the intro card, Today) is kept on the device. Which words come next still reads the shared record. Real fix: Pick 0.1, one record per learner.
- **Two-option English cards** have a 50% guess rate. This is softened because which form is shown is random, and FSRS needs repeated correct answers.
- **Sun-letter "heard" error frequency** is not measured in any study we found. It is kept because it targets exactly the rule the teach card states.

## 6 · Verify (results)

| Check | Result |
|---|---|
| Unit, property and screen tests | full suite green; `alifLam.test.js`, `basics.test.jsx`, `firstVisit.test.jsx`, `home.test.jsx` |
| Mutation (`npm run mutate`) | `alifLam.js` 99.2%, `lesson.js` 96.2%. Left: equivalent only (`TANWEEN` without `$`: tanween only ever ends a word; loop `<` → `<=` reading past the end; a due id is never also unseen) |
| Arabic accuracy (second agent, all 128 words) | no wrong entry. Acted on: الَّيْل is the Qur'an's own spelling (92:1), so `heard` is never built for ل; day/night/tiger/envelope swapped for unambiguous words; tanween keeps a final shadda |
| Code review (fresh agent) | guests' shared record (→ device flag), Grow tab reopened jumping into a lesson (→ `handed`), Basics answers not counted under Grow (→ `GROW_MODULES`), Today mislabels and a stuck hero (→ `hasWork`), two Arabic words swapping in a feedback line (→ reworded): all fixed, each with a test |
| R9: Playwright at 375 px + axe (wcag2a/aa, 21aa, 22aa) | Home first visit, intro, teach, question, wrong-answer feedback, to-English card, Grow home in dark mode: 0 violations, no sideways scroll, 3 taps to the first question |
