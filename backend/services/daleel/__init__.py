"""Daleel: one search across every book the app holds.

Open `search.py` first: it fetches passages from daleel.db and ranks them. `expand.py` turns the
typed words into search terms (using `lexicon.py`), `model.py` defines a Passage and a Source,
and `registry.py` is the one list of books. Each book is an adapter in `sources/`. Served by
`routers/daleel.py`; `scripts/build_daleel_index.py` builds the index.
"""
