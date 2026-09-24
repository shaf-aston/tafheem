# Tafheem: the long version

The full notes behind `CORE-FLOW.md`, kept for detail. The short file is the one to read first.

Type an Arabic sentence and get a word-by-word grammatical breakdown (I'raab), see how a
sentence's words join into one another (Tarkeeb), root and pattern analysis (Sarf), Qur'an
lookup with hand-verified grammar, dictionary search, and a vocabulary quiz; offline by
default, with every answer labelled by where it came from.

## Run it

```bash
# Backend (from project root, with venv already set up)
venv\Scripts\Activate
python -m uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```
Open http://localhost:5173. (unverified: `start.sh` one-shot launcher, not run this pass.)

```bash
venv/Scripts/python -m pytest tests -q   # backend
cd frontend && npm test && npm run lint  # frontend
```

### Data the app needs (built once, never committed)

```bash
python backend/scripts/build_quran_corpus.py   # downloads + indexes the Qur'anic grammar
python backend/scripts/build_quran_meanings.py # the word-by-word meaning of every word, English and Urdu, so a surah reads offline
python backend/scripts/build_quran_search_index.py # makes the Qur'an searchable with no network, from corpus.db
python backend/scripts/build_quran_layout.py   # which page of the Madani mushaf each ayah is on
python backend/scripts/build_quran_tafsir.py   # a scholar's commentary on each ayah, as plain text
python backend/scripts/fetch_quran_editions.py  # downloads the tafsirs and translations named in data/quran/editions.json
python backend/scripts/import_quran_editions.py # those files into one library, one book per manifest entry
python backend/scripts/build_dictionary.py     # needs the Wiktionary dump, see its docstring
python backend/scripts/build_tarkeeb.py …      # the recorded tarkeeb, see its docstring for the two downloads
python backend/scripts/build_root_meanings.py  # Ibn Faris's origin sense for 4,738 roots (needs access-parser)
python -m backend.scripts.build_lane_verbs     # every Form I bab Lane's Lexicon states, from lexicons.db
python backend/scripts/build_lexicon.py        # one table of every quiz word (needs the dictionary above)
python backend/scripts/backfill_root_english.py # optional: put the Maqayees entries into English ahead of time (needs an AI backend)
python backend/scripts/build_urdu_links.py     # what each quiz word's letters mean in Urdu; candidates for a person to check
python backend/scripts/export_quiz_words.py    # that table as the three files the quiz fetches
python backend/scripts/build_asbab.py          # al-Suyuti's Lubab al-Nuqul, cut into one asbab al-nuzul passage per ayah
python backend/scripts/build_tamreen.py save|build # the Tamreen form quizzes as a tagged library; the browser half is tamreen_harvest.js
python backend/scripts/build_daleel_index.py   # every book into one searchable index (the whole thing, never --only)
python backend/scripts/build_daleel_index.py --words # just the word table, added to the index already there
python backend/scripts/build_daleel_index.py --meta  # just the source/book table, added to the index already there
```

## Core flow

1. **A tab picks the tool**: `frontend/src/App.jsx` holds the tabs and one `/api/health`
   check, so the user knows the backend is up before trying anything. It also carries a root
   from one tab to another (`onGo`), which is what stops the six being six separate apps.
   Nahw is one tab with two zoom levels, `NahwPanel.jsx` chooses between the wide view
   (tarkeeb) and the close-up (i'raab) and hands a sentence from one to the other.
2. **Local morphology tags a typed sentence**: `arabic_text.words()` first decides what a word
   is (a token with an Arabic letter, the Qur'an's reading marks taken off), so a pause sign or
   an ayah number never gets a card. Then `backend/services/morphology.py` runs CAMeL
   Tools (falling back to Qalsadi, then PyArabic) for root, POS, case and diacritics. Neighbouring
   words disambiguate homographs (ذهب = "gold" or "he went"). This is a guess and is labelled as one.
3. **The rule engine derives I'raab deterministically**: `backend/services/rule_engine.py`
   applies classical Nahw rules to those tags and scores its own confidence, so the tool works
   with no network and no API cost. Every word it names carries a `role_key` beside the Arabic
   role, the stable name the grid colours by, checked against `schemas.ROLE_KEYS` on the way
   out so the AI's answer cannot invent one. `lib/roleColors.js` turns that name into a theme
   token and reads nothing else; the Arabic prose is for the reader, never for the colour.
   Only when that confidence falls below the threshold in `backend/config.py` does
   `backend/routers/analysis.py` call an AI backend, one sentence at a time with the answer kept
   (`ai_answer_cache_size`), because the free tier allows about three I'raabs a minute. A backend that fails permanently (dead
   key, missing model) retires itself, so the app stops claiming it.
4. **Tarkeeb is a tree, and a separate question**: which words join into a unit, and what that
   unit then does. Two sources, and the badge always says which: `tarkeeb_store.py` reads what
   scholars recorded (`data/tarkeeb/tarkeeb.db`, 5,023 of the 6,236 ayahs), and where that has
   nothing `tarkeeb.py` derives what it can from the corpus tags: a governing word (إِنَّ, كَانَ,
   كَادَ and their sisters) decides the case of its ism and khabar, and a word that shows no
   case, typed Arabic without harakat, is placed by position. Every Arabic term and tag
   either reads is in `data/nahw_rules/tarkeeb.json`; `tarkeeb_examples.py` serves the trees
   taken from books in `data/tarkeeb/examples/`. `frontend/src/lib/tarkeebLayout.js` works out
   where every brace goes from the tree's shape alone, nothing about drawing is stored, and
   `TarkeebDiagram.jsx` draws it. A join that cannot be made is drawn open, not guessed.
5. **The Qur'an's grammar is looked up, never guessed**: `backend/services/quran_corpus.py`
   reads the hand-tagged Quranic Arabic Corpus from `data/quran/corpus.db`; the English gloss
   comes from `quran_meanings.py` (`data/quran/meanings.db`, built once from Quran.com, with the
   network as a fallback when it has not been built). `quran_service.py` joins the two. Two files,
   not one, because they are two sources under two licences; either can be rebuilt alone.
   Searching is its own module, `services/quran_search/`, with two ways of answering behind
   one function: Quran.com, which searches the translations too, and `data/quran/search.db`,
   built from the corpus so search works with no network. Whichever answered says so on the
   result, because they are two different texts.
6. **A surah is read whole, an ayah is studied**: `GET /api/quran/surah/{n}` returns a surah's
   text and English in two local queries (~35ms for al-Baqarah's 286 ayahs, which used to mean 286
   network calls). The word-by-word grammar is ~2MB a surah, so it is left out of the reading view
   and fetched for the one ayah you open, `frontend/src/components/SurahReader.jsx`. What the ayah
   is *about* is a third question, and many books answer it: an **edition** is one book hung on
   the ayahs, a tafsir or a translation, and because they all have one shape they all live in
   `data/quran/library.db` with `quran_library.py` as its only reader. `data/quran/editions.json`
   is the only place a book is named, so adding one is an entry there plus its file, never code.
   `GET /api/quran/editions` lists what is installed, `/editions/{surah}/{ayah}` is one ayah
   across the books, and `/editions/surah/{n}?id=` is one book across a surah, which is what puts
   an English sentence under every ayah of the reading view in one request rather than 286.
   `AyahTafsir.jsx` shows one commentary shut, fetches nothing until it is opened, keeps the
   others one click away and remembers which was chosen; a passage that comments on a run of
   ayahs is stored once and says which ayahs it covers. Memorise deals a *printed* page, not about 135 words of one:
   `quran_layout.py` reads `data/quran/layout.db`, the page of the 604-page Madani mushaf every
   ayah begins on, `get_surah` hands that number down with each ayah and `lib/memorise.js` groups
   by it. Without that build the number is absent and the word count is used, as before.
7. **The root is the spine**: every Qur'anic word carries a verified root, so one click sends
   it to Sarf to be conjugated (`services/conjugation.py`, rules in `data/sarf/patterns.json`),
   to the dictionary, or to every other place it occurs (`GET /api/quran/root/{root}`). The
   باب comes only from a named dictionary that states it, never guessed from a bare root:
   Lane's Lexicon (`data/sarf/lane_verbs.json`, built by
   `python -m backend.scripts.build_lane_verbs`) and Wiktionary, wired in
   `services/verb_sources/SOURCES` (`services/verb_sources/README.md` says how to add one)
   and merged by `services/verb_forms.py`'s `babs_of()`, citing both books when they agree
   and keeping disagreeing babs as separate readings. A
   word neither book records shows no table, only the form picker, and says so rather than
   falling back to a guess. A root whose letters shift (weak, doubled, hamzated) is named and
   refused rather than conjugated wrongly. `tests/test_conjugation.py` pins the tables to the
   book.
