# Ear index: speech to text in Tafheem

Paths from the repo root. `B` = `backend/services/recitation/`, `F` = `frontend/src/`. Checked against this tree on 2026-10-26.

## 1. What the ear does

Turns a few seconds of voice into Arabic words. For a Qur'an recitation it also says where in the Qur'an the words sit, and how sure it is of each page word, so the page can mark words right, doubtful or wrong.

Two jobs, kept apart:
- **Writing the words down**: Groq first, then letters, then this machine (section 4).
- **Checking each word**: always a Whisper model on this machine. The setting Settings > Reciting > Word checker (`F/settings.json:74`, key `listening-ear`) picks which one: **Base** (`recitation_model`) or **Fine-tuned** (`recitation_tuned_model`, `backend/config.py:197`). It changes only the checker. Groq writes the words either way. The choice is ignored while the server offers no tuned model (`F/lib/useHealth.js:58` `useTuned`, health field `recite_tuned`).

## 2. Uses (every place that records voice)

| Use | Frontend entry | Asks for |
|---|---|---|
| Recite a page, hidden words (Memorise) | `F/components/memorise/hooks.js:205` `useReciting` (`F/lib/useReciting.js`) then `F/lib/recitingSession.js:243` `createRecitingSession` | `/listen?recite&near&before`, then `/listen/check` |
| Grow step "Say it" | `F/components/grow/Practice.jsx:197` `MicButton recite`, checks in `F/lib/grow/cards/recite.js:10` | `/listen?recite`, then `/check` (ayah) or `/check-text` (phrase) |
| Find an ayah by reciting | `F/components/quran/QuranSearchBar.jsx:46` `MicButton match` | `/listen?match` (words and ayahs) |
| Spoken search boxes | `MicButton` in `DaleelPanel.jsx`, `Dictionary.jsx`, `hadith/HadithSearchResults.jsx`, `nahw/IraabAnalyzer.jsx`, `SarfPanel.jsx`, `colloquial/WordCards.jsx` (`anyArabic`) | `/listen` (words only) |

`KitPanel.jsx:264` is a kit demo mic. `useRecitation.js` / `useRecitedWord.js` are playback timing, not the ear.
Shared: `F/components/ui/MicButton.jsx` (one shot), `F/lib/microphone.js` (the only `getUserMedia`, line 65, and `MediaRecorder`, line 97), `F/lib/dictation.js` `watchForVoice`.

## 3. Flows

### A. One-shot button
1. `MicButton.jsx:91` opens the microphone and recorder; `watchForVoice` stops it after quiet (`F/dictation.json` `after-speech-s`, `quiet-stop-s`). Under `too-short-s` or no voice: nothing is sent.
2. `MicButton.jsx:125` calls `api.js:349` `listen`: multipart POST to `/api/listen?match&recite&fusha`.
3. `backend/routers/listen.py:191` `listen`: `_read_recording` (cap `recitation_max_mb`), empty body returns empty `Heard`, `_refuse_unless_audio` (`B/recording.py:11` magic bytes, 415).
4. A recitation with `ears.would_answer_locally()` (`B/ears.py:288`) waits on `_turn` (router `:76`, `_my_turn` `:161`); dropped if the page left.
5. `B/__init__.py:106` `hear`: Arabic for recite/match, else no language; hint is `recitation_hosted_hint` for recitations, the fusha text for the rest; then `ears.hear`.
6. `B/ears.py:225` `hear` walks `order()` (`:206`, `listening_ears`: hosted keys least-recently-used first, then letters for recitations, then here). A rejected key retires its ear for the run (`permanent_failure`); any other failure rests it. `Unreadable` stops the chain.
7. Hosted: `hosted.py:52` `transcribe` (Groq, `verbose_json`, `:98`). Letters: `letters.py:68` `read`. Here: `listen.py:227` `transcribe`, `sound_of` `:99` (PyAV decode, `loudness.levelled`), `_read` `:435`.
8. `match` only: `recitation.find` then `match.best`. With `near` (Memorise): `page_span` (router `:231`) and `find_place` (`:279`, `locate.find`) add `place {surah, ayah, sure, home}` to the answer.

