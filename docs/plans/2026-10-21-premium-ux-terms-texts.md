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

### Critic findings · task 1 (phone + look audit, 96 screens)
Measured text contrast is sound in all looks (body 11.5–13.8:1, dim 7.8–8.0, eyebrow ≥ 7.3; chroma
under the caps); no horizontal overflow; grounds change per look. The "hurts the eye" complaint is
therefore not raw text contrast → it is washes/alpha layers, size and crowding. Real findings:
| sev | where | finding | fix |
|---|---|---|---|
| 1 | Settings 390 | Appearance Segmented clips; Parchment cut, Device unreachable | Segmented wraps under 420px (one rule in ui/) |
| 1 | header 390 | icon buttons 40×40; banner ✕ 28×28 | one tap-min token (44) on the icon button |
| 1 | Nahw 390 | 57 targets < 44 (chips/word tokens); Settings 43, Quran 18, Daleel 17 | chip min-height or 24px + spacing (WCAG 2.5.8) |
| 2 | Quran | 9%-alpha watermark text is in the a11y tree | aria-hidden |
| 2 | Home 1280 | stray "4" pill under the tab row (leaked badge) | anchor to its tab or remove |
| 2 | Home 390 | search placeholder truncated | shorter phone placeholder (copy in home.json) |
| 3 | Home 1280 | فهم outline art is transparent text | aria-hidden |
| 3 | dock 390 | More slot moves when the current tab is not docked | keep More fixed |
| 3 | Home parch 390 | three CTA styles on one screen | one primary per screen |
Audit-tool gotchas: the look is `localStorage.settings.theme`, not the hint key; computed colours
arrive as `color(srgb r g b / a)` and must be composited.

### Critic findings · task 2 (code audit A2/A4)
Colours: 18 grep hits, **0 real UI violations** (masks, HTML entities, tokenised hsl). Deliverable
= the allowlist test (`/(?<!&)#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i`, skip `mask-image` lines).
Durations: 16 literal `Nms` left → components.css:211, 922–952; emblem.css:35; pbs.css:9–31 (+3
cubic-bezier); micMark.css:81; PbsChart.jsx:73 inline stagger; `--motion-spring-ms * 4ms` hacks in
growWorlds/command/layers → name them (`--motion-loop-ms`, `--motion-enter-ms`). ~15 lines, one slice.
Easings: 84 bare `ease*` outside motion.css → A4 sharpened to **"0 literal `Nms` and 0
`cubic-bezier(` outside motion.css/theme.json"**; add one `--motion-ease` token used by the shared moves.

### Worker · slice 1 (rendered audit, `frontend/scripts/contrast-audit.mjs`, 96 rows, ~5.5 min)
Text: **one** real failure, the "Ayah" label in `button.wheel-pill` (Quran): 3.33 ink / 2.77 dark /
2.44 parchment. Controls: `--border` on cards reads 1.4–1.5:1 everywhere (an upper bound: a filled
tile passes on its fill, WCAG 1.4.11); Timelines hue borders 1.9–2.4; parchment rose/gold edges
(`close`, `Try again`, `lift`) 1.26–1.55. Small targets at 390: nahw 105, settings 57, quran 22,
daleel 18, dict 17, quiz 16 … repeat offenders `.icon-button` 40×40, `.cta.type-small` 84×36,
close 28×28, `button.w-8.h-8`. `a.sr-only` is noise → exclude.
### Worker · slice 2 (sources)
al-Wasitiyya on OpenITI (Shamela0022665, 69 KB; JK000359 49 KB). Jawhara and Tuhfa **not on
OpenITI**. Orchestrator: the Jawhara matn is on Arabic Wikisource (public domain, vowelled,
**144 bayts**, 22 blocks) → fetched to the scratchpad. Tuhfat al-Murid has no clean digital text we
may ship → the Ashʿarī world teaches the Jawhara's own words, with our English drawn from the
Tuhfa's well-known explanations (as the Tahawiyya world does), never a quoted Tuhfa passage.
### Critic · task 3 (research)
Comfort: caps confirmed by APCA (text Lc ≤ ~90 dark); **gap: Midnight `text-dim` is Lc 54** (WCAG
7.8 passes, still faint for small type) → add `dim-min-lc: 60` floor + test. Motion picks (≤3):
(1) one `.reveal` scroll-rise with capped stagger; (2) elevation tokens e0–e3 (layered shadow +
1px inner highlight) + ≤3° tilt on fine-pointer hover only; (3) static 3–4% grain on the ground
(never animated). Rejected: WebGL, scroll parallax, wide glass blur. Term-tree patterns: label the
split by its **question** (`by`), diff cards for confused pairs (`axis`), optional `lugha`.

