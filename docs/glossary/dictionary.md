# Dictionary glossary

One word per idea, the same in the backend, the API and the frontend. Where the code
uses one word for two ideas, the second column says which is which. Main glossary:
`CORE-FLOW.md`.

| Word | Means | Backend / API field | Frontend |
|---|---|---|---|
| **root** | the letters typed or clicked | `?root=` | `asked` (as typed), `root` |
| **book root** | the root as one book spells it, sent only when it differs | `book_root_of`, `book_root` | `entry.book_root` |
| **entry** | what one book prints under one root or word. Three kinds: a word's (Wiktionary), a Maqayees root's, a shelf book's | `dictionary_service`, `root_meaning.Entry`, `lexicons` | `Entry` (word card), `RootMeaningCard`, `BookEntry` |
| **origin sense** | Ibn Faris's first sentence: what the letters mean at heart | `core_meaning` | `core_meaning` |
| **rest** | the Maqayees entry after the origin sense | `root_gloss.rest_of`, `rest` | `rest` |
| **view** | how the rest is read: `together` (one English text), `lines` (each line with its English under it), `one` (one line at a time) | `/root-meaning/english`, `/root-meaning/english/lines` | `VIEWS`, `LinePage`, `LineSpotlight` |
| **line** | one Arabic sentence of the rest paired with its English; the backend pairs, the frontend never re-cuts | `lines: [{arabic, english}]` | `pair` |
| **verse gap** | the space down the middle of a line of poetry; must match on both sides | `VERSE_GAP` (root_gloss.py) | `VERSE_GAP` (lib/entryLines.js), `halves` |
| **shelf** | Lisan, Taj and Lane together under the Maqayees card | `/lexicons`, `entries[].book` | `LexiconShelf` |
| **book** | one dictionary on the shelf, by id: `lisan`, `taj`, `lane`, `maqayis` | `book` | `entry.book`, `LANE` |
| **headword** | one word Lane opens a section with | `head` (db column) | `form.word`, `LaneIndex` |
| **form** | (1) a verb form I to X; (2) in Lane, one headword's section | `verb_forms` | (1) `form.form`; (2) `forms[i]` |
| **sense** | one numbered meaning in Lane; a `sub` sense qualifies the one above | | `laneEntry` `sense.kind` |
| **bab** | the vowel pattern a verb follows, only as Lane or Wiktionary states it | `verb_forms.babs_of`, `/babs` | `RootBabs`, `VerbFormTag` |
| **pronunciation** | a word's sound in plain English letters | `transliteration` | `Pronunciation` |

**Known overlaps, kept on purpose** (renaming would break saved data or the API):
`english` names four things (origin-sense gloss, whole-rest English, a line's English, a
book title's meaning); read it by where it sits. `rest-lines` in `dictionary.json` is a
height, not a count of lines. The book id is `maqayis`, the name on screen Maqayees.

**Saved choices** (browser): `dict.entry-view`, `dict.lines-tap`,
`dict.lines-try-first`, `lane-tidy`, `dict-history`.
