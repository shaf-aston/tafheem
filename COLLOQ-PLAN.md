# COLLOQ-PLAN — Colloquial (عامية) section

## Goal
Turn the empty "Coming soon" ColloquialPanel into a working section that teaches
spoken Damascene Arabic. Learners study situation-based lessons, then answer
exercises by typing or speaking. Each answer gets "natural / too formal / not quite" feedback.
The content comes from unit-01.json … unit-16.json, which the user supplies. We build the
structure, loading, UI and checking. We never write or change Arabic content.

## Hard rules
1. **No Arabic authoring.**
   - Never invent, correct or "improve" the Arabic, transliteration or translations.
   - Report problems in the content instead of fixing them.
   - Test fixtures may only copy entries from the supplied files.
2. **No overlap.** Don't touch Nahw, Sarf, Quran, Daleel, Dictionary, Memorise, Quiz or Timelines. Their shared utilities may be reused.
3. **Reuse first.** Use the existing components, styles, theme, Arabic text handling and speech pipeline. Add no new dependencies without approval.
4. **Phased.** Finish one phase, show its evidence, then stop and wait for "go".
5. **Commits.** One commit per phase. Never force-push.
6. Follow CLAUDE.md and the rules files.

## Phases
- [x] **Phase 0 — Recon (read only).** Report on:
  - ColloquialPanel, its tabs.js entry and its theme colour
  - how Quiz and Memorise check answers, and any existing Arabic normaliser
  - the speech pipeline: can it transcribe free Arabic speech, and which function or endpoint to call
  - where static data lives, and how tests are set up (vitest, Playwright)
  - whether the panel needs `study: true`

  Then recommend (a) a folder for the unit files and (b) whether to reuse the speech pipeline.
- [x] **Phase 1 — Schema and validator.**
  - Write a JSON Schema that matches the one below.
  - Write a node validator script and a vitest test. Rules:
    - `type` ∈ {say_it, respond, de_book, shadow, listen_choose, role_play}
    - `options` is non-empty only for listen_choose
    - `given_lines` appears only for respond and role_play
    - every exercise has `answer`, at least one `accepted`, and `tip`
    - no form is in both `accepted` and `too_formal` after normalising
    - lesson ids are unique across all units
    - minimums: phrases ≥10, dialogue ≥10, de_book ≥4, exercises ≥10
  - Report as file → lesson → problem. Never auto-fix, and report key renames rather than making them.
- [x] **Phase 2 — Data loading.**
  - Load one unit at a time, lazily. Don't put units in the main bundle.
  - Show only valid units. An invalid unit shows "Unit unavailable" in dev and is hidden in production.
  - Evidence: the build output shows unit files split out, and a test loads one unit.
- [ ] **Phase 3 — Lesson UI.**
  - Navigation goes unit list → lesson list → lesson page.
  - The lesson page shows, in order:
    - situation and goal
    - phrases, each with its reply
    - dialogue, with a toggle to hide transliteration and English
    - "Book vs natural"
    - culture note
    - Practise button
  - Arabic is RTL with the app font. Transliteration and English are LTR.
  - Test at 390, 768, 1280 and 1600 px. Keyboard accessible. Arabic text carries `lang="ar"`.
  - Evidence: Playwright screenshots at each width, and lint and build passing.
- [ ] **Phase 4 — Typed checking.**
  - `checkAnswer(input, exercise) → {result, feedback}`, where result ∈ {correct, too_formal, incorrect}.
  - Normalise before comparing:
    - strip tashkeel and tatweel
    - أ/إ/آ → ا, ة → ه, ى → ي
    - remove punctuation and collapse spaces
  - Check in this order:
    1. answer or accepted → correct, shown with the tip
    2. too_formal → too_formal, shown with its feedback
    3. anything else → incorrect, shown with the answer and the tip
  - UI per exercise type:
    - typed input for say_it, respond, de_book and role_play
    - buttons for listen_choose
    - shadow is marked done on attempt
  - Progress lives in memory for the session only.
  - Evidence: vitest tests built from real exercises, and a Playwright run through one lesson.
