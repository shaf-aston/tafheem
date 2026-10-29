# The sounds loop

Teach the phoneme ear (wav2vec2 CTC, writes pronunciation symbols) on Kaggle, and keep a round only if a strict judge says it flags fewer correct words without going deaf to slips.
Same shape as the word-ear loop (`../finetune_ear/README.md`); it runs through the same `cloud.py`.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `sounds/settings.py` | every knob: data mix, learning rate, and the judge's bar |
| 2. Make the data (once) | `python backend/scripts/recitation/finetune_sounds/prepare.py` | uploads two private Kaggle datasets: `sounds-model` (the start model, copied from this PC's Hugging Face cache, its Hub page answers 401) and `sounds-checks` (the marked learner recordings, with each word's mark and reference phonemes) |
| 3. Run | `python backend/scripts/recitation/finetune_ear/cloud.py --loop finetune_sounds` | bundles both loops' packages into one file, pushes it to Kaggle's free GPU, waits, fetches |
| 4. Judge | `backend/data/models/finetune-sounds/verdict.json` | untuned and trained model on the same marked recordings and the same held professional clips |
| 5. Check the judge | `python backend/scripts/recitation/finetune_sounds/checks/judge_cases.py` | this PC, no GPU: planted cases decide right, and 15 planted bugs in `judge.py` are each caught |

`--fetch` waits for the last run and fetches it. The trained weights come back as `sounds-trained/` whether kept or not; `verdict.json` says `keep`. Nothing serves this model yet.

## Files

```
prepare.py             this PC: build and upload the two datasets
kernel-metadata.json   which Kaggle notebook, GPU, attached data (Tarteel v1, sounds-model, sounds-checks)
sounds/                runs on the GPU machine, in this order:
  run.py               the run: hear untuned, self-check, teach, hear trained, write verdict.json
  sources.py           the marked recordings; held professional clips; what is taught
  targets.py           an ayah's phonemes, made by quranic-phonemizer from its text
  train.py             one round of CTC fine-tuning, feature encoder frozen
  hear.py              the model's symbols for a recording (greedy CTC)
  judge.py             words flagged per group, bootstrap, keep or not, professional error rate
  settings.py          every knob
checks/
  judge_cases.py       the judge decides 23 known cases right, and 15 planted bugs are each caught
```

Reuses the word loop's package, bundled alongside: `ear.parquet` (read a big Hugging Face set cheaply), `ear.sound` (decode, noise, room, speed), `ear.text` (the Qur'an's text and ayah matching), `ear.judge.gain` (paired bootstrap), and its held voices, noise recipe and interval settings.

## A run

1. The marked recordings (1,945; 12 more were too long or did not line up with the phonemizer) are heard by the untuned model. The judge checks itself first: its numbers must land on `BASELINE`, the ones `score_phoneme_checker.py` recorded, and a model must not beat itself.
2. Held professional clips are made: 210 mid-surah ayahs by 7 reciters, from everyayah.com. No training clip comes from those reciters or those ayahs.
3. Taught: 6,000 professional clips (`tarteel-ai/everyayah`, reciters equal) and 2,500 Tarteel v1 learner clips, each with its ayah's phonemes as the answer, made harder with the word loop's speed, room and noise.
4. The trained model hears the same recordings. The recordings the untuned model matched under 70% of their ayah (partial clips) are left out for both.
5. `verdict.json`: per group, untuned against trained, with the 95% interval of the change.

## The judge

A word is flagged when the model's phonemes disagree with the reference in a consonant (articulation) or a vowel (length), as `score_phoneme_checker.py` counts. Tajweed-only marks are left out. Groups:

- **right**: words with no mark (5,876). Lower flagged is better.
- **vowel**: words the reviewer marked as a vowel slip (202). Higher caught is better.
- **letter**: words marked as a letter or wording slip (31, noisy: one word is 3 points). Reported only.

A round is kept when both hold against the untuned model:

- **Fewer false flags:** correct words flagged fall by at least `DROP_MIN` (3) points, and the 95% bootstrap interval of the fall (resampling whole recordings, paired) sits above zero.
- **Still hears vowel slips:** vowels caught fall by at most `VOWEL_FALL_MAX` (3) points.

Professional held-out phoneme error rate (every symbol, tajweed too) is reported for both models and is not part of the bar.

Untuned baseline, recorded: right flagged 22.9%, letter caught 54.8%, vowel caught 89.6%.

## Words

- **untuned**: `quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final-20260909` as published.
- **marked recordings**: `sobolev210/quran-recitation-errors` and `MuazAhmad7/Surah_Ikhlas-Labeled_Dataset`, reviewer-marked. Judged on, never taught; neither is a teaching source here (the word loop teaches on the second, this loop does not).
- **flagged**: a word the model's phonemes disagree with. **caught**: a marked word that was flagged.
- **held**: reciters and ayahs of the professional test; no training clip comes from either.

## Keys

- Kaggle: `~/.kaggle/kaggle.json` or the access token the CLI is set up with.
- Hugging Face: none (public sets only). Nothing is shipped.
