"""Grade recitation ears on the reviewer-marked recordings, and say whether a new one is kept.

    python -m backend.scripts.recitation.ear_bench                  the ear in config
    python -m backend.scripts.recitation.ear_bench OLD NEW          NEW against OLD, with a keep-or-drop verdict

words.py loads the marked words, measures.py is the maths, keep.py the rule, bench.json the knobs.
Each model needs rescore_recitation.py run on it first.
"""
