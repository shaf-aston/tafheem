# Brief: turn the Tafheem strategy review into a visual page

## Your job
Build **one visual web page (an artifact)** that shows the strategy review below, so the founder can
understand it at a glance.

**Who reads it:** the founder. They want simple words, like explaining to a 12-year-old, short
lines, arrows (→), and no jargon.

**Source files** (repo `shaf-aston/tafheem`, branch `claude/intelligent-hawking-o2qgop`, folder
`docs/strategy/`). Read these if you need more detail; everything needed is already in this brief.
- `README.md` (summary + decisions)
- `5-picks/*.md` (detail per pick)
- `3-assessment/impact-vs-complexity.md` (scores)
- `6-architecture/three-layers.md` (design)
- `2-where-we-are/audit-evidence.md`, `4-research/market-prior-art-ip.md` (raw evidence; don't put these on the page)

## What the page should look like

One page, scroll top to bottom, in this order:

1. **Hero**: one line: "Best at *understanding* an ayah → now make learners *remember* and *see progress*."
2. **Where we are**: two columns, "Great at" and "Missing", plus 5 red-flag chips.
3. **The 16 ideas**: cards grouped into Built already / Good, not built / Bad fit.
4. **Value vs effort chart**: a 2×2 quadrant chart (data in section C). Hover shows the idea's name and score.
5. **Research**: a competitor table + 4 short "what protects us" points.
6. **Top picks 0 → 3**: a numbered timeline or stepper, each pick expandable.
   - Pick 1 gets the most space and includes the "wrong options = mistake test" table.
7. **The 3 layers**: a simple stacked diagram, Facts → Rules → Words (AI).
8. **Parked ideas**: a small table with "start when…".
9. **Decisions D1–D6**: cards, each with a recommendation. Nice to have: a yes/no toggle on each,
   remembered in the browser.

**Design rules:**
- Calm and clean, light and dark mode, works on a phone.
- Big headings, short text, plenty of space.
- Arabic words right-to-left, in an Arabic-friendly font (e.g. Amiri or Noto Naskh Arabic).
- Colour per pick:
  - Pick 0: grey
  - Pick 1: green (the star ⭐)
  - Pick 2: blue
  - Pick 3: purple
- **No made-up numbers.** Use only what is in this brief.

---

## A. Where we are

**Great at:**
- The app works out Arabic grammar using the grammar books' rules, not AI.
- Every answer shows its source, labelled checked by a person / made by a fixed rule / guessed by AI.
- Nobody else combines this.

**Missing:**
- The app can't remember a learner.
- No progress view for the learner.
- No accounts, no payments.

**Red flags:**
1. Everyone shares one learner record, and "forget" wipes it for everyone.
2. Data licences are unclear for selling:
   - Quranic Arabic Corpus ("not for commercial use")
   - sunnah.com narrator data (scraped)
   - Bayna Yadayk flashcard decks
   - the "80% words" book
3. About 2,000 tests, but nothing runs them automatically (no CI).
4. No grammar accuracy number is written down.
5. When a learner picks a wrong answer, which one they picked is thrown away.

**Size today:** about 2,600 files, about 1,160 backend tests + about 800 frontend tests, runs on one
free server.

## B. The 16 ideas

**Built already** (the outside AI didn't know):
- Rules + small AI model together (built in a safer way)
- Showing the source of every answer
- Explanations made from stored pieces
- Spaced repetition (FSRS)

**Good, not built:**
- Know *why* a word was wrong and fix it
- Word meaning per ayah (word graph)
- Check what the AI says
- Coverage meter
- One record per learner
- Hadith chain check
- Teacher mode
- Tajweed checking
- Offline phone app
- Payments

**Bad fit:**
- The big server stack (Postgres, Redis, Kafka, vector database): slower for one person
- A separate "pedagogy router": too vague
- A teen safety engine: already covered by the design

## C. Value vs effort scores

Score = (helps learner + helps business + hard to copy) × fits what we have ÷ effort.
Effort: S = 1, M = 2, L = 3, XL = 4.

| Idea | Learner | Business | Hard to copy | Fit | Effort | Score |
|---|---|---|---|---|---|---|
| Coverage meter | 5 | 4 | 2 | 5 | S | 55 |
| One record per learner | 4 | 5 | 1 | 5 | S | 50 |
| AI answers checked against proof | 4 | 4 | 4 | 5 | M | 30 |
| Hadith chain check | 2 | 2 | 4 | 5 | S–M | 27 |
| Explanation pieces (ids + links) | 3 | 2 | 3 | 5 | S–M | 27 |
| Know why wrong + fix it | 5 | 4 | 4 | 4 | M | 26 |
| Word graph with meanings | 4 | 3 | 5 | 4 | L | 16 |
| Rules + model pick-best | 2 | 1 | 2 | 5 | M | 12.5 |
| Pedagogy router | 3 | 2 | 1 | 4 | M | 12 |
| Offline phone app | 3 | 2 | 1 | 3 | M | 9 |
| Teen safety engine | 2 | 3 | 1 | 3 | M | 9 |
| Tajweed checking | 4 | 4 | 3 | 3 | XL | 8 |
| Teacher mode | 3 | 5 | 3 | 2 | L | 7 |
| Payments | 1 | 4 | 1 | 2 | L | 4 |
| Big server stack | 1 | 1 | 0 | 1 | L | <1 |

Quadrant positions (x = effort 0–1, y = value 0–1):

| Idea | x | y |
|---|---|---|
| Coverage | .12 | .85 |
| Learner record | .10 | .70 |
| Proof-checked AI | .40 | .80 |
| Know-why engine | .45 | .88 |
| Explanation pieces | .25 | .55 |
| Hadith check | .28 | .52 |
| Word graph | .70 | .80 |
| Teacher mode | .75 | .70 |
| Tajweed | .92 | .72 |
| Pick-best | .45 | .30 |
| Router | .50 | .38 |
| Offline | .50 | .35 |
| Payments | .72 | .38 |
| Big stack | .80 | .08 |

Quadrant labels: top-left "Do first", top-right "Big bets", bottom-left "Fill-ins", bottom-right "Avoid".

## D. Research

**Competitors:**

| Who | Good at | Missing |
|---|---|---|
| Quran.com (free) | word-by-word translation, tafsir, learning plans | grammar analysis |
| Tarteel | recitation mistakes | understanding, grammar, full tajweed |
| Bayyinah / Understand Quran | video courses, common words | analysing any ayah, proof |
| Quranic Arabic Corpus | grammar data | it's a research site, not for learners |
| AI chatbots | answer anything | trust (made-up verses; a fatwa against AI tafsir) |

**Prices people pay:** $4–11 a month, $99 a year, $1,000 lifetime.

**UK madrasah software:** many admin tools, none teaching grammar → a possible gap, not proven.

**What protects us:**
1. Patents are a weak fit (about £4–16k, and likely refused for teaching methods).
2. Database right protects our checked data for 15 years.
3. Keep our rules secret (don't ship the bulk data to phones).
4. Trust + published accuracy + teacher community.

**Biggest risk:** data we can't use commercially.

## E. Top picks (build order 0 → 1 → 2 → 3)

**Pick 0: Foundation** (about 1–2 weeks)
- Each learner gets their own record (an anonymous id).
- Save which wrong answer was picked.
- Run the tests automatically.
- Measure and publish grammar accuracy.
- Check every data licence.
- → Nothing else can be measured without this.

**Pick 1 ⭐: Smart vocabulary engine + coverage meter**
- **What the learner gets:** "I know 62% of Surah Mulk's words, up from 41%". When they're wrong, the app knows why and fixes exactly that.
- **The trick:** each wrong option is chosen on purpose to test one kind of mistake → the option they pick *is* the diagnosis, with no AI guessing.
- **The loop:** ask → wrong → spot the mistake type → tiny fix (10–20 s) → 1 re-check question → update memory → pick what's next.
- **What's next:** words due for review first, then the unknown word that raises coverage most in the learner's chosen surah.
- **Coverage** = how often the learner's known words appear in the surah ÷ total words in the surah.
- **Is it working?** Re-check pass rate, the same mistake coming back less often, coverage growth per week.
- **Protection:** the mistake types + fix rules stay secret, and the mistake data builds up over time.

Mistake-test table (Arabic right-to-left):

| Wrong option is… | Example | Fix shown |
|---|---|---|
| same root | عِلْم knowledge vs عَالِم scholar | root family card |
| same pattern | مَكْتُوب vs مَعْلُوم | pattern card |
| other meaning of the same word | ضَرَبَ "strike" vs "give an example" | two ayahs side by side |
| look-alike (only the dots differ) | نَصَرَ vs نَظَرَ | dot/sound contrast with audio |
| **Urdu false friend** (unique to us) | آخَر "other" vs Urdu "at last" | "Urdu says X, Qur'an says Y" |
| close synonym | خَوْف vs خَشْيَة | contrast pair |
| particle mix-up | مَا "what" vs مَا "not" | the particle's job |

**Pick 2: Proof-checked answers**
- The rules decide what's true; AI only makes the wording friendlier.
- AI runs ahead of time, not when the learner asks → instant, and always the same answer.
- A checker makes sure every term in the AI's text is in the proof. If one isn't → show the plain version instead.
- No open "ask anything" chatbot.
- → "Tafheem never makes things up", and we can prove it.

**Pick 3: Word meanings per ayah (word graph)**
- Tap a word → "it means *this* here", plus its family, look-alikes and false friends.
- We have a human translation of every word in every ayah → group them per word → each group is one meaning → a person approves it.
- Start with the 382 most common words (about 80% of what learners meet).
- → Our deepest protection: our own checked data, covered by database right.

## F. The 3 layers (draw as stacked boxes, arrows going up)

- **WORDS (AI):** only friendlier wording, checked, done ahead of time
- **RULES:** grammar engine, mistake finder, memory, coverage, proof checker
- **FACTS:** Qur'an data, word graph, book rules; built ahead of time, each with its source

Side label: "Learner record runs through all 3."

Two notes:
- **Fast:** every request is a lookup and never waits for an AI.
- **Trusted:** facts have sources, rules have book pages, AI can't add claims.

## G. Parked

| Idea | Start when… |
|---|---|
| Teacher mode | ~10 madrasah teachers say they'd pay |
| Tajweed | more recitation data + a patent check |
| Hadith chain check | any free week |
| Offline phone app | classrooms need it |
| Payments | Picks 0–1 are live |

## H. Decisions for the founder

| # | Question | Recommendation |
|---|---|---|
| D1 | Data licences | Email the owners for permission now, Corpus first; replace a source if they say no |
| D2 | First paying customer | Adult self-learners; ~10 teacher interviews alongside |
| D3 | Learner login | Anonymous id now, real accounts later |
| D4 | Open AI chatbot | No, for now |
| D5 | Patents | Don't file; one hour with an IP lawyer instead |
| D6 | Build order | Foundation → vocab engine → word graph basics → proof-checked answers → word meanings |

**Footer:** "Strategy review, 6 Oct 2026. Research from web snippets and not fully checked. Not legal advice."
