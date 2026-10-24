# Colloquial: a map

Spoken Arabic as one tree, the same shape at every layer:

```
dialect → unit → topic → phrases · dialogue · words · exercises
```

Every dialect walks the same spine (data/colloquial/spine.json), so the same unit
and topic exist in each; a dialect that has not written one shows it as Coming.
Every module opens with a docstring that says what it owns. Read that before you edit it.

## Where each thing lives, once

```
data/colloquial/                         the content
  spine.json        the tree: units, topics, the slots each topic fills, the word ids it teaches
  dialects.json     each dialect's card: name, where, countries, cities
  words.json        every meaning once (English, group, picture); <dialect>/words.json says it
  <dialect>/unit-NN.json   that dialect's phrases for the spine's slots
  images/           pictures, shared by every dialect (emoji/chosen.json: which emoji means which word)
  colloquial.json   the content rules (knobs.py checks them)
  FORMAT.md         how to write a unit

backend/services/colloquial/             the reading
  schema.py         what reaches the page: the one list of fields per level (DialectCard → UnitCard
                    → TopicCard; Unit → Lesson → Phrase). The loader builds through these models,
                    so a field added here and in the data needs no other edit
  loader.py         the files → the catalogue, a unit, a comparison
  wordlist.py       a topic's word ids → each dialect's Arabic
  exercises/        one file per exercise type + registry.py (the union the schema names)
  wordcheck.py      is a word in an independent reference (scripts/colloquial/check_colloquial_words.py)
backend/routers/colloquial.py            the routes, typed by schema.py

frontend/src/                            the drawing
  components/colloquial/ColloquialPanel.jsx         the tab: where the reader is, and which level to draw
  components/colloquial/
    course/         the lists above a topic: Lists (dialects, units, topics), Cards, Trail
    topic/          one topic: TopicView and its sections (Dialogue, Pairs, Mosaic, Sheet, OtherDialects)
    words/          a topic's words: WordsView, its modes (cards, match, review) and the unit's WordBank
    exercises/      one file per exercise type + registry.js, mirroring the backend's
    parts/          small pieces every level uses (PhrasePicture, Spelling, Face)
  lib/colloquial/   logic with no drawing: place (the tree as a URL), answer, wordGroups, wordPractice
  colloquial.json   the page's own knobs (not the content rules)
```

## Adding something

- A field on a card → schema.py and the data. The drift test in tests/colloquial/test_colloquial.py fails if
  the data has a key the schema drops.
- An exercise type → one file in backend `exercises/` and one in frontend `exercises/`, a line in each registry.
- A dialect → its entry in dialects.json, a folder of units, its words.json.
- A word's picture → its id in images/emoji/chosen.json, then `scripts/colloquial/emoji_pictures.py`.
