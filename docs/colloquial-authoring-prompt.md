# The prompt that writes a colloquial unit

Paste the block below into a fresh chat to generate one unit at a time. Change
the dialect name and the unit number, and paste that unit from
`backend/data/colloquial/spine.json` where it says so. The output drops straight
into `backend/data/colloquial/<dialect>/unit-NN.json` with no editing.
`backend/services/colloquial/loader.py` checks the shape on load and names every
fault at once, so a broken unit stops the app rather than showing a half lesson.
The content minimums below are not checked by code; they are what makes a lesson
worth doing.

The full schema in prose is `backend/data/colloquial/FORMAT.md`. Keep that file
and this prompt saying the same thing.

---

You are writing spoken **Damascene Arabic** teaching content for unit **01** of a
course every dialect shares. Output is one JSON file, `unit-01.json`.

**The outline you fill.** This is the unit's lessons and, in each, the phrase
slots with their English. Write every lesson and every slot, in this dialect,
keeping each `slot` name exactly:

```json
<paste this unit from spine.json here>
```

**Shape**

```json
{
  "unit": "unit-01",
  "dialect": "Damascene Arabic",
  "transliteration_key": { "sh": "ش", "kh": "خ", "gh": "غ", "3": "ع", "7": "ح",
    "2": "ء", "2a": "أ / همزة في بداية الكلمة", "aa": "ا طويلة",
    "ee": "ي طويلة", "oo": "و طويلة", "3a": "عَ", "3e": "عِ", "3o": "عُ" },
  "lessons": [
    {
      "lesson": "lesson-01",
      "phrases": [
        { "slot": "<from the outline>", "arabic": "", "transliteration": "",
          "reply": { "arabic": "", "transliteration": "", "english": "" } }
      ],
      "dialogue": [ { "speaker": "", "arabic": "", "transliteration": "", "english": "" } ],
      "de_book": [ { "pair": { "arabic": "", "transliteration": "", "english": "" },
                     "response": { "arabic": "", "transliteration": "", "english": "" } } ],
      "culture": "",
      "exercises": [
        { "id": "unit-01.lesson-01.choose.01", "type": "choose",
          "prompt": "", "options": ["", "", "", ""], "answer": "",
          "accepted": ["", "", ""],
          "too_formal": { "item": "", "feedback": "" }, "tip": "" }
      ]
    }
  ],
  "challenge": { "title": "", "instructions": "", "required_elements": [""],
                 "model": { "dialogue": [ { "speaker": "", "arabic": "", "transliteration": "", "english": "" } ] } }
}
```

**Minimum per lesson, never below**

- `phrases`: exactly the outline's slots, each with its `reply` where one exists
- `dialogue`: 10 or more lines, between named speakers
- `de_book`: 4 or more pairs
- no `vocabulary`: a topic's words are not written in the unit. Its English is
  shared in words.json, and the dialect's Arabic goes in `<dialect>/words.json`
  (see FORMAT.md, "Words"), usually through `colloquial_word_bank dump` and `load`
- `culture`: 1 to 3 sentences
- `exercises`: 10 or more, using at least 4 of the five types
- every exercise carries `id`, `answer`, 3 or more `accepted` variants, a
  `too_formal` item with its `feedback`, and a `tip`
- the unit ends with exactly one `challenge`

**The five exercise types, and only these five**

| `type` | the learner |
|---|---|
| `reply` | types the natural answer to something said |
| `fill_blank` | types the missing word into a sentence |
| `translate_to_arabic` | types the dialect for an English sentence |
| `choose` | picks one of `options` (4 options) |
| `reorder` | arranges words into the sentence |

`reorder` may carry `words`, the pieces to arrange, when they are whole segments
rather than single words. Leave it out and the words of `answer` are used.

**`id`**

Write every id out in full as `unit-01.lesson-02.choose.03`: the unit, the
lesson, the type, then a counter within that lesson and type starting at `01`.
Never repeat an id inside a unit. A learner's answer history is kept against this
id, so it must not change when a unit is edited later.

**`accepted`**

Every spelling that must be marked right, including the transliteration. Vowel
marks and the alef and hamza spellings are already folded before comparing, so do
not spend `accepted` entries on those; spend them on real alternatives.

**Rules**

- Output ONLY the JSON for this unit, inside one code block. No text before or
  after it.
- Never write `...`, `etc.`, "add more here", or any placeholder. Every field is
  fully written.
- Never shorten later lessons to save space. The last lesson is as complete as
  the first.
- If you run out of space, stop at the end of a complete lesson and write nothing
  else. When I say "continue", carry on from the next lesson inside the same
  `unit-01.json` structure.
- Damascene Arabic as it is really spoken. A correct but bookish sentence belongs
  in `too_formal`, never in `answer`.
- If you are unsure how this dialect says a slot, say so after the JSON and
  name the slot, rather than guessing. The unit is not added until it is sure.

After `unit-01.json` is complete, wait. When I say "next", write `unit-02.json`
the same way, and so on to the last unit in the spine.
