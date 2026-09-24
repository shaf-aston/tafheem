# Tafheem

Study Arabic and the Qur'an in one app: grammar of a typed sentence, the Qur'an with checked
grammar and tafsir, roots and conjugation, a dictionary, quizzes, timelines, and reciting
checked word by word. Offline by default, and every answer says where it came from.
Full notes: `docs/core-flow-detail.md`.

## Run it

```bash
venv\Scripts\Activate
python -m uvicorn backend.main:app --reload --port 8000   # backend, project root
cd frontend && npm run dev                                 # frontend, open http://localhost:5173
venv/Scripts/python -m pytest tests -q                     # backend tests
cd frontend && npm test && npm run lint                    # frontend tests
EAR=http://127.0.0.1:8000 node frontend/scripts/probe-ear.mjs  # reciting, end to end
venv/Scripts/python -m backend.scripts.score_iraab             # i'raab roles vs the books, as a score
venv/Scripts/python -m backend.scripts.score_iraab --set checked  # and vs the 72 checked sentences
```

Data is built once by the scripts in `backend/scripts/`, each explained in its own
docstring, and never committed. The Qur'an builds come first: `build_quran_corpus.py`, then
`build_quran_meanings.py`. Rebuild the Daleel index whole: `build_daleel_index.py`, never `--only`.

## Core flow

1. **A tab picks the tool.** `frontend/src/App.jsx` holds the tabs and checks `/api/health`,
   and carries a root from one tab to another (`onGo`), so the tabs work as one app.
2. **A typed sentence is tagged, parsed, then named.** `services/morphology.py` (CAMeL)
   gives each word's root and features; `services/rule_engine.py` works out the i'raab with
   no network; then `services/syntax/` reads which word hangs off which
   (`catib_onnx.py`, offline), names the role (`naming.py`), which is right far
   more often, so its name wins and the rules fill the gaps, and draws the same
   reading as brackets (`tree.py`), so the cards and the picture cannot disagree.
   Only below the confidence in `backend/config.py` does
   `routers/analysis.py` ask an AI backend (`services/ai/`), which retires itself when its
   key is dead (`services/fallback.py`).
3. **The Qur'an is looked up, never guessed.** `services/quran_corpus.py` reads the
   hand-tagged corpus; `quran_service.py` joins it with the English gloss. Tafsirs and
   translations are **editions**, all in `data/quran/library.db`, read only by
   `quran_library.py` and named only in `data/quran/editions.json`.
4. **The root is the spine.** One click sends a word's root to Sarf
   (`services/conjugation.py`), the dictionary, or every place it occurs. A verb's bab
   comes only from a dictionary that states it (`services/verb_forms.py`), never a guess.
   Conjugation fills a template from `data/sarf/patterns.json`, then runs the book's rules
   over the letters (`services/sarf/`): so قَوَلَ becomes قَالَ, يَمْدُدُ becomes يَمُدُّ, and a
   root whose rules are not built says so rather than guess.
5. **Reciting is heard quickly, then checked carefully.** `lib/recitingSession.js` records a
   phrase at each pause and posts it to `POST /api/listen` (`routers/listen.py`). The
   ears in `services/recitation/ears.py` write down the words, Groq first, in about 0.3 s,
   and `lib/follow.js` marks the page at once. A second request, `POST /api/listen/check`,
   asks this computer how sure it is of each word, and the marks are adjusted when that
   answer arrives. Every step goes to `logs/recite-journal.jsonl`
   (`services/journal.py`, `lib/journal.js`), joined by the reading number.
6. **Time is data.** `services/timelines.py` reads `backend/data/timelines/`, checks it
   on load, and the Timelines tab draws it; asbab al-nuzul reports hang on Seerah events.
7. **Every answer says where it came from.** `services/provenance.py` attaches a `source`
   from `data/sources.json`; `ui/SourceBadge.jsx` shows it. Verified, derived and guessed
   never look alike.

## Glossary

- **I'raab**: the ending on one word, its case and the reason for it.
- **Tarkeeb**: which words join into a unit and what that unit does. A bracket tree,
  never a per-word list. One Nahw page now draws it above the i'raab cards for the
  same typed sentence, from the same reading; the books' 47 worked examples sit in
  a drawer under it.
- **Sarf**: a word's root and pattern. The **gardaan** is the full table of 14 persons.
  **I'lal** is the rules that reshape a filled pattern when the root holds a weak letter, a
  hamzah or a doubled one, one per entry in `data/sarf/ilal.json`.
- **Root**: the three letters most Arabic words are built from; the one link every tab
  shares.
- **Bab**: which vowel pattern (or which form, II to X) a verb follows, read from Lane's
  Lexicon or Wiktionary, never worked out from a bare root.
- **Edition**: one book hung on the ayahs, a tafsir or a translation, all stored one way.
- **Ear**: anything that turns sound into words. Three: `hosted` (Groq, about 250 ms),
  `letters` (tilawa's small Qur'an model on this computer, recitations only,
  `recitation/letters.py`) and `here` (Whisper on this computer). Tried in the order
  `recitation_ears` names, `here` always last. An ear that fails rests for 60 s; one
  whose key is rejected is dropped for the run. `/api/health` names them (`ear`,
  `recite_ear`, `recite_sure`).
- **Recitation / reading**: Qur'an said aloud. A **reading** is one request about one
  phrase, with a reading number (`X-Reading-Id`) that the page and server both log. The
  words only place the reciter on the page; the mark comes from this computer's sureness,
  and the reciter's checking level (`frontend/src/recite.json`) says how strict to be.
- **Source / confidence**: where a fact came from: `verified` (a person checked it),
  `derived` (a fixed rule made it) or `guessed` (a model made it and may be wrong).
- **Token**: a colour, timing or size in `frontend/src/theme.json`; components use
  `var(--...)` and never a literal.

## Where things live

- `backend/routers/`: thin endpoints. `backend/services/`: the logic.
  `backend/config.py`: every setting, and the only reader of the environment.
- `backend/services/sarf/`: the pure core of morphology. `word.py` holds a word as letters
  that know their job, and names the alphabet once; `ilal.py` the rules. `conjugation.py`
  is the only caller. Every label, column and template is in `data/sarf/`, never in code.
- `backend/data/`: reference data, built by `backend/scripts/`; derived files are
  rebuilt, never hand-edited (see `backend/data/maqayees/README.md`).
- `backend/data/progress.db`: learners' answers, the one database written while running.
- `backend/data/nahw_notes/`: the teacher's theory notes, one file per topic, read only by
  `services/nahw_notes.py` (format: its `FORMAT.md`). Testable pieces are marked in place as
  `{{role|text}}`; the Notes view in Nahw hides them or turns them into flashcards
  (`lib/notes.js`), so the stored note stays the reference. Tamreen questions link to it.
- `frontend/src/components/`: one component per tab, shared parts in `ui/`.
  `frontend/src/lib/`: helpers, and `journey.js` for where the reader has been.
- `logs/recite-journal.jsonl`: the reciting log, rolled over at 5 MB, last 3 kept.
