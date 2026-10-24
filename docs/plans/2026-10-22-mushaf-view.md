# Mushaf view: the Qur'an as printed pages, more than one printing

Date 2026-10-22 · `/lifecycle` stages 1–4 (grill → research → architect → plan). Nothing built yet.

## 1 · Requirements (assumed, testable)

Who: a minority of readers who memorise or revise by the printed page and want the page they know.

| # | Criterion | Check |
|---|---|---|
| R1 | The reader gets a second layout, **Page**, beside today's ayah list; the choice is remembered | toggle in ReadingOptions, survives reload |
| R2 | A page is the print: same words on the same line, same lines per page | for every page of a mushaf: line count = source; words in order = the app's ayah text; pages 1–2 are 8 lines (header + 7) |
| R3 | Every ayah is on exactly one page start, and it agrees with today's `layout.db` | 6,236 / 6,236 for Madani 1421 |
| R4 | More than one printing, listed in data, never in components | `data/quran/mushafs.json`; adding one = an entry + a build run, no code |
| R5 | Phone first: a page fits 360px width, no sideways scroll; next page shows < 300 ms | measured in Playwright with prefetch on |
| R6 | A page font costs ≤ 200 KB, and only the page in view (± 1) is loaded | network panel; measured 150 KB for Madani 1421 page 3 |
| R7 | Tapping a word or an ayah does what it does in the list (gloss, ayah study) | same handlers, same tests |
| R8 | Every source credited with the terms it actually states | `sources.json` entries + Credits |

Printings, in order of who asks for them most: **Madani 1421 (KFGQPC V2, 604 pages, 15 lines)** → Madani 1405 (V1) → IndoPak 15 and 16 lines (South Asia) → Warsh and Qaloon (North and West Africa, a different riwayah, so different text, not only a different look) → tajweed colours.

## 2 · Research

### What already exists here

- `services/quran/layout.py` + `scripts/quran/build_quran_layout.py`: **ayah → page** for Madani 604, from `api.quran.com`. Only Memorise uses it (`lib/memorise/memorise.js` `pagesOf`). No line data.
- Text is Unicode in `Scheherazade New` (OFL), with the mushaf spelling and the tanween-meem rule (`arabic_text.mushaf_words`).
- `data/quran/editions.json` already imports QUL sqlite exports (`qul-tafsir`, `qul-translation`), so a `qul-layout` format fits the existing pattern.

### Sources

