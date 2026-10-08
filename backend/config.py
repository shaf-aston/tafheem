"""Application settings, overridable via .env or environment variables."""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ai_backend blank: groq if a key is present, else probe ollama, else none.
    ai_backend: str = ""

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # gpt-oss thinks and answers out of one token budget; unset, it can spend it all thinking and return nothing.
    # Blank sends no setting (for models without the knob).
    groq_reasoning_effort: str = "low"
    # SDK default is 60s plus two silent retries, and on a rate limit it sleeps as long as Groq says
    # (29s seen 2026-09-05). Ours is the only retry loop now.
    groq_timeout_seconds: float = 20.0

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    # Longer sentences are refused (422): the parser and the rules grow with length.
    max_sentence_words: int = Field(default=160, gt=0)  # the longest ayah (2:282) is about 130 words
    # Low so grammar answers repeat. Every AI backend reads this one.
    ai_temperature: float = 0.1
    sarf_max_tokens: int = 1500
    # Between two ceilings, measured 2026-09-01. Below: thinking and the ~40-line JSON share this budget;
    # at 2000 the answer was cut off, failed the count check and retried for 20-40s.
    # Above: groq free refuses requests over 8000 tokens including prompt (biggest prompt ~3500); at 6000 got 413.
    root_entry_max_tokens: int = 3500
    # Longest Maqayees entry is ~15,000 chars; 6000 is what the smallest local model can hold.
    root_entry_truncate_chars: int = 6000

    quran_timeout_seconds: float = 15.0
    quran_search_limit: int = 20
    # "auto" tries Quran.com then the local index; "online"/"local" pin one.
    # Measured 2026-08-26: Quran.com ~770ms; network unplugged it takes 15.7s to give up with nothing.
    quran_search_source: str = "auto"
    # Deliberately far below quran_timeout_seconds: waiting past a second is worse than the local answer.
    quran_search_timeout_seconds: float = 4.0
    # Built by backend/scripts/build_quran_search_index.py, never written while serving.
    quran_search_index_path: str = "data/quran/search.db"
    # Some roots occur over a thousand times; list is capped, true total still shown.
    root_occurrence_limit: int = 50

    dictionary_cache_size: int = 256
    # Fuzzy scan covers every indexed key, so a one-letter query matches thousands; past this cap extra candidates cannot change what is shown.
    dictionary_fuzzy_candidates: int = 200
    # Without a minimum, single letters match inside every query: a search for اخذ returned alif, khaa and dhal.
    dictionary_fuzzy_min_key: int = 3
    # The book whose English is the sense of a whole ayah typed into the dictionary (data/quran/editions.json).
    sentence_translation: str = "saheeh-en"
    # Word by word, each piece of a word shows up to this many of CAMeL's senses.
    sentence_senses: int = Field(default=2, gt=0)
    # Candidate senses the model may pick from per word (CAMeL's readings, then the dictionary's).
    sentence_candidates: int = Field(default=8, gt=0)
    # One English sentence back, plus a reasoning model's thinking.
    sentence_max_tokens: int = Field(default=1200, gt=0)

    # Ibn Faris's Maqayees as {"ك ت ب": {"core_meaning", "sarf_pattern", "variances": [...]}}.
    # Not shipped; panel says so until the file exists. Relative paths resolve inside backend/.
    root_meaning_path: str = "data/maqayees/roots.json"

    # Built by backend/scripts/import_quran_editions.py, never written while serving.
    # The manifest is the only place a book is named; adding one needs no code change.
    quran_library_path: str = "data/quran/library.db"
    quran_editions_path: str = "data/quran/editions.json"
    # quran.com imlaei spelling, which the Qur'an ear writes. On 80 clean recitations the ear was
    # >=0.9 sure of 74% of right words in this spelling vs 51% in Uthmani. Fetched by fetch_recitation_checks.py.
    quran_imlaei_path: str = "data/quran/imlaei.json"
    # Verbally similar verses (mutashabihat). The catalogue is built by
    # scripts/build_mutashabihat.py; the rest tune the finder in
    # services/mutashabihat.py, judged by scripts/score_mutashabihat.py.
    mutashabihat_path: str = "data/quran/mutashabihat.json"
    # Words per shingle. Two reached 77% pair recall over the benchmark.
    mutashabihat_shingle_size: int = Field(2, ge=1)
    # A shingle in more verses than this is a stock phrase, not a clue.
    mutashabihat_shingle_cap: int = Field(200, ge=1)
    mutashabihat_candidate_limit: int = Field(10, ge=1)
    # Shared shingles over the shorter verse's shingles, 0-1, to be proposed.
    mutashabihat_propose_min_score: float = Field(0.5, gt=0, le=1)
    mutashabihat_propose_limit: int = Field(50, ge=1)
    # Floor, not exact count: tafsirs skip ayahs (Ibn Kathir, the fullest, reaches 6,011 of 6,236).
    # Below it the download broke. A partial-coverage book (juz-thirty commentary) is added by lowering this.
    quran_tafsir_ayah_floor: int = 3000

    # Hear on Groq's machines when a key exists: the model is several sizes bigger than what fits here.
    # Measured on one English word: 450ms with no local CPU vs 2,700ms with eight cores busy.
    # Local engine stays the fallback (no internet, dead key, spent allowance).
    # False means no sound ever leaves this computer.
    listening_hosted: bool = True
    # Ear names from services/recitation/ears.py: "hosted" Groq, "here" local, "letters" local Qur'an model (recitations only).
    # "here" goes last because it needs no key or internet, so it catches the fall.
    # Unknown names are logged and skipped; "here" is always appended so a typo cannot leave the app deaf.
    listening_ears: str = "hosted,letters,here"
    # Measured, one word: turbo ~135ms, whisper-large-v3 250 to 800ms. Speed wins until the full one hears better.
    listening_model: str = "whisper-large-v3-turbo"
    # Sets register, not words. Sent only when "Prefer Fusha" is on, never to the Qur'an model:
    # with it the last word of every ayah fell to 0.90 sure and it looped on invented words; without it every real word is 1.00.
    listening_fusha_hint: str = "هذا كلامٌ بالعربية الفصحى."
    # Short because the local engine answers in ~3s and a slow cloud answer has already lost; Groq turbo takes ~0.5s.
    listening_timeout_s: float = 4.0
    # Rest for a transient failure (no internet, rate limit, bad gateway); a settled one (rejected key, missing model) retires the ear.
    # Used only when the refusal does not say how long to wait.
    listening_rest_s: float = Field(default=60.0, gt=0)
    # Comma separated, one key per Groq account: Groq counts allowance per account, so two keys from one account buy nothing.
    # Separate from GROQ_API_KEY so a long recitation cannot exhaust grammar explanations. Blank falls back to the shared key.
    listening_groq_api_keys: str = ""
    # Groq free tier: 20/min for whisper-large-v3-turbo. Times the keys, it is the pace /api/health gives the page.
    listening_rpm_per_key: int = Field(default=20, gt=0)
    # Read only by the frontend ears benchmark via process.env; declared so a shared .env validates.
    recitation_deepgram_api_key: str = ""

    # Real reciters are played by the page, not listed here.
    speech_voices: str = "fastpitch"
    # FastPitch has four speakers; 3 was heard best by Whisper (21% letters wrong, speaker 0 41%).
    speech_fastpitch_speaker: int = Field(default=3, ge=0, le=3)
    # Below 1 speaks slower at the same pitch; a learner hears each sound.
    speech_fastpitch_pace: float = Field(default=0.85, gt=0.5, le=1.5)
    # Whole colloquial dialogue lines; the longest is 104.
    speech_max_chars: int = Field(default=120, gt=0)
    speech_rest_s: float = Field(default=60.0, gt=0)
    # A word is ~25 KB, a dialogue line a few hundred; the oldest go first past this.
    # Every Colloquial line made ahead (scripts/premake_speech.py) is ~1.5 GB, so this leaves room past it.
    speech_cache_max_mb: float = Field(default=3000.0, gt=0)
    # Asks a minute per visitor; a phrase counts one ask per speech_chars_per_ask letters.
    speech_per_minute: int = Field(default=60, gt=0)
    speech_chars_per_ask: int = Field(default=40, gt=0)

    # Chosen over plain "base" on 36 mid-surah ayahs (310 words, frontend/scripts/ears.test.js):
    # this scored 8.1% error at 2050ms/ayah on this CPU; base 42.6% at 1504ms. Groq whisper-large-v3-turbo also 8.1%.
    # Over 16 recitations "base" beat "small" (both right first 15/16; 26s vs 64s), so smaller wins; sloppy words are absorbed by the matching.
    # A folder works too. To try a model tuned by scripts/finetune_ear, put in .env:
    #   RECITATION_MODEL=data/models/finetune-ear/ear-tuned
    #   LISTENING_EARS=here          (else Groq answers first and the folder is only the fallback)
    recitation_model: str = "OdyAsh/faster-whisper-base-ar-quran"
    # Empty means no trial offered. A folder inside backend/ (data/models/finetune-ear/ear-tuned),
    # loaded like recitation_model; a learner's "Trial" listening hears and checks with it alone.
    recitation_trial_model: str = ""
    # Search boxes are dictation, and the Qur'an model knows no other words:
    # "knowledge" came back as ذَرَ ضِرِّ الْمُؤْمِنِينَ, "mercy" as مَسْكُوبُ, where base heard both.
    # A recording is a recitation only when its language is asked for by name.
    dictation_model: str = "base"
    # tilawa's small Qur'an model (services/recitation/letters.py); writes letters in one pass. Only places.
    recitation_letters_path: str = "data/models/tilawa"
    recitation_device: str = "cpu"
    recitation_compute: str = "int8"
    # Pinned: a few seconds of speech is too little for language detection, and a wrong guess returns the wrong language.
    recitation_language: str = "ar"
    # Pinning search boxes to Arabic wrote English words in Arabic letters ("knowledge" as نالج).
    # Choosing only from this list stops the guess drifting to Urdu or Persian. One name pins it again.
    dictation_languages: str = "ar,en"
    # Default was 5, five times the work for the same ayah every time; matching needs close, not right. Most of the speed win.
    recitation_beam: int = 1
    # Browser recordings always carry silence before and after.
    recitation_trim_silence: bool = True
    # The untrimmed retry means silence reaches the model, which fills it with a real word (3s of nothing became وَالْمُؤْمِنِينَ).
    # Measured no-speech: 0.24 to 0.27 on silence and room noise, 0.00 on every ayah.
    recitation_no_speech_max: float = 0.15
    # 0 = off, the biggest saving in reciting: dropping unsure words needed word timing, most of the cost.
    # The transcript now only says where on the page you are, so dropping words just breaks the run that finds the place.
    # Measured on 30 marked recordings, 0.94 vs 0.0:
    #   2708ms vs 1292ms per recording; placed 97% vs 100%; whole ayah found 57% vs 87%; words judged 84% vs 93%.
    # See backend/scripts/time_placing.py.
    recitation_word_min: float = 0.0
    # Bring quiet recitations up before listening (services/recitation/loudness.py): voice, silence trim and word
    # sureness are all judged against a fixed idea of loudness. Target is mean level; 0.06 is an ordinary laptop-mic speaking level.
    recitation_loudness_target: float = 0.06
    # Peak cap, so nothing crackles.
    recitation_loudness_ceiling: float = 0.95
    # Below this it is left alone, so a silent room is never lifted into a word.
    recitation_loudness_floor: float = 0.002
    recitation_loudness_most: float = 20.0
    # How a word's pieces become one sureness: "worst" (strict), "mean", "worst-but-one" (forgives one bad piece,
    # e.g. a word-final vowel where the reciter stopped). Swept over 1,950 recordings, 6,832 judged words (sweep.txt),
    # matched at the same vowel-slip catch:
    #   worst, under 0.1          5.1% marked though right, 62% of vowel slips
    #   worst-but-one, under 0.9  3.2% marked though right, 61% of vowel slips
    # Cost: whole-word slips caught 9% vs 27%, weakest number here (only 34 such words in the corpus).
    # See rescore_recitation.py, sweep_sureness.py.
    recitation_sure_of_word: str = "worst-but-one"
    # Decoder holds 448 pieces, ~3 per word; a ten-second recording holds far fewer than this, so more means placing went wrong.
    recitation_sure_max_words: int = 100
    # Frames of sound handed to the ear when scoring words; a frame is 10ms, so 1500 is 15s.
    # Padding to the ear's full 30s costs the same as sound (5s and 25s recordings both took 1,410ms over 483 checks);
    # handing the recording's length rounded up to a block cut the middle check from 967ms to 541ms over 1,950 recordings.
    # Not lower than 1500: the ear was trained only on 30s stretches, and shorter windows score lower, not just noisier.
    # At block 100 the same false-red rate caught 6.5% of vowel slips vs 17.8% at 30s.
    # At 1500: beginner 0.6% wrongly red, 19.5% slips caught (was 0.7%, 17.8%); standard 1.5%, 33.5% (was 1.6%, 31.9%).
    # Rounded so the ear sees a few sizes repeatedly. 3000 restores full 30s padding.
    # Before lowering, rerun rescore_recitation.py then sweep_sureness.py.
    recitation_window_block: int = Field(default=1500, gt=0, le=3000)
    recitation_check_ayahs_max: int = Field(default=60, gt=0)
    # POST /api/listen/check: a page is a few hundred chars; far past that no reading could have produced it.
    recitation_check_heard_max_chars: int = Field(default=2000, gt=0)
    # A recording cut inside a word (4s chunk of إياك نعبد وإياك نستعين) made the model loop: نعبد وإياك eleven times, 12s to decode.
    # 1.2 stopped the loop (2s) and changed no other reading tried; no_repeat_ngram_size misspelt الرحيم.
    recitation_repetition_penalty: float = 1.2
    # Measured on 12 recitations each, read/check ms: 4 threads 4029/1300, 8 3660/1109, 12 3147/912, 16 2717/887.
    # More is faster all the way up. 12 not 16: 16 buys 14% more and leaves nothing to draw the page while someone recites.
    recitation_threads: int = 12
    recitation_matches: int = 5
    # How much better the best place in the Qur'an must fit than the next before it is sure (locate.py).
    # 1,050 Groq readings in 4-word pieces: 0.05 placed 1,602 right and 2 wrong, 0.1 1,247 and 0, 0.15 1,012 and 0.
    recitation_place_margin: float = Field(default=0.1, gt=0, lt=1)
    # How well the best place must fit (0 to 1) before it can be sure; a lone candidate used to be sure at any fit.
    recitation_place_fit: float = Field(default=0.9, gt=0, le=1)
    # Words of an unsure reading carried in front of the next one's lookup; more drags the fit of a fresh reading down.
    recitation_place_carry_words: int = Field(default=8, gt=0)
    # A minute of browser audio is about 1 MB.
    recitation_max_mb: int = Field(default=12, gt=0)
    # No default-book setting on purpose: the panel opens on the manifest's first book, then the reader's last choice.
    # A setting would be a second source that could disagree.

    catib_parser_enabled: bool = True
    # The top disambiguator reading comes from bare letters and can contradict typed vowels (آفِلًا for typed أَفَلَا);
    # the first of these that agrees is used. Scoring all costs nothing extra. 40 because a rare passive (أُكِلَ) can rank below the 20th.
    catib_readings: int = 40
    # Holds encoder.onnx (int8), scorer.onnx, tokenizer.json, labels.json, config.json, clitic_feats.csv.
    # See catib_onnx.py's docstring for sources. Relative paths resolve inside backend/.
    catib_parser_dir: str = "data/parser"

    # See services/journal.py. Relative to the project root (folder holding backend/), unlike data_path's paths: it sits beside backend.log.
    journal_path: str = "logs/recite-journal.jsonl"
    journal_max_kb: int = Field(default=5120, gt=0)
    # Older rotated files are deleted, which keeps the log folder bounded.
    journal_keep: int = Field(default=3, gt=0)
    # Page batches are capped by event count and wire size so one runaway session cannot fill the journal with an unbounded POST.
    journal_page_events_max: int = Field(default=50, gt=0)
    journal_page_bytes_max: int = Field(default=65536, gt=0)

    # Rebuilt by backend/scripts/build_daleel_index.py, never written while serving.
    daleel_index_path: str = "data/daleel.db"
    # Hand-written, read once. See routers/grow.py.
    grow_path_path: str = "data/grow/paths.json"
    # Past a handful of passages the list is scrolled, not read.
    daleel_result_limit: int = 12
    # A common word expands to its root family plus synonyms (hundreds for قول); capped to avoid a hundred-term search.
    daleel_root_expand_max: int = 6
    # Lower than the cap above because each translation also brings its root: six made a twelve-term search vs one to three for Arabic.
    # Measured over twelve English questions: three kept as many exact matches (more on six) and made most searches twice as fast.
    daleel_english_expand_max: int = 3
    # Longest question any search box sends (Daleel, Hadith, Dictionary, Qur'an); past it, a paste, not a search.
    search_max_query_chars: int = 200
    # No minimum-word-length setting here on purpose: it is a property of SQLite's trigram tokenizer and lives in services/fts.py.
    # A duplicate here once switched off typo tolerance silently when only one copy changed.

    # Fetched once by backend/scripts/build_asbab.py; timelines use it to place reports that name no event.
    quran_surah_type_path: str = "data/quran/surah-type.json"
    # Written by the same script; lets the panel say how many reports are not shown.
    asbab_unmatched_path: str = "data/quran/asbab-unmatched.json"

    # Hadith that seem to conflict, grouped by al-Tahawi's own chapters, and the
    # paragraphs the cutter could not place. Both written by build_mushkil.py.
    mushkil_path: str = "data/hadith/mushkil-tahawi.json"
    mushkil_unplaced_path: str = "data/hadith/mushkil-unplaced.json"

    # library.json plus one file per section under sections/; checked on load by services/timelines.py.
    timelines_dir: str = "data/timelines"
    dawah_path: str = "data/dawah/dawah.json"

    # Model-written, checked on load by services/colloquial/loader.py.
    colloquial_dir: str = "data/colloquial"

    # Written by scripts/fetch_hadith_collections.py.
    hadith_dir: str = "data/hadith"
    # Built from hadith_dir by scripts/build_hadith_index.py. Never written while serving.
    hadith_index_path: str = "data/hadith.db"
    # Narrators of the hadith chains, read from sunnah.com by scripts/fetch_rijal.py (knobs in rijal_dir/rijal.json).
    rijal_dir: str = "data/rijal"
    # Raw pages the fetch cached; build_rijal.py reads them, the app never does.
    rijal_pages_dir: str = "data/rijal/pages"
    # Built by scripts/build_rijal.py. Never written while serving.
    rijal_index_path: str = "data/rijal.db"
    # Narrators one search lists.
    rijal_result_limit: int = Field(default=20, gt=0)
    # Narrators one page of the narrator list shows, and the most a request may ask for.
    rijal_list_page: int = Field(default=60, gt=0)
    rijal_list_max: int = Field(default=200, gt=0)
    # Hadith one narrator's page lists, all of them behind "Show all".
    rijal_hadith_limit: int = Field(default=5000, gt=0)
    # A hadith is read in full, so a long results page stops being read.
    hadith_result_limit: int = 20
    # A typed word no search knows is swapped for the likeliest meant word
    # (services/spelling.py): at most this many slips per letter (a quarter:
    # one in a short word, two in a long one), each slip costing this much
    # log-frequency, so a word a slip further must be that much more common.
    spelling_edits_per_letter: float = 0.25
    # Below this many letters a word is mostly particle; one edit turns it into too many others.
    spelling_min_letters: int = 3
    spelling_edit_cost: float = 3.0
    # How common a hadith word is: this much its share of everyday writing
    # (services/spelling.py everyday), the rest its share of the hadith. Everyday
    # writing keeps real words the hadith never use ("jail") from being "fixed".
    hadith_repair_everyday_weight: float = 0.9
    # English letters spell a long Arabic vowel doubled (dawood, jibreel); undoing
    # them is one slip in all (services/spelling.py slips), not one per letter.
    spelling_long_vowels: dict[str, str] = {"ee": "i", "oo": "u", "ou": "u", "aa": "a"}
    # A collection's name words that the hadith themselves use at least this
    # share of the time ("muslim", مسلم) read as words, not the name, unless the
    # search is only the name and a number (services/hadith/reference.py).
    # Measured: names at most 2e-5 of the text, "muslim" 6e-4.
    hadith_name_common_share: float = 1e-4
    # Words that describe the question, not the hadith: "hadith about the cat".
    # No index can count these, since the hadith never say them of themselves.
    hadith_query_framing: tuple[str, ...] = ("hadith", "hadeeth", "ahadith", "narration", "narrations",
                                             "about", "regarding", "concerning", "حديث", "احاديث")
    # Chapters offered beside the hits, counted from where the hits fall.
    hadith_chapter_hints: int = 5
    # Search by meaning (services/hadith/meaning.py). Built from hadith_index_path by
    # scripts/build_hadith_meaning.py; absent means words alone. Chosen on the
    # yardstick: mpnet-base 64/70 (loose 17/22) vs MiniLM-L12 61 (14), e5-small 60,
    # potion 55, words alone 54. Costs ~3x MiniLM to build; a search 54 -> 61ms on a desktop.
    hadith_meaning_path: str = "data/hadith_meaning.db"
    hadith_meaning_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    # The model was trained on 128 tokens; a long hadith is judged by its opening.
    hadith_meaning_max_tokens: int = 128
    # Word and meaning rankings are merged by reciprocal rank: 1/(k + rank) summed.
    # 60 is the standard constant; larger flattens the difference between ranks.
    hadith_meaning_fusion_k: int = 60
    # After the model fails to load (no network for its first fetch), searches
    # answer by words alone for this long before loading is tried again.
    hadith_meaning_retry_seconds: float = 300.0

    # The only database written while serving. Created on first use; deleting the file forgets everything.
    progress_db_path: str = "data/progress.db"
    # Slower answers keep right/wrong but skip timing averages: past two minutes the question likely sat open,
    # and one such value buries every real answer around it.
    progress_timing_cap_ms: int = 120_000
    # FSRS-6 spaced review (services/review_schedule.py): the chance of still remembering a word
    # when it comes due. Higher means more reviews; both knobs must be inside (0, 1).
    progress_review_retention: float = 0.9
    # A word counts as known once it has left learning and the chance of recalling it is at least this.
    # Below the retention target, so a word stays known a while after it falls due rather than the day it does.
    progress_known_retrievability: float = 0.8
    # A first right answer comes back after this many hours to be confirmed; a wrong one is due at once.
    # A day keeps same-session guesses out of Review and makes "known" mean right on two separate days.
    progress_learning_hours: int = 24
    # Without it SQLite gives up the moment two answers land together, which auto-advance makes ordinary.
    progress_busy_timeout_ms: int = 5000
    # Accounts (services/profile.py): a username, no password. Longest name allowed after cleaning.
    profile_name_max: int = 40
    # Names nobody may type: "local" is the record of every answer given before names existed.
    profile_reserved: list[str] = ["local"]
    # Largest shelf (everything the page keeps for one account) the server takes, in bytes.
    saved_max_bytes: int = Field(default=512_000, gt=0)
    # Beta testing: the log-in box lists every username so a tester can pick one. Off before launch.
    beta_list_accounts: bool = True
    # How many accounts the leaderboard lists; the asker's own place is always sent too.
    leaderboard_size: int = 20
    # Checked practice sentences (services/sentence_check.py): AI tries per request,
    # learnt words needed before asking, and particles any sentence may use.
    sentence_max_tries: int = Field(default=3, gt=0)
    sentence_min_learnt: int = Field(default=10, gt=0)
    sentence_prompt_words: int = Field(default=60, gt=0)  # a random few, so prompts stay short and vary
    sentence_free_words: list[str] = ["و", "ب", "ل", "ف", "في", "من", "على", "إلى"]

    # Declared because .env sets PORT and this class forbids unknown keys; dropping it fails startup.
    # The running port comes from the --port flag start.sh passes to uvicorn.
    port: int = 8000
    # Startup loaders by name (services/startup.py STEPS). wait: done before the first request is served.
    startup_wait: list[str] = ["dictionary", "root_meanings"]
    # background: started and left to finish, so the first use finds them loaded. Drop a name on a small machine:
    # recitation ~1s, 150MB (first recitation loads it instead); nahw_parser ~110MB ONNX + CAMeL BERT, ~600MB, ~8s+;
    # colloquial reads and checks every unit, ~3s, which the first Colloquial visit after a restart waited out;
    # hadith_meaning ~2s, ~150MB model + 50MB vectors, which the first hadith search waited out;
    # sarf_reader ~4s building the verb shapes the Nahw tab reads commands with.
    startup_background: list[str] = ["recitation", "speech", "colloquial", "nahw_parser", "sarf_reader", "hadith_meaning"]

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

    @field_validator("progress_review_retention", "progress_known_retrievability", mode="after")
    @classmethod
    def _check_probability(cls, value: float, info: ValidationInfo) -> float:
        """A chance of 0 or 1 breaks the schedule maths, so startup stops."""
        if not 0 < value < 1:
            raise ValueError(f"{info.field_name.upper()} must be between 0 and 1 (exclusive), got {value!r}")
        return value

    @field_validator("progress_learning_hours", mode="after")
    @classmethod
    def _check_learning_hours(cls, value: int) -> int:
        """No wait would let one lucky guess count as learnt, so startup stops."""
        if value <= 0:
            raise ValueError(f"PROGRESS_LEARNING_HOURS must be above 0, got {value!r}")
        return value

    @field_validator("quran_search_source", mode="after")
    @classmethod
    def _check_search_source(cls, value: str) -> str:
        """A typo would silently pin search to the last branch, so it stops startup."""
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
        return "groq" if self.groq_api_key.strip() else "auto"

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key.strip())

    @property
    def listening_keys(self) -> list[str]:
        """Own listening keys, else the shared one, else none. Deduplicated."""
        own = list(dict.fromkeys(key.strip() for key in self.listening_groq_api_keys.split(",") if key.strip()))
        shared = self.groq_api_key.strip()
        return own or ([shared] if shared else [])


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def confined(name: str, value: str) -> Path:
    """Checking half of data_path, also for a model folder named by its value (services/recitation/listen.py); cached per value (not per name, which froze the first path a test set)."""
    base = Path(__file__).resolve().parent
    target = (base / value).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"{name} must stay inside {base}, got {value!r}")
    return target


def data_path(name: str) -> Path:
    """A configured data file, confined to backend/.

    `base / value` discards base when value is absolute, so one absolute path in .env
    could move a database anywhere, and build scripts write to these paths.
    Takes the setting's name so the error says which to fix.
    Resolving is cached: ~1ms on Windows, and ayah lookups ask three times, which cost 20x the query.
    """
    return confined(name, getattr(get_settings(), name))
