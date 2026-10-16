# The ear loop

Teach the Qur'an ear on Kaggle, keep it only if it beats the last one, and serve it from Oracle.
Every step runs from any checkout, on this PC or in a cloud session; nothing is copied by hand.

| Step | Command or file | Why it exists |
|---|---|---|
| 1. Change the recipe | `finetune_ear.py` (knobs at the top) | the only training code; git holds every version |
| 2. Train | `python backend/scripts/finetune_ear/cloud.py` | pushes to Kaggle's free GPU, waits, fetches |
| 3. Judge | `backend/data/models/finetune-ear/verdict.json` | the keep rule is fixed before the run; `keep` is the answer |
| 4. Ship | `python backend/scripts/finetune_ear/cloud.py --ship` | uploads a kept `ear-tuned/` to the private Hugging Face repo `<account>/quran-ear` and prints its `repo@revision` |
| 5. Serve | `recitation_trial_model` in `backend/config.py` | Oracle pulls master every 5 minutes and loads that revision (`services/recitation/listen.py` `_engine`) |

`--fetch` re-fetches the last run without training. A run takes hours; watch it at the link `cloud.py` prints.

## Words

- **ear-tuned**: the folder a run makes, a CTranslate2 model faster-whisper loads.
- **verdict**: the run's own before/after word error on held-out voices, ayahs and professionals.
- **revision**: one upload's Hugging Face commit; a new upload is a new name, so a server never serves a stale copy.
- **trial ear**: the model behind a learner's "Trial" listening; the main ear is `recitation_model`.

## Keys

- Kaggle: `~/.kaggle/kaggle.json` (or `KAGGLE_USERNAME` + `KAGGLE_KEY`).
- Hugging Face, to ship: a token allowed to create repos (`hf auth login`, or `HF_TOKEN`).
- Oracle, to serve the private repo: `RECITATION_HF_TOKEN` in the server's `.env`.
