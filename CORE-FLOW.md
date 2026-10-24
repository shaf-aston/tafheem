# Tafheem

Study Arabic and the Qur'an in one app: grammar of a typed sentence, the Qur'an with checked
grammar and tafsir, roots and conjugation, a dictionary, quizzes, timelines, and reciting
checked word by word. Offline by default, and every answer says where it came from.
More: `docs/core-flow-detail.md` (long notes), `docs/glossary/` (per module; `nahw-flow.md` is the i'raab
engine, stage by stage, kept true by its test), `RECITE-PLAN.md` (reciting rules), `docs/strategy/README.md`.

## Run it

```bash
venv\Scripts\Activate
python -m uvicorn backend.main:app --reload --port 8000   # backend, project root
cd frontend && npm run dev                                 # frontend, open http://localhost:5173
venv/Scripts/python -m pytest tests -q                     # backend tests
venv/Scripts/python -m backend.scripts.worktree new|remove NAME|ci  # ready copy, data linked from ../tafheem-data; drop it safely; or tests with no data, as CI
cd frontend && npm test && npm run lint                    # frontend tests
EAR=http://127.0.0.1:8000 node frontend/scripts/probe-ear.mjs  # reciting, end to end
venv/Scripts/python -m backend.scripts.nahw.score_iraab [--set checked]  # i'raab roles vs the books, or the 72 checked sentences
venv/Scripts/python -m backend.scripts.quran.score_mutashabihat  # similar-verse finder vs the benchmark
venv/Scripts/python -m backend.scripts.nahw.analyze "جملة" [--api URL] [--json]  # one sentence's cards and tree; stdin takes one per line
```

## Open first

Folders, top down (one domain = one folder, same name on both sides):

```
frontend/src/
  config/        one JSON per feature; the only place a number or a label is hardcoded
  components/    one folder per tab (nahw/, quran/, …) + ui/ (kit shared by all) + shell/ (header, settings, offline)
  lib/           one folder per tab (same names as components/) + the shared ones:
    nav/         tabs registry, URL ↔ tab, journey, dock/recent rules, command line
    api/         axios client errors, health, sources, warm-up
    store/       localStorage helpers, settings, shelf
    learner/     progress, profile, rewards, level
    motion/      reveal, tilt, swipe, scroll, rails
    text/        Arabic text helpers, edit distance, shuffle, verse refs
    speech/      speak, pronounce, microphone, dictation
    theme/       accent, colour scheme, tone
    hooks/       small React hooks with no domain (media, modal, search, slow-pending)
backend/
  routers/       one file per tab; thin, they call a service
  services/      one package per tab (quran/, nahw/, sarf/, dictionary/, hadith/, daleel/, learner/, …) + the shared ones:
    core/        startup, fallback, rate limit, read-only db, provenance, timing
    text/        arabic_text, harakat, spelling, markup, fts, refs
  data/          the files the services read; built by scripts/
  scripts/       builders, one per data file
tests/           same folders as services/ (nahw/, quran/, …) + core/ (config, headers, deploy)
                 + scripts/ (builders); a domain with one test file keeps it at the root
```

Rule of thumb: a file about one tab lives in that tab's folder on both sides;
a file two tabs share lives in one of the shared folders above, never at the root.


One row per tab (`frontend/src/lib/nav/tabs.js`). Screen and Data call are under `frontend/src/`;
Route, Logic and Data are under `backend/` (Data: `frontend/` where said). The `.db` files and
built `.json` files are made by `backend/scripts/` and are not in git.

