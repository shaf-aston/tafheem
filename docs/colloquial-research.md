# Colloquial: source research (working notes)

Goal: cross-check model-written Damascene phrases against something a model did not write. Nothing here replaces a native speaker. Last checked 2026-09-28.

## Best prospects (verified by opening the page unless marked)

| Source | What | Licence | Use |
|---|---|---|---|
| DDDA (dc_apc_eng) | Digital Dictionary of Damascene Arabic, Damascus only, built from Prochazka's textbook; English, German, Spanish | CC BY 4.0 (CLARIN record) | Best find. Download via https://hdl.handle.net/21.11115/0000-0011-49E8-6 in a browser (agent got 403). Size and format unconfirmed. |
| Nabra | Syrian, ~60K words, per-word spelling, dialect lemma, gloss; Damascus among 10 varieties | CC BY 4.0 | Word lookup. Access by request form (Shaf submits). |
| Wiktionary (North Levantine, apc) | 764 lemmas, Syria and Lebanon | CC BY-SA | Live lookup for spelling, sound, gloss. Copying carries share-alike. |
| Tatoeba (apc) | 100+ sentences | CC BY 2.0 FR (not opened) | Does a whole phrase sound natural. |
| Shami (GU-CLASP/shami-corpus) | Syrian tweets, small, noisy, no city | Apache-2.0, but tweet rights doubtful | Weak usage check only. |

## Private reference only, never ship

- MADAR: the only source naming Damascus (2,000 sentences per city). Research use only, no commercial use, no redistribution.

## Not usable

UFAL North Levantine, 120K subtitle sentences, real but CC BY-NC-SA and not Damascus-labelled. NADI (form-gated, no Damascus label seen). MGB-3 (audio, restricted). OPUS OpenSubtitles (no Syrian subset, unclear terms). Stowasser and Ani 1964 Damascus dictionary (rights unverified). ArSyra, AraDiCE, Curras, Baladi, CAMeL Tools, Halabi.

## Gemini claims not confirmed

"camel-lab/madar 12,000 Damascus sentences" (contradicts 2,000), `arbml/syrian-arabic` (404), Lingualism samples, the Hugging Face ids (401, unchecked). The real Shami repo path differs from Gemini's.

## Considerations

- No source is Damascus only, so "not found" is never proof of an error.
- Licence decides use: lookup is safe for all; copying text into the app needs CC BY or CC BY-SA and credit through `sources.json`.
- Check ladder: word in Wiktionary and Nabra, then sentence in Tatoeba, then rule checklist below, then anything left goes to a native reviewer.
- Rule checklist (Gemini's, unconfirmed): qaf becomes hamza; `mu` before nouns and adjectives, `ma` before verbs, no `-sh`; `'am` progressive; `raH` future; `taba'` possessive; feminine ending sounds like -e.
- Our need is a learner phrase list, not AI training data, so bulk corpora matter only as lookup.

## Open decisions

0. Download DDDA in a browser and check size, format, whether it holds phrases or only headwords.
1. Shaf submits the Nabra form (needs him).
2. Find a native Damascene reviewer for the leftover list.
3. Run the ladder on Unit 1 (56 phrases) once DDDA is downloaded.