### B. Continuous recitation (Memorise)
1. `recitingSession.js` records one stream in `tick-s` chunks. A window ends on a pause (`pause-s` 0.4, `cutReason` `:54`) or `window-s`; silent windows are never sent (`spokeSince` `:62`).
2. `readyToSend` (`:86`) paces by `step-s`, `asks-share` of the server's `listen_per_minute`, one reading in flight. The whole growing window is re-sent each time, with `near` (the page's first and last ayah) and `before` (last unsure reading).
3. Answer lands at `:469`: `ofPage = place ? place.home : isOfPage(...)`. An off-page reading is dropped; a sure place elsewhere sets `elsewhere` (`:513-515`), which `hooks.js:357` turns into a jump or a question.
4. On-page words go to `follow()` (`F/lib/follow.js:234`), windows merge by `joinWindows` (`:205`). Marks are `SAID / CHECK / WRONG / MISSED / WAITING` (`follow.js:59-67`). `ReciteStrip.jsx` and `lib/reciteColors.js` colour them.

### C. Sureness check (always this machine)
1. `recitingSession.js:305` `pumpChecks` (one at a time, queue `check-queue-max`) calls `api.js:356` `checkReading`: `POST /listen/check?heard&check=2:1,...&tuned`. Phrases: `checkText` `:362` to `/check-text`.
2. `routers/listen.py:300` validates ayah list and `heard` length, picks the model (`_tuned_model` `:181`, 503 if none is set), waits on `_turn`.
3. `B/__init__.py:170` `check`: ayah words come from `imlaei.json` through `spelling.as_heard` (`spelling.py:41`, pause signs dropped); `place.reach` finds the stretch heard (2 words in a row), extends to the ayah end, caps at `recitation_sure_max_words`.
4. `listen.py:379` `weigh` / `scores` `:283`: Whisper gives each piece a probability; `aggregate` `:389` folds by `recitation_sure_of_word` (worst-but-one).
5. Answer `{sure: {"2:5": [0..1 or null per spoken word]}, detail}`; null means this recording did not reach the word.
6. Page: `ayahAt` (`F/lib/memorise.js:65`) lists each ayah's `spoken` page places (pause signs have none). `byPlace` (`recitingSession.js:125`) maps scores onto those, `settledScores` `:146` and `surer` `:151` merge recordings, `bySound` (`follow.js:339`) turns numbers into colours at `sure-at` 0.95 (`recite.json`).

## 4. Engines

| Engine | Runs | Config | Used when |
|---|---|---|---|
| hosted | Groq `whisper-large-v3-turbo`, one ear per key | `listening_model`, `listening_groq_api_keys`, `listening_hosted`, `listening_timeout_s`, `listening_rpm_per_key` | first in `listening_ears`; writes the words for every use |
| letters | CPU, tilawa ONNX in `data/models/tilawa` | `recitation_letters_path` | recitations only, second |
| here | CPU faster-whisper: `OdyAsh/faster-whisper-base-ar-quran` (recitation), `base` (search boxes) | `recitation_model`, `dictation_model`, `recitation_device`, `recitation_compute` | last, never retired |
| checker, Base | same model as here | `recitation_model` | every check when Word checker is Base |
| checker, Fine-tuned | `shafTheG/quran-ear@<commit>` (Hugging Face) | `recitation_tuned_model` | every check when Word checker is Fine-tuned |

`listen.py:157` `_engine` loads a folder under `backend/`, or `repo@revision` pinned to one upload; first load downloads, later loads are offline.
Making the tuned ear: `backend/scripts/finetune_ear/` (README there): `cloud.py` pushes to Kaggle, judges against the served ear, `--ship` uploads and moves the pin in `config.py`.

## 5. Config knobs

`backend/config.py`: `listening_ears`, `listening_hosted`, `listening_model`, `listening_fusha_hint`, `listening_timeout_s`, `listening_rest_s`, `listening_groq_api_keys`, `listening_rpm_per_key`, `recitation_model`, `recitation_tuned_model`, `dictation_model`, `recitation_hosted_hint`, `recitation_letters_path`, `recitation_device`, `recitation_compute`, `recitation_threads`, `recitation_language`, `recitation_beam`, `recitation_trim_silence`, `recitation_no_speech_max`, `recitation_loudness_*`, `recitation_sure_of_word`, `recitation_sure_max_words`, `recitation_window_block`, `recitation_place_*`, `recitation_check_ayahs_max`, `recitation_check_heard_max_chars`, `recitation_matches`, `recitation_max_mb`, `quran_imlaei_path`, `journal_path`.
`F/dictation.json`: `too-short-s`, `quiet-stop-s`, `after-speech-s`, `voice-level`, `over-room`, `level-check-ms`, `judge-s`.
`F/recite.json`: `window-s`, `pause-s`, `step-s`, `asks-share`, `asks-per-minute`, `tick-s`, `anchor-words`, `settle-words`, `costs`, `sure-at`, `check-timeout-s`, `check-queue-max`, `sound-alike-groups`, `journal-*`.
Settings (`F/settings.json`): `fusha`, `listening-ear`. Health: `GET /api/health` fields `ear`, `recite_ear`, `recite_tuned`, `recite_sure`, `listen_per_minute` (`backend/main.py:167-184`).

