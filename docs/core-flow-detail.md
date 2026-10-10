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

## Core flow (older notes, partly stale: the current one is below)

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
3. **The book's rules name every role, with no network**: `backend/services/iraab.py` is the
   one reader. `rule_engine.py` gives each word a card (type, case, sign, reason) from its tags
   and typed vowels. Then `services/syntax/` reads the sentence: `catib_onnx.py` links the
   words offline, `mask.py` overrules links the book settles, `facts.py` answers five
   independent questions per word (kind, follows, governor, slot, voice) and `walker.py`
   walks `data/nahw_rules/naming_tree.json`, the book's divisions as data, to a role and its
   page. `teacher.py` re-reads the set and dashes a name that breaks a stated rule. Those
   names replace the cards' first guess (`iraab.with_parser_roles`); a word no rule names
   stays a gap. Every word carries a `role_key` beside the Arabic role, checked against
   `models/analyze.py ROLE_KEYS`; `lib/roleColors.js` turns it into a theme token and reads nothing else.
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

## Glossary (older; current one below and in `docs/glossary/`)

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
- **Nahw**: Arabic syntax rules; `data/nahw_rules/` holds them as data (word lists, roles, the naming tree, the teacher's checks).
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
  one threshold (`sure-at` in `frontend/src/recite.json`, no levels) says
  how far. Where in the whole Qur'an a reading is comes from the words too
  (`recitation/locate.py`, asked with the open page as `near`): a reading found elsewhere,
  surely, never lands on the page; the page jumps there, or asks first while words are
  hidden. Words and vowels only: tajweed is not checked. A quiet reciter is kept twice over:
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

## Where things live (older; current one below)

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
- `backend/models/`, Pydantic request/response shapes, one file per router (`models/quran.py` for
  `routers/quran.py`) and `common.py` for the two every feature shares (`Source`, `Correction`).
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
  `loadStatus.js` (a classical book's three states), `verbClass.js`.
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

## Moved from CORE-FLOW.md

The sections below were the long part of the short map, moved here word for word. The
Glossary, Where things live and Core flow sections above them are older versions; where they
differ, these are the current ones.

### Tests, CI and data builds

CI (`.github/workflows/ci.yml`) runs both suites on every PR and push to master. Tests that
need data not in git skip themselves when it is absent (`skipif` on what they need).

Data is built once by the scripts in `backend/scripts/`, each explained in its own
docstring, and never committed. The Qur'an builds come first: `build_quran_corpus.py`, then
`build_quran_meanings.py`. Rebuild the Daleel index whole: `build_daleel_index.py`, never `--only`.

### Core flow, full wording

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
4. **The root is the spine.** Which root a word comes from has one answer, `services/roots.py`,
   asked by Sarf, Nahw, the dictionary, the Qur'an's root search and Daleel alike: the corpus,
   then the dictionary's headword, then CAMeL's reading of any form, a weak radical CAMeL
   leaves as # (ق#ل for قالوا) settled against the roots the books file. One click sends a word's root to Sarf
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

### Glossary (current)

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
  shares, and worked out in one place (`services/roots.py`).
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

### Where things live (current)

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
- Weak points on a chain: `scripts/build_usul.py` levels each narrator's grade in `rijal.db` against Ibn Hajar's
  twelve (`services/hadith/usul/level.py`, words in `data/usul/usul.json`) and writes the small, git-tracked `data/usul/usul.db`.
  `services/hadith/usul/store.py` reads it; `GET /api/rijal/chains/...` carries `notes` and `scale`; `lib/weak.js` ranks them and
  `ui/ChainDrawing` and `ui/WeakPoints` show them. A grade no term reads is listed in the gap table, never guessed.
- What scholars said of a hadith: the same build reads three ruling books (Ibn Shahin, Ibn Abi Hatim's 'Ilal, Ibn al-Jawzi's
  Mawdu'at). `services/hadith/usul/ruling.py` cuts out the scholar's own sentence, `services/hadith/usul/match.py` finds which of our hadith
  it is about (rare shared word 3-grams, then a shared narrator), knobs in `usul.json` `rulings.match`. The `ruling` table is
  quoted with book and page and never inferred; what no sentence or hadith fits goes to the gap table.
  `GET /api/rijal/chains/...` carries `rulings`; `GET /api/usul/terms[/{kind}]` (`routers/hadith.py`) feeds the Hadith tab's
  Scholars list (`ScholarTerms`); `ui/ScholarRulings` quotes them under "Possible".
- `backend/services/sarf/`: the pure core of morphology. `word.py` holds a word as letters
  that know their job, and names the alphabet once; `ilal.py` the rules. `conjugation.py`
  is the only caller. Every label, column and template is in `data/sarf/`, never in code.
- `backend/data/`: reference data, built by `backend/scripts/`; derived files are
  rebuilt, never hand-edited (see `backend/data/maqayees/README.md`).
- `backend/data/progress.db`: learners' answers, and every Nahw practice question as it was
  generated (from `data/practice/templates.json`, filed under its badge's source; `GET /api/practice/kept`). The
  one database written while running, opened only by `services/progress_store.py`. Rows are
  filed under the learner's username (no password): the page sends it on every request (`api.js` interceptor) in the `X-Tafheem-Profile`
  header, `identity.py` `current_user()` cleans it (rules only in `services/profile.py`) and
  refuses a name with no account. `POST /api/progress/signup` and `/login` return the kept spelling
  (sign-up can move the guest `local` rows onto it); `/account` and `/leaderboard` feed the profile.
  Everything else a person keeps (settings, Grow steps, favourites, history) is in the browser,
  filed by `frontend/src/lib/stored.js` under the logged-in name (`@amina/settings`; the guest's
  keys are bare). That one account's keys are its shelf: `lib/shelf.js` pulls it from
  `GET /api/progress/saved` at start-up and log-in and `PUT`s it back a moment after any change (at once when the page is hidden),
  so it follows the name to any device. Log-in and log-out reload the page.
  Teams: any account that adds a member (`POST /api/progress/team`) is a team; `GET /team`
  returns the tree below it with each person's words learnt and answers (`progress_store.team_tree`,
  loops refused). While `beta_list_accounts` is on, `GET /accounts` lists every username for the
  log-in box.
- `backend/data/nahw_notes/`: the teacher's theory notes, one file per topic, read only by
  `services/nahw_notes.py` (format: its `FORMAT.md`). Testable pieces are marked in place as
  `{{role|text}}`; the Notes view in Nahw hides them or turns them into flashcards
  (`lib/notes.js`), so the stored note stays the reference. Tamreen questions link to it.
- `frontend/src/components/`: one component per tab, shared parts in `ui/`.
  `frontend/src/lib/`: helpers, and `journey.js` for where the reader has been.
  `frontend/src/components/Backdrop.jsx`: the drifting-lights canvas behind every tab, tinted by the tab colour; it exists so the dark page has depth, and it stops when Animations is off. Maths in `lib/bokeh.js`, knobs in theme.json `lights` and `marks` (the faint drifting letters under the lights). The kit page (`/app/kit`, hidden from every menu) is where every element and token is seen.
- Styles live in `frontend/src/styles/`, one file per job (base, layers, motion, text, components, ...); `index.css` there imports them in cascade order.
- `logs/recite-journal.jsonl`: the reciting log, rolled over at 5 MB, last 3 kept.
