# Tafheem

Study Arabic and the Qur'an in one app: grammar of a typed sentence, the Qur'an with checked
grammar and tafsir, roots and conjugation, a dictionary, quizzes, timelines, and reciting
checked word by word. Offline by default, and every answer says where it came from.
More: `docs/core-flow-detail.md` (long notes, glossary, where things live) and
`docs/glossary/` (one word per idea, per module).

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

## Open first

One row per tab (`frontend/src/lib/tabs.js`). Screen and Data call are under `frontend/src/`;
Route, Logic and Data are under `backend/` (Data: `frontend/` where said). The `.db` files and
built `.json` files are made by `backend/scripts/` and are not in git.

| Tab | Screen | Data call | Route | Logic | Data |
|---|---|---|---|---|---|
| nahw | `components/NahwPanel.jsx` | `analyzeIraab` | `routers/analysis.py` | `services/iraab.py`, `services/syntax/` | `data/nahw_rules/`, `data/tarkeeb/tarkeeb.db` |
| sarf | `components/SarfPanel.jsx` | `analyzeMorphology`, `conjugateForm` | `routers/morphology.py` | `services/conjugation.py`, `services/sarf/` | `data/sarf/` |
| quran | `components/QuranLookup.jsx` | `quranSurahQuery` (`lib/quranOpen.js`), `searchQuran` | `routers/quran.py` | `services/quran_service.py`, `services/quran_corpus.py` | `data/quran/corpus.db`, `data/quran/library.db` |
| daleel | `components/DaleelPanel.jsx` | `findDaleel`, `daleelBooksQuery` | `routers/daleel.py` | `services/daleel/search.py` | `data/daleel.db` |
| hadith | `components/HadithPanel.jsx` | `searchHadith`, `hadithOpen`, `lib/useNarrators.js` | `routers/hadith.py`, `routers/rijal.py`, `routers/usul.py` | `services/hadith/`, `services/rijal/`, `services/usul/` | `data/hadith.db`, `data/rijal.db`, `data/usul/usul.db` |
| dict | `components/Dictionary.jsx` | `searchDictionary` | `routers/dictionary.py` | `services/dictionary_service.py` | `data/arabic_dictionary.json`, `data/lexicons.db` |
| mem | `components/MemorisePanel.jsx` | `getQuranSurah`, `getSimilar` (`lib/books.js`) | `routers/quran.py` | `services/mutashabihat.py`, `services/quran_service.py` | `data/quran/mutashabihat.json`, `frontend/public/jazariyya/poem.json` |
| grow | `components/GrowPanel.jsx` | `growPathsQuery` | `routers/grow.py` | none: the route serves the file; `lib/grow.js` steps | `data/grow/paths.json` |
| quiz | `components/QuizPanel.jsx` | `lib/quizBanks.js`, `fetchReviewItems` (`lib/progress.js`) | `routers/progress.py` | `services/progress_store.py` | `frontend/public/words/`, `data/progress.db` |
| timelines | `components/TimelinesPanel.jsx` | `timelinesQuery` | `routers/timelines.py` | `services/timelines.py` | `data/timelines/` |
| dawah | `components/DawahPanel.jsx` | `dawahQuery` | `routers/dawah.py` | `services/dawah.py` | `data/dawah/dawah.json` |
| colloq | `components/ColloquialPanel.jsx` | `colloquialQuery`, `colloquialUnitQuery` | `routers/colloquial.py` | `services/colloquial/loader.py` | `data/colloquial/` |
| kit | `components/KitPanel.jsx` | none (hidden, `/app/kit`) | none | none | none |

Nahw has more views: Tamreen (`getTamreen`, `routers/tamreen.py`, `services/tamreen.py`), Notes
(`getNotes`, `routers/nahw_notes.py`, `services/nahw_notes.py`) and Tarkeeb examples
(`getTarkeebExamples`, `routers/tarkeeb.py`, `services/tarkeeb_examples.py`). Reciting (Mem, Grow)
is step 5 below. Hadith weak points, in order: `components/HadithCards.jsx`, `lib/useNarrators.js`,
`rijalChainsQuery`, `routers/rijal.py` `get_chains`, `services/usul/store.py`, usul.db tables
`note` and `link` (built by `scripts/build_usul.py`); `lib/weak.js` ranks and counts them in the page.

## Core flow

1. **A tab picks the tool.** `frontend/src/App.jsx` holds the tabs, checks `/api/health`, and
   carries a root from one tab to another (`onGo`), so the tabs work as one app.
2. **A typed sentence is read by the book's rules alone, no AI.** `services/iraab.py` runs it:
   `morphology.py` (CAMeL) reads each word, `rule_engine.py` says what each is. An ayah the
   Treebank recorded is read from that record (`tarkeeb_store.py`); anything else goes to
   `services/syntax/`: `catib_onnx.py` links the words, `facts.py` answers five questions per
   word, `walker.py` walks the book's tree (`data/nahw_rules/naming_tree.json`) to the role and
   its page, `teacher.py` dashes any name that breaks a stated rule, and `tree.py` draws the
   brackets from the same reading, so cards and picture cannot disagree. A word no rule
   settles stays a gap. `iraab.cards` builds each card once, `signs.py` writes its sign, and
   the line above the cards is the picture's own top label, never a second guess.
3. **The Qur'an is looked up, never guessed.** `services/quran_corpus.py` reads the
   hand-tagged corpus; `quran_service.py` joins it with the English gloss. Tafsirs and
   translations are **editions**, all in `data/quran/library.db`, read only by
   `quran_library.py` and named only in `data/quran/editions.json`. Verses that read alike:
   `data/quran/mutashabihat.json` (`scripts/build_mutashabihat.py`), read by
   `services/mutashabihat.py`, which also proposes pairs the books missed.
4. **The root is the spine.** One answer to "which root", `services/roots.py`, asked by Sarf,
   Nahw, the dictionary, the Qur'an's root search and Daleel: the corpus, then the dictionary's
   headword, then CAMeL's reading of any form (a weak radical it leaves as # is settled against
   the roots the books file). One click sends a root to Sarf (`services/conjugation.py`), the
   dictionary, or every place it occurs. A verb's bab comes only from a dictionary that states
   it (`services/verb_forms.py`). Conjugation fills a template from `data/sarf/patterns.json`,
   then runs the book's rules over the letters (`services/sarf/`): قَوَلَ becomes قَالَ, and a
   root whose rules are not built says so. `services/verb_reader.py` reads a typed verb back.
5. **Reciting is heard quickly, then checked carefully.** `lib/recitingSession.js` records a
   phrase at each pause and posts it to `POST /api/listen` (`routers/listen.py`). The ears in
   `services/recitation/ears.py` write down the words, Groq first (about 0.3 s), and
   `lib/follow.js` marks the page at once. `POST /api/listen/check` then asks this computer how
   sure it is of each word, and the marks adjust. Every step goes to `logs/recite-journal.jsonl`
   (`services/journal.py`, `lib/journal.js`), joined by the reading number.
6. **Time is data.** `services/timelines.py` reads `backend/data/timelines/`, checks it on load,
   and the Timelines tab draws it; asbab al-nuzul reports hang on Seerah events.
7. **Every answer says where it came from.** `services/provenance.py` attaches a `source` from
   `data/sources.json`; `ui/SourceBadge.jsx` shows it. Verified, derived and guessed never
   look alike.
