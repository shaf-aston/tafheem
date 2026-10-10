"""Colloquial exercise kinds: one module per kind of practice.

Open `registry.py` first: it lists the modules and checks any exercise against all of them.
`base.py` holds what every exercise has; `choose.py`, `reorder.py` and `typed_answer.py` add
their own parts. Each module's models are the one description of its exercises, rules included.
`services/colloquial/loader.py` checks each exercise on load, and the page draws it with the
matching entry in `frontend/src/components/colloquial/exercises/registry.js`.
"""
