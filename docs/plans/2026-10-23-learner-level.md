# Learner level: beginner, intermediate, advanced

Date 2026-10-23 · `/lifecycle`. Builds on `2026-10-23-basics-alif-lam.md` (Home's beginner fork) and
`2026-10-23-basics-word-forms.md` (the Basics path).

## 1 · Requirements

**Ask (user):**
- Onboarding stays on Home: the first thing a person sees is a suggestion of where to begin.
- The level (beginner, intermediate or advanced) is chosen when the account is set up.
- It can be changed in account settings until there is enough evidence. After that, the answers decide it.
- Grow and Quiz serve things that fit the level.
- Quiz and Grow use the same question structures, so they feel the same.
- The user flow and front-end experience come first.

| # | Criterion | Check |
|---|---|---|
| L1 | First visit: one screen and **1 tap** from Home to a first question that fits the level. Picking the level *is* the start | Playwright: tap a level row → lesson or tab opens |
| L2 | Sign-up asks the level in the same sheet (+0 screens), prefilled with what Home picked | component test: the new account's shelf holds `level` |
| L3 | The level can be changed in Settings and on the profile **until settled**. Once settled, the control is locked and says which answers set it | component test: locked with reason |
| L4 | Settled = ≥ `min-answers` answers on any tier's proof modules. The level then follows the evidence (rule §4) | unit tests over the rule table |
| L5 | Grow's Today hero follows the level: beginner → Basics, intermediate → Words, advanced → Nahw (a book) | component test per level |
| L6 | The Quiz's default set follows the level. Beginners get a **Basics** set that plays Grow's own cards (same registry, same runner) | component test: Basics bank renders a Grow card |
| L7 | A level is never forced on anyone. With no level, every screen behaves as it does today | existing suite unchanged and green |
| L8 | Level text sits in config (`levels.json`), with no copy in components | lint and review |
| L9 | Mutation ≥ 90% on `lib/learnerLevel.js`; the full suite and eslint green; axe 0 at 375 px in light and dark | Stryker, vitest, Playwright |

## 2 · Context: what exists

- **Home first visit** = `BeginnerFork`: 2 tiles, each with its own button ("New to Arabic" → Basics lesson, "I can read Arabic" → Quran). The choice is not remembered. At 375 px the fork takes about 330 px.
- **Sign-up** asks only a username, then reloads.
- **Settings** are device knobs from `settings.json`. **Profile** is the account.
- **Per-account memory** = the shelf (`useRemembered` key → `@name/key`, synced to the server). A guest keeps theirs on the device, and sign-up with "keep" copies it across.
- **Evidence** = `/overview` → per module `{attempts, correct, learnt}`. It is signed-in only, because guests share one record.
- **No level concept anywhere.** "Level 3" in Grow is XP rank, so the new idea is labelled **"Your Arabic"** in the UI to keep the two apart.
- **Quiz** is vocabulary only. **Grow** cards come from `components/grow/exercises` and are run by `LessonRunner`.

## 3 · Flow (taps from Home)

```
First visit (Home)
  "How much Arabic do you know?"
   ├─ Beginner     → level=beginner     → Grow · Basics lesson (ال)        1 tap
   ├─ Intermediate → level=intermediate → Grow · Words lesson              1 tap
   └─ Advanced     → level=advanced     → Grow · Nahw (al-Ajurrumiyya)     1 tap

Sign-up sheet: username · "Your Arabic" [Beginner|Intermediate|Advanced] (prefilled) · Sign up
Settings / Profile: "Your Arabic" control
   ├─ not settled → change freely
   └─ settled     → locked: "Set by your answers: 86% right in 40 Words answers"
Grow Today hero  ← level        Quiz default set ← level (Basics | Qur'anic | All)
```

## 4 · Level rule (pure, `classify(chosen, modules)`)

Each tier lists its **proof** modules: beginner → `basics`; intermediate → `quiz`, `quiz:ur`; advanced → none (nothing above it).

For each tier with proof:
- `answers` = sum of attempts over its proof modules.
- `share` = correct ÷ answers.
- **passed** = answers ≥ `min-answers` and share ≥ `pass`.
- **struggled** = answers ≥ `min-answers` and share < `fail`.
- **held** = answers ≥ `min-answers` and not struggled.

Then:
- `settled` = some tier has ≥ `min-answers`.
- If not settled: level = chosen (`''` = none).
- If settled: level = clamp(max(chosen, highest held, highest passed + 1), ≤ lowest struggled).
- `basis` = the tier whose numbers decided it, so the UI can say why.

| chosen | evidence | level |
|---|---|---|
| beginner | basics 90% of 40 | intermediate (passed beginner) |
| advanced | words 50% of 40 | intermediate (struggled there) |
| beginner | words 70% of 40 | intermediate (held words) |
| intermediate | basics 40% of 30 | beginner |
| '' | words 85% of 30 | advanced |
| any | < 30 answers everywhere | chosen, not settled |

## 5 · Candidates

| | A · Level stored, evidence derived (chosen) | B · Server-side level column |
|---|---|---|
| Where | shelf key `level` + pure client rule over `/overview` | `accounts.level` + `/level` endpoint, server classifies |
| Guest | works (device shelf) | needs a guest path; guests share one record |
| Sync | free (the shelf already syncs) | new API, migration, tests |
| Testability | pure function, Stryker-able | integration tests |
| Cost | ~1 config, 2 lib files | backend model, router, store, migration |

B also loses guests, who are the main first-visit audience. **A** is chosen.

## 6 · Contracts

- `src/levels.json` holds `{ levels: [{ id, label, title, blurb, arabic, start: [tab, value?], proof: [module], quizBank, grow, book? }], min-answers, pass, fail }`.
- `lib/learnerLevel.js`:
  - `LEVELS`, `LEVEL_IDS`, `levelOf(id)`
  - `classify(chosen, modules = [], rules)` → `{ level, settled, basis: {id, answers, share} | null }`
- `lib/useLearnerLevel.js`: `useLearnerLevel()` → `{ level, chosen, settled, basis, choose }`. Its overview query is shared with Home (`['overview', name]`).
- `components/level/LevelPicker.jsx`: Home's rows (one tap = choose + go).
- `components/level/LevelSetting.jsx`: Segmented, locked when settled.
- `GrowHome` Today takes `level`. `useQuizSetup` falls back to the level's `quizBank`.
- `BANKS.basics = { label: 'Basics', lesson: true }`. QuizPanel renders `BasicsRound` (LessonRunner + `useBasicsWorld`) for a lesson bank.

## 7 · Slices

1. Model: config + `classify` + hook + tests.
2. Home picker (replaces BeginnerFork), sign-up row, Settings/Profile control.
3. Grow Today by level, Quiz default by level, Basics bank.
4. Verify: vitest, eslint, Playwright 375 light/dark + axe, Stryker on `learnerLevel.js`.

**Pre-mortem**
- *Sign-up reloads before the level is written* → write it to the new name's shelf before `logInAs`.
- *Basics bank fetches the word table anyway* → harmless, because that cache is shared with Review counts.
- *XP "Level" confusion* → the UI says "Your Arabic".
