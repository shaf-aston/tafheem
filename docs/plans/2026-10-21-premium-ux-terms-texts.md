# Plan: premium UX, hadith terms tree, creed & usul texts

Status: living document for one long run (2026-10-21). Stage names follow the development
lifecycle (grill → research → architect → plan → execute → verify → iterate → ship).
Team: orchestrator (PM + gates + merges), **critic** (Opus: finds problems, scores plans, verifies),
**worker** (Sonnet: builds well-specified slices).

## Stage 1 · Requirements (grilled from the ask + the codebase)

The ask, in one line each:
1. More intuitive everywhere, phone first; premium, consistent, soft on the eyes.
2. "Other themes hurt the eye": contrast must be defined and measured, not felt.
3. Advanced but restrained motion; look at 3D / Blender-style sites for ideas; keep it practical.
4. Loading screen: only if a wait is actually visible (user said "maybe scrap").
5. Hadith terminology: every term broken down, visual tree (PBS style), common mistakes,
   near-synonyms, click to open, motion.
6. Creed texts: Ashʿarī (Jawharat al-Tawhid + Tuhfat al-Murid), Salafi creed, later madhhab
   comparison; Usul al-Shashi for Hanafi usul.
7. Process: phased, verified (mutation testing), never deviating; PR + merge + deploy at the end.

What already exists (so we extend, never duplicate):
- `theme.json` tones every palette colour per look (`lib/tone.js`) and `theme.test.js` holds
  tokens to ≥ 4.5:1 and the comfort caps. But that checks **tokens**, not what the screen shows.
- `components/shell/MapPanel` + `PbsChart` + `lib/pbsTree`: nine sciences as PBS trees, zoom in.
- `components/hadith/TermGuide` lists the usul glossary (`backend/data/usul/usul.json`,
  `/api/usul/guide`) flat, inside the chain sheet only.
- `lib/manhajData` + `ManhajView`: creed and fiqh schools compared on fixed questions (tags).
- OpenITI books (`backend/data/books/openiti*`, `scripts/import_openiti.py`): Usul al-Shashi is
  already imported; Tahawi's Matn al-Aqida is in the folder but not listed. Daleel searches them.
- `ui/Skeleton`, `EmptyState`, `ErrorAlert`: the uniform loading / empty / error states.
- `docs/architecture/frontend.md`: keyframe dedupe (Phase B) partly done, 44 keyframes left.

### Success criteria (numbers or testable conditions)

Track A — look, feel, phone
- A1 **Measured contrast.** A Playwright audit (`frontend/scripts/contrast-audit.mjs`) walks
  Home, every listed tab's opening screen, All sections and Settings, in all three looks, at
  390×844 and 1280×800, and reports every rendered text node under WCAG 4.5:1 (3:1 at ≥ 24px or
  bold ≥ 18.7px) and every control border/icon under 3:1. Exit: **0 failures**, and the script
  is kept so the number can be re-checked.
- A2 **No hardcoded colour in the UI.** Count of literal `#hex` / `rgb(` in `frontend/src`
  components and feature CSS (outside `theme.json`, `landing/`, SVG art, tests) → listed; each
  either moved to a token or justified in an allowlist test that fails on a new one.
- A3 **Phone intuitiveness.** At 390×844 on the same screens: no horizontal page scroll;
  every interactive target ≥ 44×44 CSS px or ≥ 24 px with 24 px spacing (WCAG 2.5.8); axe-core
  0 serious/critical; from Home any listed tab opens in ≤ 2 taps.
- A4 **One motion vocabulary.** Every duration/easing in component CSS comes from a token
  (`grep -E '[0-9]+ms'` outside `theme.json`/`motion.css` → 0 new literals, allowlist for the
  art); `styles/keyframes.test.js` passes; everything honours `motionOff()`. At most three
  "depth" techniques picked from the research, each applied through one shared component or
  class, never per screen.
- A5 **Uniform waits.** Every panel's pending state is a Skeleton, every empty is EmptyState,
  every error is ErrorAlert (audit grep + render tests). No new splash screen unless the
  measured first paint of a cold `/app` exceeds 1 s on a throttled run.

Track B — hadith terms
- B1 **One source of truth.** The term tree lives in `usul.json` `glossary` (backend-owned):
  each term keeps `{ar, en, say, quote, book, page}` and may add `kids`, `confuse: [{ar, why}]`
  (look-alikes, common mistakes) and `kind` (links to a `/api/usul/terms` kind where one exists).
  `store.glossary()` fails loudly on: duplicate `ar`, a `confuse` target that is not a term, a
  `kind` the rulings do not know. Backend test covers each fault.
