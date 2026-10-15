"""Colloquial: spoken Arabic by dialect, from one course outline.

Open `loader.py` first: it is the only reader of data/colloquial and checks everything on load.
The outline is `spine.json`. A phrase unit fills its slots per dialect. Units 20 to 27 are word
units (`"phrases": []`), read by `wordlist.py` from `words.json`, with headings checked against
`groups.json`. `wordcheck.py` checks words against reference files. Served by `routers/colloquial.py`.
"""
