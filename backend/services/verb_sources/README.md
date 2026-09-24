# Verb sources

A source states which باب a verb takes. `verb_forms.babs_of()` asks every
one named in `data/sarf/babs.json`'s "sources" list and keeps every reading
any of them names.

**Contract every adapter keeps:** `verb_forms_of(word) -> list[dict]` returns
every verb form filed under the typed word's letters (fold the word with
`conjugation.bare()` first; Wiktionary also drops the shaddah, because its
file keeps كَتَبَ and كَتَّبَ together); `[]` when the source records nothing.
`verb_forms._pick` then keeps only the forms whose past matches what was typed.

**Registry:** `SOURCES` in `__init__.py`, one name to one function.

**Add a source, in three files plus a test:**
1. One file here with `verb_forms_of(word)` keeping the contract above.
2. One name added to `SOURCES`.
3. One line added to `data/sarf/babs.json`'s `"sources"` list, and one entry
   in `backend/data/sources.json` with `"used_in": ["sarf"]`.

Done when `tests/test_verb_forms.py` passes; it asserts every name in
babs.json's list is wired in `SOURCES` and credited in `sources.json`.

**Gotcha:** fold with `conjugation.bare()`, never a fold of your own; it is
the only fold that turns the joining alif ٱ into ا.