- B2 **A tree you can walk.** The Hadith tab gains a Terms view: the tree drawn by the existing
  `PbsChart` (built through `chartTree`), tap/Enter on a term opens its card (meaning, quote with
  book + page, "often confused with", hadith carrying the ruling where `kind` exists). On a
  phone the same data shows as collapsible list (TermGuide). Render test opens it and reaches a
  card; axe clean; motion through the shared vocabulary.

Track C — texts (creed and usul)
- C1 **A text is data.** `backend/data/books/texts.json` names each text: its OpenITI matn file,
  optional sharh file, school tag (manhaj id), and a short reader's note. Loader checks on load:
  every file exists in `openiti.db`, every school id exists in the frontend's manhaj list (shared
  JSON), no duplicate ids. Texts in: Usul al-Shashi (have), Tahawi's creed (have), Jawharat
  al-Tawhid + Tuhfat al-Murid (fetch from OpenITI raw, reachable), al-Wasitiyya (fetch).
  Licence: OpenITI CC BY-NC-SA, same as the books already shipped.
- C2 **A reader.** `/api/texts` lists texts; `/api/texts/{id}` gives headings and passages;
  where a sharh is named, each matn passage shows the sharh passages that quote it (match by
  the matn line's first 5 words), side by side on wide screens, folded under it on a phone.
  Reachable as one registry line (`lib/tabs.js`, group Read). Render test; contrast audit
  includes it.
- C3 **Compare schools** from a text's header opens the existing ManhajView at its school.

Process
- P1 Each track ships as its own PR, CI green, squash-merged, Production deploy verified.
- P2 Verification: critic runs fault-finding lanes (design, a11y, security of new routes, edge
  cases) + a mutation pass on the new pure modules (hand-rolled mutants: flip a comparison,
  drop a branch; the test must fail for each); findings classified by the back-routing table.
- P3 Order: A → B → C. If time runs out, C ships as a walking skeleton (list + reader for the
  texts already on disk), never half-wired.

## Stage 2 · Research — see `## Findings` below (filled as it lands)

## Findings

### Orchestrator findings (codebase)
- `theme.test.js` already holds tokens to 4.5:1 and comfort caps → the gap is **rendered** contrast
  (washes via `color-mix`, text over lights, per-feature CSS), so A1 needs a Playwright audit, not
  more token tests.
- Grow has **book worlds** (`worlds.json` kind `book`): Tahawiyya (creed), Quduri (fiqh),
  Ajurrumiyya, Marah. Each is a hand-authored `public/grow/<book>.json` (parts → lessons → cards:
  teach / choose / pick / sort / order), checked word-for-word against the OpenITI file by
  `lib/bookLesson.test.js`. → Track C's home is a **book world per text**, not a new tab: Jawhara +
  Tuhfa (Ashʿarī creed), al-Wasitiyya (Salafi creed), Usul al-Shashi (Hanafi usul). The Map's
  ManhajView already compares the schools → link each world's header to its school.
- `openiti.db` rebuilt locally (96,241 passages). Adding a book = one line in
  `openiti-books.json` + the file + re-run import; `bookLesson.test.js` reads the file directly.
- Hadith's `listing` state already switches Narrators / Scholars views from `HadithMoreMenu` →
  a Terms view is one more `listing` value, no new navigation.
- `PbsChart` + `chartTree` draw any `{root, branches[{ar,en,c,kids}]}`; a glossary→chart adapter
  is pure data.
- Daleel search cannot teach a text (no harakat, no English) → reading/learning belongs in Grow.

### Option families (stage 2 gate)
Track A: (i) measure-then-fix at the token/wash level + audit script kept as a check;
(ii) runtime "comfort" layer toning text as well as palette (bigger, risk of regressions);
(iii) per-screen overrides (rejected: sprinkles). Unknowns: how many rendered failures and
whether `color-mix` washes are the cause.
Track B: (i) Terms view inside Hadith (PbsChart over the usul glossary, cards); (ii) put terms in
the Map's hadith chart (rejected: duplicates the backend glossary); (iii) a Terms tab (over-scoped).
Unknowns: how to show "confused with" without a graph library; phone layout of the tree.
Track C: (i) one Grow book world per text, authored slice by slice, verified by the existing test;
(ii) a generic OpenITI reader tab (reads any book; teaches nothing; no progress); (iii) Memorise
book entry for the Jawhara poem (lines to learn by heart; complements (i)). Unknowns: are the
Jawhara / Tuhfa / Wasitiyya files on OpenITI; authoring volume per night.
