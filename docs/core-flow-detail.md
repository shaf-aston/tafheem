# Tafheem: the long version

Long notes behind `CORE-FLOW.md`: detail it leaves out. Read the short file first.

## Run it

```bash
# Backend (from project root, with venv already set up)
venv\Scripts\Activate
python -m uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```
Open http://localhost:5173. `start.sh` is a one-shot launcher for macOS/Linux.

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

## Detail not in CORE-FLOW.md

Core flow and the short glossary are in `CORE-FLOW.md`; this is what it leaves out.

### Steps in more detail

- **Reading a word.** `arabic_text.words()` decides what a word is (a token with an Arabic letter, reading marks taken off), so a pause sign or ayah number gets no card. `morphology.py` runs CAMeL, falling back to Qalsadi then PyArabic. `morphology.pick` takes one reading per word (the parser's BERT when loaded, the MLE otherwise); cards and parser share it. It is a guess and is labelled one. `mask.py` overrules parser links the book settles. Each word carries a `role_key` checked against `models/analyze.py ROLE_KEYS`; `lib/roleColors.js` turns it into a theme token and reads nothing else.
- **Tarkeeb.** Two sources, the badge says which: `tarkeeb_store.py` (what scholars recorded, `data/tarkeeb/tarkeeb.db`) and, where that has nothing, `tarkeeb.py` from the corpus tags (a governing word like إِنَّ or كَانَ decides the case of its ism and khabar; a caseless word is placed by position). Every Arabic term either reads is in `data/nahw_rules/tarkeeb.json`; `tarkeeb_examples.py` serves book trees from `data/tarkeeb/examples/`. `lib/tarkeebLayout.js` works out every brace from the tree's shape alone; `TarkeebDiagram.jsx` draws it. A join that cannot be made is drawn open. One Nahw page draws the tree above the i'raab cards from the same reading; reading order: Treebank record, then the parser, then the rules. Changing how the treebank is read means rebuilding `tarkeeb.db` (`build_tarkeeb.py`).
- **Qur'an.** English gloss: `quran_meanings.py` (`meanings.db`, network as fallback). Two files because two sources under two licences. Search is `services/quran_search/`: Quran.com, or `data/quran/search.db` built from the corpus; the result says which answered. `GET /api/quran/surah/{n}` returns text and English in two local queries; word-by-word grammar (about 2MB a surah) is fetched only for the ayah opened (`components/quran/QuranReader.jsx`). `GET /api/quran/editions`, `/editions/{surah}/{ayah}` (one ayah across books), `/editions/surah/{n}?id=` (one book across a surah). `AyahTafsir.jsx` fetches nothing until opened; a passage over a run of ayahs is stored once. Memorise deals a printed mushaf page: `quran_layout.py` reads `data/quran/layout.db`, `get_surah` hands the page down, `lib/memorise.js` groups by it (word count when the build is absent).
- **Root and bab.** `GET /api/quran/root/{root}` lists every place a root occurs. Bab sources: `data/sarf/lane_verbs.json` (`build_lane_verbs`) and Wiktionary, wired in `services/verb_sources/SOURCES` (its `README.md` says how to add one), merged by `verb_forms.babs_of()`; agreeing books are both cited, disagreeing babs stay separate. A word neither book records shows only the form picker. A weak, doubled or hamzated root is named and refused rather than conjugated wrongly; يَمْدُدُ becomes يَمُدُّ. `verb_reader.py` reads a typed verb back; Nahw asks it which command اِجْلِسِي is when the dictionary has no reading. `tests/test_conjugation.py` pins tables to the book.
- **Timelines.** Five stretches from the Prophets to the Day of Judgement, filterable by science (Seerah, Stories of the Prophets, 'Aqidah). `data/timelines/library.json` declares what a section may point at; one file per section under `sections/` holds events. `services/refs.py` (shared with Dawah) checks references on load: an event out of order, an `until` pointing backwards or a Qur'an reference past its surah stops the app and names the event. `lib/timelineLayout.js` works out rows, gaps, lanes and map pins from `at` and `until`. Qur'an references open the Qur'an tab. Asbab: `services/asbab_split.py` cuts al-Suyuti's Lubab into reports, stored as two editions (`asbab-lubab-ar`, English beside it), linked to an event by **named** wording or **period** (Makkan or Madinan surah, `services/asbab.py`). A report matching no single ayah goes to `data/quran/asbab-unmatched.json`.

### More terms

- **Corpus / segment**: the Quranic Arabic Corpus (GPL), hand-tagged; a **segment** is one piece of a written word (prefix, word, ending).
- **Sarf shapes**: **gardaan** is the full 14-person grid; **sarf sagheer** is the one-line summary of a bab; **i'lal** reshapes a filled pattern for a weak, hamzated or doubled letter (`data/sarf/ilal.json`). Bab codes in `data/sarf/babs.json`.
- **CAMeL**: the morphology library; called CAMeL everywhere, never "tagger" or "engine". **Nahw**: syntax rules, held as data in `data/nahw_rules/`.
- **Tamreen**: the teacher's form quizzes, one file per form in `data/tamreen/exercises/`; `tags.json` lists each grammar point once and a form names the ones it covers. Served at `/api/tamreen` (`?tag=`), read by `TamreenPanel.jsx` (Practise one question at a time, Browse a whole form). Picks live in the browser under `tamreen-answers` (`lib/tamreenAnswers.js`); Start over forgets them.
- **Word labels** on quiz words: word type (`word_type` in the table, `wordType` in browser files), meaning key (two words sharing one are never offered together), times in Qur'an (what the 80% list uses), attached.
- **Meaning language**: English unless changed. Only Qur'anic words have Urdu; the everyday list says so rather than fall back. Scored per module (`quiz`, `quiz:ur`). `frontend/src/lang/ur.json` is keyed by the English sentence.
- **Cognate / false friend**: a **cognate** means the same in Arabic and Urdu, a **false friend** does not (مَكَان). `build_urdu_links.py` finds candidates from two Wiktionary glosses and is often wrong, so nothing shows until a person lists it in `data/urdu_links.overrides.json`.
- **Set / group / cut**: **set** is the list a word came from (`everyday`, `book`, `quran`); **group** a named part (`book:faith`); **cut** is any of those or one surah or juz, what the picker selects. A word in two sets stays one word.
- **Timeline `at` / `until`**: `at` is a year (dated section) or a step; same `at` shares a row. `until` names the event a thing lasts until, drawn as a bar.
- **Asbab al-nuzul**: reports of what happened when an ayah came down (see Timelines above).
- **Dictation**: a search box spoken into, heard by the first ear that answers. Words are matched to the Qur'an's text to offer ayahs; both steps can be wrong, so several are offered and the badge says `guessed`. No recording is kept.

### Reciting detail

Ears are tried in the order `listening_ears` names, `here` last as it needs no key or internet; a rejected key strikes an ear off for the run (`services/fallback.py`). The words only place the reciter on the page (`place.py`); the mark comes from the local model's sureness (`recite_sure` on `/api/health`) against `sure-at` in `frontend/src/recite.json`. Where in the Qur'an a reading is comes from the words (`recitation/locate.py`, `near` is the open page): a surely-elsewhere reading jumps the page there, or asks first while words are hidden. Words and vowels only; tajweed is not checked. Quiet reciters: `lib/dictation.js` calls a voice anything above the quietest that microphone has heard, `recitation/loudness.py` lifts soft recordings. `lib/microphone.js` is the only place a microphone is opened. Plan and open work: `RECITE-PLAN.md`.

### More places

- `backend/models/`: Pydantic shapes, one file per router, `common.py` for `Source` and `Correction`.
- `frontend/src/theme.json` + `settings.json`: every visual token and reader setting; `theme.js` and `lib/settings.js` are their only readers, both writing CSS variables onto `:root`.
- `lib/journey.js` is where the reader has been; `lib/tabUrl.js` is the only writer of the address bar; `lib/session.js` the only reader and writer of the saved path (knobs in `frontend/src/session.json`). A place is a tab plus what it was opened with, never a result.
- `lib/` shared vocabularies, one file each: `roleColors.js`, `loadStatus.js`, `verbClass.js`.
- `services/arabic_text.py` owns "is this Arabic?" and root spelling; `normalize_root` keeps Arabic letters rather than dropping a separator list.
- `backend/data/lexicon.db`: one row per quiz word, from `vocabulary.json`, `quranic-words.json` and the corpus. Derived: rebuild it, and correct a type in `word_kinds.json`. `frontend/public/words/` holds it as `words.json` and `cuts.json` (positions into it), so no word is stored twice.
- `backend/data/maqayees/README.md` owns Maqayees config, spelling rules, English and coverage.

## More from the short map

### Tests, CI and data builds

CI (`.github/workflows/ci.yml`) runs both suites on every PR and push to master. Tests that
need data not in git skip themselves when it is absent (`skipif` on what they need).

Data is built once by the scripts in `backend/scripts/`, each explained in its own
docstring, and never committed. The Qur'an builds come first: `build_quran_corpus.py`, then
`build_quran_meanings.py`. Rebuild the Daleel index whole: `build_daleel_index.py`, never `--only`.

### Glossary (extra terms)

Short glossary: `CORE-FLOW.md`. Per module: `docs/glossary/`.

- **Colloquial**: spoken Arabic by dialect. `data/colloquial/spine.json` is the one course outline (units, lessons, phrase slots with English and pictures); a dialect is a folder filling it, a unit one JSON file, an exercise kind one file per end (`services/colloquial/exercises`, `components/colloquial/exercises/registry.js`); pictures are fetched by `scripts/fetch_colloquial_images.py` and approved one by one.
- **Entry / book root**: what one book prints under one headword. A word's entry comes from
  Wiktionary (`dictionary_service.py`), a root's from a classical book: Maqayees via
  `root_meaning.py`, all four on the shelf via `lexicons.py`. The **book root** is the root as
  that book spells it (`book_root_of`); an answer carries it only when it differs from
  the letters typed. A Maqayees entry opens with the **origin sense**
  (`core_meaning`); the **rest** follows (`root_gloss.rest_of`). Its **English** comes whole
  (`together`) or line by line (`lines`), kept by `root_english.py`; never called a reading,
  which is reciting's word.
- **Ear**: anything that turns sound into words. Three: `hosted` (Groq, about 250 ms),
  `letters` (tilawa's small Qur'an model on this computer, recitations only,
  `recitation/letters.py`) and `here` (Whisper on this computer). Tried in the order
  `listening_ears` names, `here` always last. An ear that fails rests for 60 s; one
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
- **Tier / nodeState**: Grow's levels (Level 1, 2, 3; `frontend/src/grow.json`,
  a path names its tier in its file under `data/grow/worlds/prayer/paths/`), and where one circle on its map stands:
  `locked`, `open`, `started` or `learnt` (`lib/grow.js`, drawn by `components/grow/`).

### Where things live

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
  `hadith/ChainDrawing` and `hadith/WeakPoints` show them. A grade no term reads is listed in the gap table, never guessed.
- What scholars said of a hadith: the same build reads three ruling books (Ibn Shahin, Ibn Abi Hatim's 'Ilal, Ibn al-Jawzi's
  Mawdu'at). `services/hadith/usul/ruling.py` cuts out the scholar's own sentence, `services/hadith/usul/match.py` finds which of our hadith
  it is about (rare shared word 3-grams, then a shared narrator), knobs in `usul.json` `rulings.match`. The `ruling` table is
  quoted with book and page and never inferred; what no sentence or hadith fits goes to the gap table.
  `GET /api/rijal/chains/...` carries `rulings`; `GET /api/usul/terms[/{kind}]` (`routers/hadith.py`) feeds the Hadith tab's
  Scholars list (`ScholarTerms`); `hadith/ScholarRulings` quotes them under "Possible".
- `backend/services/sarf/`: the pure core of morphology. `word.py` holds a word as letters
  that know their job, and names the alphabet once; `ilal.py` the rules. `conjugation.py`
  is the only caller. Every label, column and template is in `data/sarf/`, never in code.
- `backend/data/`: reference data, built by `backend/scripts/`; derived files are
  rebuilt, never hand-edited (see `backend/data/maqayees/README.md`).
- `backend/data/progress.db`: learners' answers, and every Nahw practice question as it was
  generated (from `data/practice/templates.json`, filed under its badge's source; `GET /api/practice/kept`). The
  one database written while running, opened only by `services/progress_store.py`. Rows are
  filed under the learner's username (no password): the page sends it on every request (`api.js` interceptor) in the `X-Tafheem-Profile`
  header, `identity.py` `current_user()` cleans it (rules only in `services/username.py`) and
  refuses a name with no account. `POST /api/progress/signup` and `/login` return the account, its name the kept spelling
  (sign-up can move the guest `local` rows onto it);
  `/account`, `/overview` (every module, totals, streak) and `/leaderboard` feed the profile.
  Everything else a person keeps (settings, Grow steps, favourites, history) is in the browser,
  filed by `frontend/src/lib/stored.js` under the logged-in name (`@amina/settings`; the guest's
  keys are bare). That one account's keys are its shelf: `lib/shelf.js` pulls it from
  `GET /api/progress/saved` at start-up and log-in and `PUT`s it back a moment after any change (at once when the page is hidden),
  so it follows the name to any device. Log-in and log-out reload the page.
  Circles (`/api/progress/circles...`, rules all in `progress_store`): a circle has a kind (config `circle_kinds`, each with
  `members_see_details`) and may sit inside one its creator administers. An admin invites an existing username, who sees
  nothing until they accept; admins invite, remove, change roles and delete; the last admin cannot leave while others are in.
  Joined members see the circle's ranking (`/leaderboard?circle=`). A member's overview is visible to themselves, admins of
  a circle they are in or of any circle above it, and fellow members where the kind shows details (`can_see`); else 403.
  `/leaderboard` alone is the global ranking of accounts with `public` on, plus your own row; `PUT /account/public` hides you.
  Old `teams` became circles (migration 2), their members invited. While `beta_list_accounts` is on, `GET /accounts` lists every username for the
  sign-in box.
- `backend/data/nahw_notes/`: the teacher's theory notes, one file per topic, read only by
  `services/nahw_notes.py` (format: its `FORMAT.md`). Testable pieces are marked in place as
  `{{role|text}}`; the Notes view in Nahw hides them or turns them into flashcards
  (`lib/notes.js`), so the stored note stays the reference. Tamreen questions link to it.
- `frontend/src/components/`: each tab's main screen; its own parts in `components/<tab>/`; parts two tabs share at the root; the app frame (tab bar, map, settings) in `shell/`; shared building blocks only in `ui/`.
  `frontend/src/lib/`: helpers, and `journey.js` for where the reader has been.
  `frontend/src/components/Backdrop.jsx`: the drifting-lights canvas behind every tab, tinted by the tab colour; it exists so the dark page has depth, and it stops when Animations is off. Maths in `lib/bokeh.js`, knobs in theme.json `lights` and `marks` (the faint drifting letters under the lights). The kit page (`/app/kit`, hidden from every menu) is where every element and token is seen.
- Styles live in `frontend/src/styles/`, one file per job (base, layers, motion, text, components, ...); `index.css` there imports them in cascade order.
- `logs/recite-journal.jsonl`: the reciting log, rolled over at 5 MB, last 3 kept.
