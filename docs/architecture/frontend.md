# Frontend architecture

What the app is made of today, and the plan for the four big changes still left
from the frontend review. Paths are relative to `frontend/src`.

## User Flow

open `/app/<tab>/<place>` → `lib/tabUrl.js` reads the path → `App.jsx` shows the tab
→ the registry `lib/tabs.js` lazy-loads that tab's panel → the panel asks for data
through react-query → `api.js` → backend `/api`. Moving to another tab goes through
the same `show()`, and `lib/journey.js` records it for back and forward.

## Core Parts

| Layer | Part | Job |
|---|---|---|
| Entry | `App.jsx` (259 lines) | Shell: draws the header, the panels and the overlays; the logic is in the hooks it calls |
| Entry | `lib/tabUrl.js`, `lib/journey.js` | Path URL ↔ tab, back/forward |
| Core | `lib/tabs.js` | One registry: every tab, its label, icon, colour, panel |
| Core | Nav surfaces: `ui/TabStrip`, `ui/BottomNav`, `SectionsMenu`, `SpatialHome`, `CommandBar` | Five ways to move between tabs, all read the registry |
| Core | `lib/useTabNavigation.js` over `lib/recent.js` (wide-screen strip) and `lib/dock.js` (phone bar) | Every way between tabs; which tabs each bar shows, one rule per screen (ADR-2) |
| Core | Panels: `MemorisePanel` + `memorise/hooks.js`, `QuizPanel` + `QuizBoard` + `lib/useQuizRound.js`, `TarkeebDiagram`, … | The screens |
| Data | `api.js`, `lib/quizBanks.js` | axios client, query keys shared by react-query |
| Config | `theme.json` → `theme.js` → CSS variables; `settings.json` | Colours, Arabic size ladder, motion durations |
| Style | `styles/motion.css` + per-feature CSS | Animations, 52 keyframes |

## Visual Architecture

```mermaid
flowchart LR
  URL[Path URL] --> TabUrl[tabUrl]
  TabUrl --> Shell[App shell]
  Shell --> Journey[journey]
  Registry[tabs registry] --> Shell
  Registry --> Strip[Desktop strip]
  Registry --> Bar[Phone bar]
  Registry --> Sheet[All sections sheet]
  Registry --> Launcher[Round launcher]
  Registry --> Search[Command bar]
  Recent[recent rule] --> Strip
  Dock[dock rule] --> Bar
  Shell --> Panel[Lazy panel]
  Panel --> Query[react-query]
  Query --> Api[api.js]
  Api --> Backend[(Backend /api)]
  Theme[theme.json] --> Vars[CSS variables]
  Vars --> Panel
```

## Future Architecture & Known Debt

Ranked by risk. Each item ships as its own small PR. Every step leaves the app
working.

| # | Debt | Why it hurts | Plan |
|---|---|---|---|
| 1 | No way to render a screen in a test | Only pure helpers and static markup are tested. Nothing catches a screen that throws on open | Phase A |
| 2 | 52 keyframes, about 20 near copies (fade, rise, pop, pulse) | The same move looks slightly different from place to place, and every copy needs its own reduce-motion care | Phase B |
| 3 | The Tarkeeb chart only scrolls | Long sentences go off the screen; deep trees grow tall | Phase C |
| 4 | `QuizPanel` main function is about 450 lines | Setup, scope, four queries, scoring and 170 lines of markup in one place | Phase D |
| 5 | `MemorisePanel` file is 621 lines | The panel is already thin (state lives in `memorise/hooks.js`), but four sub-components share the file and `hooks.js` (454 lines) has no tests | Phase D |
| 6 | Tab moving, tools and the header all in `App.jsx` | One 320-line function owned the active tab, the tabs kept alive, hand-offs, back/forward, the bars, the tools' armed and done looks and the banner | Phase E |

### Phase A: render-test seam

Status: steps 0 and 1 done, and the quiz half of step 2 (`src/test/`). The fake
backend answers static files from `public/`, so the quiz runs on the real word
banks. Still to do: the memorise gap.

0. Walking skeleton: add `happy-dom` + `@testing-library/react` as dev
   dependencies, plus `src/test/render.jsx` (a fresh `QueryClient`, data filled in
   with `setQueryData`, `api.js` mocked). One test renders one small panel.
1. A smoke test per core screen: Quran, Memorise, Quiz, Tarkeeb, Dictionary. Each
   one opens without throwing and shows its main heading or control.
2. One interaction per core flow: answer a quiz question, reveal a memorise gap.

Fitness: `npm test` runs them; a screen that throws on open fails CI.

### Phase B: one set of animations

Status: done for fade and rise. Nine copies are gone (52 → 44 keyframes), each
place now sets only its knobs, and `styles/keyframes.test.js` fails on a new
copy. The pop and pulse groups stay as they are: each one ends somewhere
different (overshoot, ring out, glow), so none of them is a copy.

0. Pick the shared moves in `styles/motion.css`: `fade-in`, `fade-out`, `rise-in`,
   `pop`, `pulse`. Their distance and scale come from CSS variables, so a feature
   changes how far, not which keyframe.
1. Swap the exact copies first (`entry-rise`, `sh-fade`, `grow-fade`, `late-in`,
   `xp-rise`), one file per commit.
