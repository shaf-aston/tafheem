"""Reading daleel.db: the one place that knows SQL.

`connection.py` opens the file (and says whether it is built), `row.py` is the
shape every query reads a passage in, `candidates.py` asks the index for the
passages that could match, and `share.py` hands each source its fair share of
them, reading a common word's share from `champions.py` (scored when the index
was built) when that gives the same answer. Built by `backend/scripts/daleel/build_daleel_index.py`.
"""
