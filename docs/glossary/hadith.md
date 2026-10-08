# Hadith glossary

One word per idea, the same in the backend, the API and the frontend. Main glossary:
`CORE-FLOW.md`.

| Word | Means | Backend / API field | Frontend |
|---|---|---|---|
| **level** | one of Ibn Hajar's twelve ranks of narrators (Taqrib preface); 1 is the Companions, 12 the liars | `level`, `narrator_level` | `level`, `p.level` |
| **scale** | the twelve levels with their Arabic, plain English, kind and the book each comes from; sent with the chains | `scale`, `store.scale()` | `scale` |
| **weak point** | a narrator at or below `weak_from` (level 5) named in a hadith's chain | `note`, `notes` | `weakPoints()` (`lib/weak.js`), `WeakPoints` |
| **kind** | the sort of weakness: `memory`, `innovation`, `unknown`, `weak`, `abandoned`, `lying`; level 5 holds two (رمي is an innovation) | `kind` | `p.kind` |
| **rank** | where a weak point stands among its hadith's, weakest first; equal levels share one and print as `2=` | none, worked out in the page | `rank`, `label` |
| **lift** | a line a source gives on whether support from another narration lifts a level's weakness, quoted; only a few levels have one | `lift` (usul.json, `scale`) | `p.lift` |
| **gap** | a grade wording no term reads (حسن الحديث, منكر الحديث); listed, never given a level | `gap` table | none |
| **ruling** | what a classical book says of one hadith, as the scholar's own sentence with book and page, found by matching its text and narrators; shown as "possible" | `ruling`, `rulings`, `store.rulings()` | `rulings`, `ScholarRulings` |
| **term** | one sort of ruling (`nasikh_chapter`, `ilal`, `mawdu_listed`) with its plain meaning and how many hadith carry it | `kind`, `store.terms()` | `ScholarTerms` |
