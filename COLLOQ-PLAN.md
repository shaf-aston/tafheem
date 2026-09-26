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
- [ ] **Phase 1 — Schema and validator.**
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
- [ ] **Phase 2 — Data loading.**
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
