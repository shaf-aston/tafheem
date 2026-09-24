# Maqāyīs al-Lugha: the classical root book

`roots.json` holds Ibn Fāris's origin sense for 4,738 roots. It is **derived, not
authored**: rebuild it rather than editing it.

```bash
pip install access-parser
python backend/scripts/build_root_meanings.py            # downloads the book
python backend/scripts/build_root_meanings.py book.bok  # or re-cuts a local copy
```

Restart the backend afterwards; the file is read once at startup. The
"Classical root sense" card in the Dictionary tab then fills in.

## Where the words come from

ʿAbd al-Salām Hārūn's edition, in six volumes, the same edition as the scanned
PDF, confirmed by matching printed page numbers. The book is out of copyright and
the Arabic was typed up by people for the Shamela library, so it is not a machine
reading a scan.

What the build script decides is only **where an entry starts and stops**. Ibn
Fāris opens each entry by naming the root's letters and stating its origin sense;
that statement is taken word for word. The entry list comes from the book's own
table of contents, so no root is invented.

That contents page is the editor's, and it is written the way the entry is
printed. A line arrives wearing his punctuation, and in the chapters of words
longer than three letters it wears the definite article, "(الْبَلْعُومُ)", and
sometimes the connective he opened the sentence with. Those are not letters of
the root, so they come off, and the entry is filed under its letters: `بلعوم`,
not `البلعوم`. Until that was done, 92 entries were missing and the entry above
each of them ran on and printed it as part of its own meaning; `عربس` carried
6,404 characters of the five entries after it.

The contents page is also not complete. Five entries, أن، جدف، حدأ، دفا، لمأ,
are printed in the book and absent from it. They are found in the prose instead,
by the one thing nothing else looks like: a bracketed word whose next words name
exactly its own letters, in order. `أم` had been carrying 615 characters of the
entry for `أه` that way.

## The files here

| File | What it is | Required |
|---|---|---|
| `roots.json` | the book, built | the output |
| `build.json` | every knob the builder turns, and the Arabic it looks for | yes |
| `spelling.json` | which spellings count as the same letter | no, but searches find less without it |
| `english.json` | a machine's reading of the scan, one line per root | no, and it is keyed without hamza signs, so it can never tell دفأ from دفا |
| `blanks.json` | roots the print leaves unreadable that the scan could read | no, and it now supplies none |
| `english_entries.json` | whole entries a model has already put into English | no, it fills itself |
| `scan-source/` | the raw page-by-page reading of the scan that `english.json` was cut down from | no, nothing loads it |

`english_entries.json` is a cache, not a source. Putting an entry into English
costs a call to a model and gives the same answer each time, so each one is kept
once it has been made, by a reader pressing the button, or by
`backend/scripts/backfill_root_english.py` doing the whole book ahead of time.
Deleting the file loses nothing but the time it took to make.

A reading in it is badged "the book's own words, put into English", because it
was made from the typed Arabic with the Arabic beside it and read back against it
by a second reader. A reading made in the second a reader presses the button, by
whichever model the app can reach, is badged "a guess"; the two are not the same
claim, and one badge over both would lend the second the standing of the first.

`scan-source/` is the archive behind `english.json`, not an input to anything.
The machine that read the scan recorded more per root than shipped: the Arabic
core meaning, the named ṣarf pattern, the variant usages with their citations,
and its own notes on what was illegible, and `english.json` keeps only the one
English line, the printed page and the page index. Re-running the reading over
the scan is the only other way back to the rest, so the folder is kept here
rather than in a scratch directory that gets cleared. `merge_maqaayees.py` is
the script that grouped the three page ranges by first root letter; it reads the
folder it sits in.

`blanks.json` is held to the same bar as the book: an opening that is a
manuscript gap, or that names only the root's letters, is not a meaning there
either. Every entry it once supplied has since come out of the book itself, so
it currently adds nothing, kept because the next reading of the scan may.

`build.json` and `spelling.json` are why the script holds no tuning value of its
own: re-cut the book differently by editing them, not the code. Both the builder
and `services/root_meaning.py` read `spelling.json`, so the file and the search
can never disagree about what أ and ا are.

## The shape of the file

```json
{
  "كتب": {
    "core_meaning": "الْكَافُ وَالتَّاءُ وَالْبَاءُ أَصْلٌ صَحِيحٌ وَاحِدٌ يَدُلُّ عَلَى جَمْعِ شَيْءٍ إِلَى شَيْءٍ",
    "sarf_pattern": "",
    "variances": [],
    "body": "… the whole entry, verbatim …",
    "english": "indicates gathering one thing to another"
  }
}
```

