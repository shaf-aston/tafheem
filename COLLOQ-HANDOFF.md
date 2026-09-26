# COLLOQ-HANDOFF: instructions for the next Claude Code session

This document is the single brief for finishing the **Colloquial (عامية)** tab of Tafheem.
Read it top to bottom before touching code. Background and the original task are in
`COLLOQ-PLAN.md`; this document is the up-to-date instruction set and takes priority where the two differ.

---

## 1. What this is

The Colloquial tab teaches **spoken Damascene Arabic** through situation-based lessons:
- phrases, each with its reply
- a dialogue
- "book vs natural" contrasts (textbook Arabic vs how people actually say it)
- a culture note
- exercises, answered by typing or speaking

Each answer is judged **correct / too formal / incorrect**.

## 2. Hard rules (from the owner, non-negotiable)

1. **No Arabic authoring.** Never invent, correct or "improve" Arabic, transliteration or translations. Report bad content; never fix it. Test fixtures may only copy entries from supplied content. Placeholders use English/ASCII or single Arabic letters.
2. **No overlap.** Do not modify Nahw, Sarf, Quran, Daleel, Dictionary, Memorise, Quiz or Timelines. Their shared utilities may be reused.
3. **Reuse first.** Use existing components, styles, theme tokens, `lib/arabicText.js` and the speech pipeline. Add no new dependencies without approval.
4. **No hardcoding.** Every value is defined once and read everywhere: types, minimums, labels, paths, limits. The frontend reads knobs from `frontend/src/colloquial.json`, the backend from `backend/config.py` settings.
5. **Modular and format-agnostic.** The content format *will* change and sources *will* be swapped. A new format or storage must mean adding one file, not editing the screens.
6. **Workflow:** explore → plan microsteps → **get the plan approved** → implement → verify.
   - One commit per phase, pushed to `master`. Never force-push.
   - Stop after each phase and wait for the owner to say "go".
   - Do not start building without an approved plan; this was broken once already.
7. Keep answers to the owner short, plain and concise.

## 3. Current state (master, commit 0050e9f)

| Phase | Status | Commit |
|---|---|---|
| 0. Recon | done | b8075d7 |
| 1. Schema and validator | done | 742dfd3 |
| 2. Lazy loading of files, in the frontend | done, but **replaced by the step 5 design below** | 5c54f53 |
| 3. Lesson UI | done | 0050e9f |
| 4. Typed answer checking | **next** | none |
| 5. Speaking | todo | none |
| 6. Conversation challenge (proposal only) | todo | none |
| 7. Final verification | todo | none |

### Files that exist
The first six paths are under `frontend/src/`.
- `colloquial.json` holds all the knobs:
  - `exercise-types`: for each type, `lists` (options / given_lines allowed), `input` (text / choice / shadow) and `speak` (mic offered)
  - `lesson-minimums`
  - `copy`: every UI label
- `colloquial/unit.schema.json`: the JSON Schema for a unit (the shape in `COLLOQ-PLAN.md`).
- `colloquial/validate.js`: pure `checkSchema`, `checkLesson`, `validateAll` and `formatReport`, driven by the schema and the config.
- `colloquial/units.js`: `unitIds()`, `loadUnit(id)` and `shown()`, lazy `import.meta.glob` over `data/colloquial/*.json`. **To be replaced** by the API client in step 5.
- `colloquial/parts.jsx`, `UnitList.jsx`, `LessonList.jsx`, `LessonPage.jsx`: the screens. `components/ColloquialPanel.jsx` only routes between them.
- `lib/arabicText.js` `spokenForm()`:
  - the normaliser for answers, built on `bareForm`
  - strips tashkeel and tatweel
  - folds أإآ→ا, ى→ي, ة→ه
  - turns punctuation into single spaces
- `frontend/scripts/colloq-shots.mjs`: Playwright screenshots and axe at 390/768/1280/1600. Needs `npm run dev`. Uses a temporary placeholder unit when the content folder is empty.
- `npm run validate:colloq` (in `frontend/`) prints the file → lesson → problem report.
- Tests: `colloquial/*.test.js` and the `spokenForm` tests in `lib/arabicText.test.js`.

### Known issues (not ours, leave them alone)
- `frontend/scripts/ears.test.js` fails because `backend/data/quran/imlaei.json` is missing from checkouts.
- axe flags `TabStrip.jsx` `role="tablist"` (aria-required-children). This is excluded from our audit.
- The older `scripts/probe*.mjs` open `/`, which is now the landing page. The app is at `/app?tab=<id>`.