| Tab | Screen | Data call | Route | Logic | Data |
|---|---|---|---|---|---|
| home | `components/home/HomePanel.jsx` | `fetchOverview` (`lib/learner/progress.js`) | `routers/progress.py` | `services/learner/progress_store.py` | `data/progress.db` |
| nahw | `components/nahw/NahwPanel.jsx` | `analyzeIraab` | `routers/analyze.py` | `services/nahw/iraab.py`, `services/nahw/syntax/` | `data/nahw_rules/`, `data/tarkeeb/tarkeeb.db` |
| sarf | `components/sarf/SarfPanel.jsx` | `analyzeMorphology`, `conjugateForm` | `routers/morphology.py` | `services/sarf/conjugation.py`, `services/sarf/` | `data/sarf/` |
| quran | `components/quran/QuranPanel.jsx` | `quranSurahQuery` (`lib/quran/quranOpen.js`), `searchQuran` | `routers/quran.py` | `services/quran/service.py`, `services/quran/corpus.py` | `data/quran/corpus.db`, `data/quran/library.db` |
| daleel | `components/daleel/DaleelPanel.jsx` | `findDaleel`, `daleelBooksQuery` | `routers/daleel.py` | `services/daleel/search.py` | `data/daleel.db` |
| hadith | `components/hadith/HadithPanel.jsx` | `searchHadith`, `hadithOpen`, `lib/hadith/useNarrators.js` | `routers/hadith.py` | `services/hadith/` (`rijal/`, `usul/` inside) | `data/hadith.db`, `data/rijal.db`, `data/usul/usul.db` |
| dict | `components/dictionary/DictionaryPanel.jsx` | `searchDictionary` | `routers/dictionary.py` | `services/dictionary/service.py` | `data/arabic_dictionary.json`, `data/lexicons.db` |
| mem | `components/memorise/MemorisePanel.jsx` | `getQuranSurah`, `getSimilar` (`lib/memorise/books.js`) | `routers/quran.py` | `services/quran/mutashabihat.py`, `services/quran/service.py` | `data/quran/mutashabihat.json`, `frontend/public/jazariyya/poem.json` |
| grow | `components/grow/GrowPanel.jsx` | `growPathsQuery` | `routers/grow.py` | none: the route serves the file; `lib/grow/lesson.js` builds the steps | `data/grow/sources.json`, `data/grow/worlds/prayer/` |
| quiz | `components/quiz/QuizPanel.jsx` | `lib/quiz/quizBanks.js`, `fetchReviewItems` (`lib/learner/progress.js`) | `routers/progress.py` | `services/learner/progress_store.py` | `frontend/public/words/`, `data/progress.db` |
| timelines | `components/timelines/TimelinesPanel.jsx` | `timelinesQuery` | `routers/timelines.py` | `services/timelines.py`, `services/text/refs.py`, `services/quran/asbab.py` | `data/timelines/` |
| dawah | `components/dawah/DawahPanel.jsx` | `dawahQuery` | `routers/dawah.py` | `services/dawah.py` | `data/dawah/dawah.json` |
| colloq | `components/colloquial/ColloquialPanel.jsx` | `colloquialQuery`, `colloquialUnitQuery` | `routers/colloquial.py` | `services/colloquial/loader.py` | `data/colloquial/` |
| kit | `components/kit/KitPanel.jsx` | none (hidden, `/app/kit`) | none | none | none |

Nahw has more views: Tamreen (`getTamreen`, `routers/tamreen.py`, `services/nahw/tamreen.py`), Notes
(`getNotes`, `routers/nahw_notes.py`, `services/nahw/notes.py`) and Tarkeeb examples
(`getTarkeebExamples`, `routers/tarkeeb.py`, `services/nahw/tarkeeb_examples.py`). Reciting (Mem, Grow)
is step 5 below. Hadith weak points, in order: `components/hadith/HadithCards.jsx`, `lib/hadith/useNarrators.js`,
`rijalChainsQuery`, `routers/hadith.py` `get_chains`, `services/hadith/usul/store.py`, usul.db tables
`note` and `link` (built by `scripts/hadith/build_usul.py`); `lib/hadith/weak.js` ranks and counts them in the page.

## Core flow

1. **A tab picks the tool.** `frontend/src/App.jsx` holds the tabs, checks `/api/health`, and
   carries a root from one tab to another (`onGo`), so the tabs work as one app.
   Home is the first screen and lists the tabs from the registry.