## Stage 2 gate: passed (option families + unknowns above). Critic's cuts accepted:
C3 cut; A5 → grep audit only; sharh side-by-side → stretch; easing sweep → durations +
cubic-bezier only; A1 gains A1b (APCA floors); A3 becomes three concrete fixes.

## Stage 3 · Architecture

### Track A — candidates
| | i · measure → fix tokens, keep the audit | ii · runtime comfort layer (tone text too) | iii · per-screen overrides |
|---|---|---|---|
| Speed | 5 (CSS only) | 3 (JS on every look switch) | 4 |
| Quality | 4 (audit + theme.test hold it) | 3 (new maths, regressions) | 2 |
| UX | 4 | 4 | 3 |
| Maintainable | 5 (one token each) | 2 | 1 (sprinkles) |
| Novelty | 3 | 4 | 1 |
**Pick i.** Loser ii: the only win is auto-toning text; one `dim-min-lc` floor + test gets that.
Components (level 3→4):
- `theme.json` → `themes.comfort.<scheme>.dim-min-lc: 60`; Midnight `text-dim` raised to meet it;
  `type` gains nothing; `motion` gains `loop-ms`, `enter-ms`, `ease` (one cubic-bezier string);
  `layout.tap-min: 44`; `shadow.e1..e3` + `glass.grain` (alpha).
- `theme.test.js` → APCA Lc of `text` ≥ 75 and `text-dim` ≥ `dim-min-lc` on every ground.
- `styles/palette.test.js` (new) → colour-literal allowlist (masks, entities) fails on a new literal.
- `styles/keyframes.test.js` → also fails on literal `Nms` or `cubic-bezier(` outside motion.css.
- `ui/Segmented.jsx` → wraps under `layout.phone` width; `.icon-button`, close/dismiss → `tap-min`.
- `styles/motion.css` → `.reveal` (rise + fade, `--i` stagger, capped 6), `.e1/.e2/.e3`, `.tilt`
  (fine pointer only), ground grain in `shell/Backdrop`. All read `motionOff()` via `--motion-scale`.
- Quran wheel-pill label → `--text-dim`; watermark + فهم art `aria-hidden`; stray "4" badge; Home
  phone placeholder copy (`home.json`).
Spike: none needed (all CSS/tokens).

### Track B — candidates
| | i · Terms view in Hadith over usul glossary (PbsChart ≥ 640, list < 640) | ii · terms in the Map's chart | iii · a Terms tab |
|---|---|---|---|
| Speed | 4 | 4 | 3 |
| Quality | 5 (backend-checked data, one source) | 2 (duplicates glossary) | 4 |
| UX | 4 (where hadith readers already are) | 3 | 3 (one more tab) |
| Maintainable | 5 | 2 | 3 |
| Novelty | 3 | 2 | 2 |
**Pick i.** Loser ii recorded: the Map stays an overview; its hadith card may link to the view later.
Contracts:
- `usul.json.glossary[]` → `{title, ar, by?, terms[{ar, en, say, lugha?, quote, book, page, kind?,
  kids?[same shape], confuse?[{ar, why, axis}]}]}`; target ≥ 40 terms, ≥ 10 confuse pairs.
- `store.glossary()` → same tree in API shape (`arabic, en, meaning, lugha, quote, source, page, kind,
  kids, confuse[{arabic, why, axis}]`, group `by`); `store.glossary_faults()` → list of strings
  (dup ar; confuse target not a term; kind unknown to `rulings`); the app stops on faults at load,
  `tests/test_usul_glossary.py` covers each fault.
- `lib/termsChart.js` (pure) → glossary → `{root, branches[{ar, en, c, kids:[[ar,en]]}]}` for
  `chartTree`/`PbsChart`, colours from `theme.json` `pbs` hues by group index; `termAt(glossary,
  arabic)` → the term + its group; tested, mutation-checked.
- `hadith/TermsView.jsx` → `useQuery(usulGuideQuery)`; ≥ `layout.phone` → `PbsChart` (zoom into a
  group), tap a leaf → `TermCard`; below → `TermGuide` groups as `Disclosure`s, tap → same card.
- `hadith/TermCard.jsx` (BottomSheet) → meaning, lugha, quote + source/page, confused-with rows
  aligned on `axis`, "hadith carrying this" via `usulTermQuery(kind)` when `kind`.