## 4. Content: the blocker

**No lesson content exists yet.** The folder `frontend/src/data/colloquial/` is empty.
- The owner was expected to supply `unit-01.json` … `unit-16.json`.
- Research (report: `docs/research/Damascene Arabic open sources.md`) found no ready-made, openly licensed Damascene lesson set. Best candidates:
  - **DLI Syrian Arabic Course** (archive.org, US-government so presumed public domain; probably scanned, so it needs OCR)
  - **Tatoeba** apc/ajp sentences (CC BY 2.0 FR)
  - **Wikivoyage, Wikibooks and Wiktionary** Levantine pages (CC BY-SA, share-alike)
  - **Peace Corps Jordan** lessons (Jordanian dialect)
- Avoid for commercial use: MADAR, Levanti and UFAL (non-commercial licences), Liddicoat's book and the paid courses.
- Content must be written or checked by a native Damascene speaker. **You do not write it.**
- Everything below must work with zero content (an empty state) and with any number of units.

## 5. Architecture to build next: the format-agnostic content layer

The app's "database" is **not** an Oracle Database.
- The backend runs on a free **Oracle Cloud VM** (`deploy/README.md`).
- Its data is files copied by `deploy/copy-data.sh`, plus SQLite (`data/progress.db`).
- Colloquial content therefore belongs **on the backend**, behind an API, like Tamreen. The frontend must never know where or how lessons are stored.

Layers (each one replaceable on its own):

```
storage (where)  →  adapter (which format)  →  canonical model (one shape)  →  API  →  frontend client  →  screens
```

1. **Canonical model.** One internal shape: Pydantic models in `backend/models/schemas.py`, mirroring `unit.schema.json`.
   - Add a `schema_version` field.
   - Required fields stay strict. New optional fields default to empty, and unknown extra fields are ignored rather than rejected.
2. **Adapters,** in `backend/services/colloquial/adapters/`. There is one module per content format; each exposes `FORMAT` (a string id) and `to_unit(raw) -> Unit`.
   - The first is `unit_json_v1.py`: today's format, a pass-through.
   - A registry (`adapters/__init__.py`) maps a format id to its adapter. It chooses the format from the pack manifest, never by guessing in the screens.
3. **Storage,** in `backend/services/colloquial/stores/`. There is one module per backend, each implementing `list_units()` and `get_unit(id)`, which returns raw data and a format id.
   - The first is `files.py`: reads `backend/data/colloquial/<pack>/`.
   - SQLite or Oracle DB stores can be added later as one new file each.
   - The store is chosen by a setting in `backend/config.py` (for example `colloquial_store = "files"`, `colloquial_dir = "data/colloquial"`), and paths go through `config.data_path`.
4. **Content packs.** Each pack folder has a `manifest.json`: `{ "format", "source", "license", "attribution", "dialect" }`.
   - A CC BY-SA pack stays in its own pack.
   - The API returns the attribution so the UI can show credits.
5. **Service,** in `backend/services/colloquial/__init__.py`, which is the only thing routers call. It runs store → adapter → validation, and caches the results (see `services/tamreen.py` for the house pattern).
   - Validation lives here: port the frontend rules, reading the minimums and type rules from **one** shared source.
   - Preferred: move `exercise-types` and `lesson-minimums` into a JSON file the backend owns and the frontend fetches or imports at build time. Decide and document; do not keep two copies.
   - Invalid units are excluded and logged, with a reason available in development.
6. **Router,** `backend/routers/colloquial.py`, following the `routers/tamreen.py` style, and registered in `backend/main.py`:
   - `GET /api/colloquial/units` returns `[{id, title, lesson_count, attribution}]`
   - `GET /api/colloquial/units/{id}` returns the full canonical unit, or 404
7. **Frontend client:** add `getColloquialUnits()` and `getColloquialUnit(id)` to `frontend/src/api.js`, following the existing pattern.
   - Replace `colloquial/units.js` internals with those calls, keeping its exported names so the screens barely change.
   - Use `@tanstack/react-query` as the other tabs do.
   - Remove `data/colloquial/` from the frontend once the backend serves the content.
   - Keep `npm run validate:colloq`, or replace it with a backend CLI (`python -m backend.scripts.validate_colloquial`) that prints the same report.
8. **Tests:**
   - pytest for each adapter, the store, the service validation and the router (`tests/test_colloquial_*.py`; see `tests/test_progress_api.py` for API tests)
   - vitest for the client with the API mocked

