# The ear loop

Teach the Qur'an ear on Kaggle, keep it only if it beats the champion and catches slips better than the ear users have, then serve it from Oracle.
Every step runs from any checkout, on this PC or in a cloud session; nothing is copied by hand.

## Scoreboard

IqraEval (`../ear_bench/iqra.py`): 15 ordinary speakers, 955 planted slips, 3,719 words said right, never taught. A word is red when its least sure piece is under the app's cut (`wrong-below` in `frontend/src/config/recite.json`, 0.000256). Measured 2026-11-26.

| Ear | AUC (95%) | Slips caught | Red that were slips | F1 | Right words red | Caught at 7.2% red | Best F1 |
|---|---|---|---|---|---|---|---|
| untuned (`tarteel-ai/whisper-base-ar-quran`) | 0.917 (0.903-0.929) | 85% | 63% | 0.72 | 12.9% | 79.2% | 0.77 |
| champion `0034c0bd`, served | 0.918 (0.905-0.931) | 81% | 74% | 0.78 | 7.2% | 81.4% | 0.79 |
| **v28** (run 28, 2026-11-07) | **0.924** (0.912-0.937) | 78% | 84% | **0.81** | **3.7%** | **83.0%** | **0.81** |
| v34 (2026-11-14) | 0.924 (0.911-0.936) | 65% | 85% | 0.74 | 2.8% | 82.3% | 0.79 |

- **AUC**: how well the ear ranks a slipped word below a right one, over every cut (0.5 is chance, 1 perfect). The one number that does not depend on the cut.
- **Slips caught** (recall) and **red that were slips** (precision), at the app's cut. **F1** joins the two.
- **Right words red**: how often a correct reciter is told they slipped. The cost users feel most.
- **Caught at 7.2% red**: each ear at the cut that reddens as many right words as the champion did, so ears compare at one cost.

v28 was refused on 2026-11-07 under the old word rule (`worst-but-one`) and never re-graded after the rule became `worst` (#847). Re-graded against the champion, paired over clips: AUC +0.002 to +0.010, F1 +0.017 to +0.045, right words red -2.8 to -4.0 points, caught at 7.2% red +0.3 to +4.5 points, all sure; caught at the app's cut -2.2 to -5.3 points (the price of half the false red). The full `ear_bench` check (2026-11-26) says KEEP: on the marked recordings no sure harm, and right words red -0.8 to -2.2 points. It sits in `backend/data/models/finetune-ear/ear-tuned/`, ready for `--ship`.
Lesson: when the word rule or the cut changes, re-grade every kept candidate, not only the next one.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `ear/settings.py` | every knob, including `PLAN`, the list of candidates a run tries |
| 2. Run | `python backend/scripts/recitation/finetune_ear/cloud.py` | bundles `ear/` (plus the app's `spelling.py`) into one file, pushes it to Kaggle's free GPU, waits, fetches |
| 3. Judge | `backend/data/models/finetune-ear/verdict.json` | every candidate scored on the same held clips as the champion and untuned ears |
| 4. Ship | `python backend/scripts/recitation/finetune_ear/cloud.py --ship` | runs `ear_bench` (slip catching on IqraEval, ~20 min the first time for a new ear) against `recitation_model`; a DROP stops here. Otherwise uploads `ear-tuned/` and moves both pins on master: `recitation_model` in `config.py` and `CHAMPION` in `settings.py` |
| 5. Serve | nothing to do | Oracle pulls master every 5 minutes and loads that revision (`services/recitation/whisper.py` `_engine`) |

`--fetch` waits for the last run and fetches it. `--loop finetune_sounds` runs the sounds loop instead (`../finetune_sounds/README.md`). A run takes hours; watch it at the link `cloud.py` prints.
`verdict.json` is rewritten after every step and a winner is saved the moment it wins, so a crash hours in keeps both (`done: false`). It records the library versions and every knob in `settings.py` (`run.settings`).
Every fetched run's `verdict.json` (with the untuned and champion versions it was judged against) and its full log are kept in `backend/data/models/finetune-ear-runs/<date>/`.
To undo a ship: revert its "Serve the ear" commit on master. The message names the old version, and Hugging Face keeps every revision, so the server serves the old version again within 5 minutes.
The server logs `loaded model=<repo@revision>` at start, and `/api/health` `recite_sure` names the model in use.
On Lightning.ai or Colab: copy `backend/services/recitation/spelling.py` into `ear/`, then `python -m ear.run` from this folder, on a GPU machine.

## Files

```
RUNS.md                every run and probe, in order, with what it measured
cloud.py               this PC: bundle, push, wait, fetch; --ship; --tlog; --loop picks which loop folder
kernel-metadata.json   which Kaggle notebook, GPU, attached data (Tarteel v1)
ear/                   runs on the GPU machine, in this order:
  run.py               the run: hold out tests, score untuned + champion, walk PLAN, write verdict.json
  split.py             which clips are held for the judge and which are taught (v13's seeded split)
  parquet.py           finding Kaggle's attached files; reading big Hugging Face parquet sets cheaply, clips kept decoded (the sounds loop reuses it)
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

## Next levers

- **The sounds ear as a second vote (measured 2026-11-26, not built).** `services/recitation/sounds.py`'s model, the page's sounds lined up against what it hears (CTC forced alignment), each word scored by its least sure sound. On IqraEval alone: AUC 0.842, 40% caught at 7.2% red. Blended with the word ear (rank product): AUC 0.918 to 0.935, but 75% caught at 7.2% red, against 81%. With a light weight (word rank x sounds rank^0.3, weight picked on half the clips and tested on the other half, 10 splits): +1.9 points caught on average, -1.9 to +3.9 across splits. Too small and unsure to build yet; it needs no new model, since the server already runs this ear.
- **Real learner slips.** Every training source since v28 moved how sure the ear is, not how well it separates (`RUNS.md`). IqraEval is the only large set of real slips and must stay untaught.
- **A held tlog group**, so real phone audio is judged, not only taught.

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