- `core_meaning`: required. A row without it is treated as no entry, so a blank
  line is never printed under Ibn Fāris's name. Where the editor closed the
  root's letter-enumeration with a full stop, the sentence after it is taken as
  well: an opening that names only the letters tells the reader what they typed.
- `sarf_pattern`: always empty here. This book gives origins, not patterns.
- `variances`: the separate origins, and only where Ibn Fāris marks them
  ("أحدهما … والآخر"). An entry that names several origins without marking them
  is left with none rather than a guessed split.
- `body`, the whole entry: his examples, the Qur'ān verses with their
  references, the poetry. Shown as prose behind "The rest of the entry", never
  cut into pieces. Three ways of measuring how often he marks where one sense
  ends gave 35%, 52% and 91%; a boundary three methods disagree about that much
  is not one to print a guess at. It stops where the next chapter of the book
  begins, so no entry carries a chapter it does not belong to.
- `english`, a plain gloss, and the only field here a machine read off a page
  image. It carries its own weaker badge on the card and is never merged into the
  Arabic.

## One root, one entry, two spellings

Each root is stored **once**, under the spelling Hārūn used. Matching a reader's
spelling to it happens at lookup, not by storing the entry twice, so `هدى` and
`هدي` both reach the one entry, in either direction, and the file carries no
duplicate keys.

The spelling searched is answered first, and only then a folded one. Two roots
that fold together are two different roots, `هنأ` and `هنا`, and neither is
ever allowed to answer for the other. When the book's spelling differs from what
was typed, the response carries `book_root` and the card says so, because an
entry about `بدأ` shown for a typed `بدا` would otherwise read as an answer about
the letters typed.

## What is not covered

Five entries the print itself leaves unreadable: بقم، روب، رتب، كسا، وضخ. Each
opens on the row of spaced dots the editor uses to mark a stretch he could not
read, so there is no sense to print.

Two more used to be on that list, أقر and وأق, and were not blank at all: the run
of three dots that separates the two halves of a line of poetry was being read as
one of those gaps, so both entries were thrown away and a machine's reading of a
photograph stood in for them, giving وأق "al-'usharrad" where the book says
al-ṣurad, the shrike. The gap mark now has to be spaced dots, and both entries
come out of the book in full.

One entry, `عشط`, is the letters and nothing else: the printed text of it is
incomplete, and the card shows it as the book shows it.

`قرأ` is absent. It has no heading in this typed copy and none in the second
typed copy either (see below), so it is missing from the transcription rather
than from this build.

## Somewhere else?

Set `ROOT_MEANING_PATH` in `.env` to the file, not the folder, which reads as
"not installed". Default: `data/maqayees/roots.json`. `spelling.json` is looked
for beside whatever that names.

## Proofreading

Two sources, two badges, because the Arabic and the English did not come from the
same place and one badge over both would lend the weaker the standing of the
stronger.

- The Arabic: `sources.json` marks `maqayees` as `derived`, "Worked out by a
  fixed rule". Six entries across four volumes were read off the printed page and
  matched exactly. A second typed copy of the same edition, made by someone with
  no connection to this app and shared as an Anki deck, agrees with **4,039 of
  the 4,723 entries the two share word for word**, boundaries included; 583 of
  the rest are places that copy itself ran past the end of an entry, and 3 are
  places both are illegible. That is strong evidence and not a reading: change to
  `verified` only once a person has held this text against the printed page.
- The English: two of them, and they are not worth the same.
  - `english.json`, badged `maqayees_english` / `guessed`. A machine read it off
    a photograph of the page and nobody has proofread it. It has been *measured*,
    though: 300 roots judged against the entry printed beside them gave 6 wrong
    outright and 28 saying less than the book does, roughly **one in fifty
    wrong, one in eleven thin**. The thin ones share a shape: the reader stopped
    at Ibn Fāris's opening clause and never reached the sentence holding the
    meaning, so `وسد` reads "a single isolated usage" where the book says
    *al-wisāda*, the cushion.
  - The first sentence of the whole-entry translation in `english_entries.json`,
    badged `maqayees_translation`. Made from the typed Arabic with the Arabic in
    front of it and read back against it by a second reader.
  Ibn Fāris always opens by naming the letters and stating the one sense, so
  these two say the same thing, and `services/root_gloss.py` prefers the second
  wherever it exists, which is also how the wrong and thin glosses above get
  retired one root at a time. The first is the fallback, and it shrinks as the whole-book
  translation run proceeds.
