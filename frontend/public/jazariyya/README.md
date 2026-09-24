# Al-Muqaddimah al-Jazariyyah: the Memorise tab's second book

`poem.json` holds all 107 verses of Ibn al-Jazari's tajweed poem. Same pattern as
`frontend/public/words/` next door: a static file the browser fetches once, no
backend, no database, no AI at request time; fine for a small, fixed text with
one consumer.

## Where the Arabic comes from

Typed from our own scanned copy of the Arabic-only printed matn (`matn al
jazaria muqaddimah al jazaria ARABIC only.pdf`), verified by a page-by-page
vision pass against every printed line, then checked against the poem's own
closing line, "أَبْيَاتُهَا قَافٌ وَزَايٌ فِي الْعَدَدْ" (qaf=100 + zay=7 = 107)
which states its own verse count. The classical text is centuries old and
public domain.

## Where the English comes from

**Not** the translator's commentary in the study-edition PDF we also own, that
translation is the translator's own copyrighted work, and none of its wording
was read or reused. Each `english` field is a short gloss written fresh, from
the Arabic alone, describing what the verse says rather than translating it
word for word. It exists so a reader who is stuck has somewhere to look; it is
not a scholarly translation and should not be presented as one.

## Shape

```jsonc
{
  "bayt": [
    { "n": 1, "sadr": "...", "ajuz": "...", "english": "..." },
    ...
  ]
}
```

A **bayt** is one printed line of the poem split into two hemistichs, the
`sadr` (right half, read first) and the `ajuz` (left half, read second). The
pair is one memorisation unit and is never split across a page, the same way
`lib/books.js`'s Qur'an entry never splits an ayah.

`sections` names the traditional chapter headings (بَابُ ...) and which bayt
number each starts after, kept as data for anyone who wants to render them
later; the current UI does not need them.

## If a verse or gloss needs fixing

Edit `poem.json` directly, there is no build step, unlike `maqayees/roots.json`
next door. Keep `totalBayt` and the array length at 107; that number is the
poem's own internal checksum, not a guess.