2. **A typed sentence is read by the book's rules alone, no AI.** `services/nahw/iraab.py` runs it:
   `morphology.py` (CAMeL) reads each word, `rule_engine.py` says what each is. An ayah the
   Treebank recorded is read from that record (`tarkeeb_store.py`); anything else goes to
   `services/nahw/syntax/`: `catib_onnx.py` links the words, `facts.py` answers five questions per
   word, `walker.py` walks the book's tree (`data/nahw_rules/naming_tree.json`) to the role and
   its page, `teacher.py` dashes any name that breaks a stated rule, and `tree.py` draws the
   brackets from the same reading, so cards and picture cannot disagree. A word no rule
   settles stays a gap. `iraab.cards` builds each card once, `signs.py` writes its sign, and
   the line above the cards is the picture's own top label, never a second guess.
3. **The Qur'an is looked up, never guessed.** `services/quran/corpus.py` reads the
   hand-tagged corpus; `quran_service.py` joins it with the English gloss. Tafsirs and
   translations are **editions**, all in `data/quran/library.db`, read only by
   `quran_library.py` and named only in `data/quran/editions.json`. Verses that read alike:
   `data/quran/mutashabihat.json` (`scripts/quran/build_mutashabihat.py`), read by
   `services/quran/mutashabihat.py`, which also proposes pairs the books missed.
4. **The root is the spine.** One answer to "which root", `services/dictionary/roots.py`, asked by Sarf,
   Nahw, the dictionary, the Qur'an's root search and Daleel: the corpus, then the dictionary's
   headword, then CAMeL's reading of any form (a weak radical it leaves as # is settled against
   the roots the books file). One click sends a root to Sarf (`services/sarf/conjugation.py`), the
   dictionary, or every place it occurs. A verb's bab comes only from a dictionary that states
   it (`services/sarf/verb_forms.py`). Conjugation fills a template from `data/sarf/patterns.json`,
   then runs the book's rules over the letters (`services/sarf/`): قَوَلَ becomes قَالَ, and a
   root whose rules are not built says so. `services/sarf/verb_reader.py` reads a typed verb back.
5. **Reciting is heard quickly, then checked carefully.** `lib/recite/recitingSession.js` records a
   phrase at each pause and posts it to `POST /api/listen` (`routers/listen.py`). The ears in
   `services/recitation/ears.py` write down the words, Groq first (about 0.3 s), and
   `lib/recite/follow.js` marks the page at once. `POST /api/listen/check` then asks this computer how
   sure it is of each word, and the marks adjust. Every step goes to `logs/recite-journal.jsonl`
   (`services/learner/journal.py`, `lib/recite/journal.js`), joined by the reading number.
6. **Time is data.** `services/timelines.py` reads `backend/data/timelines/`, checks it on load,
   and the Timelines tab draws it; asbab al-nuzul reports hang on Seerah events.
7. **Every answer says where it came from.** `services/core/provenance.py` attaches a `source` from
   `data/sources.json`; `ui/SourceBadge.jsx` shows it. Verified, derived and guessed never
   look alike.

## Glossary

- **I'raab**: one word's case and why. **Tarkeeb**: which words join into a unit, as a bracket tree.
- **Root**: the three letters a word is built from; the link every tab shares (`services/dictionary/roots.py`).
- **Bab**: a verb's vowel pattern or form, read from Lane or Wiktionary, never worked out.
- **Edition**: one tafsir or translation hung on the ayahs. **Ear / voice**: sound to words, words to sound; the Trial ear is taught, judged and shipped by `backend/scripts/recitation/finetune_ear/README.md`.
- **Source**: `verified`, `derived` or `guessed`, carried by every answer.
- **Weak point**: a flagged narrator or link in a chain; `notes` and `links` in code (`docs/glossary/hadith.md`).
- **Token**: a theme value in `frontend/src/config/theme.json`; components use `var(--...)`, never a literal.
- **Search words**: `?q=` is what a search sends, `query` is what the answer echoes back, `asked` is the
  text as the reader typed it, before any cleaning. Qur'an: `surah` and `ayah` (the large majority already);
  `verse` and `chapter` are for poetry and hadith books. New code follows these; old names that are stored
  or come from outside (URL params, the `verse` search table, upstream payloads) stay as they are.
