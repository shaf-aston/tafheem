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
venv/Scripts/python -m backend.scripts.score_mutashabihat  # similar-verse finder vs the benchmark
venv/Scripts/python -m backend.scripts.analyse "جملة" [--api URL] [--json]  # one sentence's cards and tree; stdin takes one per line
```

CI (`.github/workflows/ci.yml`) runs both suites on every PR and push to master. Tests that
need data not in git skip themselves when it is absent (`skipif` on what they need).

Data is built once by the scripts in `backend/scripts/`, each explained in its own
docstring, and never committed. The Qur'an builds come first: `build_quran_corpus.py`, then
`build_quran_meanings.py`. Rebuild the Daleel index whole: `build_daleel_index.py`, never `--only`.

## Core flow

1. **A tab picks the tool.** `frontend/src/App.jsx` holds the tabs and checks `/api/health`,
   and carries a root from one tab to another (`onGo`), so the tabs work as one app.
2. **A typed sentence is read by the book's rules alone, no AI.** `services/iraab.py` runs it:
   `morphology.py` (CAMeL) reads each word, `rule_engine.py` says what each one is,
   then an ayah the Treebank recorded is read from that record (`tarkeeb_store.py`)
   and anything else goes to `services/syntax/`: the offline parser links the words
   (`catib_onnx.py`), `facts.py` answers five questions per word and `walker.py` walks the
   book's tree (`data/nahw_rules/naming_tree.json`) to the role and its page, `teacher.py`
   dashes any name that breaks a stated rule, and `tree.py` draws the same reading as
   brackets, so the cards and the picture cannot disagree. A word no rule settles stays a gap.
   Last, `iraab.cards` builds each card once from that reading and `signs.py` writes its sign;
   the line above the cards is the picture's own top label, never a second guess.
3. **The Qur'an is looked up, never guessed.** `services/quran_corpus.py` reads the
   hand-tagged corpus; `quran_service.py` joins it with the English gloss. Tafsirs and
   translations are **editions**, all in `data/quran/library.db`, read only by
   `quran_library.py` and named only in `data/quran/editions.json`.
   Verses that read alike: `data/quran/mutashabihat.json` (built by `scripts/build_mutashabihat.py`),
   read by `services/mutashabihat.py`, which also proposes pairs the books missed.
4. **The root is the spine.** One click sends a word's root to Sarf
   (`services/conjugation.py`), the dictionary, or every place it occurs. A verb's bab
   comes only from a dictionary that states it (`services/verb_forms.py`), never a guess.
   Conjugation fills a template from `data/sarf/patterns.json`, then runs the book's rules
   over the letters (`services/sarf/`): so قَوَلَ becomes قَالَ, يَمْدُدُ becomes يَمُدُّ, and a
   root whose rules are not built says so rather than guess. The same table reads a typed
   verb back (`services/verb_reader.py`): Nahw asks it which command اِجْلِسِي is when the
   dictionary has no reading, so the rules live in one place.
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

Per-module glossaries, one word per idea across backend and frontend: `docs/glossary/`.

- **I'raab**: the ending on one word, its case and the reason for it.
- **Tarkeeb**: which words join into a unit and what that unit does. A bracket tree,
  never a per-word list. One Nahw page now draws it above the i'raab cards for the
  same typed sentence, from the same reading; the books' 47 worked examples sit in
  a drawer under it. The reading comes from the best source there is, in order: a
  typed ayah the Quranic Treebank recorded (`tarkeeb_store.for_sentence`, hand
  checked), else the parser (`services/syntax`), else the rules. Every Arabic term
  on any of those paths is spelled once, in `data/nahw_rules/tarkeeb.json`: a
  particle is named by what it is (`particle_kinds`), a unit carries its job.
  Changing how the treebank is read means rebuilding `tarkeeb.db`
  (`backend/scripts/build_tarkeeb.py`, see its docstring).
- **Sarf**: a word's root and pattern. The **gardaan** is the full table of 14 persons.
  **I'lal** is the rules that reshape a filled pattern when the root holds a weak letter, a
  hamzah or a doubled one, one per entry in `data/sarf/ilal.json`.
- **Colloquial**: spoken Arabic by dialect. `data/colloquial/spine.json` is the one course outline (units, lessons, phrase slots with English and pictures); a dialect is a folder filling it, a unit one JSON file, an exercise kind one file per end (`services/colloquial/exercises`, `lib/exercises/registry.js`); pictures are fetched by `scripts/fetch_colloquial_images.py` and approved one by one.
- **Root**: the three letters most Arabic words are built from; the one link every tab
  shares.
- **Bab**: which vowel pattern (or which form, II to X) a verb follows, read from Lane's
  Lexicon or Wiktionary, never worked out from a bare root.
- **Entry / book root**: what one book prints under one headword. A word's entry comes from
  Wiktionary (`dictionary_service.py`), a root's from a classical book: Maqayees via
  `root_meaning.py`, all four on the shelf via `lexicons.py`. The **book root** is the root as
  that book spells it (`book_root_of`); an answer carries it only when it differs from
  the letters typed. A Maqayees entry opens with the **origin sense**
  (`core_meaning`); the **rest** follows (`root_gloss.rest_of`). Its **English** comes whole
  (`together`) or line by line (`lines`), kept by `root_english.py`; never called a reading,
  which is reciting's word.
- **Edition**: one book hung on the ayahs, a tafsir or a translation, all stored one way.
- **Ear**: anything that turns sound into words. Three: `hosted` (Groq, about 250 ms),
  `letters` (tilawa's small Qur'an model on this computer, recitations only,
  `recitation/letters.py`) and `here` (Whisper on this computer). Tried in the order
  `recitation_ears` names, `here` always last. An ear that fails rests for 60 s; one
  whose key is rejected is dropped for the run. `/api/health` names them (`ear`,
  `recite_ear`, `recite_sure`).
- **Voice**: anything that says a word aloud, the ear's opposite. `lib/speak.js` tries
  them in `frontend/src/speak.json`'s order: `recorded` (a reciter from quran.com, for
  Qur'an words mapped by `scripts/build_word_audio.py`), `server` (FastPitch via
  `/api/speak`, `services/speech.py`) and `browser` (the device). `ui/SpeakButton` is
  the one button; it names the voice that spoke.
- **Recitation / reading**: Qur'an said aloud. A **reading** is one request about one
  phrase, with a reading number (`X-Reading-Id`) that the page and server both log. The
  words only place the reciter on the page; the mark comes from this computer's sureness,
  and the reciter's checking level (`frontend/src/recite.json`) says how strict to be.
- **Source / confidence**: where a fact came from: `verified` (a person checked it),
  `derived` (a fixed rule made it) or `guessed` (a model made it and may be wrong).
- **Token**: a colour, timing or size in `frontend/src/theme.json`; components use
  `var(--...)` and never a literal.
- **Tier / nodeState**: Grow's levels (Level 1, 2, 3; `frontend/src/grow.json`,
  a path names its tier in `paths.json`), and where one circle on its map stands:
  `locked`, `open`, `started` or `learnt` (`lib/grow.js`, drawn by `components/grow/`).

## Where things live

- `backend/routers/`: thin endpoints. `backend/services/`: the logic.
  `backend/config.py`: every setting, and the only reader of the environment.
- Hadith search (`services/hadith/search.py`): words matched as written and by dictionary form
  (`lemma.py`, CAMeL), numbers matched however written, misspellings swapped by `repair.py`
  (fewest slips, most common word in everyday writing via `language.py`, so a real word the hadith
  never use is kept, not "fixed"), and hadith close in meaning merged in by `meaning.py`
  (multilingual sentence model on onnxruntime; vectors from `scripts/build_hadith_meaning.py`).
  Scored by `scripts/score_hadith_search.py` against `data/hadith/search_yardstick.json`.
- `services/mushkil_split.py` cuts al-Tahawi's Mushkil al-Athar into issues (hadith that seem to
  conflict); `scripts/build_mushkil.py` writes `data/hadith/mushkil-tahawi.json`. No tab reads it yet.
- `backend/services/sarf/`: the pure core of morphology. `word.py` holds a word as letters
  that know their job, and names the alphabet once; `ilal.py` the rules. `conjugation.py`
  is the only caller. Every label, column and template is in `data/sarf/`, never in code.
- `backend/data/`: reference data, built by `backend/scripts/`; derived files are
  rebuilt, never hand-edited (see `backend/data/maqayees/README.md`).
- `backend/data/progress.db`: learners' answers, and every Nahw practice question as it was
  generated (from `data/practice/templates.json`, filed under its badge's source; `GET /api/practice/kept`). The
  one database written while running, opened only by `services/progress_store.py`. Rows are
  filed under the learner's typed name: the page sends it in the `X-Tafheem-Profile` header,
  `routers/progress.py` `current_user()` cleans it (rules only in `services/profile.py`), and
  `POST /api/progress/profile` returns the kept spelling and can move the unnamed `local` rows onto it.
- `backend/data/nahw_notes/`: the teacher's theory notes, one file per topic, read only by
  `services/nahw_notes.py` (format: its `FORMAT.md`). Testable pieces are marked in place as
  `{{role|text}}`; the Notes view in Nahw hides them or turns them into flashcards
  (`lib/notes.js`), so the stored note stays the reference. Tamreen questions link to it.
- `frontend/src/components/`: one component per tab, shared parts in `ui/`.
  `frontend/src/lib/`: helpers, and `journey.js` for where the reader has been.
  `frontend/src/components/Backdrop.jsx`: the drifting-lights canvas behind every tab, tinted by the tab colour; it exists so the dark page has depth, and it stops when Animations is off. Maths in `lib/bokeh.js`, knobs in theme.json `lights` and `marks` (the faint drifting letters under the lights). The kit page (`/app?tab=kit`, hidden from every menu) is where every element and token is seen.
- Styles live in `frontend/src/styles/`, one file per job (base, layers, motion, text, components, ...); `index.css` there imports them in cascade order.
- `logs/recite-journal.jsonl`: the reciting log, rolled over at 5 MB, last 3 kept.
