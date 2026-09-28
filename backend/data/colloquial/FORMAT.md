# How a colloquial unit is written down

One file per unit, `<dialect>/unit-NN.json`. The dialect folder is named in
`dialects.json` beside this file. A unit is self-contained: everything a learner
sees in it is in that one file, so a unit can be added, replaced or dropped on
its own.

```json
{
  "unit": "unit-01",
  "title": "First Conversations",
  "dialect": "Damascene Arabic",
  "transliteration_key": { "3": "ع", "7": "ح" },
  "lessons": [ ... ],
  "challenge": { ... }
}
```

`transliteration_key` explains the English letters and digits used for sounds
that have no English letter, so the spelling is never a mystery. Write the same
key in every unit of a dialect.

## A lesson

| field | what it is |
|---|---|
| `lesson` | `lesson-01`, counting from one within the unit |
| `title` | what the lesson is about, in English |
| `phrases` | the things to learn: `arabic`, `transliteration`, `english`, and optionally `reply` (the natural answer) and `search_term` |
| `dialogue` | one real conversation, in order: `speaker`, `arabic`, `transliteration`, `english` |
| `de_book` | question and answer drill: `pair` and `response`, each a phrase |
| `culture` | one or two sentences on when and with whom this is said |
| `exercises` | the practice, see below |

`search_term` is a short everyday English noun phrase for finding a picture, for
example `"a glass of tea"`. The English meaning alone is usually too idiomatic to
search with, so a picture is only ever fetched from `search_term`. Leave it out
when the phrase has nothing to show. Nothing is guessed on your behalf: a phrase
with no `search_term` gets no picture.

## Exercises

Every exercise has `id`, `type`, `prompt`, `answer` and `accepted`.

`id` is written out, never counted from position: `unit-01.lesson-02.choose.03`.
A learner's answer history is stored against this id, so an id that moves when a
unit is reordered would throw that history away.

`accepted` is every spelling of the right answer that must be marked right,
including the transliteration. Harakat and the alef and hamza spellings are
already folded before comparing, so `accepted` is for real alternatives, not for
vowel marks.

| type | what the learner does | extra fields |
|---|---|---|
| `reply` | types the natural answer to something said | |
| `fill_blank` | types the missing word into a sentence | |
| `translate_to_arabic` | types the dialect for an English sentence | |
| `choose` | picks one of `options` | `options`: Arabic strings, or `{"label", "image"}` for picture options |
| `reorder` | arranges words into the sentence | `words`, optional; without it the bank is the answer's own words shuffled |

These five cover every kind of practice. Picking a picture is `choose` with
pictures as its options; arranging whole segments rather than single words is
`reorder` with `words` holding the segments. There is no separate type for
either, and a picture beside a phrase is `phrase.search_term`, not an exercise.

Two optional fields on any exercise:

- `too_formal`: `{"item", "feedback"}`. A correct but bookish answer, and why it
  is not what is being practised. Shown as a note, never as a mistake.
- `tip`: one line of help, shown after answering.

## The challenge

One per unit, at the end: `title`, `instructions`, `required_elements` (what the
learner's own conversation must contain) and `model`, holding a `dialogue` in the
same shape as a lesson's. Not graded.

## Honesty rules

- Write the dialect as it is actually spoken, not Modern Standard Arabic with a
  dialect word dropped in. A formal sentence belongs in `too_formal`.
- Never write a placeholder. No `...`, no `etc.`, no "add more here".
- English is the meaning of what is there, not an explanation added to it.
- If you are unsure a phrase is really said in this dialect, leave it out. The
  tab tells the learner these lessons were written by a model and no speaker has
  checked them, and that is only honest while nothing is invented past it.