## 6. Tests and measurement

| File | Measures |
|---|---|
| `tests/test_recitation*.py`, `tests/test_loudness.py` | ear order and fallback, Groq call shape, letters, placing, checks, spelling, magic bytes, loudness (162 pass) |
| `F/lib/recitingSession.test.js`, `follow.test.js`, `dictation.test.js`, `microphone.test.js` | pacing, `byPlace` with pause signs, marking, voice meter |
| `backend/scripts/sweep_sureness.py`, `rescore_recitation.py`, `score_recitation_checker.py` | sureness rule and threshold against reviewer-marked clips |
| `score_place.py`, `time_placing.py`, `letters_missed.py` | placing accuracy, which ear places, letters an ear confuses |
| `F/scripts/ears.test.js` (+ `ears-local.js`, `ears-score.js`) | engines compared on 36 ayahs |
| `F/scripts/probe-ear.mjs`, `probe-recite.mjs` | real browser, fake microphone |
| `backend/scripts/finetune_ear/` | train, judge and ship the tuned ear |

## 7. Glossary (code's words)

- **ear**: anything turning sound into words (`ears.py:Ear`): hosted, letters, here.
- **checker**: the model that scores each word's sureness (Base or Fine-tuned).
- **reading**: one request about one recording. **window**: one recording between pauses.
- **place / home**: where in the Qur'an a reading sits / whether that is on the open page (`locate.py`).
- **sure**: 0 to 1 per spoken page word. **spoken**: the page places of words the ear scores (no pause signs).
- **elsewhere**: a sure place off the open page. **turn (`_turn`)**: lock so one local reading runs at a time.
- **retire / rest**: strike an ear off for the run / pause it (`fallback.Retirable`).

## 8. Known gaps (measured 2026-10-26 on live API, Alafasy and Husary, Memorise page 2:1-2:5)

2. **Out-of-order ayahs.** `follow.js:87` `lineUp` is one alignment over the joined stream. Reciting 2:3 then 2:2 leaves 2:2 empty and paints the first 7 words of 2:4 orange. Aligning each window alone worked in a prototype.
3. **Noise sets `elsewhere`.** Quiet pink noise got a sure place off the page (`recitingSession.js:513`). No word was marked, but `hooks.js:357` can offer a jump.
4. **2:1 الٓمٓ is never marked** in any run. Cause not traced.
5. **Fine-tuned checker reads مِّن falsely low.** It is scored with `as_heard` spelling, which drops a word-initial shadda (`spelling.py:49-50`), but it was trained on raw imlaei (`finetune_ear/ear/text.py:10`). 9 of 252 perfect words were low, all مِّن; Base: 0 of 253 below 0.95. The red spreads to neighbours on skips and swaps. Base separates a changed word (0 to 0.12) cleanly.
6. **Wrong ayah noticed late.** Reciting 2:10 on a 2:1-2:5 page marked nothing, but the place was unsure for the first ~8 s. A look-alike with identical text (31:5 on 2:5) passes; unavoidable.
7. Dead names: `F/scripts/probe-ear.mjs:9` (`RECITATION_HOSTED`), `F/recite.json:37` (`recitation_hosted_rest_s`).
8. `B/__init__.py:76` tests `"letters" in listening_ears` as a substring; `ears._wanted` parses a list.
9. `listen_check` (`routers/listen.py:300`) and `listen_check_text` (`:367`) repeat one validate, turn, run, error block.
10. `imlaei.json` (needed by `/check`) is gitignored (`.gitignore:227`) and absent from `deploy/copy-data.sh`. The live server does score, so it has one; how it got there is not recorded.
