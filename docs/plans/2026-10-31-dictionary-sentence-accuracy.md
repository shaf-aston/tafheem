# Dictionary: a typed sentence read more accurately

Date 2026-10-31 · `/plan-build`. Brief: make the Dictionary's meaning of a typed Arabic phrase or sentence
more accurate, review how fast and how good the answer is, keep it modular, add a 1000-input regression
test, and name what affects accuracy.

## 1 · How a typed sentence is read today

```
typed Arabic → read_words (iraab.analyze: CAMeL + CATiB parser; CAMeL alone when the parser is absent)
             → a whole ayah?  → published translation + the Qur'an's word-by-word English
             → else           → language model (Groq gpt-oss-120b) handed one line of facts per word
             → answer filed in progress_store, so a text asks the model once
```

The rows the reader sees (word, English, lemma, role, case) always come from the grammar; the model writes
only the one-line sense. That rule stays: the model never changes a row.

## 2 · What affects accuracy (the criteria)

Measured on 613 Qur'an ayahs (gold: the Qur'an's own word-by-word English) and 1105 Fusha course phrases
(gold: the course's English), production path, parser on:

| Factor | What it does | Seen |
|---|---|---|
| Parser present | Without CATiB the roles are empty and CAMeL guesses alone | Qur'an gloss hit 50.9% → 72.2% with it |
| CAMeL's pick on particles | إن read as an abbreviation ("N."), إذ "because", الم "painful", رب "owner" | the most common wrong rows |
| Model told glosses are settled | The old prompt said every gloss was right, so a wrong row became a wrong sentence | prompt review |
| Senses shown to the model | Only the reader's 2 senses per word: the right one was often cut | prompt review |
| Part of an ayah typed | Only a *whole* ayah used the Qur'an's English; a fragment went to CAMeL | 281 sampled fragments |
| Cache not tied to the prompt | A prompt change kept serving answers written under the old prompt | code review |
| Speed | The parser (p50 123 ms, p95 1.2 s, ~20 s cold) and one model call dominate | timed |

## 3 · Requirements

| # | Criterion | Check |
|---|---|---|
| S1 | A run of 2+ words from inside one ayah gets the Qur'an's own English on its rows, with "Open ayah" | pytest (fabricated index) + scorer: run_found / run_right |
| S2 | A sentence that only shares words with an ayah is not taken for part of it | pytest; 5 of 1700 non-Qur'an inputs match, 4 of them real quotes (بسم الله, إنا لله…) |
| S3 | The model is handed wider senses (4) as candidates, and told to choose or translate from the sentence | pytest: handed facts |
| S4 | Answers filed under an older prompt are never reused (question name `meaning3`) | pytest |
| S5 | 1000 in-repo inputs: none breaks, every one has a row per typed word and a prompt line per row | `tests/dictionary/test_sentence_set.py` in CI's nahw job |
| S6 | No count on the yardstick worse than its baseline | `score_sentences --check` (same test) |
| S7 | ayah_run costs nothing on non-Qur'an text | p50 0.5 ms, p95 5.8 ms |
| S8 | The rows, the API and the page are unchanged in shape | existing suites green |

## 4 · Designs scored

| | A · better facts, same flow | B · model rewrites the rows | C · split response (words first, sense later) |
|---|---|---|---|
| Accuracy | + Qur'an runs exact; model chooses among candidates | + could fix any row | 0 |
| Trust | + model never touches rows | − a wrong model answer changes a lookup | 0 |
| Speed | 0 (ayah_run < 6 ms p95) | − more tokens, slower | + sense arrives later, rows at once |
| Change size | small, backend only | medium | API + Dictionary + Nahw pages |
| **Pick** | **chosen** | rejected: breaks the "model never changes rows" rule, adds hallucination | deferred: a follow-up for perceived speed |

## 5 · What was built

- `quran_search.ayah_run(text)` (search/local.py): the ayah holding the words as one run, in order, and
  where the run starts. Inside a word, hamza seats and alif are left out on both sides (وآتوا = وءاتوا);
  a word's first letter is kept as one alif, so لينا is never إلينا.
- `sentence_meaning._ayah_words`: the grammar's rows with the Qur'an's English, `words_source` "translation",
  `ref` the ayah. Any count mismatch or missing English → CAMeL's rows stand.
- Facts carry `senses` (config `sentence_fact_senses`, default 4); the prompt calls them candidates and
  adds "keep the meaning of every word; add nothing the Arabic does not say".
- Cache question renamed `meaning3`, with a note to rename it whenever `SENTENCE_USER` changes.
- The yardstick: `backend/data/dictionary/sentence_set.json` (595 Fusha phrases with English, 405 Nahw
  sentences, 400 Qur'an ayah keys), `backend/scripts/dictionary/score_sentences.py` (`--check`,
  `--save-baseline`, `--quran`, `--show`, `--write-set`), baseline `sentence_baseline.json`.

## 6 · Results

The set (Qur'an index and dictionary left out, both gitignored, so CI and a laptop score alike; model stood in for):

| Count | Value |
|---|---|
| inputs / broke | 1000 / 0 |
| aligned (row per word) | 1000 |
| rows with English | 3593 of 3615 |
| junk tags | 0 |
| Fusha English covered | 1361 of 2446 content words (55.6%) |
| read time | p50 144 ms, p95 540 ms |

Qur'an part (local only, needs meanings.db and the index): 400 ayahs, rows matching the Qur'an's English
2806 of 5113; runs cut from them found 379 of 390, with the exact English 331.

The yardstick also caught a crash in the syntax tree: the parser rooted Al-Baqarah 2:259 on its first أَوْ,
and a jar-majroor hung on a حرف عطف at the root looked up a word that is not there (KeyError 'pos'), which
dropped every role in the ayah. Fixed in `syntax/tree.py`; `tests/nahw/test_catib_onnx.py` reads the
ayah and fails on the old code.

## 7 · Follow-ups

- C above: send the rows first and the sense after, for perceived speed.
- رَحِمَهُ اللهُ matches 3:107 "رحمة الله" (ة and ه fold together). Rare; left as is.
- The model-side gain (S3) can only be scored with a model; run `score_sentences` against a live key once,
  never against production (it files answers).
