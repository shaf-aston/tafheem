# The ear loop

Teach the Qur'an ear on Kaggle, keep it only if it beats the last one, and serve it from Oracle.
Every step runs from any checkout, on this PC or in a cloud session; nothing is copied by hand.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `finetune_ear.py` (knobs at the top) | the only training code; git holds every version |
| 2. Train | `python backend/scripts/finetune_ear/cloud.py` | pushes to Kaggle's free GPU, waits, fetches |
| 3. Judge | `backend/data/models/finetune-ear/verdict.json` | the new ear, the starting model and the served ear are scored on the same held clips; `keep` means it beat the served ear |
| 4. Ship | `python backend/scripts/finetune_ear/cloud.py --ship` | uploads a kept `ear-tuned/` to the public Hugging Face repo the pin names and moves the pin to that upload on master, from any branch |
| 5. Serve | nothing to do | Oracle pulls master every 5 minutes and loads that revision (`services/recitation/listen.py` `_engine`) |

`--fetch` waits for the last run and fetches it, without training. A run takes hours; watch it at the link `cloud.py` prints.

## The judge

1. Before training, the held clips are set aside; no ear learns from them.
2. The starting model, the champion and the new ear each write out every held clip, run exactly as the app runs them (faster-whisper).
3. Score = share of words wrong, lower is better, on four groups: new voices, new ayahs, professional, tadabur new voices.
4. Keep only if the new ear is at least `BAR` points better than the champion on new ayahs (the only proof it learnt listening, not text) and at most `SLIP` points worse on professionals. Both knobs sit at the top of `finetune_ear.py` and are fixed before the run, so a wobble cannot pass as a win.
5. Lost: `ear-tuned/` is deleted and the app keeps its ear. Won: run step 4.

A server fetches a new revision from Hugging Face once, on first use, and after that loads its own copy (`listen.py`), offline included.

## Words

- **ear-tuned**: the folder a run makes, a CTranslate2 model faster-whisper loads.
- **verdict**: words wrong for the starting model, the served ear and the new one on held voices, ayahs and professionals.
- **held**: the voices and ayahs no run trains on: v13's own seeded split (same data, same clips every full run), plus one Tadabur reciter in five by a fixed hash.
- **champion**: the served ear: `recitation_trial_model` in master's `backend/config.py` (`repo@revision`). The app serves it and the judge scores it, so the two never differ.
- **revision**: one upload's Hugging Face commit; a new upload is a new name, so a server never serves a stale copy.
- **trial ear**: the model behind a learner's "Trial" listening; the main ear is `recitation_model`.

## Keys

- Kaggle: `~/.kaggle/kaggle.json` (or `KAGGLE_USERNAME` + `KAGGLE_KEY`).
- Hugging Face, to ship: a token allowed to create repos (`hf auth login`, or `HF_TOKEN`).
- Oracle: none; the repo is public.
