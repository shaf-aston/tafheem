"""Hadith: the books, the search, the cut between chain and text, the narrators and the weak points.

Open `loader.py` first: it is the only reader of hadith.db (collections, books, hadith).
`search.py` finds hadith by words, helped by `lemma.py`, `repair.py`, `words.py` and `meaning.py`.
`chain.py` cuts each Arabic text into chain, teller and body by data/hadith/chain.json; the app,
the index and the usul build all use that one cut. `rijal/` reads the narrators (rijal.db);
`usul/` the weak points and scholars' rulings (usul.db). All served by `routers/hadith.py`.
"""
