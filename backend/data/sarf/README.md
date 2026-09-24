# Sarf data

- **patterns.json**: the sound-root conjugation templates. Read by
  `services/conjugation.py`. Hand-written, edit directly.
- **babs.json**: the six Form I bab codes, quadriliteral form-name spellings,
  and which sources to try in order. Read by `services/conjugation.py`
  (`babs()`) and `services/verb_forms.py`. Hand-written, edit directly.
- **lane_verbs.json**: every Form I bab Lane's Lexicon states, keyed by bare
  past. Read by `services/verb_sources/lane.py`. Derived from
  `data/lexicons.db`; rebuild with `python -m backend.scripts.build_lane_verbs`.

**Gotcha:** lane_verbs.json is derived from lexicons.db; fix the reader
(`scripts/build_lane_verbs.py`), never the file.
