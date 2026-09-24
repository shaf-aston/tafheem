# How a topic's notes are written down

One file per topic, `topics/<id>.json`. It is the reference: the teacher's page
turned into text, nothing added, nothing summarised away. Testing hides pieces
of it when the page is opened, so never write a gapped or shortened version.

```json
{
  "id": "haal",
  "title": "Al-haal",
  "arabic": "الحال",
  "tamreen": ["haal"],
  "blocks": [ ... ]
}
```

`tamreen` names Tamreen exercise files (`backend/data/tamreen/exercises/*.json`)
that test this topic. Leave it `[]` when none does.

## Blocks

In page order. Every block has `id`, `kind` and `page` (0 for the first page).
Give an id as `p03-2`: the page number, then a counter within that page.

| kind | what it is | fields |
|---|---|---|
| `heading` | a title on the page | `ar`, `en` |
| `rule` | a statement of theory in prose | `ar`, `en` |
| `list` | numbered or bulleted lines | `items` (Arabic lines), `ar`/`en` for a lead-in |
| `example` | a worked sentence | `ar` (the sentence), `en` (translation), `labels`: `[{"word": "راكبا", "label": "حال"}]` |
| `table` | a table as drawn | `caption`, `caption_en`, `columns`, `rows`, `answer_col`, `note_ar`, `note_en` |
| `picture` | a page that is a diagram no text would carry, such as a tarkeeb tree | `caption`, `caption_en` saying what it shows |

`answer_col` is the column a test should ask for, given the other columns:
usually the column holding the rule or the name, not the example.

## Marking what can be tested

Inside any Arabic or English string, wrap a testable piece as `{{role|text}}`:

```
"ar": "الحال {{ruling|منصوب}} و{{ruling|نكرة}} أبدا، وصاحبه يسمى {{term|ذو الحال}}"
```

Roles are declared in `roles.json`: `term`, `ruling`, `condition`, `label`,
`example`. Mark the pieces a teacher would actually ask for, a few per block,
not every word. Nothing else about the text changes: remove the markers and the
teacher's own wording is back.

## Honesty rules

- Copy the harakat exactly as printed or handwritten. Never add a vowel the page
  does not show, and never drop one it does.
- A word you cannot read goes in as `⟨?⟩` inside the text, never a guess.
- A page that is a diagram becomes a `picture` block with a caption. Do not
  invent prose for it.
- Sentences the teacher wrote to be wrong on purpose stay wrong.
- English is a translation of what is there, not an explanation added to it.

Every block says which page it came from, and `/api/notes/<id>/page/<n>.png`
serves that page, so anything here can be checked against the handwriting.
