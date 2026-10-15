# Tafheem: competitor, prior-art, IP and market research (as of 2026-10-06)

Method note: built from web-search snippets plus a few fetches, within a small token budget. Most figures are secondary-source and unverified. Items marked (UNCERTAIN) need checking before anyone relies on them. This is not legal advice.

## A. Competitors

### What each one does

- **Quran.com / Quran Foundation** (non-profit, free). Word-by-word translation in six languages, translations, tafsir, recitations. Structured Learning Plans, with over 100,000 enrolments, no sign-up needed, and topical or surah-based content (reflection, hadith, scholarly insight). No i'raab engine that I found. https://quran.foundation/year-in-review ; https://quran.com/en/product-updates/introducing-learning-plans ; https://quran.com/learning-plans
- **Tarteel AI.** Recitation memorisation app with over 10M downloads (per the app-store/aggregator snippet, UNCERTAIN). Its "Mistake Detection" flags word-level errors, skipped words and wrong tashkeel, and was trained on about 75,000 minutes of curated recitation data. It is premium-gated. https://tarteel.ai/blog/introducing-mistake-detection/ ; https://apps.apple.com/us/app/tarteel-ai-quran-memorization/id1391009396
  - Funding: public databases show only a small seed (about $53K, Dec 2020; Founders Inc, Wadi Makkah). The company was said to be self-funded or revenue-funded. Later rounds may be undisclosed (UNCERTAIN). https://www.crunchbase.com/organization/tarteel ; https://pitchbook.com/profiles/company/458036-74
  - I found no Tarteel-owned patent. I did not search assignee records exhaustively (UNCERTAIN).
  - Tarteel's mistake detection checks words and diacritics (tashkeel). A critical review argues the field still needs "knowledge-centric" tajweed evaluation. https://arxiv.org/pdf/2510.12858
- **Bayyinah TV / Dream** (Nouman Ali Khan). Classical-grammar-informed Arabic courses and the Dream textbook, aimed at Qur'an understanding. Video-led, with no deterministic analyser. Price: about $11/month, or $1,000 lifetime. https://bayyinah.com/lifetime/ ; https://explore.bayyinahtv.com/arabic/
- **Understand Al-Quran Academy.** Courses on high-frequency Qur'anic vocabulary (for example 232 words that cover about 50% of occurrences). Subscription at $10/month or $99/year, plus a lifetime option. It also has a free "80% Quran Words" flashcard app. https://understandquran.com/ ; https://apps.apple.com/fr/app/80-quran-words/id6777562186?l=en-GB
- **Quranic (getquranic.com)** and similar apps (Quran Progress at about $4/month, Quran IQ, Learn Quranic Arabic). These are mostly vocabulary or flashcard apps. https://www.getquranic.com/ ; https://apps.apple.com/us/app/quran-progress-learn-arabic/id1136011989
- **Duolingo Arabic.** Free tier with paid Super. It covers MSA, not Qur'anic or classical Arabic, and has no i'raab. https://preview.duolingo.com/course/ar/en/Learn-Arabic
- **Quranic Arabic Corpus** (Kais Dukes, Leeds, since 2009). Word-by-word morphology plus an i'rab-based dependency treebank of all 77,430 words. Free to use, and the data is downloadable. https://corpus.quran.com/ ; https://en.wikipedia.org/wiki/Quranic_Arabic_Corpus
  - The corpus is released under GPL, but its pages also say the data "should not be used for commercial purposes". That is an apparent licence conflict. Check the exact terms before building a commercial product on it. https://corpus.quran.com/download/ ; https://corpus.quran.com/faq.jsp
- **Madinah Arabic / Arabic101, Mufradat, Al-Quran word-by-word apps.** Not researched in depth. I would expect textbook-style or flashcard products without deterministic i'raab (UNCERTAIN, no source).
- **AI tafsir chatbots (Ansari, ChatGPT-based "Quran GPT" types).**
  - Ansari is open source and retrieval-grounded, with more than 140,000 conversations in 25+ languages. In its own paper it reports 4.41/5 human-rated quality and zero hallucinations. These are self-reported figures. https://arxiv.org/html/2608.20390 ; https://docs.ansari.chat/faq/
  - Trust problems: Egypt's Dar al-Ifta fatwa against using AI to interpret the Qur'an (the January 2026 date is from the search snippet; verify). The literature also documents fabricated verses and hadith. https://time.com/article/2026/05/26/ai-muslim-worship/ ; https://arxiv.org/html/2601.06092v1 ; https://openreview.net/pdf?id=EbGr5iIcMi ; https://muslimmatters.org/2025/12/30/can-you-fatwah-shop-with-ai/