| Source | Gives | Covers | Catch |
|---|---|---|---|
| [Quran.com API v4](https://api-docs.quran.com/docs/tutorials/fonts/page-layout/) `verses/by_page/{n}?words=true&word_fields=line_number,code_v2,…` | each word's **page + line** + glyph code + Unicode text | Madani V1, V2 | **Spiked:** page 3 = 15 lines, 2:6–2:16, matches the print; page 1 = lines 2–8. `mushaf=6/7` (IndoPak) is ignored on the public API: same lines come back |
| [QUL mushaf layouts](https://qul.tarteel.ai/docs/mushaf-layout) (Tarteel), sqlite / json | `pages(page_number, line_number, line_type ayah·surah_name·basmallah, is_centered, first_word_id, last_word_id, surah_number)` + a `words` script db | ~20 approved: KFGQPC V1, V2, V4 tajweed, Digital Khatt, IndoPak 13/15/16, Nastaleeq 15, Qatar | download only, no API; no licence on the page (tarteel terms); V4 tajweed fonts "disabled, proofreading" |
| QCF page fonts, `quran.com/fonts/quran/hafs/v2/woff2/p{n}.woff2` | one font per page, a glyph per word: pixel-true print | V1, V2 | [QF terms](https://api-docs.quran.com/legal/mushaf-fonts-and-images/): may cache/bundle with an active QF developer account, credit Quran Foundation, never re-offer the files separately |
| [KFGQPC fonts](https://fonts.qurancomplex.gov.sa) | Unicode Hafs, Warsh, Qaloon fonts | the riwayat | [licence](https://scancode-licensedb.aboutcode.org/kfgqpc-uthmanic-script-hafs.LICENSE): proprietary, no modification without written approval |
| [zonetecde/mushaf-layout](https://github.com/zonetecde/mushaf-layout) | page JSON per edition + 1,211 fonts (~140 MB) | V1, V2 | no data licence stated; useful only as a cross-check |
| Warsh: [quran-database-verifier](https://github.com/M97Chahboun/quran-database-verifier) (ayah → page), archive.org scans | ayah-level only | Warsh | **no open line-level Warsh layout found** |

### How others do it

- **Quran.com** reading mode: font picker (KFGQPC V1, V2, Uthmani, IndoPak) + line count for IndoPak; per-page glyph fonts; hover a word for its meaning.
- **Quran Android / Ayah** (iOS): page **images** per printing (Madani, Warsh, Qaloon, Shamarly…), downloaded on demand, ayah highlight from a bounding-box db. Exact, every riwayah, but no word-level interaction.
- **Tarteel**: glyph pages, used for hifz with mistakes marked on the word.
- Rendering pitfalls ([quranportal](https://quranportal.io/blog/rendering-the-quran-mushaf-digitally)): justify every line incl. the last; kill inline whitespace; load only the page's font and block until it arrives (wrong glyphs otherwise); never mix V1 and V2 data; headers/basmala lines have no word ids; fetch a page's words in one range query.

Known unknowns: QUL word ids = Quran.com word ids? (join on `s:a:w` keys, never ids); Warsh text with word positions; whether the QF developer account is a fit for this app.

Gate → three option families (glyph pages, Unicode lines, images), each with its unknowns. **Pass.**

## 3 · Architecture

### Candidates, scored

| | A · Glyph pages (QCF font per page) | B · Unicode lines (our font, print's line breaks) | C · Page images |
|---|---|---|---|
| Accuracy | pixel-true print | same words per line; letter shapes are ours, a line can run long or short | pixel-true |
| Speed | 150 KB font per page, prefetch ±1 | zero new bytes | 100–300 KB per page |
| UX | word tap via word id | word tap, gloss, meem rule, search: all reused | no word interaction, poor a11y |
| Maintainable | new render path; terms to keep | one renderer for every printing that has text | a second content type, a coordinate db per printing |
| Riwayat | only where glyph fonts exist | any printing with text + layout | any printing with scans |

**Chosen: one layout model, two renderers behind one seam.** The page data is the same for A and B (lines → word keys); a printing names its `script`: `glyph` (A, Madani V1/V2) or `text` (B, IndoPak, and A's stand-in while a page font loads). **C is the loser**: exact, but it throws away every word feature this app is built on; kept only as a last resort for a riwayah with no text.

### Level 1 · Context
```
Reader ──> Tafheem (web app) ──> Tafheem API ──> (build time only) api.quran.com · QUL downloads
                                                 page fonts: built into our own site, never hotlinked
```

### Level 2 · Containers
```
frontend (Vercel) ──GET /api/quran/mushaf…──> backend (FastAPI, Oracle) ──reads──> mushaf.db (sqlite, built)
frontend ──GET /fonts/mushaf/{id}/p{n}.woff2──> static site
scripts/quran/build_mushaf.py ──writes──> mushaf.db   (run by hand, like build_quran_layout.py)
```

### Level 3 · Components (one owner, one reason each)
```
data/quran/mushafs.json        which printings exist: id, name, pages, lines, script, source, credit
scripts/quran/build_mushaf.py        harvest a printing into mushaf.db (sources: quran-api | qul-layout)
services/quran/mushaf.py             the only opener of mushaf.db; absorbs quran_layout.py (ayah→page is a query on it)
routers/quran.py (+3 routes)   list · page · locate
lib/mushaf.js                  fetch + cache pages, prefetch ±1, page-font loader (FontFace)
quran/MushafPage.jsx           one page: lines → words; renderer chosen by script; per-line fit
quran/MushafReader.jsx         page nav (swipe, ←/→, picker), spread of two on wide screens
ui/ReadingOptions              + "Layout: Ayahs | Page" + printing picker, fed by the list route
settings.js                    remembers layout + printing
theme.json mushaf group        page width, line height, paper colour: no number in a component
```

### Level 4 · Contracts (slice 0–2)
```
GET /api/quran/mushaf                       → [{id, name, pages, lines, script, credit}]
GET /api/quran/mushaf/{id}/page/{n}         → {page, lines: [{type: ayah|surah|basmala, surah?, centered,
                                                words: [{key: "s:a:w", text, glyph?, end?: ayah}]}], font?}
GET /api/quran/mushaf/{id}/locate?ayah=s:a  → {page}
mushaf.db: line(mushaf, page, line, type, surah, centered, first_key, last_key)
           word(mushaf, key, surah, ayah, pos, text, glyph)      -- keyed by s:a:w, never source ids
services/quran/mushaf.py: printings() · page(id, n) · page_of(id, surah, ayah) · for_surah(id, surah)
Renderer seam: script → MushafLineText | MushafLineGlyph, same props {line, onWord, onAyah}
```
Gate → every box maps up; every arrow is a call below; each slice below names its component. **Pass.**

## 4 · Plan (vertical slices, skeleton first)

| Slice | Builds | Done when | Pre-mortem: "fails because…" |
|---|---|---|---|
| **S0 skeleton** | `mushafs.json` (Madani 1421 only), `build_mushaf.py --pages 1-3`, `services/quran/mushaf.py`, page route, `MushafPage` text renderer behind the Page toggle | page 3 renders 15 lines, words in order, at 360 and 1280 | Scheherazade lines don't fit the print's breaks → spike a per-line fit (shrink font-size to width) here, before anything else |
| **S1 whole printing** | all 604 pages; tests: R2 line counts, R3 6,236 ayahs vs `layout.db`; then `quran_layout.py` reads from `mushaf.db` and `layout.db` goes | tests green; Memorise unchanged | Quran.com rate limits → reuse build_quran_layout's pause + retry |
| **S2 glyph pages** | page fonts copied into our build (QF account + credit), `MushafLineGlyph`, FontFace loader, text renderer while the font loads | font ≤ 200 KB, only ±1 loaded, no wrong glyph ever painted | terms don't fit → stay on S0's text renderer; nothing else changes |
| **S3 reading** | `MushafReader`: swipe/keys, page picker, ayah → page jump from search, last page remembered, two-page spread ≥ 1024px | R5 measured | content-visibility on rows → pages are their own component, not AyahList rows |
| **S4 words** | tap word → gloss, tap ayah → study, recitation highlight on the page | R7: the list's tests run on the page too | glyph words have no Unicode to gloss → look up by `key` |
| **S5 more printings** | Madani 1405 (same source), IndoPak 15/16 via `qul-layout` import + an IndoPak font | each new printing = entry + build, zero code; R2 per printing | QUL ids ≠ Quran.com ids → keys only; IndoPak text differs → it carries its own `text` |
| **S6 riwayat (research-gated)** | Warsh, Qaloon: needs text with word positions + a line layout | an open source with both is found | none exists → images (C) for that printing only, or wait |

Order of value: S0–S3 give a real Madani page view to the readers who asked; S5 covers most of the rest; S6 waits on data that is not yet out there.
