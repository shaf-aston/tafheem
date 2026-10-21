# The ear loop

Teach the Qur'an ear on Kaggle, keep it only if it beats the one served, and serve it from Oracle.
Every step runs from any checkout, on this PC or in a cloud session; nothing is copied by hand.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `ear/settings.py` | every knob, including `PLAN`, the list of candidates a run tries |
| 2. Run | `python backend/scripts/finetune_ear/cloud.py` | bundles `ear/` into one file, pushes it to Kaggle's free GPU, waits, fetches |
| 3. Judge | `backend/data/models/finetune-ear/verdict.json` | every candidate scored on the same held clips as the served and untuned ears |
| 4. Ship | `python backend/scripts/finetune_ear/cloud.py --ship` | uploads a kept `ear-tuned/` to the Hugging Face repo the pin names and moves the pin on master |
| 5. Serve | nothing to do | Oracle pulls master every 5 minutes and loads that revision (`services/recitation/listen.py` `_engine`) |

`--fetch` waits for the last run and fetches it. A run takes hours; watch it at the link `cloud.py` prints.
On Lightning.ai or Colab: `python -m ear.run` from this folder, on a GPU machine.

## Files

```
cloud.py               this PC: bundle, push, wait, fetch; --ship
kernel-metadata.json   which Kaggle notebook, GPU, attached data (Tarteel v1)
ear/                   runs on the GPU machine, in this order:
  run.py               the run: hold out tests, score untuned + served, walk PLAN, write verdict.json
  split.py             which clips are held for the judge and which are taught (v13's seeded split)
  sources.py           where clips come from: learners, professionals, Tadabur, everyayah replay
  sound.py             recordings as 16 kHz numbers; training clips made harder (speed, room, noise)
  text.py              the Qur'an's own text; matching a printed ayah; what the model can write
  ears.py              ears as faster-whisper folders: served, untuned, blended, trained
  weights.py           an ear's numbers: read/write model.bin, blend two ears, carry an ear back into training
  train.py             one LoRA round on a start model
  judge.py             hear every held clip, count words wrong, decide keep or not
  settings.py          every knob
checks/                run on this PC, no GPU:
  judge_mutants.py     the judge decides 12 known cases right, and 9 planted bugs in it are each caught
  weights_carry.py     weights.py changes nothing it should not (byte-exact round trip, exact carry)
```

## A run

1. Held clips are set aside: new voices, new ayahs, 200 professional clips by 7 reciters, Tadabur strangers. No ear learns from them.
2. The untuned model and the served ear are scored. The judge checks itself first: the served ear must not beat itself, and the untuned ear must not beat the served one.
3. Each `PLAN` step makes one candidate. `('blend', s)` moves the served ear `s` of the way back toward the untuned model, no training. `('train', None)` trains a LoRA starting from the ear held so far, so rounds build on each other instead of restarting.
4. A candidate that wins becomes the held ear; the next step is judged against it.
5. If the held ear is no longer the served one, it is saved as `ear-tuned/`; run step 4 of the table.

## The judge

Score = share of words wrong, lower is better, heard exactly as the app hears (faster-whisper, one guess).
A candidate is kept when all three hold, against the ear held so far:

- **Better somewhere:** by at least its margin (`MARGIN`: new ayahs 1.5 points, professional 1.0), and the 95% bootstrap interval of that gain sits above zero, so a lucky handful of clips cannot pass as a win.
- **Worse nowhere:** by more than that group's margin.
- **Not forgotten:** professionals at most `FORGET` (1.0) points worse than the *untuned* model; an ear already past that may stay, within noise, but not slip further. Anchoring to the untuned model stops small slips piling up round after round.

New ayahs is the only proof an ear learnt listening rather than text; professional is the proof it kept what it had.

## Words

- **untuned**: `tarteel-ai/whisper-base-ar-quran` as published, the model every ear descends from.
- **served** (champion): `recitation_trial_model` in master's `backend/config.py` (`repo@revision`). The app serves it and the judge scores it, so the two never differ.
- **held**: the ear a candidate must beat; the served one until a candidate wins. Also: the clips no run trains on.
- **blend**: two ears' numbers mixed, tensor by tensor; no training.
- **replay**: professional recitation (`tarteel-ai/everyayah`, reciters the test never hears) mixed into training so the ear keeps hearing what it was first taught.
- **ear-tuned**: the folder a winning run leaves, a CTranslate2 model faster-whisper loads.
- **revision**: one upload's Hugging Face commit; a new upload is a new name, so a server never serves a stale copy.

## Keys

- Kaggle: `~/.kaggle/kaggle.json` (or `KAGGLE_USERNAME` + `KAGGLE_KEY`).
- Hugging Face, to ship: a token allowed to create repos (`hf auth login`, or `HF_TOKEN`).
- Oracle: none; the repo is public.
