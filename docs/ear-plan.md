# Ear plan: repeats, full transcript, layered pronunciation

## Requirements
- **R1 Repeats stay put.** Saying "قد تبين الرشد من الغي" 3 times colours nothing after الغي. Test: vitest on 2:256, 1 to 6 copies, zero CHECK/WRONG past the phrase.
- **R2 Whole transcript visible.** Everything heard this page shows, wrapped, scrollable, even before the page is matched.
- **R3 Layered checking.** Letters (makhraj) → harakat → tajweed, each a separate module, trained and scored separately on held-out reciters, each switchable.
- **R4 No hard-coding.** Knobs in config, one mechanism per job.

## Where it is now (measured)
| Area | Today | Gap |
|---|---|---|
| Follower `lib/recite/follow.js` `lineUp` | edit-distance DP, costs in `config/recite.json:15` (wrong 4 < extra 5, page skips free) | A repeat has no step of its own. Each repeated word is cheaper as "wrong" on the next page word, so the page walks forward. Reproduced: 6 copies = 22 orange words, matching the screenshot. |
| Transcript `components/memorise/ReciteStrip.jsx:54` | `heard.slice(-6)`, one truncated line, only once `started` | Last 6 words only; vanishes when the line-up resets; repeats deduped by `joinWindows`; readings placed off-page dropped. |
| Letters | tuned whisper, scored on bare letters (`finetune_ear/ear/text.py`) | Word level, not per letter or makhraj. |
| Harakat | only the sureness score on the vowelled word (`whisper.scores`) | No per-vowel verdict. |
| Tajweed | nothing served; one unshipped spike `scripts/recitation/score_phoneme_checker.py` (vowel length 84% caught / 14% false) | Whole layer missing. |

## Outside view
- **Quran Muaalem** (obadx): one model, a phoneme head plus 10 tajweed-quality heads, compared against a reference built from the text. Phoneme error rate 5.8%, tajweed F1 75.8% (ghunna 87, qalqala 95, ikhfaa 45). Too big to retrain on a T4; can be run as-is.
- **Quranic-Phonemizer / quran-transcript**: text → expected phonemes with tajweed rule tags. This is the "answer key" every layer compares against.
- Madd is best judged by timing (held length against the reciter's own pace), not by a classifier.
- Iqra'Eval 2026 winner: F1 0.72 with a frozen XLS-R + CTC head, which is a T4-sized recipe.

## Design

### R1: repeats. Chosen: a "went back" step in `lineUp`
| Candidate | How | Score |
|---|---|---|
| **A. Back step in the DP (chosen)** | A heard word may restart at any page word already reached, cost `back` (config). Repeats, restarts mid-ayah and partial repeats all become one cheap jump. | One model, no patches, handles varied hearing (قدّ / قد). Cost: DP becomes O(heard × page) with a running minimum. |
| B. Collapse repeated n-grams before lining up | Pre-filter heard text | Fails when the ear spells a repeat differently; a second mechanism beside `joinWindows`. Rejected. |

`joinWindows`'s dedupe then becomes redundant and is deleted (one mechanism per job).

### R2: transcript. One owner
- `recitingSession` keeps `transcript`: every reading's raw text, in order, for the page; it is not filtered by `ofPage` and not deduped.
- `ReciteStrip` renders it whole, wrapped, scrolled to the end, whenever listening. "Heard" means only this; a mis-heard word on a mark is renamed `mark.instead`.

### R3: layered pronunciation
| Candidate | How | Score |
|---|---|---|
| **A. One shared engine, three layer judges (chosen)** | One phoneme/quality model (Muaalem first, run zero-shot) produces a timed phoneme lattice once per reading; each layer compares its slice against the answer key. | One expensive pass on the CPU server; layers stay separate in code; any layer can later get its own engine behind the same seam. |
| B. Separate model per layer | Three trainings, three passes | Three times the CPU per reading, which the ARM server cannot afford (one reading already costs more than real time). Kept as the swap path per layer, not the start. |

Backend layout:
```
backend/services/recitation/pronounce/
  __init__.py        check(audio, ayahs, layers) -> marks per word per layer
  expected.py        answer key: text -> phonemes + rule tags (phonemizer)
  engine.py          interface + factory; muaalem.py the first engine
  layers/
    letters.py       makhraj: consonant phonemes vs key
    harakat.py       vowel phonemes vs key
    tajweed/
      madd.py        held length / reciter pace vs rule counts
      ghunna.py  qalqala.py  idgham.py  ikhfaa.py
```
Training layout (shared skeleton from `finetune_ear`: split, judge, verdict, ship, pin):
```
backend/scripts/recitation/train/
  common/            split.py judge.py verdict.py ship.py (lifted from finetune_ear/ear)
  words/             today's finetune_ear
  letters/  harakat/  tajweed/<rule>/
```
Each layer has its own judge, its own held-out test and its own config block (`pronounce.json`: on/off per layer, thresholds). The frontend shows one layer's verdict per word, colours from `reciteColors.js`, so a layer is added without touching the follower.

## Measured: Muaalem spike (2026-10-27, this laptop, 4 CPU threads)
| Build | Seconds per second of audio | al-Fatihah 1:1-1:7 (everyayah, clean) |
|---|---|---|
| float32 | 0.70 to 0.91 | phonemes and tajweed qualities equal the answer key on all 7 |
| int8 (dynamic, Linear layers) | 0.52 to 0.67 | same, all 7 |

Package: `quran-muaalem` 0.2.2 needs `transformers<4.56`. Not yet measured: the Oracle ARM box (assume 2-3x slower, so near or over real time) and whether it catches real mistakes (needs the reviewer-marked recordings in `backend/data/recitation_checks`). Both gate step 4.

## Milestones (each its own commit, tested)
1. **R1**: back step in `lineUp` + vitest for 1 to 6 copies, plus the current follow tests unchanged.
2. **R2**: `transcript` in session + `ReciteStrip` full block; probe in the running app.
3. **R3 spike**: run Muaalem int8 on the Oracle CPU over 50 held clips; record time per second of audio and phoneme error. Go / no-go for engine A.
4. **R3 letters layer** end to end (service, route field, UI underline), scored on the held-out set.
5. Harakat layer, then madd, then the other tajweed rules, one at a time.
6. Lift `finetune_ear/ear` common parts into `train/common/`, move `finetune_ear` to `train/words/`.