### Microsteps (get these approved before building)
1. Read `services/tamreen.py`, `routers/tamreen.py`, `models/schemas.py`, `config.py` (`data_path`), `api.js` and `tests/test_progress_api.py`.
2. Canonical Pydantic models, plus a test that they accept a structural fixture and reject missing required fields.
3. The adapter registry and `unit_json_v1`, with tests.
4. The file store, the manifest and the setting in `config.py`, with tests (use `tmp_path`).
5. The service (load, adapt, validate, cache) with one shared rules source, with tests.
6. The router and its registration, with API tests.
7. The frontend client, `units.js` rewired to it, and the UI checked against a running backend.
8. Remove the frontend content glob. Update `COLLOQ-PLAN.md` and this file.
9. Verify: `pytest`, `npm run lint`, `npm test` and `npm run build`, then `node scripts/colloq-shots.mjs` with backend and dev server running.

Commit "Colloquial: backend content layer", push, then stop.

## 6. Remaining phases after that (from `COLLOQ-PLAN.md`)

**Phase 4: typed checking**
- `frontend/src/colloquial/checkAnswer.js` exports `RESULT` and `checkAnswer(input, exercise) -> {result, feedback, tip, answer}`.
  - Compare with `spokenForm` in this order: answer or accepted → correct; too_formal → too_formal (with its feedback); else incorrect (show the answer and tip).
  - If the backend owns validation, the checker can stay client-side for speed, but it must use the same normaliser rules.
- `Exercise.jsx` picks its input by `exercise-types[type].input`:
  - `TextAnswer` (`dir="rtl" lang="ar"`)
  - `ChoiceAnswer` (shuffle with `lib/shuffle.js`)
  - `ShadowLine`
- `Feedback.jsx`: one component, colours from `--success`, `--danger` and theme tokens.
- `Practice.jsx`: progress in `useState` only, drawn as an `AnswerSquare` strip. Wire up the Practise button in `LessonPage`.
- Tests use real exercises only, once content exists. Also a Playwright run through one lesson.

**Phase 5: speaking**
- `components/ui/MicButton.jsx`: add an optional `fusha` prop that overrides the user setting. This is the only shared change.
- For types with `speak: true`, render `<MicButton fusha={false} onHeard=…>` and send the text through the same `checkAnswer`.
- Show "We heard: …" (copy from the config) before the result. Errors go through `lib/apiError.js` and `ErrorAlert`, and typing stays available.
- The backend is `POST /api/listen` (Groq `whisper-large-v3-turbo`). With `match=false, recite=false, fusha=false` it returns free Arabic text.
- Tests use a mocked `api.listen`. Give the owner a manual test script.

**Phase 6: conversation challenge, a proposal only** (written into `COLLOQ-PLAN.md`)
- `POST /api/colloquial/turn`, reusing `backend/services/ai` (`complete_json`, settings in `config.py`) with a prompt in `services/ai/prompts.py` built from the challenge fields.
- Each turn returns `{reply_ar, reply_translit, reply_en, checklist_hits[]}`.
- Include a cost estimate per conversation.

**Phase 7: final verification**
- Lint, build, vitest, pytest and the Playwright screenshots at all four widths, plus the validator report.
- A fresh subagent reviews the diff against the plan and reports gaps only.

## 7. Environment notes

- The frontend is in `frontend/` (Vite, React 19, Tailwind 4, vitest). The backend is FastAPI in `backend/`, with tests in `tests/`.
- Playwright: Chromium is at `/opt/pw-browsers/chromium`. Do not run `playwright install`.
- The app is at `http://localhost:5173/app?tab=colloq`. The dev server proxies `/api` to `127.0.0.1:8000`.
- There are about 17 known backend recitation test failures that predate this work (commit 463e68a).
- To inspect the live server:
  - The owner adds the duckdns host to the environment's allowed network domains, and you call its `/api/...` read-only with curl.
  - Alternatively, an SSH key is stored as an environment secret (the proxy may block SSH).
  - Never ask for secrets in chat.

## 8. Open questions for the owner

1. Where will real content come from, and who (a native speaker) writes or checks it?
2. Should content live only on the backend (recommended), or also ship bundled for offline use?
3. Connection to the live server: allow-list the domain (recommended) or use an SSH key?
4. The one shared rules source: a backend-owned JSON file the frontend imports at build time, or fetched at runtime?