- `HadithPanel` → `listing === TERMS_PLACE` renders `TermsView`; `HadithMoreMenu` gains "Terms".
- Security: read-only, no new route.

### Track C — candidates
| | i · one Grow book world per text | ii · generic OpenITI reader tab | iii · Memorise book entry (Jawhara) |
|---|---|---|---|
| Speed | 4 | 3 (new routes) | 5 |
| Quality | 5 (word-for-word test exists) | 3 (teaches nothing) | 4 |
| UX | 5 (lessons, progress, review) | 2 | 3 |
| Maintainable | 5 (data only) | 3 | 5 |
| Novelty | 3 | 2 | 3 |
**Pick i**, iii as a stretch (the Jawhara is a poem: Memorise's `books.js` could list it like the
Jazariyya). Loser ii: a reader with no progress is what Daleel already half-does.
Contracts:
- `backend/data/books/openiti/` gains Wasitiyya (Shamela0022665); `backend/data/books/wikisource/`
  gains the Jawhara written in the same `# ` / `~~` / `### | ` shape with a header naming the source
  (Wikisource, public domain) and the bayt numbers; `openiti-books.json` gains an `aqida-books`
  collection (Tahawi, Wasitiyya) so Daleel also searches them.
- `bookLesson.test.js` → a book `file` holding a `/` is read from `books/<file>`, else from
  `books/openiti/<file>` (one line).
- `worlds.json` → three worlds of kind `book`: `wasitiyya` (module `wasitiyya`), `shashi`
  (`shashi`), `jawhara` (`jawhara`), colours in `theme.json` `world`, each `idea` naming the school.
- `public/grow/<book>.json` → walking skeleton = ≥ 2 parts, ≥ 4 lessons, ≥ 24 cards each, every
  `ar` word-for-word from the file (the test proves it), `madhhab` line names the school.
- Security: static files only; no new API.

Level-4 gate: every slice below names its component; nothing invents a name.

## Stage 4 · Slices (walking skeleton first; each runnable + testable)
A1 audit script lands (worker) · A2 palette/keyframe literal tests + 16 duration fixes · A3 tap-min,
Segmented wrap, dismiss, badge, placeholder, aria-hidden · A4 comfort floor + Midnight text-dim +
wheel-pill label · A5 motion vocabulary: `.reveal`, elevation, grain, tilt on Home tiles + lists.
Pre-mortem A: "fails because raising text-dim breaks the max-contrast cap" → test both bounds.
B1 glossary data + faults + backend test · B2 `termsChart` + tests · B3 TermsView/TermCard + menu +
render test. Pre-mortem B: "tree too wide on 640–900px" → zoom at group level by default.
C1 files + manifest + import + test seam · C2 three skeleton books · C3 worlds.json + theme + tests.
Pre-mortem C: "a card quotes a line the test can't find" → author from the file's own lines only.
Each track: lint + 1700 tests + audit re-run → PR → CI → squash merge → Production deploy check.

## Stage 3 gate: passed, with the critic's changes
- Terms tree: `PbsChart` is 1784px wide for 7 groups → **< 1100px: group list, tap a group → the
  chart of that one branch; ≥ 1100px: the full tree.** Render test asserts a rendered label ≥ 12px.
- `lib/termsChart.js` builds the `{ar,en,c,kids}` tree itself and hands it to `layoutChart`/`PbsChart`
  (never `chartTree`, whose DEEP/SUB keys belong to the Map).
- Glossary diff rows: group-level `axes: [{id, q}]` + per-term `answers: {id: text}` (any two terms
  in a group line up); `confuse: [{ar, why}]` names the pair. `glossary_faults` also checks every
  answered axis is in its group. Faults stop the backend at startup (as dawah does), tested.
- `TermCard` degrades to `EmptyState` when the rulings index is not built; render test mocks it.
- Track C cut to **two worlds: jawhara (Ashʿarī) + wasitiyya (Salafi)**, ≥ 2 parts, ≥ 3 lessons,
  ≥ 16 cards each; Usul al-Shashi next run; Memorise entry for the Jawhara is the stretch.
- The Jawhara is written into `books/openiti/` in OpenITI shape (`build_jawhara.py`, 21 slips
  corrected, `tests/test_jawhara.py`), so neither the book test nor the importer changes; it joins
  Daleel under a new `aqida-books` collection with Tahawi and the Wasitiyya.
- Midnight `text-dim` floor test also keeps |Lc(text)| − |Lc(text-dim)| ≥ 15.