8. **Time is its own tab**: the Timelines tab lays five stretches of time end to end, from
   the Prophets to the Day of Judgement, each labelled with the science it belongs to
   (Seerah, Stories of the Prophets, 'Aqidah) and filterable by it. The content is data:
   `backend/data/timelines/library.json` declares everything a section may point at (a
   science, a place, a caution flag, a hadith collection, the map's shapes) and one file per
   section under `sections/` holds its events, so adding an event is an edit to a JSON file.
   `services/timelines.py` is that folder's only reader and checks it on load, an event out of
   order, an `until` pointing backwards or a Qur'an reference past the end of its surah stops
   the app and names the event. `lib/timelineLayout.js` works out rows, gaps, gutter lanes and
   map pins from `at` and `until` alone, and the components only draw it. Every Qur'an
   reference is a button into the Qur'an tab; a hadith number says it is not checked, because
   no hadith collection is installed here. Inside the Seerah, each event also carries the
   **asbab al-nuzul** reports for its ayahs: al-Suyuti's Lubab, cut into reports by
   `services/asbab_split.py`, stored as two editions (`asbab-lubab-ar` and the English
   Claude wrote beside it) and linked to an event either by the wording that names it or,
   failing that, by whether its surah came down at Makkah or at Madinah.
9. **Every answer says where it came from**: `backend/services/provenance.py` reads
   `data/sources.json` and attaches a `source` to each response; `ui/SourceBadge.jsx` shows it.
   This is the app's core honesty rule: verified, derived and guessed never look alike.

## Glossary

The words this app uses, in plain terms. A check, not a gate: if a term here reads unclearly,
it is the term that is wrong.

- **I'raab**: the ending on one word: its case, and the reason for it.
- **Tarkeeb**: the other question: which words join into a unit, what that unit is, and what
  it does in the sentence. A bracket tree, never a per-word list. The two are not the same
  thing and never share a panel.
- **Sarf**: morphology: a word's root and derivational pattern. Its two shapes, both named
  after the books: the **gardaan**, the full grid of 14 persons by tense, and the **sarf
  sagheer**, the one-line summary of a باب that heads a chapter.
- **Bab**: which of the six Form I vowel patterns a verb follows (نَصَرَ يَنْصُرُ, ضَرَبَ
  يَضْرِبُ, ...), or which mazid form (II to X) it is. Read from a named dictionary that
  states it, Lane's Lexicon or Wiktionary; never worked out from a bare root, which cannot
  say. Names and codes in `data/sarf/babs.json`.
- **CAMeL**: CAMeL Tools, the Arabic morphology library installed here. It reads a word
  apart into root and features, and can build a verb's present tense by rule. Called CAMeL
  everywhere, never "tagger" or "engine".
- **Nahw**: Arabic syntax rules; `data/nahw_rules/rules.json` is the rule data.
- **Root**: the three letters nearly every Arabic word is built from. The one identifier
  shared by every tab, and the thing a cross-tab link carries.
- **Corpus / segment**: the Quranic Arabic Corpus v0.4 (GNU GPL), 130,030 hand-tagged
  segments. A **segment** is one piece of a written word, a prefix, the word itself, an
  ending; the corpus tags each separately, which is how the app can show a word being built up.
- **Tamreen**: the teacher's Google Form quizzes, one file per form under
  `data/tamreen/exercises/`. Tag-driven: `tags.json` lists every grammar point once,
  each exercise just names the ones it covers, so a new form is a new file, never new code.
  Served at `/api/tamreen`, filterable by `?tag=`, and read by the Nahw tab's third view
  (`TamreenPanel.jsx`): Practise drills one question at a time, Browse reads a whole form.
  Practise answers the Quiz's way, same keys and same waits, sharing
  `ui/AutoAdvanceToggle.jsx`; picks live in the browser under `tamreen-answers`
  (`lib/tamreenAnswers.js`), which the header's Start over forgets.
- **Edition**: one book of text hung on the ayahs. A tafsir, a translation. Every one has
  the same shape, an id, a language, a name, whose it is, its licence, and passages that
  each cover a run of ayahs, so they are all stored one way and read one way. Named only in
  `data/quran/editions.json`.
- **Ear**: anything that turns sound into words. There are three, `hosted` (Groq, about
  250ms), `letters` (tilawa's small Qur'an model on this computer, about 640ms,
  recitations only, `recitation/letters.py`) and `here` (Whisper on this computer, about
  1,600ms), behind one interface in `backend/services/recitation/ears.py`. They are tried
  in the order `recitation_ears` names, Whisper here always last because it needs no key
  and no internet; an ear that answers with a rejected key is struck off for the rest of
  the run, the same way the AI backends are (`backend/services/fallback.py`).
  `/api/health` says which would answer a search (`ear`) and a recitation (`recite_ear`).
- **Recitation**: Qur'an said aloud, heard by whichever ear answers first, same as a
  search. Two questions of the same recording, asked separately (`POST /api/listen` for the
  words, `POST /api/listen/check` for the sureness) so a slow score never holds back a
  reciter reading on. What was written down says only *which part of the page* this is
  (`place.py`); it never decides a mark, because one correctly recited word in ten came
  back misspelt. How sure the model on this machine is of each page word decides the mark
  instead (`recite_sure` on `/api/health`; only that model can score, see ears.py), and the
  reader's checking level (beginner, standard, advanced, in `frontend/src/recite.json`) says
  how far. Words and vowels only: tajweed is not checked. A quiet reciter is kept twice over:
  `lib/dictation.js` calls a voice anything above the quietest that microphone has heard
  rather than above one fixed number, and `recitation/loudness.py` lifts a soft recording
  before the model. `lib/microphone.js` is the only place a microphone is opened. **Dictation** is a search box
  spoken into, heard by whichever ear answers first. Words are matched
  against the Qur'an's own text to offer the ayahs they might be; both steps can be wrong,
  so several are offered and the badge says `guessed`. No recording is kept.
- **Source / confidence**: where a fact came from, as `verified` (a person checked it),
  `derived` (a fixed rule produced it) or `guessed` (a model produced it and may be wrong).
- **Word labels**: on every quiz word: **word type** (noun/verb/adjective, so a question's four
  options match), **meaning key** (two words sharing one are never offered together),
  **times in Qur'an** (what the 80% list is built from), **attached** (stuck to a prefix or
  ending). Written `word_type` in the table, `wordType` in the files the browser reads.
- **Meaning language**: which language the quiz shows a meaning in, English unless the reader
  changes it. Only the Qur'anic words have an Urdu meaning; the everyday list has no Urdu
  source, so an Urdu round says so instead of falling back to English. Each language is scored
  under its own module (`quiz`, `quiz:ur`), because knowing a word in one is not knowing it in
  the other. `frontend/src/lang/ur.json` holds the interface in Urdu, keyed by the English
  sentence, so an untranslated sentence shows its English rather than a blank.
- **Cognate / false friend**: what a quiz word's letters mean to someone who reads Urdu, which
  took much of its vocabulary from Arabic. A **cognate** means the same in both; a **false
  friend** does not, and مَكَان is a place in Arabic and a house in Urdu.
  `backend/scripts/build_urdu_links.py` finds candidates by comparing two Wiktionary glosses
  and is wrong often, so nothing reaches the screen until a person lists it in
  `backend/data/urdu_links.overrides.json`; the same arrangement `word_kinds.json` has.
- **Set / group / cut**: a **set** is which list a word came from (`everyday`, `book`,
  `quran`); a **group** is a named part of one (`book:faith`, `everyday:travel`); a **cut** is
  any of those, or one surah or juz, and is what the picker actually selects. A word can be in
  two sets and stay one word, the list it came from is a tag on its row, not a separate file.
- **Timeline section / `at` / `until`**: a **section** is one stretch of time on the
  Timelines tab (the Seerah, the Grave), belonging to one science. **`at`** is when an event
  happens: a year in a dated section, a step in the others. Two events with the same `at`
  happen together and share a row. **`until`** names the event a thing lasts until, and is
  drawn as a bar beside the line (the Muslims in Abyssinia, 615 to 628).
- **Asbab al-nuzul**: the reports of what was happening when an ayah came down. Here,
  al-Suyuti's Lubab al-Nuqul from OpenITI, cut into reports by rule and matched to ayahs by
  the words each report quotes. A report matching no single ayah is listed in
  `data/quran/asbab-unmatched.json`, never attached to a guess. Each report says how it
  reached an event: **named**, its wording names that event, or **period**, it is filed on
  the Makkan or Madinan stretch by its surah.
- **Token**: a colour, timing or size value in `frontend/src/theme.json`. `theme.js` is its
  only reader; components use `var(--…)` and never a literal.

## Where things live

- `backend/routers/`, API endpoints; thin, delegate to services.
- `backend/services/`, the logic: morphology, rule engine, conjugation, corpus, dictionary,
  practice, provenance, tarkeeb, and the AI backends behind one interface (`services/ai/`).
- `backend/data/`, all reference data and config: `sources.json` (who to credit and how far
  to trust them), `quran/` (corpus, word-by-word English, mushaf page breaks, and `library.db`, every tafsir and
  translation, named in `editions.json` and built from the files in `downloads/`),
  `sarf/patterns.json`, `nahw_rules/`, `practice/templates.json`, `tarkeeb/` (`topics.json`,
  the topics every book is browsed by, and `examples/`, one file per book), and `maqayees/`,
  what Ibn Fāris says a root has meant at its origin. Maqayees is derived, never authored:
  rebuild it rather than editing it, and read `backend/data/maqayees/README.md` before
  touching anything in there; that file owns its config knobs, its spelling rules, its
  English, and what the book does not cover.
- `backend/scripts/`, one-time builders for the data above.
- `backend/models/schemas.py`, Pydantic request/response shapes.
- `frontend/src/theme.json` + `settings.json`, every visual token, and every setting a
  reader can change. `theme.js` and `lib/settings.js` are their only readers; both write
  CSS variables onto `:root`, which is why no component holds a colour or a size.
- `frontend/src/lib/journey.js`, where the reader has been: the list of places the trail
  line and the browser's back arrow both read. `lib/tabUrl.js` is the only writer of the
  address bar; `lib/session.js` the only reader and writer of the saved path, with its knobs
  (shelf life, size caps, record version) in `frontend/src/session.json`. A place is a tab
  plus what it was opened with, never a result, so a reload refetches and cannot show stale.
- `frontend/src/components/`, one component per tab, plus shared `ui/`.
- `frontend/src/lib/`, client helpers (errors, export, history, colour, quiz generation).
  The vocabularies shared with the backend live here as one file each, so a name is written
  down once rather than retyped: `roleColors.js` (role → colour token),
  `rootMeaningStatus.js` (the classical book's three states), `verbClass.js`.
- `backend/services/arabic_text.py`, the single owner of "is this Arabic?" and of root
  spelling. `normalize_root` keeps the Arabic letters rather than dropping a list of
  separators, because that list can never be complete; an en-dash or a zero-width space
  would otherwise file a root under a key no search can produce.
- `backend/data/lexicon.db`, one row per quiz word, built from the two hand-written lists in
  `backend/data/` (`vocabulary.json`, `quranic-words.json`) and the corpus. Derived, never
  authored: rebuild it rather than editing it, and correct a word's type in
  `backend/data/word_kinds.json`.
- `frontend/public/words/`, that table as three files the quiz fetches once: every word in
  `words.json`, and `cuts.json` saying which words each cut holds, as positions into it. So
  **All** is no filter rather than three lists merged, and no word is stored twice.
- `backend/data/progress.db`, every answer a learner has given. The one database written
  while the app is running, and the only one with no build script: it makes itself on the
  first answer. Settings > Clear saved data empties it (`DELETE /api/progress`) along with
  the browser store, so one button forgets everything. Owned by `backend/services/progress_store.py`, which knows nothing about
  Arabic, only `(user, module, item, correct, ms)`, so any panel can file answers in it.
  What kind of word an item was is joined back on in `frontend/src/lib/insights.js`, from
  the word list the page already holds.
