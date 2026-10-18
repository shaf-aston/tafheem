# I'raab engine: a map

How a typed sentence becomes word cards and a tree, and where to fix each kind of mistake.
Every module opens with a docstring that says what it owns. Read that before you edit it.

## The pipeline (`iraab.analyze`)

```
typed sentence
 → morphology.pick           one reading per word: CAMeL readings, ranked by BERT, chosen by the typed vowels
                             (harakat.vowel_agreement); sarf table (verb_reader) fills verbs CAMeL lacks
 → syntax.catib_onnx.parse   dependency links (head, rel) per token; mask.py bans links the book forbids
 → syntax.repair             corrects the parser's tokens in place, in a fixed order (repair/__init__.py)
 → syntax.particles          one reading per many-reading particle (لا، إلا، إذا ...), once per sentence
 → syntax.condition          where a شرط opens, by the book's test (shared by naming, tree and cards)
 → syntax.facts/*            the questions (axes) the naming tree splits on:
                               word      what a word shows alone: kind, typed case, listed families
                               kind      harf / fi'l / ism
                               slot      place in its clause: subject, object, predicate, hal, zarf
                               governor  which word works its case on it
                               follows   is it a تابع (naat, atf, badal, tawkeed)
                               voice     active / passive
                               sentence  the parsed sentence, with lookups built once
 → syntax.naming + walker    walks data/nahw_rules/naming_tree.json to each word's role; then
                             FINISHES (pair names, زائدة باء, كافة ما) add keys to each FoundEntry
                             (the typed schema every later step reads)
 → syntax.teacher            second reading; dashes a role the vowels or the rules reject
 → syntax.tree               the bracket picture (tarkeeb)
 → iraab.cards               one card per word: rule_engine (what the word is) + role
 → signs.settle              the sign (ضمة، مبني على السكون ...) from the final case
 → card_wording              the card's words after the sign: pair names, زائدة باء, كافة ما,
                             counted khabars, followers (backend/services/card_wording, fixed order);
                             a reason is held as parts (card_wording/reason.py) and written once
```

## Data (`backend/data/nahw_rules/`)

| File | Holds |
|---|---|
| `closed_words.json` | closed word families: inna/kana sisters, built words, mawsul, tamyeez heads... Edit it as text, because a JSON rewrite reformats the whole file |
| `roles.json` | role frames and evidence notes (conditions, answers) |
| `naming_tree.json` | the book's classification tree that walker.py walks |
| `particle_tree.json` | how a many-reading particle is decided |
| `teacher.json` | the teacher's checks |
| `*_sentences.json`, `answer_key.json` | scored sets; `score_baseline.json` is the gate |

## Where a mistake belongs

| Symptom | Look in |
|---|---|
| Wrong kind of word (verb read as noun) | `morphology.pick` (reading choice), `facts/word.is_verb`, `repair/typed.py` |
| Parser link is wrong but the vowels say otherwise | `repair/*` (one file per repair) |
| Right kind, wrong role | the matching `facts/` axis, then `naming_tree.json` |
| Role named for a governor that isn't there | `facts/governor.py` |
| Condition / answer wrong | `condition.py` |
| Right role, wrong sign | `signs.py`, `harakat.py` |
| Right role and sign, wrong wording on the card | `card_wording/` (one pass per feature; naming leaves the key it reads) |
| A closed list *is* the grammar (built words, sisters) | `closed_words.json`, read through `nahw_book`'s questions (`extra_ba_on`, `kaffa_sister`), never its raw shape |

## Adding a grammar feature that changes a card

```
closed_words.json (the list)  → nahw_book question  → naming FINISHES step (sets a FoundEntry key)
                              → card_wording pass (words the card from that key) → a parser-free test
```

Rule of thumb: fix the cause by a grammar rule. Never key a fix to one sentence or one hadith.

## Verifying a change

```
venv/bin/python -m pytest -q -p no:cacheprovider                 # full suite
PYTHONPATH=$PWD venv/bin/python -m backend.scripts.score_iraab --check   # no set may drop
PYTHONPATH=$PWD venv/bin/python -m backend.scripts.score_iraab --save-baseline  # only when better
```

Add each fix's test to `tests/test_rule_engine.py` with a **sibling sentence** the fix was not built
from. Then mutation-check it: revert the fix's file (`git show HEAD:<file> > <file>`), confirm the test
fails, and restore the file. A test that still passes guards nothing.
