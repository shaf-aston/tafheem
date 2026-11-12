# The ear loop

Teach the Qur'an ear on Kaggle, keep it only if it beats the champion and catches slips better than the ear users have, then serve it from Oracle.
Every step runs from any checkout, on this PC or in a cloud session; nothing is copied by hand.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `ear/settings.py` | every knob, including `PLAN`, the list of candidates a run tries |
| 2. Run | `python backend/scripts/recitation/finetune_ear/cloud.py` | bundles `ear/` (plus the app's `spelling.py`) into one file, pushes it to Kaggle's free GPU, waits, fetches |
| 3. Judge | `backend/data/models/finetune-ear/verdict.json` | every candidate scored on the same held clips as the champion and untuned ears |
| 4. Ship | `python backend/scripts/recitation/finetune_ear/cloud.py --ship` | runs `ear_bench` (slip catching on IqraEval, ~20 min the first time for a new ear) against `recitation_model`; a DROP stops here. Otherwise uploads `ear-tuned/` and moves both pins on master: `recitation_model` in `config.py` and `CHAMPION` in `settings.py` |
| 5. Serve | nothing to do | Oracle pulls master every 5 minutes and loads that revision (`services/recitation/whisper.py` `_engine`) |

`--fetch` waits for the last run and fetches it. `--loop finetune_sounds` runs the sounds loop instead (`../finetune_sounds/README.md`). A run takes hours; watch it at the link `cloud.py` prints.
`verdict.json` is rewritten after every step and a winner is saved the moment it wins, so a crash hours in keeps both (`done: false`). It records the library versions, the seed and every knob the run used.
Every fetched run's `verdict.json` (with the untuned and champion versions it was judged against) and its full log are kept in `backend/data/models/finetune-ear-runs/<date>/`.
To undo a ship: revert its "Serve the ear" commit on master. The message names the old version, and Hugging Face keeps every revision, so the server serves the old version again within 5 minutes.
The server logs `loaded model=<repo@revision>` at start, and `/api/health` `recite_sure` names the model in use.
On Lightning.ai or Colab: copy `backend/services/recitation/spelling.py` into `ear/`, then `python -m ear.run` from this folder, on a GPU machine.

## Files

```
cloud.py               this PC: bundle, push, wait, fetch; --ship; --tlog; --loop picks which loop folder
kernel-metadata.json   which Kaggle notebook, GPU, attached data (Tarteel v1)
ear/                   runs on the GPU machine, in this order:
  run.py               the run: hold out tests, score untuned + champion, walk PLAN, write verdict.json
  split.py             which clips are held for the judge and which are taught (v13's seeded split)
  parquet.py           reading big Hugging Face parquet sets cheaply, clips kept decoded (the sounds loop reuses it)
  sources.py           where clips come from: learners, professionals, Tadabur, everyayah replay, tlog, Iqra phrases
  spread.py            which few of many files to read; cloud.py uses it too
  sound.py             recordings as 16 kHz numbers; training clips made harder (speed, room, noise, rough channel)
  text.py              the Qur'an's own text, spelt as the app checks it (SAID); what the model can write
  ears.py              ears as faster-whisper folders: champion, untuned, blended, trained
  weights.py           an ear's numbers: read/write model.bin, blend two ears, carry an ear back into training
  train.py             one LoRA round on a start model
  judge.py             hear every held clip, count words wrong, decide keep or not
  settings.py          every knob
checks/                run on this PC, no GPU:
  judge_mutants.py     the judge decides known cases right, and planted bugs in it are each caught
  weights_carry.py     weights.py changes nothing it should not (byte-exact round trip, exact carry)
```

## A run

1. Held clips are set aside: new voices, new ayahs, 200 professional clips by 7 reciters, the same 200 through a rough channel, Tadabur strangers. No ear learns from them.
2. The untuned model and the champion are scored. The judge checks itself first: the champion must not beat itself, and the untuned ear must not beat the champion.
3. Each `PLAN` step makes one candidate. `('blend', s)` moves the champion `s` of the way back toward the untuned model, no training. `('train', None)` trains a LoRA starting from the ear held so far, so rounds build on each other instead of restarting.
4. A candidate that wins becomes the held ear; the next step is judged against it.
5. If the held ear is no longer the champion, it is saved as `ear-tuned/`; run step 4 of the table.

## What it is taught

- Learners (Tarteel v1), professionals (everyayah replay), Tadabur, and tlog: real app users. A tlog clip is taught only when large-v3-turbo hears exactly the ayah's letters, so a slip is never taught as right (`TLOG_*`).
- **Iqra phrases** (2026-11-08, `IQRA_*`): `Iqra_TTS` (synthetic voices saying Qur'an phrases, ~half with a planted slip) is taught with `sentence_aug`, the text really said, so a slip is a labelled mistake the target contains; its clips of held ayahs make the `spoken slips` group (recorded, not a keep rule). The ayah is found from `sentence_ref`. `Iqra_train` (real voices) adds Qur'an phrases (half, never from held ayahs) and everyday fusha (the rest, with tashkeel). Phrases the IqraEval bench says are left out: `cloud.py` writes them into the bundle as `bench_phrases.json`, and a run without it stops.
- Targets are spelt `as_heard`, the spelling the app scores in, so training and checking agree on every word.
- `ROUGH_P` of training clips go through a worse channel: low-bitrate opus, phone band, old tape with hiss, or clipping. The `rough professional` held group measures that.

## The judge

Score = share of words wrong, lower is better, heard exactly as the app hears (faster-whisper, one guess).
A candidate is kept when all three hold, against the ear held so far:

- **Better somewhere:** by at least its margin (`MARGIN`), and the 95% bootstrap interval of that gain sits above zero, so a lucky handful of clips cannot pass as a win.
- **Worse nowhere:** by more than that group's margin.
- **Not forgotten:** professionals at most `FORGET` (1.0) points worse than the *untuned* model; an ear already past that may stay, within noise, but not slip further.

Words wrong never measures slip catching, so `--ship` asks `ear_bench` before anything is served.

## Words

- **untuned**: `tarteel-ai/whisper-base-ar-quran` as published, the model every ear descends from.
- **champion**: `CHAMPION` in `ear/settings.py` (`repo@revision`), the best tuned ear so far. Each run must beat it.
- **served**: `recitation_model` in `backend/config.py`, the one checker users get. A ship moves it and `CHAMPION` together.
- **held**: the ear a candidate must beat; the champion until a candidate wins. Also: the clips no run trains on.
- **blend**: two ears' numbers mixed, tensor by tensor; no training.
- **replay**: professional recitation (`tarteel-ai/everyayah`, reciters the test never hears) mixed into training so the ear keeps what it was first taught.
- **rough**: a clip as a worse channel carries it (`sound.rough`).
- **ear-tuned**: the folder a winning run leaves, a CTranslate2 model faster-whisper loads.
- **revision**: one upload's Hugging Face commit; a new upload is a new name, so a server never serves a stale copy.

## What we learnt (measured)

- **Training on correct text hides slips.** It strengthens what the model expects to hear, so it writes the expected word over a real slip. Slip AUC on slips never trained on: untuned 0.618, served 0.588 (2026-11-03, `ear_bench` + RetaSy, 743 clips, 83 reciters). Words wrong falling does not mean slips are caught better; that is why `--ship` asks `ear_bench`.
- **Synthetic text slips are dead.** True text vs a one-word mutant differ by a median 20 to 24 nats on pro clips, so a margin loss never fires and a mutant benchmark is passed by memory.
- **The judge reads letters only** (`bare()` strips marks), so vowel slips are invisible to it; training targets are vowelled.
- **Honest tests hold out voices AND ayahs.** Judge on new ayahs and professionals, never new voices alone: run 7 memorised 45 ayahs' text. Keep v13's seeded split (`split.py`); a hash split put 4 in 5 training clips into the tests.
- **Judge against the served ear, not untuned:** the old gate would have shipped a worse pilot.
- **Data coverage is the lever, not layers or rank** (2026-10-02 sweep all within noise). A better step needs a new-ayahs gain, i.e. more distinct ayahs, not more voices.
- **tlog labels are only the ayah meant** (from the file name). Probe 2026-11-04: the local ear changes the text on 84% of shard 0 clips (many off-ayah or noise); on 300 Groq-labelled clips base AUC 0.800, tuned 0.788, no gain. A human-checked set is needed before any claim.
- **Planted slips hide from ayah lookup:** a slipped sentence matches no ayah, so a source of slips must carry the meant text beside the said text (`Iqra_TTS` has `sentence_ref`); looking the ayah up from the said text dropped every slipped clip (2026-11-08).
- **More hours of the same ayahs do not reach new ayahs** (2026-11-05: 64 h with tlog and the rough channel gained new voices 1.5 and Tadabur 2.0 points, new ayahs 0.46, within noise).
- **Untuned base beats every tuned ear on professionals** in most runs; FORGET guards it.

## Results so far (words wrong %, untuned / champion / new)

| Run | New voices | New ayahs | Pros | Tadabur | Decision |
|---|---|---|---|---|---|
| 2026-10-04 v13 | 24.0 to 15.6 | 24.2 to 18.0 | 4.98 to 4.30 | | kept, served |
| 2026-10-18 full Tadabur | 21.3 / 13.2 / 11.7 | 20.8 / 14.5 / 13.8 | 0.71 / 2.13 / 2.84 | 5.4 / 8.4 / 3.5 | rejected, new-ayahs gain 0.67 < 1.5 |
| 2026-10-21 blend + replay | 21.3 / 13.2 / 12.5 | 20.8 / 14.5 / 13.1 | 0.44 / 1.81 / 0.79 | 5.1 / 6.4 / 5.9 | blend 0.25 kept (`quran-ear@0034c0bd`); .5 and .75 lost new ayahs; replay-trained not past margin |
| 2026-11-05 tlog + rough channel, 21,724 clips (64 h) | 21.3 / 12.5 / 11.0 | 20.8 / 13.1 / 12.6 | 0.44 / 0.79 / 0.62 | 5.1 / 5.9 / 3.9 | rejected: trained better everywhere but new ayahs only 0.46 (95% -0.62 to 1.39) < 1.5; blends .25 to .75 no gain, .5 and .75 lost new ayahs. Rough pros 0.79 / 1.28 / 0.97 |
| 2026-11-06 run 26, more Tadabur, 27,926 clips (84 h) | 21.4 / 12.8 / 11.5 | 22.1 / 13.9 / 13.4 | 0.44 / 0.79 / 0.79 | 4.5 / 5.8 / 3.3 | thrown away on Kaggle: new ayahs +0.58 < 0.75, never slip-tested. Prep 1.7 h (was 3.3), training 3 h, 5.5 h in all. The Kaggle judge now hands back any ear not worse, and `--ship`'s ear_bench decides; rerun sent the same day |
| 2026-11-07 run 28, run 26 rerun with tlog from `TLOG_COPY` (875 tlog clips) | 21.4 / 12.8 / 11.4 | 22.2 / 13.9 / 13.6 | 0.44 / 0.79 / 0.75 | 4.5 / 5.8 / 3.2 | Kaggle kept (new voices +1.5, Tadabur +2.6, both sure). ear_bench DROP against both: IqraEval AUC 0.891 vs served 0.890 (gain -0.006 to +0.010) and champion 0.896 (-0.010 to 0.000). At the app's cut 0.1 fewer right words red (5.7% vs 7.2% champion, 12.3% served) but fewer slips caught (71% vs 73%). Trains words wrong down, not slip separation. 6.5 h in all. Same day, the champion against the served ear at cut 0.1: KEEP (F1 0.68 to 0.73, red 12.3% to 7.2%), served the same day with the cut split into `wrong-below` 0.1 and `said-at` 0.95 |
| 2026-11-09 v31, Iqra slips share 0.1 | 21.4 / 12.9 / 11.7 | 22.1 / 13.9 / 13.4 | 0.44 / 0.79 / 0.79 | 4.5 / 5.8 / 2.4 | Kaggle kept; ear_bench DROP: IqraEval AUC 0.899 vs 0.896 (-0.002 to +0.009). At cut 0.1 red 7.2% to 4.4%, slips caught 73% to 67%. Spoken slips 75.5 to 56.4 |
| 2026-11-09 v32, slips doubled (`IQRA_SLIPS_SHARE` 0.2, 6 shards) | 21.4 / 12.8 / 11.8 | 22.1 / 13.9 / 13.5 | 0.44 / 0.79 / 0.84 | 4.5 / 5.8 / 3.0 | Kaggle kept; ear_bench DROP: IqraEval AUC 0.897 vs 0.896 (-0.005 to +0.006). At cut 0.1 red 7.2% to 4.7% (sure), caught 73% to 68%. Twice the slips moved nothing: training shifts where the cut falls, not how well slips are told apart. Next: read the slips the champion misses by kind before another run |

Scoring changed after v13 (faster-whisper, pause signs stripped, 600-clip cap), so later rows sit lower; the ratios match.

**What the champion misses (0034c0bd, IqraEval, cut 0.1, 2026-11-10).** 955 slips, 73% caught. By kind: swapped consonant 503, 93% caught; wrong short vowel 182, 72%; **dropped consonant 149, 22% (116 of the 260 misses)**; dropped vowel 59, 37%; long/short vowel 9, 0%. A dropped consonant with a sukun (next sound a consonant) is almost never caught: ل 0/19, ض 0/10, ذ 0/10, د 2/19, ع 1/10. The ear scores each written letter, and a silent letter that is skipped leaves its neighbours to carry its piece. Next run targets that, not more slips of every kind: train on clips with a sukun letter cut out, and check whether the word rule (`worst-but-one`) hides a single missing letter.

**It does (same data, same ear).** Rule, AUC, slips caught / dropped consonants caught at 7.2% red: `worst` 0.918, 81% / 47% (cut 2.6e-4); `worst-but-one` 0.896, 73% / 22% (cut 0.10); `mean` 0.888, 62% / 32%. At 4.7% red: `worst` 77% / 37%, `worst-but-one` 70% / 19%. The gap (0.022) is about 4x the AUC noise. Not switched yet: `worst` was dropped because it reddened right words in real app recordings, and its cut sits near zero, so one small shift in the ear moves it a lot. Switch only after the marked app recordings agree. **Switched 2026-11-10 (#847):** on the marked recordings never trained on, no sure harm (ear_bench keep rule); the cut is 0.000256.

**v32 re-graded under `worst` (2026-11-10): still DROP.** IqraEval AUC gain -0.001 to +0.008, F1 at the cut surely lower (0.731 vs 0.777).

**Why more Iqra slips cannot fix it.** In `Iqra_TTS` a slipped clip holds 3 to 6+ changes (2 shards, 6,153 slipped clips: 1 change 167, 2 changes 509, 3+ the rest); one clean dropped unvowelled letter alone: 9. IqraEval plants one slip per clip. So v31/v32 were taught garbled phrases and tested on single slips, and reweighting toward dropped letters has almost nothing to weight. The next lever is single-slip clips made from clean ones: cut one silent letter's sound out of a clean recording, at times from a letter aligner, and teach what is then said. Not built.

**Letter by letter (2026-11-10, `ear_bench/letters.py`).** IqraEval holds only 97 distinct slips (each said by ~10 of its 15 speakers), so a letter-and-vowel cell there is one slip, not a measure of the letter. By vowel it still shows the shape: a dropped letter with sukun after kasra 28% caught, after damma 0% (10 clips, one slip), after fatha 60%; a damma or kasra swapped 59 to 67%, a fatha 84%; swapped consonants 97%. Right letters are wrongly red about 1% of the time; the reddest (ى 29%, ءَا, لرَّأْسُ, بْنَ) are IqraEval spelling quirks (it writes فِى where the page writes فِي), not hearing.
So `ear_bench/spliced.py` makes a per-letter set: professional ayahs by the test reciters, one sound cut out or swapped at a place the phoneme ear timed, kept only if at that spot the old sound is gone and a swapped-in one is heard (judging the whole ayah fails: the phoneme ear restores a missing letter from context just as the word ear does). `teach` makes the same from other reciters and ayahs, with what each clip now says, for v33 (`LONE_*`, replacing `Iqra_TTS`'s many-slip clips).
First run (2026-11-11, ear 0034c0bd, 4,093 slips from 900 ayahs): 5% caught, against 47-97% on IqraEval. Not a scoring fault: word counts line up on every clip, and right letters are red 0% of the time. The ear does hear the change. The slipped word's median sureness falls from 0.9995 to 0.97 for a dropped or swapped letter, 0.86 for a swapped vowel and 0.30 for a wrong length, but almost never below the cut 0.000256. One sound changed inside a fluent professional ayah is far subtler than a learner's slip, and the word ear's sense of Arabic fills it back in. By kind: vowel length 8%, vowel swapped 3%, letter dropped 4%, letter swapped 2%. No vowel context reaches 12%. Treat this set as a hard floor for comparing ears with each other, not as the rate app users see.
**v33 (2026-11-11): lone slips at 0.2, capped at 1,200 a kind (4,435 clips used), IQRA_SLIPS_SHARE 0.**
Kaggle kept it, with fewer words wrong: new voices -1.2 points, tadabur -3.5, spoken slips -4.2, nothing worse. `ear_bench` refused it (DROP). On IqraEval at the app's cut, F1 fell from 0.78 to 0.75: recall 0.81 to 0.66, precision 0.74 to 0.85, right words red 7.2% to 3.0%. AUC rose from 0.918 to 0.924, and at its own best cut (0.002 against 0.000) its F1 is 0.79, level with the champion. So it ranks slips no worse, but it is surer of words overall, and the shared cut now lets slips through. Not served. A pure cut move would only tie, so the next run needs a real ranking gain, not a new cut.

**Where the champion is deaf, letter by letter (2026-11-12, `letters.py --set spliced`, new `heard` column).** Caught at the cut is 0 to 11% in every spliced cell, so it cannot rank letters; `heard` (the slipped word under half as sure as the same word in the untouched recording) can. By kind: vowel length 47% heard, vowel swapped 27%, letter swapped 22%, letter dropped 21%. Deafest: a dropped letter carrying damma 6% or kasra 11%, a letter swapped with sukun after damma 4%, a swapped kasra vowel 22%. By letter (all kinds): ه 17%, ن 19%, ذ 23%, ظ 24%, ع 24%; best ش 68%, ج 60%. Cells at 0% heard (20 slips each): ه swapped under kasra, ن dropped with sukun after kasra, ه kasra to fatha. Every past run moved how sure the ear is, not how well it separates (v28, v31, v32, v33 AUC within noise), because the said text alone stops teaching once the said word wins, while the app asks about the page word and needs it under 0.000256.

**v34 (2026-11-12): v33's data unchanged, plus the slip push** (`train.py` `SlipTrainer`, `SLIP_BELOW`, `SLIP_WEIGHT`). On each lone slip the ear is also asked about the page word, as the app asks, and its least sure piece from where the said word parts from it is pushed under 1e-4. One change against v33, so the result reads as the push's. Checked first on this PC (untuned base, CPU): taught 195 lone clips, measured on 150 slips of other ayahs against their untouched twins. Slips noticed (slipped word under half as sure as its twin): 49% before, 75% taught plainly, 82% with the push; median sureness gap -0.6 to -3.5 plainly, -6.3 with the push; right words unchanged in both. A first try at 40 slips showed the reverse (52% vs 50%), within its noise.

## Next levers (research 2026-11-05)

**Read first (ear_bench on IqraEval, 2026-11-06).** `ear_bench` now decides on IqraEval (`ear_bench/iqra.py`: 955
planted slips, 15 ordinary speakers, never trained on); the 35 slips of the old marked recordings can only refuse.

| | served (OdyAsh base) | champion (`0034c0bd`) |
|---|---|---|
| IqraEval AUC | 0.888 (0.871 to 0.902) | 0.896 (0.880 to 0.911), sure gain +0.003 to +0.016 |
| IqraEval at cut 0.95: slips caught / right words red | 87% / 31.1% | 85% / 26.8%, surely fewer red |
| old set (35 slips) right words red | 5.1% | 8.1%, surely more: DROP |

Training did help ordinary voices a little, and hurt the old professional set; the keep rule drops a mixed result.
The bigger finding is the cut: 0.95 was set on professional recordings (2.9% right words red there) and marks 31% of
right words red on ordinary voices, 5% to 83% by speaker. The least sure word is the slipped one 75% of the time
(within one word 90%). Lower cuts on IqraEval: 0.5 gives 82% caught / 19% red, 0.05 gives 75% / 11%; a cut set from
each reciter's own words gained 3 points on unseen speakers, within noise. The old single cut `sure-at` also counted a word the
transcript missed as said. Measured (120 clean IqraEval clips, a word added to the text that was never said, OdyAsh): at 0.95 it passes 1% of skipped random words, 3% of short particles, 0% of a repeated word; at 0.2: 3%, 4%, 11%; at 0.1: 3%, 4%, 18%. So the two jobs want different cuts: passing a missed word stays near 0.95, marking red wants a low one. Poor sound (a third of IqraEval, phone band at 12 kbps, pink noise at 10 dB SNR): AUC barely moves (0.884 clean, 0.873 noise), but noise raises right words red: served ear at 0.95 52%, at 0.1 24% (clean 14%), slips caught 79%. The champion stays 8 to 10 points fewer red at 0.1 in every condition. So recite.json has two knobs now: `wrong-below` 0.1 (red) and `said-at` 0.95 (a missed word passed). Forgiving the last word's final
piece did not help (right words red unchanged): stops are not why last words are red more often (48% vs 30%).

0. **See small steps first (done 2026-11-05).** One run gains about half a point on new ayahs; 600 test clips gave ±1.0 and the margin was 1.5, so no single step could ever pass and gains could not stack run by run. `TESTED` 600 to 1,800 (about ±0.6, ~45 min more) and the new-ayahs margin 1.5 to 0.75. The interval low end must still sit above zero, and `--ship` still asks `ear_bench`. Then each run changes one knob and keeps any sure gain.
0b. **More Tadabur, faster prep (2026-11-06, next run).** Tadabur covers every ayah in 600+ voices; we taught 16 h of its 1,400. 8 files held 7,478 usable rows, so 4,796 were taught of 6,693 wanted: `TADABUR_SHARDS` 8 to 28, `TADABUR_SHARE` 0.25 to 0.4 (~14,600 clips), replay and tlog shares 0.1 so their counts stay as they were. Blends dropped from `PLAN`. Prep was 3.3 h: filters unpacked every clip's sound to read its name (~45 min, now `input_columns`), and ffmpeg decoded one clip at a time (~5 a second, now one per CPU, `sound.decoded`). After run 26 was sent, tlog's clips go through `sound.decoded` too, so they decode while the checker listens on the card, and it stops downloading files once it has enough. Fetched clips are kept decoded at 16 bits, a sixth of Tadabur's stored size. Proven to pick the same clips in the same order. Training grows from ~9,000 s to ~14,000 s; the run should still finish well inside Kaggle's 12 h.
1. **A sound-only second checker.** The best Qur'an mistake detectors (IQRA 2026 challenge, arXiv 2603.29087, top F1 about 0.72) judge from sound alone (CTC), with no text expectation. A word is red when either checker doubts it.
2. **More real slips (done 2026-11-06).** `IqraEval/Iqra_Extra_IS26` is in `ear_bench` (AUC range about ±0.015, against ±0.1 on the old 35 slips). `IqraEval/QuranMB.v2` is audio only, its labels hidden, so no use. The cut is set (`wrong-below`, see Read first). Left: real handset and room noise, not synthetic. Never train on IqraEval, or the bench stops measuring anything.
3. **A held tlog group**, so real phone audio is judged, not only taught.
4. Open from review: `new voices` is not speaker-disjoint for Tarteel v1 (no speaker ids); runs report words wrong only, not slip AUC. (`ear_bench` now judges F1 and false red on 95% ranges too, 2026-11-05: surely lower or surely redder refuses, noise neither passes nor blocks.)

## Machines

This PC and the Oracle server have no GPU (Oracle `RECITATION_THREADS=2`); training runs only on Kaggle.

Traps:
- Kaggle runs at most 2 GPU sessions at once; a third push fails "Maximum batch GPU session count of 2 reached". The CLI cannot cancel a run, and the web Stop button shows a CAPTCHA. Cancel through the SDK: `api.build_kaggle_client().kernels.kernels_api_client.cancel_kernel_session(ApiCancelKernelSessionRequest(kernel_session_id=<id>))` (`kagglesdk`). The id is `run.id` from the signed-in page's `POST /api/i/kernels.KernelsService/ListKernelVersions` (body `{kernelId, pageSize}`, header `x-xsrf-token` from the `XSRF-TOKEN` cookie).
- `kaggle kernels logs` prints nothing while a run is live; the SDK's `get_kernel_session_logs_stream` (user and slug, no version) replays the live log.
- `--ship` runs ear_bench for over 10 minutes. A shell timeout kills `cloud.py` but leaves its ear_bench child running; stop the child by PID before shipping again.

## Keys

- Kaggle: `~/.kaggle/kaggle.json` (or `KAGGLE_USERNAME` + `KAGGLE_KEY`).
- tlog on Kaggle: the run reads a private copy, `shafeinhashmi/tlog-sample` (`TLOG_COPY`), not Hugging Face. tlog is gated and Kaggle never gives a run sent from the command line its secrets (staff: no API for secrets, github.com/Kaggle/kaggle-cli/issues/582; measured `ConnectionError`, 2026-11-05 to 11-06). `cloud.py --tlog` makes it from this PC's own Hugging Face login: the 30 files `TLOG_SHARDS` spreads over, 200 random clips each (`TLOG_TRY`, seed 19: the clips every run since 2026-11-04 heard), ~1 GB up. Run it again after changing either number. Without it the run stops in its first minute.
- Hugging Face, to ship: a token allowed to create repos (`hf auth login`, or `HF_TOKEN`).
- Oracle: none; the repo is public.
