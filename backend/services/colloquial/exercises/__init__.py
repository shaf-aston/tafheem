"""Colloquial exercise kinds: one module per kind of practice.

Open `registry.py` first: it names which module owns which exercise type. `base.py` holds what
every exercise has; `choose.py`, `reorder.py` and `typed_answer.py` add their own parts.
`services/colloquial/loader.py` checks each exercise on load, and the page draws it with the
matching renderer in `frontend/src/components/colloquial/exercises/registry.js`.
"""
