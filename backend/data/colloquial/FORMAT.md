# How a colloquial unit is written down

Every dialect follows one course outline, `spine.json` beside this file. The
spine holds what is the same in every dialect: each unit's and lesson's title,
their order, and each phrase **slot** with its English, `search_term` and picture.
A dialect holds only what is said: one file per unit, `<dialect>/unit-NN.json`,
in the folder named in `dialects.json`.

To change the course, edit the spine. A lesson or slot added there is reported
missing by every dialect until each one writes it, so a template change cannot
reach one dialect and skip another. A dialect may leave whole units unwritten;
the tab lists them as coming. It may not leave half a lesson.

## The spine

```json
{ "units": [ { "unit": "unit-01", "title": "First Conversations",
  "lessons": [ { "lesson": "lesson-01", "title": "Greetings and Names",
    "phrases": [ { "slot": "hello", "english": "Hello.", "search_term": "person waving hello" } ] } ] } ] }
```

A lesson's `words` lists the ids of the words that topic teaches, in order: every
common word of the scene, not only those in its phrases. See "Words" below.

`slot` is a short name written out, never a position, unique within its lesson.
It ties the same phrase together across dialects, so never rename one.
`image` is added by the picture script, and one picture serves every dialect.
A unit's optional `cover` names the slot whose phrase and picture front its card on
the unit list; without one, the unit's first pictured phrase does.

## A dialect's unit

```json
{
  "unit": "unit-01",
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
| `lesson` | `lesson-01`, one of the spine's lessons for this unit |
| `phrases` | one per spine slot: `slot`, `arabic`, `transliteration`, optionally `english` (only when this dialect's words mean something other than the spine's English; it replaces it for this dialect), and optionally `reply` (the natural answer, with its own `english`) |
| `dialogue` | one real conversation, in order: `speaker`, `arabic`, `transliteration`, `english`. A line that repeats a phrase of the lesson is written `{"speaker", "slot"}` instead (add `"reply": true` for that phrase's reply) and takes the card's words; this is the preferred form, and a full copy of a phrase is a fault |
| `de_book` | question and answer drill: `pair` and `response`, each a phrase |
| `culture` | one or two sentences on when and with whom this is said |
| `exercises` | the practice, see below |

`search_term`, in the spine, is a short everyday English noun phrase for finding a picture, for
example `"a glass of tea"`. The English meaning alone is usually too idiomatic to
search with, so a picture is only ever fetched from `search_term`. Leave it out
when the phrase has nothing to show. Nothing is guessed on your behalf: a phrase
with no `search_term` gets no picture.

## Words

Each meaning is written once, in `words.json` beside this file, one line each:

```json
"tired": {"english": "tired", "group": "feelings"}
```

`group` is the heading the word sits under in a topic's list (family, food,
actions, describing ...). The id is named from the English and never renamed, as
every dialect links to it. A word taught by two topics is one id in both.

A dialect gives its Arabic in its own `<dialect>/words.json`, once per id:

```json
"tired": {"arabic": "تعبان / تعبانة", "transliteration": "ta3baan / ta3baane"}
```

- A word whose form only changes for a woman is one meaning, both forms split by
  ` / `, the man's first, with the same split in the transliteration. Two ids only
  when the words differ and the difference is the point: brother and sister.
- A word, not a phrase: at most two pieces a form (a fixed name like عيد ميلاد).
  Arabic letters only in `arabic`, none in `transliteration`.
- A topic is all or none: a dialect that has written a lesson says every word of
  it, or none yet. Two words of one topic never share their Arabic.
- A topic teaches 8 or more words, and never a filler to reach 8.
- A topic with `"phrases": []` in the spine is a word list: no phrases, conversation or exercises, only its words,
  learnt as cards, match, quiz and review. A unit made only of word lists (unit-20, Word Banks) needs no challenge.

The loader checks all of this on start and stops on any fault. To review a
dialect's words, `python -m backend.scripts.colloquial_word_bank dump <dialect>`
prints them topic by topic, `id | english | arabic | transliteration`, each word
once. Edit the last two columns and `load <dialect> <file>` puts it back, checked
as above, all or nothing.

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
- If you are unsure a phrase is really said in this dialect, name it. The
  tab tells the learner these lessons were written by a model and no speaker has
  checked them, and that is only honest while nothing is invented past it.
