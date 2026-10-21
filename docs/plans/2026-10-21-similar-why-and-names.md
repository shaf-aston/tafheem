# Similar: why they differ, bigger type, one name

Date 2026-10-21 · `/plan-build` on https://tafheem-app.vercel.app/app/similar

## Criteria (checked)

| # | Criterion | Result |
|---|---|---|
| 1 | A tab's name is written once: grep "Similar verses" in src (non-test) → 0 | 0; `lib/tabs.js` holds `Similar`, SectionHeader reads it via `tab="similar"`. Hadith (5 places), Memorise, Quran, Colloquial, Kit, Quiz, Grow moved to the same `tab` prop |
| 2 | Tab label fits one line at 1280 | yes (screenshot) |
| 3 | No `type-tiny` in Similar; pair refs at ui size (14px), labels at 12px, drill text at 14px | yes |
| 4 | Wide screen: both verses side by side over their own difference columns | yes; page 1,635px with Why open |
| 5 | Meaning layer: per difference, each side's English + each word's role; per verse, the translation + one tafsir; fetched only when opened | `similar/Why.jsx`; test proves no Qur'an call until opened |

## Design

Two candidates for the meaning layer. (A) Reuse `AyahTafsir` twice and `WordCard` for grammar: two book pickers, two walls of text, the drill page triples. (B) One `Why` disclosure under Compare: the differing words glossed from the reader's word-by-word grammar (`quranAyahQuery`, cached by the reader), the reader's translation (`useTranslation`), and one short tafsir (the reader's remembered `tafsir-edition`, else `similar.json.tafsir` = al-Mukhtasar, per-ayah and a paragraph long). B chosen: the logic in two lines, grows on demand, zero cost until opened.

```
Compare ─┬ Verse ×2 (sm:grid-cols-2)
         ├ differences · what comes next
         └ Why (Disclosure) ─ useContext(verse) ─ quranAyahQuery · useTranslation · getAyahEditions
                               Words: lib/similar.glossAt(words, grammar, span) → meaning + roles
                               Context: translation line + tafsir (ShowRest)
SectionHeader(tab) ← lib/tabs.js TABS  (title, arabic, emblem)
```

Pre-mortem: grammar word count ≠ imlaei word count → `glossAt` returns null and the side says so, never a meaning on the wrong word.
