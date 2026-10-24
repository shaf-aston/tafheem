"""Daleel: one search across every book the app holds.

Open `search.py` first: it is the whole pipeline in a dozen lines. Then, one
folder per step, each opening with a docstring that maps it:

    search.py       search(query) → [Hit], the one entry point
    catalogue.py    which books there are, and their English names
    query/          typed words → an Expansion of terms to look for
    index/          daleel.db: the connection, the candidates, each source's share
    match/          pure word rules: ranking, typo distance, marking the words found
    sources/        the books, one adapter each; registry.py lists them

Served by `routers/daleel.py`; `scripts/daleel/build_daleel_index.py` builds the index
from `sources/`. Try any query without the app: `python -m backend.services.daleel صبر`.
"""