- [ ] **Phase 5 — Speaking.**
  - Build this only if Phase 0 confirmed the pipeline can transcribe free Arabic speech.
  - Put a mic button on say_it, respond, de_book, role_play and shadow.
  - Send the transcript through the same `checkAnswer`, and show "We heard: …" first.
  - Handle denied mic permission, no speech and API errors. Typing always stays available.
  - Evidence: tests with mocked transcripts, and a script for the user's manual test.
- [ ] **Phase 6 — Conversation challenge (proposal only).** Cover the Groq endpoint, how the prompt is built from the challenge fields, how turns and the checklist are scored, and the cost per conversation.
- [ ] **Phase 7 — Final verification.**
  - Lint, build, vitest and Playwright at all four widths.
  - A fresh subagent reviews the diff against this plan and reports gaps only.
  - Final report.

## Unit schema (source of truth)
```json
{
  "unit": "unit-01",
  "title": "string",
  "lessons": [{
    "id": "1.1",
    "situation": "string",
    "goal": "string",
    "phrases": [{ "ar": "", "translit": "", "en": "", "use": "",
                  "reply": { "ar": "", "translit": "", "en": "" } | null }],
    "dialogue": [{ "speaker": "", "ar": "", "translit": "", "en": "" }],
    "de_book": [{ "book": "", "natural": "", "why": "" }],
    "grammar": "string" | null,
    "culture": "string",
    "exercises": [{
      "id": "1.1-e1",
      "type": "say_it|respond|de_book|shadow|listen_choose|role_play",
      "prompt": "string",
      "given_lines": ["string"],
      "options": ["string"],
      "answer": "string",
      "accepted": ["string"],
      "too_formal": [{ "answer": "", "feedback": "" }],
      "tip": "string"
    }]
  }],
  "challenge": { "scenario": "", "partner_role": "", "learner_goals": [""],
                 "target_phrases": [""], "checklist": [""] }
}
```

## Phase 0 findings
- **Panel:** `frontend/src/components/ColloquialPanel.jsx` is a stub. Its entry in `lib/tabs.js` is `id: 'colloq'`, with the accent `#fb923c` from `theme.json` via `accentOf`. Add `study: true` so the text-size setting applies, as it does for mem and daleel.
- **Normaliser:** `lib/arabicText.js` owns this. `bareForm` strips harakat and folds أإآ→ا.
  - `recitedForm` is not usable here: it drops spaces, and it keeps ة≠ه on purpose.
  - Plan: `colloquialForm` = `bareForm` + tatweel, ى→ي, ة→ه, punctuation→space, collapse spaces. It lives in the colloquial module and composes `bareForm`, so none of the shared logic is duplicated.
- **Quiz** and **Memorise** have no free-text checker to reuse. Quiz compares option ids; Memorise uses `recitedForm` for page gaps.
- **Speech** can be reused as is:
  - capture with `lib/microphone.js` and `ui/MicButton.jsx`
  - transcribe with `api.js` `listen(blob, {fusha:false})` → `POST /api/listen`, Groq whisper-large-v3-turbo, returns `{text}`
  - with match and recite off, nothing forces a Quran match, and `fusha:false` sends no MSA hint
- **Data:** units go in `frontend/src/data/colloquial/`, loaded with `import.meta.glob(..., {import:'default'})`, lazily, one chunk per unit.
- **Tests:** vitest, colocated `*.test.js`. There is no Playwright config, so Playwright runs as a standalone script with the preinstalled Chromium. Lint with `npm run lint`, build with `npm run build`.
- There is no CLAUDE.md or rules directory in the repo.

## Phase 1 notes
- Shape: `frontend/src/colloquial/unit.schema.json`. Rules: `frontend/src/colloquial.json` (types, minimums). A test keeps the two type lists equal.
- Checker: `frontend/src/colloquial/validate.js`. Normaliser: `spokenForm` in `frontend/src/lib/arabicText.js`, reused by Phase 4.
- Run: `npm run validate:colloq` (frontend/) prints file → lesson → problem.

