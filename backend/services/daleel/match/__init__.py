"""Pure rules about words: no SQLite, no files, so each is tested on its own.

`words.py` says what counts as a passage using a term. `rank.py` orders the
candidates by it, `typos.py` measures how near a misspelling is, and `marks.py`
finds the same uses again in the text as printed, so the screen can underline
them. Nothing here imports `index/`; `index/` imports `typos.trigrams` from here.
"""