2. Then the near copies (`pbs-rise`, `ayah-rise`, `cb-drop`, `grow-popin`,
   `grow-pulse`, `xp-pulse`), with the distance passed as a variable.
3. Fitness test: a vitest that reads every CSS file and fails when a new
   `@keyframes` only animates opacity/translate/scale outside `motion.css`.

One-off moves (mascot, landing art, mic) stay where they are.

### Phase C: Tarkeeb chart fits any screen

Status: done. The chart shrinks as a whole (CSS `zoom`) to fit, floored at
`arabic.chart-fit-min` (0.7), then scrolls. Dots and jumps read word positions
off the screen, so they stay right when shrunk. Rows past the first four fold
behind "▸ N more rows"; book examples (at most 4 rows) never fold, long ayahs
(18:1 has 7) do. The fold state lives in the diagram itself, not in
`useTarkeebView`: only the diagram reads it, and the larger view (`whole`)
always draws every row.

0. Fit to width: `TarkeebDiagram` already measures the scroller through `useRail`.
   When the grid is wider than the scroller, set a per-chart
   `--arabic-chart-rem` scaled down, never below `arabic.small-rem`. Past that
   floor it scrolls as it does today.
1. Fold deep levels: show only the top N rows of names (N in `theme.json`); the
   folded lower rows open from a "▸ more" chip. The open/closed state sits in
   `lib/useTarkeebView.js` next to split/merged and maximise.
2. Unit tests in `tarkeebLayout.test.js` for the fold (levels count from the
   leaves, so "deep" is measured from `levels.length`).

### Phase D: smaller screens (needs Phase A)

Status: Quiz done (steps 0 and 1). `QuizPanel` is 184 lines (was 510): it joins
`useQuizSetup`, `useQuizQuestion`, `useQuizRound` and `useQuizScore` and draws
the page; the setup line is `quiz/QuizSetup`, the note is `lib/quizNote` (tested).
Memorise step 2 done: `MemorisePanel.jsx` is 322 lines (was 621); `Line`, `Gap`,
`RecitedWord` and `SimilarCards` are each their own file in `memorise/`. Lint
does not catch a JSX component left unimported, so the move was checked by
scanning every tag against the imports, and by the same Playwright run (Type,
Pick from 4, Recite, Check) on old and new code. Step 3 (hooks.js tests) next.
Sarf done: `SarfPanel.jsx` is 76 lines (was 551); the word, the three requests
and the table they add up to are `lib/useSarf`, and the result, gardaan, cards
and titles are each their own file in `sarf/`. `test/sarf.test.jsx` types a
word and finds its root and its table cell.

Quran reader split: `quran/QuranReader.jsx` is 192 lines (was 508) and only
draws; `useSurahReading` holds the text, glosses, translation and recitation,
`useSurahPlace` the place, scroll, split and keys. `AyahList`, `AyahRow`,
`GlossedAyah`, `AyahRail` and `SplitBar` are each their own file in `quran/`,
and `test/quranReader.test.jsx` steps a surah and swaps the translation.

0. Quiz: move the setup into `useQuizSetup`: language, direction, bank, scope and
   group, the four queries, then `pool` and `question` derived from them. Move the
   score into `useQuizScore`: the score, best, `onAnswer` and its streaks.
   `QuizPanel` keeps the markup only. Render test first, then move.
1. Pull the `note` nested ternary out into one named function.
2. Memorise: move `SimilarCards`, `Line`, `RecitedWord`, `Gap` into
   `components/memorise/`. No behaviour change.
3. Split `memorise/hooks.js` one file per hook, with tests for `useGaps` and
   `useBookPage` through `renderHook`.

Fitness: no component file over 400 lines; no function over 50 lines in these
screens.

### Phase E: one navigation module (needs Phase A)

Re-read before building, the plan changed. The surfaces are not five ways to do
one job: the strip is the wide screen's bar, the bottom bar is the phone's, All
sections is the one list (and where the phone bar is arranged), and the header
search and the launcher share `useCommandLine`. Every one reads `lib/tabs.js`.
What was tangled was the code behind them, all inside `App.jsx`.

Status: done. `lib/useTabNavigation` owns every way between tabs (active, kept
alive, hand-offs, back arrow, number keys, strip, dock, the practice report for
the pen); `lib/useTools` the tools' armed and done looks; `shell/StatusPill` and
`shell/BackendBanner` (which owns its own dismissal) moved out. `App.jsx` is 259
lines (was 435) and only draws. `src/test/app.test.jsx` opens the whole app and
switches tab. The same Playwright run of every shell action gives the same
results before and after.

### ADR-1: the round launcher stays

- Status: accepted.
- It is the pen's click, the app's look, and it holds no list of its own: it
  draws `LISTED` and searches with the header's `useCommandLine`. Removing it
  would save one file and lose the identity.

### ADR-2: two bar rules stay, one per screen

- Status: accepted.
- A phone has four slots under the thumb. Tabs that move by themselves there
  break the reach the hand has learned, so the reader pins them (#454). A wide
  screen has eight, where recent tabs that keep their places (#478) cost nothing.
  The rules differ because the screens do; both live behind
  `useTabNavigation`, so a change to either is one file.