## Phase 2 notes
- `frontend/src/colloquial/units.js`: `unitIds()`, `loadUnit(id)`, `shown(loaded)`. Each unit is its own lazy chunk; the folder is the list.
- Per-type `lists` / `input` / `speak` flags live in `colloquial.json`; UI copy in its `copy` block.

## Microsteps (approved)
## Module map (where each thing lives, and why)
| Concern | Module | Reused from |
|---|---|---|
| Unit shape | `src/colloquial/unit.schema.json` (done) | none |
| Rules and knobs (types, minimums, UI copy, data folder) | `src/colloquial.json` | same pattern as quiz.json and memorise.json |
| Arabic normalising | `spokenForm` in `src/lib/arabicText.js` (done) | `bareForm` |
| Validation | `src/colloquial/validate.js` (done) | schema and config |
| Loading | `src/colloquial/units.js` | `import.meta.glob`, `validate.js` |
| Checking | `src/colloquial/checkAnswer.js` | `spokenForm`, config |
| Screens | `src/colloquial/*.jsx`, kept small; `ColloquialPanel.jsx` only routes | `SectionHeader`, `EmptyState`, `ArabicText`, `PrimaryButton`, `SmallButton`, `Segmented`, `Disclosure`, `AnswerSquare`, `ErrorAlert`, `MicButton`, `lib/shuffle.js`, `--c` accent |
| Speech | none new | `MicButton` → `api.listen` → `POST /api/listen` (Groq whisper) |
| Conversation (P6, proposal only) | a backend router plus a prompt in `services/ai/prompts.py` | `services/ai` backend and `config.py` settings |

Rules applied throughout:
- Labels and messages ("Unit unavailable", "We heard:", the result words) go in `colloquial.json`.
- Result names (`correct`, `too_formal`, `incorrect`) are exported once from `checkAnswer.js`.
- Exercise types come from `colloquial.json` `exercise-types`; each type gets an `input` field (`text`, `choice`, `shadow`) so the UI never hardcodes type lists.
- Mic-capable types are a config flag (`speak: true`).
- Colours come only from theme tokens and `--c`. No new CSS values if an existing class fits.

## Phase 2 — Loading
1. Add `"input"` and `"speak"` flags to each type in `colloquial.json`. Extend the schema/config sync test to cover them.
2. Write `units.js`:
   - `UNIT_FILES = import.meta.glob('../data/colloquial/*.json', { import: 'default' })`, lazy with one chunk per file
   - `unitIds()`: sorted file names, derived from the glob keys, with no list written by hand
   - `loadUnit(id)`: imports the file, runs `validateAll` for that unit, and returns `{unit}` or `{problems}`
3. Visibility rule in one function, `visible(result)`:
   - production (`import.meta.env.PROD`): hide invalid units
   - dev: show them with the "Unit unavailable" text from the config
4. `units.test.js`: `loadUnit` with a unit copied from a supplied file (blocked until the files exist, otherwise skipped with a clear message), plus an invalid-unit case built from the structural fixtures.
5. Verify:
   - `npm run build`: a chunk per unit, and the main bundle size is unchanged
   - lint and vitest pass
   - commit

## Phase 3 — Lesson UI
1. In `tabs.js`, add `study: true` to the colloq entry. This is its only change.
2. `ColloquialPanel({accent})` holds the view state `{unitId, lessonId, mode}` and renders one of these screens.
3. `UnitList.jsx`:
   - loads titles lazily
   - reuses the card and button classes already used for lists in other panels (find the nearest match, e.g. Tamreen/Notes)
4. `LessonList.jsx`: situation and goal for each lesson.
5. `LessonPage.jsx`, with the sections in plan order:
   - `PhraseList`: `ArabicText` for Arabic, plus the reply under each phrase
   - `Dialogue`: a `Segmented` toggle hides transliteration and English; the toggle is local state
   - `BookVsNatural`
   - `CultureNote`
   - `PrimaryButton` "Practise"

   Section titles come from the config.
