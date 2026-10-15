# Tafheem audit (read-only, 2026-10-06, HEAD 1e5c95b, 50 commits, ~2,617 tracked files)

Method: grep/sed excerpts. Could NOT run anything (no fastapi in sandbox; corpus.db, lexicon.db, library.db, rijal.db etc. are "built, never committed", so DB contents were read from build-script schemas, not rows).

## 1. Trust-by-sources / verified generation — PARTIAL (strong on labelling, none on checking)
Evidence
- Provenance registry: backend/services/provenance.py:38 `of(key)` raises on unknown key; sources.json has 35 entries, each with confidence in {verified 20, derived 5, translated 2, guessed 8} (data/sources.json `_confidence_comment` line 4), `where`, `used_in` (drives tab footers), url, category.
- Every API response attaches a Source; UI: frontend/src/components/ui/SourceBadge.jsx, lib/confidence.js:20-28 (`levelOf` defaults unknown -> guessed). Tests: tests/test_sources.py.
- Per-edition badges: provenance.for_edition (provenance.py:~50).
- LLM is used ONLY in: (a) /meaning Sarf enrichment: services/ai/__init__.py:101 analyze_sarf, routers/morphology.py:40-75, labelled `ai`(guessed) at :72; (b) Maqayees entry -> English (prose, ai/__init__.py:109; line-by-line :137); (c) sentence translation for non-Qur'an text, handed CAMeL's word-by-word (services/sentence_meaning.py:1-15, ai/__init__.py:125), cached in progress_store; (d) offline authoring: backend/scripts/backfill_root_english.py, and content "written with Claude" (sources.json: timelines, dawah, colloquial, nahw-notes, tamreen answers marked "claude"; tamreen.py:12-14).
- Grammar (i'raab/tarkeeb/sarf tables/practice questions) is NO-LLM: routers/analysis.py:4, practice_service.py:1.
- Only output check on LLM: line-count guard on line-by-line English (routers/dictionary.py:290-296: 502 if count mismatches, "English under the wrong Arabic is a false claim"); the prompt asks for JSON with rule names (ai/prompts.py:7-17) but nothing validates the citations. Maqayees English labelled "about 1 in 50 wrong" (sources.json maqayees_english).
- Qur'an lookups are "looked up, never guessed" (CORE-FLOW.md step 3); asbab links carry "derived".
What's missing: claim-level citation/entailment checking of LLM output; refuse-if-uncited; per-sentence (vs per-response) labels; a retrieval step that feeds approved sources to the LLM. (Daleel is a search over books with quote+location, services/daleel/, closest to RAG but returns passages, not generated text.)
Integration path: wrap services/ai/__init__.py `_ask` with a verifier that checks emitted rule names / roots against nahw_rules/*.json, quran_corpus root_of, maqayees; downgrade `Source` from `ai` to a new `ai-checked` key in sources.json; badge already renders any key.
Complexity: M for a verifier on the 3 existing LLM features (surface is tiny); L if it means open-ended generation.

## 2. Hybrid symbolic + neural morphology/syntax — EXISTS (inverted order: neural proposes, rules constrain/veto)
Pipeline (iraab.py:20-35; services/syntax/__init__.py:45 `read`):
1. morphology.py: CAMeL analyzer + MLE disambiguator for sentence-level homograph choice (morphology.py:4,46-57,455-470), fallback Qalsadi -> PyArabic.
2. rule_engine.py gives each word a card from tags + typed vowels.
3. If ayah is in Quranic Treebank: use recorded tree (tarkeeb_store.for_sentence; 5,023/6,236 ayahs) = highest trust, skips parser.
4. Else neural: syntax/catib_onnx.py (CAMeL BERT disambiguator + ONNX CATiB dependency scorer, data/parser/scorer.onnx 5.6MB) gives link scores; syntax/mask.py:1-12 masks out (dep, head, rel) labels the book forbids BEFORE decoding (vetoes toggled in nahw_rules/closed_words.json); mask.book_links:169 overwrites links the book settles outright.
5. facts.py (808 lines) answers 5 questions/word; walker.py:94 walks data/nahw_rules/naming_tree.json to role+page.
6. teacher.py:1-10: re-reads result against stated rules; a violating role is DASHED (gap) not re-guessed ("a dash is better than a confident wrong name"). iraab.py:50 turns gaps into cards.
7. signs.py (205 lines) writes the sign once, after roles settle; tree.py draws same reading so cards and picture cannot disagree.
Ambiguity detection: implicit (disambiguator ranking, mask impossibility, teacher check). No explicit ambiguity score / "ask model only when rules tie" arbiter; no second reading offered (single reading + gap).
Measured: backend/scripts/score_iraab.py (modes: default = 47 book examples; checked 72; fresh 137 tune/hold split; exam 258 blind two-reader; hadith 77; rules 130; also counts confident-wrong, gaps, card/picture disagreement; --api scores live app). score_tarkeeb.py scores rules vs treebank. NO RESULT NUMBERS recorded anywhere I found (grep "Roles right" only hits the script; git log shows one commit mentioning score). I could not run it (no fastapi). Held-out sets exist and are in repo: data/nahw_rules/{checked,fresh,exam,hadith,rule}_sentences.json.
Missing: recorded benchmark table; calibrated confidence; n-best readings; arbitration policy beyond mask/veto.
Integration path: add n-best to decode.py + have teacher.py choose among them (cheap: it already vetoes); persist score_iraab output to a docs/benchmarks file in CI.
Complexity: S to record scores; M for n-best arbitration; novelty claim itself is largely already built.

## 3. Word Identity Graph — PARTIAL (nodes exist; typed edges and sense_id missing)
Evidence
- Token->lemma->root->POS->features per Quran word: corpus.db `segment(surah,ayah,word,segment,form,pos,root,lemma,features)` with indexes on root and lemma (scripts/build_quran_corpus.py:34-52); VF:n form decoded to wazn by quran_corpus._verb_pattern (:76). Noun patterns (awzan) NOT stored (not found; searched: wazn, pattern in quran_corpus, sarf/).
- Per-token contextual gloss: meanings.db `meaning(surah,ayah,word,...)` English+Urdu from Quran.com word-by-word (build_quran_meanings.py:62-72). This is context-specific text per token but NOT a sense_id (searched: sense_id, senseId, band: not found in backend/ or frontend/src).
- Lexicon table of all quiz words: lexicon.db `word(id, ar, bare, en, ur, meaning_key, word_type, root, times_in_quran, attached, source)` + `word_tag(axis set|group)` + `word_place(word_id,surah,ayah)` (scripts/build_lexicon.py:92-131). Identity = vocalised spelling; meaning_key merges synonyms. 
- Inputs: quranic-words.json (382 words, "80% of Qur'anic Words", with timesInQuran), vocabulary.json (230 everyday MSA words), word_kinds.json (hand overrides: 10 kinds, 25 lemmas), urdu_links.json (898 words with verdict cognate/false-friend + urduSenses, build_urdu_links.py:170-190 -- an Arabic<->Urdu confusion edge).
- Root as spine: quran_corpus.occurrences_of_root:314; /api/quran/root/{root}; root_meaning (Maqayees 4,738 roots, origin sense), lexicons.py (Lisan, Taj, Lane 5,183 roots, Maqayees via OpenITI), root_gloss.py. Dictionary synonyms (dictionary_service.py:175).
- Edges that exist implicitly: same-root (segment_root index), occurs-in (word_place), twin verses (mutashabihat.py + data/quran/mutashabihat.json, benchmarked), sound-alike (frontend/src/lib/soundalike.js), narrator teacher/student ties (rijal `tie`). 
Missing: unified graph store/API; word-sense inventory per lemma (the "Maqayees origin sense" is root-level only; Wiktionary has multi-sense entries but no mapping from a Quran token to one); confused-with edges between lemmas; pattern nodes for nouns.
Integration path: new `word_graph.db` built by a script joining corpus.db segment + meanings.db + lexicon.db + root_meaning + urdu_links; expose via services/word_graph.py (ReadOnlyDb pattern, services/readonly_db.py). Sense assignment = alignment of meanings.db gloss strings to Wiktionary senses (hard part).
Complexity: M for lemma/root/occurrence/related graph; XL for true sense_id disambiguation of Quran tokens.

## 4. Vocabulary mastery engine — PARTIAL (FSRS exists; per-item only)
Evidence
- review_schedule.py:30 `card_of` replays (time, correct) into FSRS-6 (py-fsrs), desired retention 0.9 (config.py:336), learning steps, `is_known`:49 uses retrievability. Pure; schedule is recomputed by replay, nothing stored (progress_store._replay).
- progress.db (services/progress_store.py:~30-70): tables attempts(user, module, item, correct, ms, context JSON, at), questions (generated practice Qs kept w/ source key), feedback. Summary: attempts/wrong/avg_ms per item (progress_store.py:_SUMMARY). Routes /api/progress/{attempts,summary,review,feedback,forget} (routers/progress.py).
- Written by exactly 3 callers: QuizPanel.jsx:312 (item = meaningKey; context {bank, group, direction}), GrowPanel.jsx:68,77 (item = path/step, module grow), colloquial/ExerciseHost.jsx:39. Memorise, Tamreen, Nahw practice, Hadith, Sarf do NOT record attempts (grep recordAttempt: 3 files).
- Per word: yes (meaningKey). Per sense: no. Per root: only via join: lib/insights.js joinStats/byCategory/hardestWords/slowestWords/overall (insights.js:30-110) joins by word_type/topic/set tags client-side; QuizInsights.jsx shows it. Minimum-attempts guard before a rate is shown (insights.js header).
- Distractors: chosen distractor NOT stored. QuizPanel.jsx:312-317 sends only answerId + correct; `picked` exists in React state (QuizPanel.jsx:304) but never leaves the browser. Distractor choice is itself smart: lib/quiz.js:114 pickDistractors (same word type, shape-matched gloss, same topic group, no synonyms, distinct senses).
- Grow: client-side localStorage record {tries, cleanDays[], done} per step (lib/grow.js:113-125; GrowPanel.jsx:45 useRemembered(progressKey)), tiers/unlock/nodeState/upNext (grow.js:137-225), data/grow/paths.json (8 paths: wudu, salah, surahs, full-salah, adhkar, amma, kursi, mulk; basics/intermediate/advanced), clean-days threshold in grow.json; plus a server attempt copy. Learner state is therefore split: FSRS attempts server-side, Grow record client-side.
Missing: record of chosen option; per-root/per-sense mastery; unified learner model; mastery across modules.
Integration path: add `picked` into context in QuizPanel.jsx:317 (no schema change: context JSON already free-form; AttemptIn.context at schemas.py:1115). Root/lemma rollups via lexicon.db word.root join in progress_store.summary.
Complexity: S (log distractor), M (per-root/lemma mastery), L (cross-module learner model).

## 5. Misconception classifier + micro-interventions — MISSING (building blocks present)
Searched: misconception, confus, common mistake, "why wrong" in backend/services, routers, frontend/src, data/practice, data/nahw_rules. Hits are only: recite.json + lib/soundalike.js (orange rule = "slip or mishearing?", recite RECITE-PLAN standing rule 2), lib/quiz.js distractor design, urdu_links false-friend verdicts. Nothing classifies WHY a quiz/Tamreen answer was wrong. Practice templates (data/practice/templates.json) carry only question/answer/hint strings; Tamreen tags (data/tamreen/tags.json, 63 topic tags, 6 exercises + munsarif) are topics, not error types. insights.js groups errors by word category only.
Recitation has a 5-state taxonomy (follow.js:57-70: waiting/said/check(orange)/wrong/missed + red dashed "extra word"), which is a real error taxonomy for recitation only. The scorer buckets reviewer marks as letter-or-word / vowel / tajweed (score_recitation_checker.py:61-67).
Integration path: log picked option (item 4) -> classify by distractor attributes already computed in quiz.js (same-shape, same-topic, soundalike, same-root) -> map to nahw_notes topic/Tamreen tag deep links (Tamreen "link to notes" already exists per CORE-FLOW). 
Complexity: M (rule-based classifier over distractor features, ~weeks of content mapping), L if the target is i'raab misconceptions (needs student free-text answers; Tamreen/practice are not auto-graded per attempt today).

## 6. Pedagogy router / adaptive path — MISSING (static sequencing + SRS queue only)
Evidence: grow.js:218 `upNext` = first unlearnt step in first unlocked tier (fixed order); grow.js:161 `unlocked`; quiz Review mode = FSRS due list (routers/progress.py /review, progress_store.review_items). Nothing chooses lesson/strategy from learner state (searched: adaptive, recommend, next lesson in frontend/src/lib, services). journey.js/session.js are navigation history only (trail, back/forward), not pedagogy.
Complexity: M to add a "what next" recommender using FSRS due + insights weak categories + Grow upNext; the inputs mostly exist.

## 7. Teacher mode / class reports / accounts — MISSING
No accounts: routers/progress.py:28-32 "There are no accounts... LOCAL_USER = 'local'"; `user` column exists in attempts/questions/feedback (progress_store SCHEMA) and `forget(user)` exists. No auth, sessions, roles, class concept (searched: login, auth, oauth, password, class, student in backend/ and frontend/src; only hits are Tamreen "teacher" as a content author, nahw_notes "teacher's notes").
IMPORTANT operational finding: on the shared Oracle VM every visitor writes to user 'local' in one progress.db, so FSRS/review/summary mix all visitors (progress.py:32). Also /api/progress/forget wipes it for everyone.
Content-side teacher features that DO exist: teacher's notes (nahw_notes), Tamreen library harvested from a teacher's Google Forms, "teacher.py" is the nahw rule checker (not a user role).
Integration path: replace LOCAL_USER with an auth dependency (explicitly designed for this, progress.py:30-31); class = new table; reports = SQL over attempts.
Complexity: L (auth + privacy + UI), M for anonymous device-id user (cheap fix to the shared-'local' problem: S).

## 8. Recitation feedback — PARTIAL/EXISTS for words; tajweed MISSING in serving path
Evidence
- RECITE-PLAN.md milestones M0-M10 (headings lines 39-278; M3 "two ears", M5 marks, M6 strip, M7 hidden words + reciting). Standing rules (L9-33): fold spellings first, five states, nothing marks instantly, 20 req/min Groq ceiling, "No paid provider, no card, ever" (L282).
- services/recitation/: ears.py (hosted Groq -> letters -> here Whisper, 60s rest on failure, per-minute limiter), hosted.py, letters.py (tilawa FastConformer ONNX, data/models/tilawa 85MB, MIT/CC-BY), locate.py (place recitation on the page), place.py, match.py, listen.py (434 lines; /api/listen, /api/listen/check "how sure of each word"), loudness.py, spelling.py, recording.py. Journal: services/journal.py + lib/journal.js -> logs/recite-journal.jsonl joined by X-Reading-Id.
- Client follower: lib/follow.js (alignment with COSTS from recite.json, states at :57-70), soundalike.js, recitingSession.js, ReciteStrip.jsx.
- Tuned thresholds recorded in config.py:70-190 comments (e.g. >=0.9 sure of 74% right words imlaei vs 51% Uthmani; sureness "worst-but-one" 3.2% marked though right at 61% vowel-slips caught; 1,950 recordings / 6,832 judged words).
- Tajweed: phoneme checker is a RESEARCH SPIKE only (scripts/score_phoneme_checker.py; no import from services/ -> not served). Header explicitly says ikhfaa/idgham/iqlab/ghunnah/qalqalah out of scope. Recorded result (data/recitation_checks/phoneme_report.txt): 1,825 clips scored; articulation: 12% false flags on right words, 45% of letter/word errors caught (31 words); length/vowel: 14% false flags, 84% of vowel errors caught (202); 2.3 s/clip mean. Caveat in same file: all 14,571 vowel durations measured exactly one 20ms frame (duration not actually measurable by CTC).
- Reviewer-marked tajweed errors: 838 words in recitation_checks/report.txt, only 39-61% caught by the sureness method depending on threshold. No tajweed RULE engine (no madd/ghunna/qalqalah rule code; grep hits only in scripts, arabic_text, ilal as unrelated). data/books has Al-Jazariyyah (sources.json jazariyya, 107 verses) and Grow/ Daleel can show it, but nothing links rules to the recitation checker. "Error lattice" as such: not found.
Integration path: services/recitation/listen.py check endpoint already returns per-word sureness; add tajweed annotation layer = per-word rule tags from a phonemizer-driven rule table (quranic-phonemizer is already prototyped) displayed via lib/follow.js states.
Complexity: L (tajweed rules + validation set); data (1,950 reviewer-marked clips, sweeps) is an unusual asset.

## 9. Explanation atoms / composable explanations — EXISTS (largely)
- Rule text as data: data/nahw_rules/{roles,teacher,naming_tree,particle_tree,closed_words,tarkeeb,answer_key}.json. teacher.json holds `reasons`, `signs` tables (kind -> case -> sign words), `case_said`, `checks` with ar/en reasons. Every Arabic term spelled once (tarkeeb.json; CORE-FLOW glossary).
- Cards assembled from stored pieces: iraab.cards (iraab.py:50-75) = rule_engine card + walker role + signs.settle sign + `reason(role)`; `_pieces_said` prepends family-card sentences (iraab.py:~78-85); naming_tree.json is the book's division as data walked by services/syntax/walker.py:94.
- Notes: data/nahw_notes/topics/*.json blocks (heading/rule/list/example/table/picture), `{{role|text}}` markers (nahw_notes.py:32 MARK; FORMAT.md:39-42), load-time validation (:49-125); lib/notes.js hides markers or turns them into flashcards. Tamreen: 63 tags (tamreen/tags.json) shared across exercises; rules+examples per exercise, answers attributed teacher|claude (tamreen.py:12-14), picture images 5.5MB.
- Practice: data/practice/templates.json with {placeholders} filled from analysis (practice_service._fill).
- Not found: a recombination layer that composes multi-atom explanations for an arbitrary learner error; atoms lack stable ids/prereq edges.
Complexity: S-M to add ids/prereq edges to nahw_notes blocks and tag roles; the atoms mostly exist.

## 10. Offline-first / local learner state — PARTIAL
- Backend offline by design (README.md:7, CORE-FLOW.md "Offline by default"); data built locally (1.6 GB DBs, deploy/README.md:3-4).
- Frontend: NO service worker (searched serviceWorker, workbox, VitePWA in package.json, vite.config.js, public/, index.html: none); only public/app.webmanifest. No IndexedDB (grep indexedDB in frontend/src: none). localStorage via lib/stored.js (readSaved/writeSaved, progressKey prefix, forgetProgressKeys:61), useRemembered.js, useHistory.js (lookup history), settings.js, session.js (journey trail saved with version, parseSession), journey.js (browser history-based trail), recent.js, Grow record, quiz best streak (QuizPanel.jsx:98).
- Server-side learner state: only progress.db (single 'local' user, see 7). Grow record = client-only; attempts = server-only; neither syncs.
- frontend probes: scripts/probe-persistence.mjs, probe-session.mjs, probe-trail.mjs test persistence.
- On-device ears: tilawa ONNX and Whisper run on the backend machine, not the phone; "offline" means local to the server.
Complexity: M (service worker + IndexedDB queue for attempts), L if the heavy models must run on-device.

## 11. Upgrade triggers / monetisation / accounts / payments / analytics — MISSING
Searched stripe, payment, subscri, analytics, plausible, gtag, posthog, login, upgrade across backend/, frontend/src/, deploy/, README: nothing. Only: deploy/usage.py + usage.sh parse Caddy access logs and Groq-call log lines into per-IP/day counts (manual). Rate limits exist (speech_per_minute config.py:~135, listen_per_minute in ears), RECITE-PLAN "No paid provider, no card, ever". Product is free; hosted on Oracle Free + Vercel landing.
Complexity: L (needs accounts first, item 7).

## 12. Hadith side — EXISTS, with the most novel-looking graph assets
- Rijal DB (built by scripts/build_rijal.py:28-47 from sunnah.com via fetch_rijal.py; services/rijal/store.py): tables narrator (grade, tabaqa/generation, years, lineage, nisba, city, school), verdict (scholar quotes per narrator), tie(teacher_id, student_id) = directed teacher->student graph, mention(collection, book, number, part, start, end, narrator_id, ord) = narrator spans inside the Arabic isnad text, narrator_fts. rijal.json = 4 generation buckets mapped from tabaqat. Endpoints routers/rijal.py:16-66: /chains/{collection}/{book}, /family/{collection}/{number}, /narrators, /narrators/{id}, /narrators/{id}/hadith, /search.
- Narration families: collection numbering a/b/c parts; services/rijal/family.py:5 `meet` finds where one chain joins another (meeting narrator + borrowed rest); frontend lib/familyTree.js builds a chain-trie tree from the Prophet down with shared nodes (madar/common-link style drawing), NarratorPage.jsx, NarratorList.jsx, lib/rijal.js tones by grade rank. Chain/matn split: services/hadith/chain.py (port of hadithWords.js chainOf, rule in frontend/src/hadith.json).
- Hadith search: services/hadith/search.py + lemma.py + repair.py + meaning.py (multilingual sentence model on onnxruntime; vectors by build_hadith_meaning.py), scored by score_hadith_search.py against data/hadith/search_yardstick.json (9KB).
- Mushkil: services/mushkil_split.py (99 lines) cuts al-Tahawi's Sharh Mushkil al-Athar per bab -> data/hadith/mushkil-tahawi.json (built); CORE-FLOW: "No tab reads it yet" (searched frontend/src jsx for mushkil: only 0 hits in components). So conflict-and-reconcile structure exists as data, unsurfaced.
- Mutashabihat (Qur'an twin verses) with scholar benchmark + proposer for missed pairs (services/mutashabihat.py, score_mutashabihat.py; config says shingle size 2 -> 77% pair recall).
- Not found: grading (jarh/ta'dil) computation over chains, chain-continuity checks (does teacher->student tie exist for each adjacent pair) as an automated verdict, even though `tie` + `mention.ord` make it directly computable.
Complexity: S-M for chain-connectivity check and exposing mushkil in a tab; M-L for graph analytics (common-link detection).

## (a) Data assets in backend/data/ (size, nature, licence)
Committed unless "built": sizes from du.
- sources.json: provenance registry (hand-made). 
- quran/: tags.json (corpus shorthand -> Arabic terms, hand), mutashabihat.json (derived from scholar lists, CC/benchmark keys in sources.json), editions.json (manifest), juz.json, surah-type.json, asbab-surahs.json / asbab-unmatched.json (derived from Lubab al-Nuqul by rule). BUILT, not committed: corpus.db (Quranic Arabic Corpus 0.4, GNU GPL), meanings.db (Quran.com wbw), library.db (QUL tafsirs/translations), layout.db, search.db, imlaei.json, tarkeeb.db (in data/tarkeeb, 15MB committed, Quranic Treebank hand-recorded).
- quran_cache/: cached Quran.com verse JSON samples (network-derived).
- quranic-words.json: 382 words from "80% of Qur'anic Words" (Abdulraheem, Islamic Book Trust) -- book transcription; copyright status of that book not stated (flag).
- vocabulary.json: 230 everyday MSA words (hand-made). word_kinds.json: hand overrides. quiz_words.config.json: build config. urdu_links.json (+ .overrides.json): 898 Arabic<->Urdu verdicts, derived, candidates for human review.
- wiktionary-urdu.jsonl (32MB): Wiktionary extract (CC BY-SA). Dictionary itself built from Wiktionary dump (dictionary_service.py:3-4; Hans Wehr deliberately not shipped).
- maqayees/ (33MB): Ibn Faris origin senses for 4,738 roots (roots.json derived from Shamela typed text; README: out-of-copyright), english*.json (machine English, "guessed", ~1/50 wrong), scan-source (scans/OCR with human corrections), blanks/spelling.json.
- sarf/: patterns.json, reading.json, babs.json, ilal.json (hand-written rule tables); lane_verbs.json (derived from Lane's Lexicon, public domain).
- nahw_rules/: roles, teacher, naming_tree, particle_tree, closed_words, tarkeeb, answer_key (hand-made rule data) + 5 benchmark sentence sets (72/137/258/77/130 sentences; hand-keyed, exam set two-blind-readers).
- nahw_notes/ (31MB): teacher's Year-3 notes transcribed by Claude from page images + page images; sources.json says "guessed".
- nahw_forms/ (35MB): teacher forms harvest work, tarkeeb.json, iraab.json, units (working data for tamreen).
- tamreen/ (5.5MB): 7 exercises, tags (63), images; answers from teacher or Claude.
- tarkeeb/: examples (47 Tasheel al-Nahw trees, hand-transcribed), topics.json, tarkeeb.db.
- parser/: scorer.onnx + tokenizer/labels/config/clitic_feats: neural CATiB scorer exported from CAMeL (check CAMeL licence MIT; model provenance should be confirmed).
- models/tilawa/ (85MB): yazinsai/tilawa v0.2.0 ONNX (MIT; NVIDIA FastConformer CC-BY-4.0).
- practice/templates.json: hand-made question wording.
- grow/: paths.json (8 paths, hand), hadith-sources.json.
- hadith/: collections.json (manifest), search_yardstick.json (benchmark). Collections themselves BUILT from fawazahmed0/hadith-api; mushkil-tahawi.json BUILT from OpenITI.
- rijal/rijal.json config only; rijal.db BUILT from sunnah.com (scraped with browser impersonation, 1s pace: ToS/licence risk worth flagging).
- books/ (35MB): openiti-books.json + openiti/ (OpenITI classical texts, open licence), english-titles.json; lexicons.db (Lisan, Taj, Lane; BUILT).
- timelines/ (744KB): library.json + sections/ (written with Claude; "guessed"); dawah/dawah.json (IslamQA-based replies researched with Claude; "guessed"); colloquial/ (25MB: spine.json, 9 dialect folders, images; Claude-written, "no native speaker has checked", Levanti etc. unusable commercially per docs/colloquial-research.md).
- recitation_checks/ (1.3MB committed): reports + phoneme_results.jsonl + uthmani_check.jsonl (derived from a reviewer-marked recitation dataset; sources.json inside).
- *.apkg (4 Bayna Yadayk Anki decks, 1.2MB+): third-party textbook decks (licence unclear, flag).
- urdu_links etc. above. Dictionary JSON (arabic_dictionary.json), lexicon.db, progress.db: built/runtime, not committed.

## (b) Tests
- Backend: 94 test files in tests/, ~1,159 `def test_` functions (+~74 parametrize decorators, so executed cases are higher). Covers conjugation, ilal, walker, naming, facts, teacher, catib, tarkeeb, sources, progress, recitation (7 files), rijal, hadith, daleel, tamreen outcomes, score_iraab itself.
- Frontend: 74 *.test.* files, ~804 it/test cases (vitest), plus 12 probe scripts under frontend/scripts (probe-ear, probe-recite, drive-quiz...) that drive the real app. No .github/workflows found (no CI config in repo).

## (c) Scoring/benchmark scripts and recorded results
Scripts (backend/scripts): score_iraab.py, score_tarkeeb.py, score_mutashabihat.py, score_hadith_search.py, score_place.py, score_recitation_checker.py, score_phoneme_checker.py, sweep_sureness.py, rescore_recitation.py, letters_missed.py, time_placing.py, time_search.py; frontend/scripts/ears-score.js, ears.test.js.
Recorded numbers found (grep of md/py/json/txt):
- Recitation sureness (data/recitation_checks/report.txt): 1,950 recordings; at >=0.9 passes 85-90% of right words, catches 59% letter/word (34 words), 39% tajweed (838), 13% vowel (185). sweep.txt: worst-but-one @0.9 = 3.2% false marks / 61% vowel slips; strict "worst" @0.1 = 5.1% / 62% (config.py:181-182).
- Phoneme checker spike: see item 8 (45% letters, 84% vowels, 12-14% false flags).
- Ears: Whisper-small 8.1% error 2050ms/ayah vs base 42.6% on 36 ayahs/310 words; Groq turbo 8.1% (config.py:135-136); imlaei spelling 74% vs Uthmani 51% sure (config.py:75).
- Mutashabihat: shingle size 2 -> 77% pair recall (config.py:81).
- Maqayees: machine English ~1/50 wrong (sources.json). maqayees README:111 splitter agreement 35/52/91%.
- NOT recorded anywhere: score_iraab, score_tarkeeb, score_hadith_search, score_place results. The i'raab accuracy headline number does not exist in the repo as text.

## (d) Deployment shape
- deploy/README.md: landing page on Vercel; backend on one free Oracle VM (VM.Standard.A1.Flex, 2 OCPU Arm / 12 GB / 200 GB boot), Ubuntu 24.04, Caddy HTTPS, DuckDNS name, 1.6 GB of databases copied by deploy/copy-data.sh; vercel.json proxies /api/* to the VM. tafheem@.service runs two uvicorn instances (8000, 8001) behind Caddy health checks for rolling restarts (sync.sh / tafheem-sync.timer polls git). UptimeRobot suggested to avoid Oracle idle reclamation. deploy/usage.sh+usage.py = log-based per-visitor usage report ("who uses the backend") so there are real but unquantified users. No accounts, so all learner progress is one shared 'local' record (item 7). tunnel/ (go-live.cmd) = local tunnel option. Groq keys: GROQ_API_KEY (grammar LLM) separate from RECITATION_GROQ_API_KEY; Groq free tier is a hard ceiling (20 req/min).
