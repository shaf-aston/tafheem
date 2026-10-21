# Similar verses (mutashabihat): accuracy check + a tighter flow

Date 2026-10-21 · `/plan-build` on https://tafheem-app.vercel.app/app/similar

## 1. Is the data accurate? (checked against the sources online)

| Question | Finding |
|---|---|
| Where do the pairs come from | Two places. (a) The *Quran-Similarities* benchmark (github.com/ambaqasah/mutashabihat, GPL-3.0): 2,229 pairs taken from two classical books on the subject, **Hidāyat al-Murtāb** (al-Sakhāwī) and **Tatimmat al-Bayān**. (b) A hafiz's list (Waqar144) built from Qari Idrees al-Asim's work. Merged by `backend/scripts/build_mutashabihat.py`: 3,156 pairs in 509 groups, 540 pairs recorded by both. |
| Are the highlighted words right | Worked out here on our own text with difflib on folded words (`services/mutashabihat.diff`), never copied from the benchmark's Tanzil text, so word positions cannot drift. Unit tests cover replacement, addition, order swap, pause marks. |
| Spot check of pairs every hafiz knows | 2:58/7:161, 2:173/16:115, 2:48/2:123, 6:151/17:31, 2:136/3:84, 2:34/7:11 → all present. 3:50/43:63 (فاتقوا الله وأطيعون) → missing. Coverage is strong but not total; the finder (`propose`) exists to fill gaps for review. |
| Coverage | 72 surahs have pairs; 40 short surahs (and al-Fatiha) have none, which matches the books (they list the long surahs). |
| Compared with other apps | Rusookh ships 272 pairs; HifzPath "a trainer for similar passages"; Quran Revision Companion lists twins per juz while reading; HifzMate lets the user mark their own. Ours is the biggest curated list of the set, with the difference marked word by word. |

**Verdict: accurate and usable.** Two real gaps, both fixed in this run:
1. **88 pairs are word-for-word identical** (27:3/31:4, 9:33/61:9, 26:8/26:67…). Compare showed "nothing here", Drill said "nothing to drill". But these are exactly the pairs a hafiz slips on: the tell is **what comes next**, not the wording. → the API now sends each verse's next ayah, Compare shows it, Drill asks it.
2. The benchmark's **change type** (replacement / addition / order) was stored but never shown. → shown as a plain-words tag.

## 2. Is the flow concise? (seen in the running app, 1280 and 390)

| Before | Problem | After |
|---|---|---|
| Sidebar lists all 294 pairs of al-Baqarah, one button each | 17,000px tall page on desktop; on a phone a strip of 294 chips cut off at the edge | Sidebar scrolls inside its own height on desktop; on a phone the list becomes a **Browse** sheet; a **Pair n of N** stepper walks the pairs |
| First thing on screen is "Mastered 0 / 294" and a list | No obvious first action | One **Start** button: continues the first pair that is due, else the first new one. Finishing a pair moves on to the next unmastered one, not the next by number |
| Compare → Drill is two taps + a segmented control | Fine, kept | Same, with the change-type tag and "what comes next" rows |
| Identical pairs | Dead end | Drill asks the continuation |
| Not reachable from the Qur'an reader | Apps show twins while reading; the reader already has `ayahs` with twins from the API but never used it | The ayah study shows "3 look-alikes →", which opens Similar at that ayah (`/app/similar/2/3`, shareable) |
| Footer "No sources are declared for this tab" | sources.json listed the two sources under `quran` only | `similar` added |

## 3. Architecture (level 3, components touched)

```
QuranReader ─ AyahStudy ──"look-alikes →"──▶ App.switchTab('similar', '2/3')
                 │ getSimilarSurah (cached)                 │ incoming/arrival
SimilarPanel ◀──────────────────────────────────────────────┘
  ├ lib/similarPlace  parse "2/3" ⇄ placeOf           (new, pure)
  ├ similar/hooks     useSurahPairs · usePair · useMastery · nextUp (new)
  ├ similar/PairList  desktop list / phone Browse sheet
  ├ similar/Compare   verses · tag · differences · what comes next
  └ similar/Drill     drillOf (lib/similar): wording questions + continuation question
backend
  services/mutashabihat.partners → + after (next ayah text, both sides)
  models SimilarAyah.after, SimilarPartner.after
```

Rejected: paging the list by juz (the catalogue is per verse; surah is how people memorise and the picker already exists). Rejected: a free-text recall drill (typing Arabic on a phone is the slow path; two-choice with the twin's wording as the distractor is what the printed books train).

## 4. Slices

| # | Slice | Check |
|---|---|---|
| S0 | backend `after` | test: identical pair carries different `after`; surah-end gives '' |
| S1 | lib: `drillOf` continuation question, `kindOf(change_type)` | similar.test.js |
| S2 | panel: Start/next-up, sidebar scroll, phone stepper + Browse sheet, tag, next rows | SimilarPanel.test.jsx |
| S3 | reader chip + similarPlace + arrival | similarPlace.test.js, AyahStudy test |
| S4 | sources, docs | useSources test |

Pre-mortem: S3 fails if the ayah study's surah query isn't cached → it is (`useSurahPairs` key `['similar-surah', n]`, staleTime ∞).

## 5. Shipped

All five slices in one PR (frontend 1769 tests + backend mutashabihat/sources tests green, eslint clean).
Seen in the running app: al-Baqarah's page fell from 17,488px to ~1,300px tall at 1280; the phone
shows Start, "Pair n of N" with a stepper and a Browse sheet; 27:3/31:4 shows "what comes next" and
drills it. The reader's "look-alikes" link is covered by a test only: this container's Qur'an
grammar endpoint 500s (missing `tokenizers`), so it could not be clicked here.

Next: feed the finder's proposals (`mutashabihat.propose`) through a review so gaps like 3:50/43:63
land in the catalogue; let the user pin a note (dabt) on a pair, the way HifzMate does.
