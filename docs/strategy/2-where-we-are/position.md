# Step 2. Where we are right now

Evidence for every claim: `audit-evidence.md` (code, with file:line references) and
`../4-research/market-prior-art-ip.md` (web, with URLs).

## 2.1 What Tafheem is today, in one breath

Type or tap Arabic → the app reads it **by the grammar books' rules, no AI** → shows the job of each
word, the tree, the root, the conjugation, four classical dictionaries, every place the root occurs in
the Qur'an, related hadith with their narrators. **Every answer says where it came from** (verified /
derived / guessed). Reciting is checked word by word.

Size: about 2,600 files, about 1,160 backend tests, about 800 frontend tests. Runs on one free Oracle VM.

## 2.2 Business proposition: where we stand

| Question | Honest answer today |
|---|---|
| Who is it for? | People who want to *understand* the Qur'an in Arabic, not only read or memorise it |
| What do they get that nobody else gives? | **Grammar analysis worked out by machine + proof for every answer.** Research found nobody combining this. The Quranic Corpus has the analysis but no learner product. Learner apps (Bayyinah, Understand Quran, Quranic) teach by video or flashcards and have no analysis. AI chatbots have no proof, and have lost trust (fabricated verses; Egypt's fatwa against AI tafsir) |
| Do we know who uses it? | **No.** No accounts, no analytics. Only a manual log parser (`deploy/usage.py`) |
| Can anyone pay? | **No.** No accounts, no payments |
| Can a learner see they are improving? | **Barely.** Quiz progress exists, but every visitor writes to one shared record |
| Can we legally sell it? | **Not checked.** See the licence flags below. This is the biggest business risk |
| Price anchors in the market | $4–11/month, $99/year (Understand Quran), $1,000 lifetime (Bayyinah). Big free players: Quran.com, Duolingo |

→ **Position:** a deep, unique, *trusted* engine that sits inside a product that cannot yet
remember a learner, show them their progress, or take money.

## 2.3 Usefulness to a real learner: where we stand

A learner's real journey is: **read an ayah → understand it → remember it → understand more next time.**

| Stage | Today | Grade |
|---|---|---|
| Read | Mushaf pages, word-by-word, audio, recitation check | Strong |
| Understand | I'raab, tarkeeb, sarf, roots, 4 dictionaries, tafsir, proof on every answer | **Best in market** |
| Remember | Quiz with FSRS spaced repetition (`review_schedule.py`), Grow paths, Memorise | Partial. Only the quiz records answers; the record is shared by everyone; a wrong answer is never explained |
| Grow ("I understand more of the Qur'an than last month") | Not measured anywhere | Missing |

→ **The gap is not "understand". The gap is "remember + see progress".** The app teaches a word
brilliantly once, then forgets the learner exists.

## 2.4 What already exists that the outside AI didn't know about

The brainstorm proposed several "novelties" that are already built, sometimes better:

- **Rules + model hybrid (its I2)** → built, in a *safer* order: the model proposes, the book's rules
  forbid impossible links *before* decoding (`syntax/mask.py`), and any word that breaks a stated
  rule is shown as a gap, not a guess (`syntax/teacher.py`).
- **Trust-by-sources (its I1)** → labelling built (35 sources in `data/sources.json`, a badge on every
  answer). Only 3 small features use an LLM, all marked "guessed". *Missing:* checking what the LLM says.
- **Explanation atoms (its I8)** → mostly built. Rules, reasons and signs are data
  (`data/nahw_rules/*.json`). Cards are put together from them (`iraab.py:50`).
- **Spaced repetition** → FSRS-6 built.
- **Unusual data assets:** narrator graph with teacher→student ties; 1,950 reviewer-marked recitation
  clips; 898 Arabic↔Urdu cognate / false-friend verdicts; 5 held-out grammar test sets.

## 2.5 Red flags found on the way (fix before anything fancy)

1. **Shared learner record**: every visitor is user `'local'`. `/api/progress/forget` wipes it for
   everyone (`routers/progress.py:32`).
2. **Licences unclear for commercial use**:
   - Quranic Arabic Corpus: GPL, but its pages also say "not for commercial purposes". Core grammar
     data depends on it.
   - sunnah.com narrator data: scraped.
   - Bayna Yadayk Anki decks: licence unstated.
   - "80% of Qur'anic Words" book: transcribed, licence unstated.
3. **No CI**: about 2,000 tests that nothing runs automatically.
4. **No recorded accuracy number** for i'raab. The trust story has no headline figure, even though
   `score_iraab.py` and 5 test sets exist.
5. **Wrong answers are thrown away**: the quiz keeps `picked` in the browser and never sends it
   (`QuizPanel.jsx:304-317`). Diagnosis is impossible without it.
