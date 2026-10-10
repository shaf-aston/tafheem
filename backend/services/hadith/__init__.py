"""Hadith: the books, the search, and the cut between chain and text.

Open `loader.py` first: it is the only reader of hadith.db (collections, books, hadith).
`search.py` finds hadith by words, helped by `lemma.py`, `repair.py`, `words.py` and `meaning.py`.
`chain.py` cuts each Arabic text into chain, teller and body; the app, the index and the usul
build all use that one cut. Served by `routers/hadith.py`; the narrators come from `services/rijal`.
"""
