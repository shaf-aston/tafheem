# Step 4. Research: what the outside world says

Full report with URLs: `market-prior-art-ip.md`. It is built from search snippets, so treat the
figures as indicative. Items marked UNCERTAIN there still need checking. **This is not legal advice.**

## 4.1 Competitors → nobody does "worked-out grammar + proof"

| Who | Strong at | Missing |
|---|---|---|
| Quran.com (free) | word-by-word translation, tafsir, learning plans | grammar analysis |
| Tarteel | recitation mistakes (words + tashkeel) | understanding, grammar, full tajweed |
| Bayyinah / Understand Quran | courses, high-frequency vocabulary | analysis of *any* ayah; proof |
| Quranic Arabic Corpus | i'rab treebank | it is a research site, not a learner product |
| AI chatbots (Ansari etc.) | open questions | trust (fabricated verses; Egypt fatwa against AI tafsir) |

→ Our space = **"understand any ayah, with proof, and remember it"**.

## 4.2 Prior art → the techniques are known; our *application + data* is not

| Brainstorm "novelty" | Verdict |
|---|---|
| Citation-grounded generation (I1) | Crowded as a technique (ALCE, RARR…). Thin for classical grammar with page citations |
| Rules + neural morphology (I2) | Crowded (CAMeL, MADAMIRA, Farasa) |
| Misconception tracing / vocab engine (I3, I4) | Some prior art (knowledge tracing, "option tracing"). Thin for Qur'anic morphology-shaped probes |
| Pedagogy router (I5), offline capsule (I9), upgrade triggers (I10) | Crowded / just design patterns |
| Tajweed lattice (I7) | Some prior art + **existing patents** → a freedom-to-operate check is needed before shipping |
| Explanation atoms (I8) | Thin, but low value as IP alone |

## 4.3 IP reality for a UK solo founder

1. **Patents are a weak fit.** UK law moved in Feb 2026 (*Emotional Perception*, per the research
   summaries; verify with an attorney). Software now passes the first hurdle more easily, but
   grammar rules and teaching methods would likely fail at "inventive step" as non-technical. Cost:
   about £4–7.5k for a UK patent, plus about £5.5–9k for PCT.
2. **The real protection = database right + copyright + trade secret.**
   - UK database right protects *your investment* in getting, checking and arranging data, for 15
     years, renewing when the data changes a lot. That fits a curated, cited word graph exactly.
   - Copyright covers code, original text and selection.
   - Trade secret covers rule tables and pipelines, as long as you **don't ship the bulk data to the
     browser** (this matters for any offline design).
3. **Third-party data limits what you own.** If a core dataset is GPL or non-commercial, you cannot
   build a closed moat on top of it. → Licence check = decision D1.
4. **The moat that actually works**: trusted data + measured accuracy + scholarly endorsement +
   teacher community. Patents come last.

## 4.4 Market → no reliable number; price anchors only

- $4–11/month, $99/year, $1,000 lifetime. Many strong free players.
- UK madrasah software = crowded *admin* tools (attendance, fees, hifz tracking). We found **none
  teaching grammar** → a possible B2B gap, **unproven**. It needs about 10 teacher interviews before
  any build.