6. Transliteration and English get `dir="ltr"`. All Arabic goes through `ArabicText`, which gives `lang="ar"` and RTL.
7. Keyboard: real `<button>`s, visible focus from the existing styles, and a back control on every screen.
8. Verify:
   - `scripts/colloq-shots.mjs`, a Playwright script in the pattern of the existing `scripts/probe*.mjs`: screenshots at 390/768/1280/1600 of the unit list and one lesson, plus an axe-core check (already a devDependency)
   - lint and build pass
   - commit

## Phase 4 — Typed checking
1. `checkAnswer.js`:
   - exports `RESULT = {correct, too_formal, incorrect}`
   - `checkAnswer(input, ex)` compares `spokenForm` values: `answer`/`accepted` first, then `too_formal`, else incorrect
   - returns `{result, feedback, tip, answer}`
2. `checkAnswer.test.js`: cases copied only from the supplied files, covering exact match, an accepted variant, with and without tashkeel, too_formal, and incorrect.
3. `Exercise.jsx` picks its input by `config['exercise-types'][type].input`:
   - `TextAnswer`: an input with `dir="rtl" lang="ar"`, submitted on Enter or with a button
   - `ChoiceAnswer`: `options` shuffled with `lib/shuffle.js`
   - `ShadowLine`: shows the line and marks it done on attempt
4. `Feedback.jsx` is one component for all three results. Tone uses the existing `--success` and `--danger` tokens, with the too_formal tone taken from the theme (no new colour).
5. `Practice.jsx` runs the exercises in order. Progress is a `useState` map `{exId: result}`, drawn as an `AnswerSquare` strip (the same one the Quiz and Tamreen use). Memory only.
6. Verify:
   - vitest
   - a Playwright script that completes one lesson's exercises
   - lint and build
   - commit

## Phase 5 — Speaking (the pipeline is confirmed free-text capable)
1. `MicButton`: add an optional `fusha` prop that overrides the user setting when given. This is the only shared change; the default behaviour is unchanged.
2. `Exercise.jsx`: for types with `speak: true`, render `<MicButton fusha={false} onHeard={...}>`. The text it hears goes through the same `checkAnswer`.
3. `Feedback` shows "We heard: …" (copy from the config) above the result.
4. Errors: `MicButton` already handles "refused" and silence. API errors go through `lib/apiError.js` into `ErrorAlert`. The text input always stays visible.
5. Tests:
   - mock `api.listen` to return a correct, a too-formal and a wrong transcript, plus empty text and a rejection
   - one test checks that `fusha: false` is passed
6. Write out a manual test script for the user: the exact phrase to say from unit-01 and the expected outcome. Then commit.

## Phase 6 — Conversation challenge (proposal only; write it into COLLOQ-PLAN.md)
- Endpoint: `POST /api/colloquial/turn` in a new `backend/routers/colloquial.py`. It reuses the `services/ai` backend (`complete_json`), and the model, timeout and max tokens come from `config.py` settings (new keys only if needed).
- Prompt: a template in `services/ai/prompts.py`, filled from `scenario`, `partner_role`, `target_phrases` and `learner_goals`.
- Each turn returns `{reply_ar, reply_translit, reply_en, checklist_hits[]}`. The frontend ticks off `checklist` items and runs each learner turn through `checkAnswer` against `target_phrases` for the too-formal hints.
- Cost: estimate the tokens per turn × about 10 turns at Groq's gpt-oss-120b price. Write the numbers in the proposal.
- Commit the plan text only.

## Phase 7 — Final
- lint, build, full vitest, and the Playwright scripts at all four widths
- the validator report for all 16 units
- a fresh subagent diffs the work against COLLOQ-PLAN.md and reports only these gaps: requirements not met, changes out of scope, Arabic edited, new dependencies
- final report, then commit

## Blocker
The unit files are still missing. Phase 2's real-unit test and Phases 3–5's fixtures and screenshots need at least unit-01. Until they arrive, only the structural parts can be built.
