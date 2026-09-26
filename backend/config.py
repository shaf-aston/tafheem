"""Application settings.

All values can be overridden via .env or environment variables.

AI backend priority (auto-detect when AI_BACKEND is blank):
  1. "groq": Groq cloud (fast, requires GROQ_API_KEY)
  2. "ollama", Ollama local LLM (offline, install https://ollama.com)
  3. "none": local NLP only (CAMeL + rule engine, no LLM explanations)
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ── AI backend ────────────────────────────────────────────────────────────
    # Explicit: "groq" | "ollama" | "none"
    # Blank   : auto-detect (groq if key present, else ollama probe, else none)
    ai_backend: str = ""

    # Groq cloud (optional, leave blank to run fully offline)
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # How much a reasoning model is allowed to think before it answers. The
    # gpt-oss models think first and answer second out of one token budget, so
    # left to themselves they spend the whole budget thinking and return nothing
    # at all. Blank sends no setting at all, for a model that has no such knob.
    groq_reasoning_effort: str = "low"
    # The longest one call may take. The SDK's own default is 60s with two
    # silent retries of its own, and on a rate limit it sleeps for as long as
    # Groq says (up to 29s seen 2026-09-05), so one analysis could sit for
    # minutes with nothing on screen. Ours is the only retry loop now.
    groq_timeout_seconds: float = 20.0
    # How many AI answers to keep in memory. The free tier allows 8,000 tokens
    # a minute and one I'raab costs ~2,100, so the same sentence asked twice
    # (a reload, the back button, two tabs) must cost nothing the second time.
    ai_answer_cache_size: int = 256

    # Ollama local LLM (optional, no API key needed)
    # Install: https://ollama.com  then run: ollama pull qwen2.5:3b
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    # ── Analysis tuning ───────────────────────────────────────────────────────
    # Call the AI only when rule-engine confidence falls below this (0-1)
    confidence_threshold: float = 0.72
    # How much the model may vary; low because grammar answers should repeat. Every AI backend reads this one.
    ai_temperature: float = 0.1
    # Per-operation LLM response caps (cost/latency knobs)
    iraab_max_tokens: int = 2000
    sarf_max_tokens: int = 1500
    practice_max_tokens: int = 1200
    # Between two ceilings, measured 2026-09-01. Below: the line-by-line reading
    # cuts an entry at its full stops, ~40 English lines plus JSON for a big
    # one, and the model thinks and answers out of this one budget; at 2000 the
    # answer came back cut off, failed the count check, and retried its way to
    # a 20-40s "couldn't line it up". Above: groq's free tier refuses any
    # request over 8000 tokens, prompt included, and the biggest entry's prompt
    # is ~3500 of them; at 6000 those entries were refused outright (413).
    root_entry_max_tokens: int = 3500
    # Prompt-context truncation (chars) to keep requests bounded
    iraab_summary_truncate_chars: int = 1500
    # The longest Maqayees entry runs to ~15,000 characters. Cut at a length the
    # smallest local model can still hold; the reply says when it was cut.
    root_entry_truncate_chars: int = 6000

    # ── Qur'an lookup ─────────────────────────────────────────────────────────
    # Grammar is offline; these govern only the word-by-word English and search.
    quran_timeout_seconds: float = 15.0
    quran_search_limit: int = 20
    # Searching the Qur'an is its own path with its own two ways of answering,
    # so it gets its own settings rather than sharing the ayah lookup's.
    #
    # Where a search is answered from: "auto" asks Quran.com first and falls back
    # to the local index when the network does not answer; "online" and "local"
    # pin it to one. Measured 2026-08-26: Quran.com replies in ~770ms, and with
    # the network unplugged it takes 15.7s to give up and returns nothing at all,
    # which is why the fallback exists.
    quran_search_source: str = "auto"
    # How long a search waits for Quran.com before using the local index. Much
    # shorter than quran_timeout_seconds on purpose: there a slow answer is the
    # only answer, here waiting past a second is worse than the local one.
    quran_search_timeout_seconds: float = 4.0
    # Every ayah's text, indexed for search. Built by
    # backend/scripts/build_quran_search_index.py, never written while serving.
    quran_search_index_path: str = "data/quran/search.db"
    # How many places to list when showing where a root appears. Some roots occur
    # over a thousand times, so the list is capped and the true total is shown.
    root_occurrence_limit: int = 50

    # ── Dictionary ────────────────────────────────────────────────────────────
    # Repeat searches are answered from memory rather than searched again. Sized
    # for a study session's worth of distinct words, not for the whole book.
    dictionary_cache_size: int = 256
    # The fallback substring scan looks at every indexed key, so a one-letter
    # query can match thousands of entries. This caps how many are collected and
    # ranked: past it, more candidates cannot change the handful actually shown.
    dictionary_fuzzy_candidates: int = 200
    # A shorter indexed word is only offered as a partial match when it is at
    # least this long. Without it every single letter is inside every query, so
    # a search for اخذ answered with the letters alif, khaa and dhal.
    dictionary_fuzzy_min_key: int = 3

    # ── Classical root meaning ────────────────────────────────────────────────
    # Ibn Faris's Maqayees al-Lugha, extracted to one JSON file keyed by root:
    # {"ك ت ب": {"core_meaning": ..., "sarf_pattern": ..., "variances": [...]}}.
    # Not shipped, the panel says so until the file is here. Drop it at this
    # path and restart; no code changes. Relative paths resolve inside backend/.
    root_meaning_path: str = "data/maqayees/roots.json"

    # ── The Qur'an's library ──────────────────────────────────────────────────
    # An edition is one book of text hung on the ayahs: a tafsir, a translation.
    # They all have one shape, so they all live in one file, and the manifest
    # beside it is the only place a book is named. Adding a book is an entry in
    # that manifest and a re-import; no code changes.
    # Built by backend/scripts/import_quran_editions.py, never written while serving.
    quran_library_path: str = "data/quran/library.db"
    quran_editions_path: str = "data/quran/editions.json"
    # Every ayah in plain vowelled spelling (quran.com's imlaei), the spelling the
    # Qur'an ear writes. Checking a word by sound needs it: on 80 clean real
    # recitations the ear was at least 0.9 sure of 74% of right words in this
    # spelling and 51% in the Uthmani one. Fetched by fetch_recitation_checks.py.
    quran_imlaei_path: str = "data/quran/imlaei.json"
    # How much of the Qur'an a commentary must reach before the import believes
    # it. A tafsir does not comment on everything, so this is a floor and not an
    # exact count: Ibn Kathir, the fullest book here, reaches 6,011 of 6,236.
    # Under this many means the download broke, not that the scholar was quiet.
    # A book that genuinely covers only part of the Qur'an, a juz-thirty
    # commentary say, is added by lowering this rather than editing the script.
    quran_tafsir_ayah_floor: int = 3000

    # Listening to a recitation and finding the ayah. The model name is a
    # faster-whisper one. Bigger models write neater Arabic and are a free
    # one-off download, at several times the memory and the wait: "small",
    # "medium" and "large-v3" are all valid here.
    #
    # "base" rather than "small", measured over sixteen real recitations, from
    # قل هو الله أحد to the whole of Ayat al-Kursi: both put the right ayah first
    # fifteen times out of sixteen, and base did it in 26 seconds where small
    # took 64. Base does write sloppier words, ذلك الكتاب لا رب فيه حد للمتقين
    # for 2:2, and that is exactly what the matching is built to absorb. Since
    # a neater transcription that finds the same ayah is only a longer wait,
    # the smaller model is the better one for this job.
    #
    # "OdyAsh/faster-whisper-base-ar-quran" rather than plain "base", measured
    # over 36 mid-surah ayahs (310 printed words) from frontend/scripts/ears.test.js:
    # the Qur'an-tuned model scored 10 wrong, 14 missed, 1 extra, 8.1% error at
    # 2050ms/ayah on this machine's CPU; plain base scored 100 wrong, 18 missed,
    # 14 extra, 42.6% error at 1504ms/ayah. Groq's hosted whisper-large-v3-turbo
    # scored the same 8.1% error as the Qur'an-tuned model. So the local model
    # now matches the hosted ear's accuracy, for about a third more CPU time per
    # ayah, at zero cost and with nothing leaving the machine.
    # Hear it on Groq's machines rather than this one, when there is a key for
    # them. Free, on the listening keys below, and the model
    # there is several sizes bigger than the one that fits here: measured on one
    # spoken English word, 450ms with no processor used against 2,700ms with
    # eight cores busy. The engine below stays as the fallback for no internet, a
    # dead key or a spent allowance, so turning this off changes speed and
    # nothing else. Off means every recording is heard on this computer and no
    # sound ever leaves it.
    listening_hosted: bool = True
    # The ears to try, in order, by the names services/recitation/ears.py gives
    # them: "hosted" is Groq's machines, "here" is this computer, "letters" is
    # this computer's small Qur'an model, asked only for recitations. The quick
    # one first and this computer last, because this computer needs no key, no
    # internet and nobody's permission and so is the one that catches the fall.
    # Put "here" first for a session where no sound should leave the machine.
    # A name that is not an ear is said in the log and skipped, and "here" is
    # always added at the end however this is set, so a typo cannot leave the
    # app deaf.
    listening_ears: str = "hosted,letters,here"
    # Measured, one word: turbo ~135ms, "whisper-large-v3" 250 to 800ms and a
    # fuller decoder. Speed wins until the full one is shown to hear better.
    listening_model: str = "whisper-large-v3-turbo"
    # Read by Whisper before listening; sets the register, not the words. Sent
    # only when the "Prefer Fusha" switch is on. Off: any Arabic, no hint. Never
    # sent to the Qur'an model: with it the last word of every ayah fell to 0.90
    # sure and it looped on invented words; without it every real word is 1.00.
    listening_fusha_hint: str = "هذا كلامٌ بالعربية الفصحى."
    # Short: a slow cloud answer has already lost to the local engine, which is
    # sitting there able to answer in about three seconds. Groq's turbo answers
    # in about half a second, so 4s is generous and a failed wait costs little.
    listening_timeout_s: float = 4.0
    # How long a non-permanent failure (no internet, a rate limit, a bad
    # gateway) rests an ear before it is tried again, rather than being asked
    # on every single recording while it is having a bad minute. A settled
    # failure (a rejected key, a model that does not exist) still retires the
    # ear outright; this is only for the kind that might already be over.
    # Used only when the refusal does not say itself how long to wait.
    listening_rest_s: float = Field(default=60.0, gt=0)
    # Listening spends its own keys, apart from GROQ_API_KEY above, so a long
    # recitation cannot take the grammar explanations down with it. Comma
    # separated, one key per Groq account: Groq counts its allowance per
    # account, not per key, so two keys from one account buy nothing, and two
    # accounts double how often the page may ask. Each key is its own ear
    # (services/recitation/ears.py) and rests on its own when refused. Blank
    # falls back to the shared key.
    listening_groq_api_keys: str = ""
    # Readings a minute one key's account allows (Groq free tier: 20 for
    # whisper-large-v3-turbo). Times the keys, it is the pace /api/health tells
    # the page it may ask at.
    listening_rpm_per_key: int = Field(default=20, gt=0)
    # Read by the frontend ears benchmark through process.env, not by any backend
    # code; declared so a shared .env validates.
    recitation_deepgram_api_key: str = ""

    recitation_model: str = "OdyAsh/faster-whisper-base-ar-quran"
    # The search boxes are dictation, not recitation, and the Qur'an model knows
    # no other words: "knowledge" came back as ذَرَ ضِرِّ الْمُؤْمِنِينَ and
    # "mercy" as مَسْكُوبُ, where base heard both. A recording is a recitation
    # when its language is asked for by name; otherwise it is heard by this one.
    dictation_model: str = "base"
    # tilawa's small Qur'an model (services/recitation/letters.py), which
    # writes the letters of a recitation in one pass. Only ever places it.
    recitation_letters_path: str = "data/models/tilawa"
    recitation_device: str = "cpu"
    recitation_compute: str = "int8"
    # A recitation is Arabic, asked for by name: a few seconds of speech is too
    # little to detect a language from freely, and a wrong guess returns the
    # wrong language, not worse Arabic.
    recitation_language: str = "ar"
    # The search boxes are different: a word may be said in either language, and
    # pinning them to Arabic wrote English words in Arabic letters, "knowledge"
    # coming back as نالج. So there the language is chosen, but only ever from
    # this short list, which is what keeps the guess from wandering off to Urdu
    # or Persian. Comma separated; one name here pins them again.
    dictation_languages: str = "ar,en"
    # How many wordings the model weighs at once. Five was the default and it is
    # five times the work for an answer that landed on the same ayah every time,
    # because the matching does not need the words to be right, only close. One
    # means "take the first reading", and it is where most of the speed came from.
    recitation_beam: int = 1
    # Cut the silence before and after the recitation rather than transcribing
    # it. Browser recordings start when the button is pressed and end when it is
    # pressed again, so there is always some.
    recitation_trim_silence: bool = True
    # Drop a stretch the model itself says is probably not speech. The untrimmed
    # retry above means silence always reaches the model, and it fills it with a
    # real word (3s of nothing became وَالْمُؤْمِنِينَ, confidently). Measured
    # no-speech: 0.24 to 0.27 on silence and room noise, 0.00 on every ayah.
    recitation_no_speech_max: float = 0.15
    # Off, and this is the single biggest saving in reciting. A recited word the
    # model was not sure of used to be thrown away, which needed word timing,
    # which is most of the cost of writing a recitation down. It was worth it
    # while the transcript decided whether a word was wrong, because an invented
    # word became a red mark. It no longer decides that: since the transcript
    # was demoted to saying which part of the page you are on, throwing words
    # away only breaks the run of words that finds the place.
    #
    # Measured on 30 marked recordings, 0.94 against 0.0:
    #   2708ms against 1292ms to write one down
    #   placed at all          97% against 100%
    #   found the whole ayah   57% against  87%
    #   words judged at all    84% against  93%
    # Better on every count and less than half the wait. See
    # backend/scripts/time_placing.py. Above zero it comes back on, at the cost
    # in the table.
    recitation_word_min: float = 0.0
    # Sureness is asked of at most this many page words per reading. The ear's
    # decoder holds 448 pieces, about three to a word, and a ten-second
    # recording holds nowhere near this many; more means the placing went wrong.
    # How a word's pieces become one number. The ear scores each piece of a
    # word separately, and a word of five pieces is right only if every one of
    # them was said. "worst" is the least sure piece, which is the strict
    # reading and what this used to do always; "mean" averages them; and
    # "worst-but-one" forgives a single bad piece, which is what a word-final
    # vowel is when the reciter stopped there. Measured on the 1,950 marked
    # recordings: see rescore_recitation.py and sweep_sureness.py.
    # Bringing a quiet recitation up before anything listens to it. Somebody
    # reciting softly, or sitting back from the microphone, records real sound
    # that is simply small, and every judgement below is made against a fixed
    # idea of how loud speech is: what counts as a voice, what counts as
    # silence worth trimming, and how sure the ear is a word is there. See
    # services/recitation/loudness.py.
    # How loud it is brought to, measured as sound on average rather than at
    # its loudest moment. 0.06 is an ordinary speaking level recorded by a
    # laptop microphone.
    recitation_loudness_target: float = 0.06
    # The loudest any sample may end up, so nothing is pushed into crackle.
    recitation_loudness_ceiling: float = 0.95
    # Below this there is nothing there and it is left alone, so a silent room
    # is never lifted into something the ear then reads as a word.
    recitation_loudness_floor: float = 0.002
    # The most anything is lifted by, so faint hiss stays faint hiss.
    recitation_loudness_most: float = 20.0
    #
    # Swept over all 1,950 recordings, 6,832 judged words (sweep.txt). Matched
    # at the same catching of vowel slips, forgiving one piece halves the words
    # marked though they were right:
    #   worst, under 0.1          5.1% marked though right, 62% of vowel slips
    #   worst-but-one, under 0.9  3.2% marked though right, 61% of vowel slips
    # The same holds the whole way down the curve. The cost is whole-word slips,
    # caught 9% against 27%, and that is the weakest number here: there are only
    # 34 such words in the corpus, so each one is worth three points. No rule of
    # any kind catches whole-word slips well; the sound check is good at vowels
    # and poor at a word swapped for another.
    recitation_sure_of_word: str = "worst-but-one"
    recitation_sure_max_words: int = 100
    # How long a stretch of sound the ear is handed when it is asked how sure it
    # is of each word. A frame is a hundredth of a second, so 1500 is fifteen
    # seconds.
    #
    # The ear can hold thirty seconds and was always handed thirty seconds,
    # silence for whatever the recording did not fill. Silence costs exactly
    # what sound costs: a recording of five seconds and one of twenty-five both
    # took 1,410ms, measured over 483 real checks. So the recording's own length
    # is handed over instead, rounded up to a whole one of these. Over all 1,950
    # recordings the middle check fell from 967ms to 541ms.
    #
    # Fifteen and not less, which is the part that cost a day to learn. This ear
    # was only ever trained on thirty second stretches, so handing it six
    # seconds is asking it something it was never shown, and its answers come
    # back not just noisier but lower: at a block of 100 the same false-red rate
    # caught 6.5% of vowel slips where thirty seconds caught 17.8%. Strictly
    # worse the whole way down the curve. At 1500 it is not worse at all:
    # beginner 0.6% wrongly red and 19.5% of vowel slips caught, against 0.7%
    # and 17.8% before; standard 1.5% and 33.5%, against 1.6% and 31.9%.
    #
    # Rounded rather than exact so the ear is asked for a handful of sizes over
    # and over rather than a different one every time. Set this to 3000 and
    # every recording is padded to the full thirty seconds again, which is what
    # the app did before. Do not lower it without re-running
    # rescore_recitation.py then sweep_sureness.py and reading that curve.
    recitation_window_block: int = Field(default=1500, gt=0, le=3000)
    # How many ayahs one reading may ask to be checked against: a page, with room.
    recitation_check_ayahs_max: int = Field(default=60, gt=0)
    # The longest `heard` text POST /api/listen/check accepts: what a words
    # reading wrote down, echoed back to be scored. A page is a few hundred
    # characters; well past that is not a transcript any reading could produce.
    recitation_check_heard_max_chars: int = Field(default=2000, gt=0)
    # A recording cut inside a word, as a four-second chunk of إياك نعبد وإياك
    # نستعين is, sent the model looping: نعبد وإياك eleven times over, twelve
    # seconds to decode, and every repeat marked wrong on the page. Above one,
    # a word already written costs more to write again. 1.2 stopped the loop
    # (إياك نعبد وإياك, in two seconds) and changed no other reading tried;
    # forbidding repeats outright (no_repeat_ngram_size) misspelt الرحيم.
    recitation_repetition_penalty: float = 1.2
    # How many of this machine's sixteen cores the model may use. Measured
    # again on twelve recitations each, reading and checking: four 4029/1300ms,
    # eight 3660/1109, twelve 3147/912, sixteen 2717/887. So more is faster all
    # the way up, which is the opposite of what was measured here before and of
    # what the note here used to say. Twelve rather than sixteen because the
    # rest of the machine still has to answer while somebody recites: sixteen
    # buys another 14% of the reading and leaves nothing to draw the page with.
    recitation_threads: int = 12
    # Load the model and fold the Qur'an in the background as the app starts, so
    # the first person to press the microphone does not wait for it. Costs about
    # a second of startup and 150MB. Turn off on a small machine; the first
    # recitation then loads it, as it did before.
    recitation_warm: bool = True
    # How many ayahs a recitation is answered with. Enough to recover from a
    # near miss, few enough to read at a glance.
    recitation_matches: int = 5
    # The largest recording accepted, in megabytes. A minute of browser audio is
    # about one; anything far larger is not a recitation.
    recitation_max_mb: int = Field(default=12, gt=0)
    # Not a knob. Which book a panel opens on is the first one the manifest
    # names, and after that whichever the reader last switched to. A default
    # setting here as well would be a second way of saying the same thing, and
    # the two would be free to disagree.

    # ── Syntax parser (CATiB dependency links) ───────────────────────────────
    # Whether backend/services/syntax/catib_onnx.py runs at all. Off by
    # default costs nothing; on, the first parse() call loads a ~110MB ONNX
    # encoder plus CAMeL's BERT disambiguator, so it stays off until a caller
    # actually wants dependency links.
    catib_parser_enabled: bool = True
    # encoder.onnx (int8), scorer.onnx, tokenizer.json, labels.json,
    # config.json, clitic_feats.csv. See catib_onnx.py's docstring for where
    # each one comes from. Relative paths resolve inside backend/.
    catib_parser_dir: str = "data/parser"

    # ── Recite journal ────────────────────────────────────────────────────────
    # A second, narrower log beside backend.log: one JSON line per event, server
    # and page side both, joined by a reading id. See services/journal.py.
    # Relative to the project root (the folder that holds backend/), not to
    # backend/ the way data_path's paths are: it belongs beside backend.log.
    journal_path: str = "logs/recite-journal.jsonl"
    # How big one journal file grows before it is rotated.
    journal_max_kb: int = Field(default=5120, gt=0)
    # How many rotated files are kept; older ones are deleted automatically, so
    # this is what keeps the log folder from growing forever.
    journal_keep: int = Field(default=3, gt=0)
    # A batch from the page is capped both by how many events it may carry and
    # by its size on the wire, so one runaway page session cannot fill the
    # journal or the request body with an unbounded POST.
    journal_page_events_max: int = Field(default=50, gt=0)
    journal_page_bytes_max: int = Field(default=65536, gt=0)

    # ── Daleel (find the quotation) ───────────────────────────────────────────
    # The index every searchable book is built into. Rebuilt by
    # backend/scripts/build_daleel_index.py, never written to while serving.
    daleel_index_path: str = "data/daleel.db"
    # How many quotations one search returns. A reader compares a handful of
    # passages; past that the list stops being read and starts being scrolled.
    daleel_result_limit: int = 12
    # A common word expands into its root's whole family plus its synonyms,
    # which for a word like قول is hundreds. Capped so one ordinary query
    # cannot turn into a hundred-term search.
    daleel_root_expand_max: int = 6
    # How many Arabic translations one English word is searched as. Lower than
    # the cap above because each translation also brings its root, so six made
    # an English word a twelve-term search against one to three for an Arabic
    # word. Measured over twelve English questions: three kept as many exact
    # matches (more on six of them) and made most searches twice as fast.
    daleel_english_expand_max: int = 3
    # Not a knob. How short a word may be before the index cannot see it is a
    # property of SQLite's trigram tokenizer, so it lives beside the code that
    # depends on it, in services/daleel/search.py. It was a setting here for a
    # while; two copies of one number meant changing this one switched off typo
    # tolerance silently, with the other copy still saying 3.

    # Where each surah came down, Makkah or Madinah, fetched once by
    # backend/scripts/build_asbab.py. The timelines put a report that names no
    # event on the Makkan or the Madinan stretch by it.
    quran_surah_type_path: str = "data/quran/surah-type.json"
    # The reports in that book whose quoted words match no single ayah. Written
    # by the same script, read so the panel can say how many are not shown.
    asbab_unmatched_path: str = "data/quran/asbab-unmatched.json"

    # ── Timelines ─────────────────────────────────────────────────────────────
    # library.json (sciences, places, collections, map) and one file per section
    # under sections/. Hand-written data, checked on load by services/timelines.py.
    timelines_dir: str = "data/timelines"

    # ── Progress (what a learner has answered) ────────────────────────────────
    # The only database this app writes to while serving. Made on first use, so
    # there is no build script and nothing to install; deleting the file simply
    # forgets everything and starts again.
    progress_db_path: str = "data/progress.db"
    # An answer slower than this keeps its right or wrong but is left out of the
    # timing averages: past two minutes the likeliest explanation is that the
    # question sat open while the learner did something else, and one of those
    # in an average buries every real answer around it.
    progress_timing_cap_ms: int = 120_000
    # How many right answers in a row clear a word from the review list. Two,
    # because one is as easily a lucky guess between four options as it is
    # knowledge, and three keeps a word that is plainly learnt in the way.
    progress_review_clear_streak: int = 2
    # How long a write waits for another to finish. Without one SQLite gives up
    # the moment two answers land together, which auto-advance makes ordinary.
    progress_busy_timeout_ms: int = 5000

    # ── Server ────────────────────────────────────────────────────────────────
    # Declared because .env sets PORT and this Settings class forbids unknown
    # keys, dropping the field makes startup fail. The running port itself comes
    # from the --port flag start.sh passes to uvicorn.
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
        ]
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("groq_api_key", "listening_groq_api_keys", mode="after")
    @classmethod
    def _check_key_format(cls, value: str, info: ValidationInfo) -> str:
        """Refuse a malformed key (an inline comment, a space inside it) at startup."""
        if any(" " in key.strip() or "#" in key for key in value.split(",")):
            name = info.field_name.upper()
            raise ValueError(
                f"{name} appears malformed (contains spaces or '#'). "
                "Remove inline comments from .env. "
                f"Example: {name}=your_key_here"
            )
        return value

    @field_validator("quran_search_source", mode="after")
    @classmethod
    def _check_search_source(cls, value: str) -> str:
        """Reject a value nobody reads. A typo here would silently pin search to
        whichever branch happened to be last, so it stops startup instead."""
        allowed = {"auto", "online", "local"}
        if (cleaned := value.strip().lower()) not in allowed:
            raise ValueError(
                f"QURAN_SEARCH_SOURCE must be one of {', '.join(sorted(allowed))}, got {value!r}"
            )
        return cleaned

    @property
    def effective_backend(self) -> str:
        """Resolve which AI backend to use: groq | ollama | auto | none."""
        explicit = self.ai_backend.strip().lower()
        if explicit in {"groq", "ollama", "none"}:
            return explicit
        # Auto-detect: prefer Groq when a key is present
        return "groq" if self.groq_api_key.strip() else "auto"

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key.strip())

    @property
    def listening_keys(self) -> list[str]:
        """The keys the microphone spends: its own when there are any, else the
        shared one, else none. The only place that choice is made. A key listed
        twice is one key."""
        own = list(dict.fromkeys(key.strip() for key in self.listening_groq_api_keys.split(",") if key.strip()))
        shared = self.groq_api_key.strip()
        return own or ([shared] if shared else [])


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def _resolved(name: str, value: str) -> Path:
    """The checking half of data_path, remembered per value it has been given.

    Split out so the setting itself is still read on every call: a test that
    points a database somewhere else must take effect, and caching on the
    setting's name alone froze the first path each name ever had.
    """
    base = Path(__file__).resolve().parent
    target = (base / value).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"{name} must stay inside {base}, got {value!r}")
    return target


def data_path(name: str) -> Path:
    """A configured data file, confined to the app's own backend directory.

    Checked rather than trusted, because `base / value` quietly throws the base
    away when the value is absolute: one absolute path in a .env would move a
    database anywhere on the machine, and the build scripts write to these same
    paths. Reading the wrong file is bad; overwriting one is worse.

    Takes the setting's name rather than its value so the error can say which
    setting to go and fix.

    The resolving is remembered per value, because it costs about a millisecond
    on Windows and never changes for a given one. Every ayah lookup asks for a
    path three times, which made the path arithmetic cost twenty times the
    database query it was for.
    """
    return _resolved(name, getattr(get_settings(), name))