### Feature matrix

"Y" means present, "p" means partial, "-" means not found, "?" means unverified. Grammar means i'raab or syntax analysis. Based on snippets, so treat it as indicative.

| Product | Price | Scale signal | Grammar (i'raab) | Root-based vocab | SRS | Recitation correction | Citations / sources |
|---|---|---|---|---|---|---|---|
| Quran.com | Free (donations) | 100k+ plan enrolments | - | p (word-by-word) | - | - | Y (tafsir / translations) |
| Tarteel | Freemium / premium | 10M+ downloads (UNCERTAIN) | - | - | p ? | Y (words, tashkeel; not full tajweed) | - |
| Bayyinah / Dream | $11/mo; $1,000 lifetime | Large following | Y (taught, not computed) | Y (taught) | - | - | p (teacher-led) |
| Understand Quran Academy | $10/mo; $99/yr | Large (UNCERTAIN) | p | Y (frequency-based) | Y (flashcards in the 80% app) | - | - |
| Quranic / Quran Progress etc. | Free to about $5-30 | Small to medium | - | p | Y | - | - |
| Duolingo Arabic | Free / Super | Huge (MSA only) | - | - | Y | - | - |
| Quranic Arabic Corpus | Free | Widely used by academics and developers | Y (treebank, i'rab-based) | Y (root/lemma) | - | - | p (academic) |
| Ansari and AI chatbots | Free / freemium | Ansari 140k conversations | p (LLM) | p | - | - | Y (Ansari retrieves sources; the others vary) |
| Tafheem (proposed) | n/a | n/a | Y (deterministic, book-cited) | Y | Y (FSRS) | Y (word-level, Whisper/Groq) | Y (verified/derived/guessed) |

The gap I could find in the sources: nobody combines deterministic, book-cited grammar, sarf and i'lal, dictionaries, SRS and recitation checking with explicit provenance labels. The Corpus has the analysis but no learner product, and the learner products lack the analysis. Absence from my searches is not proof of absence.

## B. Prior art by novelty

### Verdict table

| # | Novelty | Verdict | Key references |
|---|---|---|---|
| 1 | Source-grounded generation, per-claim citations, refusal | **Crowded** as a technique. Thin as a product in classical Arabic grammar with page citations. | ALCE: https://www.emergentmind.com/papers/2305.14627 ; RARR (claim-level attribution); ClaimVer: https://aclanthology.org/2024.findings-emnlp.795.pdf ; VeriCite: https://arxiv.org/pdf/2510.11394 ; ALiiCE: https://arxiv.org/html/2406.13375 ; Ansari (Islamic RAG): https://arxiv.org/html/2608.20390 |
| 2 | Hybrid symbolic+neural Arabic morphology with ambiguity arbitration | **Crowded.** Analyse-then-disambiguate is the standard design. | CAMeL Tools: https://www.researchgate.net/publication/341542088_CAMeL_Tools_An_Open_Source_Python_Toolkit_for_Arabic_Natural_Language_Processing ; Camelira: https://arxiv.org/pdf/2211.16807 ; MADAMIRA / Farasa comparison: https://mdpi-res.com/d_attachment/information/information-12-00523/article_deploy/information-12-00523-v5.pdf?version=1640226336 ; Quranic Corpus: https://corpus.quran.com/ ; Corpus parsing: https://arxiv.org/pdf/1510.07193 |
| 3 | Word identity graph, sense disambiguation, misconception classifier, micro-interventions, exposure planner | **Some prior art** in each part (knowledge tracing, misconception diagnosis, SRS). Thin for the Qur'anic-vocabulary application. | KT survey: https://dl.acm.org/doi/10.1145/3569576 ; DKT variants: https://arxiv.org/pdf/1809.08713 ; Option tracing: https://arxiv.org/pdf/2104.09043 ; FSRS (open-source SRS algorithm; search found no specific reference, check the open-spaced-repetition GitHub org) |
| 4 | Pedagogy router | **Crowded** in general (adaptive tutoring). It is a design pattern, not an invention. | KT survey above |
| 5 | Teacher lesson compiler with provably correct quizzes | **Some prior art** in automatic question generation. "Provable" correctness from a deterministic rule engine is a differentiator in practice, but I did not research quiz-generation papers (UNCERTAIN). | None found in this pass |
| 6 | Recitation feedback as error lattice with tajweed and pedagogy-weighted scoring | **Some prior art.** Tajweed mispronunciation detection is an active research area, and recitation-error patents exist. | MDD of Quranic rules: https://arxiv.org/pdf/2305.06429 ; Pronunciation error detection and correction: https://arxiv.org/html/2509.00094v2 ; Smartajweed: https://arxiv.org/pdf/2101.04200 ; Recognition: https://arxiv.org/abs/2305.07034 ; Critical review: https://arxiv.org/pdf/2510.12858 ; Patents: https://www.google.com/patents/WO2014082654A1?cl=en , https://patents.google.com/patent/WO2008083689A1/en ; Tarteel: https://tarteel.ai/blog/introducing-mistake-detection/ |
| 7 | Precomputed "explanation atoms" composed per level | **Thin** as prior art, but low IP value. It is an architecture choice. | None found |
| 8 | Edge "learning state capsule", offline-first | **Crowded** (offline-first and local-state sync are standard). | None specific |
| 9 | Upgrade triggers tied to learning moments | **Crowded** (standard freemium growth practice). | None specific |

Caveats: the patent search was a single snippet-level query. The two patents above are old (WO2008, WO2014) and may have lapsed, but that is UNCERTAIN. A professional freedom-to-operate search would be needed before launching a recitation feature at scale. The tajweed papers cited are academic and no one licence-checks them against products.

## C. IP strategy for a UK solo founder

- **Patentability in the UK changed in 2026.** The UKSC decision in *Emotional Perception AI v Comptroller* (11 Feb 2026) held that an ANN is a "program for a computer", but dropped the Aerotel test and moved towards an EPO-style approach. It sets a low "any hardware" threshold at the first stage, so many software claims now get past that hurdle. Non-technical features are still excluded when assessing novelty and inventive step, and my reading is that rules and curated content count as non-technical. This is my inference from the summaries; verify with an attorney. https://www.linklaters.com/insights/blogs/digilinks/2026/february/emotional-perception-ai-supreme-court-overhauls-decades-of-uk-case-law ; https://www.hlk-ip.com/news-and-insights/emotional-perception-ai-ltd-v-comptroller-general-of-patents-designs-and-trade-marks-judgement/ ; https://www.eversheds-sutherland.com/en/united-kingdom/insights/supreme-court-overhauls-uk-patent-law-for-ai-emotional-perception-ai-v-comptroller-general-2026
- **Implication.** A claim on a grammar rule engine or a citation-verification scheme would likely face the inventive-step filter as a linguistic or educational method. A claim on a technical audio-processing step (for example, a recitation lattice built from ASR output) is the most patent-shaped of the nine, but it sits in crowded prior art (section B).
- **US.** I did not research Alice in this pass. From general knowledge, abstract-idea rejections are a major risk for education and language methods in the US (UNCERTAIN, no source gathered).
- **Cost.**
  - UK patent: about £4,000-£7,500 total (£3,000-£6,000 attorney fees). Renewals run from £70 in year 5 up to £610 in year 20, about £6,110 for 20 years. https://sprintlaw.co.uk/articles/how-much-does-a-patent-cost-in-the-uk/ ; https://sprintlaw.co.uk/articles/patent-fees-renewals-in-the-uk-full-cost-breakdown/ ; https://www.design2market.co.uk/academy/uk-patent-cost-guide/
  - PCT: roughly £5,500-£9,000 for the international filing phase, with national phases extra. These are law-firm marketing estimates. https://sprintlaw.co.uk/articles/how-much-does-a-patent-cost-in-the-uk/
- **Database right** is the most relevant right. The UK sui generis database right (Copyright and Rights in Databases Regs 1997) protects databases with substantial investment in obtaining, verifying or presenting the contents. It prevents extraction or re-utilisation of a substantial part, and lasts 15 years with renewal on substantial change. After Brexit, EEA persons generally do not qualify for new UK database rights, and vice versa. A UK founder qualifies in the UK, but EU protection for new databases is a question to check. https://www.legislation.gov.uk/uksi/1997/3032/part/III ; https://sprintlaw.co.uk/articles/understanding-sui-generis-database-rights-in-the-uk/ ; https://www.bclplaw.com/en-US/events-insights-news/protecting-your-investment-in-databases-created-in-the-uk-or-the-eu-during-the-transition-period-and-afterwards.html
  - Caveat: only your own investment counts. A dataset derived from the Corpus (GPL, with a non-commercial note), Lane or other sources may carry third-party rights that limit what you can claim or commercialise. This is the biggest practical IP risk I found.
  - Copyright still protects code, original text and original selection or arrangement. It does not protect facts or classical rules themselves.
- **Trade secret** is the cheapest option for rule tables, curated mappings and internal data pipelines. It works only while the data is not shipped to clients in extractable form, which matters for the offline-first capsule.
- **What moats actually work for small edtech.** I did not find one authoritative source on this. The common view in edtech strategy writing is that moats come from content and data quality, community and distribution, and brand and trust, not patents. Treat this as general knowledge, not sourced. The Qur'an sector adds one factor: trust and scholarly endorsement carry unusual weight, as the AI-tafsir debates above show.

## D. Business

- **Market size.** I found no reliable standalone market figure for online Quran learning. Only broad numbers appeared: the global online education market at about $315B in 2025 (Vantage), and one analyst claim that "cultural-context education" including Arabic and Quranic studies was about 14.7% of the Arabic-language digital education market (UNCERTAIN). Do not quote these as the TAM. https://www.vantagemarketresearch.com/online-education-e-learning-market ; https://www.technavio.com/report/online-education-market-industry-analysis
  - The Muslim population of about 2B was not sourced in this pass. It is widely cited, for example by Pew.
- **What users pay.** Price anchors from competitors: $10-11/month, $99/year for Understand Quran, Bayyinah at $11/month or $1,000 lifetime, small apps at $4-30. Many rivals are free (Quran.com, Duolingo base tier, Quranic, 80% Quran Words), so the paid segment buys depth or a teacher.
- **UK madrasah and Islamic-school software.** A crowded niche already serves admin: IlmFlow, MadrasahConnect, Labbaik, Hidayah, Alif Cloud, Ilmify, all with attendance, fees, Hifz tracking and parent portals. None of the snippets mentioned grammar or i'raab teaching tools, which may leave room for a teaching-content product rather than an admin one. https://ilmflow.co.uk/ ; https://madrasahconnect.com/ ; https://uselabbaik.com/ ; https://hidayah.me/madrasah-management-software-uk ; https://www.alifcloud.com/ ; https://ilmify.app/
  - Scale: there is no firm data on the number of UK madrassas. A 2006 report cited about 700. A figure of 95% of Muslim children aged 5-14 attending is quoted from a 2011 IPPR paper, and that figure is doubtful (UNCERTAIN). https://ippr-org.files.svdcdn.com/production/Downloads/Madrassas-in-the-media-Feb2011_1827.pdf
- Willingness to pay for B2B teacher tools is not evidenced in my sources. It needs customer interviews.

## What this means for a defensible moat

1. Patents are a weak fit. Most of the nine "novelties" are crowded or are architecture, and the 2026 UK change helps with software but not with non-technical linguistic content. The one patent-shaped candidate (recitation lattice) is in a field with existing patents and research.
2. The defensible parts are the curated, cited, verified dataset (rules mapped to book pages, i'lal tables, rijal and dictionary linkage) and the trust position (verified/derived/guessed labels, refusal). Protect these through database right, copyright and trade secret, and by keeping extractable bulk data out of client bundles.
3. Resolve the Corpus licence question first. If any core data is GPL or non-commercial, a closed commercial moat on that layer may not be available.
4. Competitors split into content-light apps and analysis-only research tools. Tafheem's differentiation is the combination, so the moat is execution, scholarly trust and community (teachers, madrasahs), not any single technique.
5. Do a proper patent and freedom-to-operate search before building recitation scoring features that resemble existing recitation patents.
