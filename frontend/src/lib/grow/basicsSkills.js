/**
 * The Basics world's path: the ال words (lib/grow/alifLam.js), and between them the small additions that change a word. Pure.
 *
 * A skill is a few markers, and a marker is one addition: ـهُ "his", ـَتْ "she did", لَمْ "didn't", سَ "will".
 * The marker is what is learnt, so it is the item: it is taught once on كَتَبَ (or كِتَاب), then every question
 * on it draws a verb (or noun) and a person at random, so the learner learns the addition, not one word.
 *   mine      my, his, her…   on a noun     ـِي ـهُ ـهَا ـنَا ـهُمْ ـكَ ـكُمْ
 *   people    a woman, many   on a person   ة ـُونَ ـَات
 *   joined    and, with…      in front      وَ بِـ لِـ كَـ
 *   this      this, that      a word before هٰذَا هٰذِهِ ذٰلِكَ تِلْكَ, with ال or without
 *   past      who did it      an ending     ـُوا ـْتُ ـْنَا ـْتَ ـْتُمْ ـَتْ
 *   present   who does it     a letter in front (and ـُونَ)
 *   negation  not             لَا لَمْ لَنْ مَا
 *   command   do! / don't!    اُكْتُبْ · لَا تَكْتُبْ
 *   future    will            سَ سَوْفَ
 *   object    him, her, me…   on a verb     ـهُ ـهَا ـهُمْ ـنِي ـنَا ـكَ ـكُمْ
 *   patterns  forms II–X      the verb's own shape, and what it adds (lib/grow/verbPatterns.js)
 * A marker's `pool` is the forms it is told apart from (keys of lib/grow/wordForms.js tables, `{p}` the person drawn; `toEnglish`, if
 * given, the ones for the English direction);
 * the pickers there leave out any that could mean the same. A skill with its own `asks` asks its own way. The skills and
 * their markers: lib/grow/basicsSkillList.js; the order of the path: `path` in public/grow/basics.json.
 */
import { INTRO, MODULE, english, plain, teachWord, wordAsks } from './alifLam'
import { weave } from './lesson'
import { DUAL, JOINED, MISSPELT, OBJECT_VERBS, OWNED, OWNERS, POINTED, QUESTION_VERBS, SKILLS, TA_CLAUSE, THINGS } from './basicsSkillList'
import { familyTable } from './verbPatterns'
import { dualTable, joinedTable, ofTable, peopleTable, pointingTable, pronounTable } from './nounForms'
import { arabicOptions, englishOptions, objectTable, possessiveTable, questionTable, relativeTable, verbTable } from './wordForms'

export { DUAL, JOINED, MISSPELT, OBJECT_VERBS, OWNED, OWNERS, POINTED, QUESTION_VERBS, SKILLS, THINGS }

/** Every form of `word` for a skill's table. */
export const TABLES = {
  verbs: verbTable, nouns: possessiveTable, people: peopleTable, joined: joinedTable, pointing: pointingTable,
  objects: objectTable, families: familyTable, pronouns: pronounTable, pairs: ofTable, dual: dualTable,
  relative: relativeTable, questions: questionTable,
}

/** Every thing with every owner: “the teacher’s book”, “the student’s book”… (`ar` the thing's, as a noun table's is). */
const pairsOf = (things, owners) =>
  things.flatMap((thing) => owners.map((owner) => ({ id: `${thing.id}-of-${owner.id}`, ar: thing.ar, thing, owner })))

/**
 * The path as items: `path` steps in order, `{ words: n }` the next n ال words, `{ skill }` that skill's markers;
 * words the path does not name are left out (a path that names none gives every word). A marker item carries what its
 * questions draw from (`words`): the skill's list, or of it what the marker `has` (a pattern, only the verbs that have
 * it). A skill whose list did not load (`verbs`, `families` or `people` null: an older cached file, or offline) is left
 * out, and the words still come.
 */
export function pathItems(words, { verbs, families, people, path = [] }) {
  const named = (ids, list = words) => ids.map((id) => list.find((word) => word.id === id)).filter(Boolean)
  const draws = {
    verbs: verbs ?? [], nouns: named(OWNED), people: people ?? [], joined: named(JOINED), pointing: named(POINTED),
    objects: named(OBJECT_VERBS, verbs ?? []), families: families ?? [], pronouns: people ?? [],
    pairs: pairsOf(named(THINGS), named(OWNERS)), dual: named(DUAL), relative: verbs ?? [], questions: named(QUESTION_VERBS, verbs ?? []),
  }
  const items = []
  let next = 0
  for (const step of path) {
    if (step.words) {
      items.push(...words.slice(next, next + step.words))
      next += step.words
    } else {
      const skill = SKILLS[step.skill]
      if (!skill || !draws[skill.table].length) continue
      for (const marker of skill.markers) {
        const list = skill.has ? draws[skill.table].filter((word) => skill.has(word, marker)) : draws[skill.table]
        if (list.length) items.push({ id: `${step.skill}:${marker.id}`, skill: step.skill, marker, words: list })
      }
    }
  }
  return next ? items : [...items, ...words]
}

const pick = (list, random) => list[Math.floor(random() * list.length)]
/** Every form of `word` that a skill's questions draw from. */
export const tableOf = (skill, word) => TABLES[SKILLS[skill].table](word)
const keyFor = (template, person) => template.replace('{p}', person)
const tagOf = (isNew) => (isNew ? 'New form' : 'Review')

/** A marker's form of `word` (and the person), with the form it is set beside on its teach card. */
function drawn(item, word, person, direction = 'to-arabic') {
  const table = tableOf(item.skill, word)
  const at = (key) => table.find((entry) => entry.key === key)
  const { marker } = item
  const base = marker.base === 'bare' ? { ar: plain(word.ar), en: english(word, false) } : marker.base && at(keyFor(marker.base, person))
  return { table, key: keyFor(marker.key, person), asked: at(keyFor(marker.key, person)), base, pool: (direction === 'to-english' && marker.toEnglish ? marker.toEnglish : marker.pool).map((one) => keyFor(one, person)) }
}

/** Taught on the list's first verb (كَتَبَ) or noun (كِتَاب), and the marker's first person. */
export function teachMarker(item) {
  const { asked, base } = drawn(item, item.words[0], item.marker.persons[0])
  return {
    kind: 'teach',
    id: `teach:${item.id}`,
    tag: SKILLS[item.skill].title,
    ar: asked.ar,
    en: asked.en,
    ...(base && { also: { ar: base.ar, en: base.en } }),
    note: item.marker.rule,
  }
}

// `word` the form asked; `from` the verb or noun it was drawn from, and the person (none for a noun).
const record = (item, direction, asked, word, person) => ({
  module: MODULE, item: item.id, context: { world: MODULE, skill: item.skill, direction, word: asked.ar, from: word.id, ...(person && { person }) },
})

/** The marker's rule as said of one word: the ة half of "my, his, her" only for a word that ends in ة. */
const ruleFor = (marker, word) =>
  marker.key.startsWith('mine:') && !plain(word.ar).endsWith('ة') ? marker.rule.replace(TA_CLAUSE, '.') : marker.rule

/** A rule's first sentence: what the addition says. */
const leadOf = (rule) => rule.slice(0, rule.indexOf('. ') + 1) || rule

/** For each wrong option, the answer and what that pick is: another form's meaning and the rule's lead, or the misspelling. */
function wrongWhy(options, table, said, rule) {
  const wrong = options.filter((option) => option.id !== 'right').map(({ id }) => {
    const [head, kind] = id.split(':')
    const one = table.find((entry) => entry.key === id)
    return [id, `${said} ${head === 'wrong' ? MISSPELT[kind] : `${one.ar} is “${one.en}”. ${leadOf(rule)}`}`]
  })
  return Object.fromEntries(wrong)
}

/** "she wrote" → pick the Arabic, and كَتَبَتْ → pick the English: each on its own verb (or noun) and person. */
export function markerAsks(item, isNew, random) {
  const ask = (direction) => {
    const word = pick(item.words, random)
    const person = pick(item.marker.persons, random)
    const { table, key, asked, pool } = drawn(item, word, person, direction)
    const toArabic = direction === 'to-arabic'
    const options = (toArabic ? arabicOptions : englishOptions)(table, key, pool, random)
    // A question or a command ends on its own ? or !, never on another full stop.
    const said = `${asked.ar} = ${asked.en}${/[?!]$/.test(asked.en) ? '' : '.'}`
    return {
      kind: 'choose',
      id: `${toArabic ? 'pick' : 'read'}:${item.id}`,
      tag: tagOf(isNew),
      ask: toArabic ? `Which one is “${asked.en}”?` : 'What does it mean?',
      ...(toArabic ? { arabic: true } : { ar: asked.ar }),
      options,
      answer: 'right',
      why: `${said} ${ruleFor(item.marker, word)}`,
      wrong: wrongWhy(options, table, said, item.marker.rule),
      record: record(item, direction, asked, word, person),
    }
  }
  return [ask('to-arabic'), ask('to-english')]
}

/** An item's question cards: its skill's own `asks`, else asked both ways. */
export const asksOf = (item, isNew, random) => (SKILLS[item.skill].asks ?? markerAsks)(item, isNew, random)

/**
 * A lesson's cards: a new item is taught, then asked both ways; a review is asked both ways.
 * A learner's first lesson (`intro`) opens on what ال is.
 */
export function basicsCards(picked, random = Math.random, intro = false) {
  const cards = weave(picked, {
    teach: (item) => (item.marker ? teachMarker(item) : teachWord(item)),
    asks: (item, isNew) => (item.marker ? asksOf(item, isNew, random) : wordAsks(item, isNew, random)),
  })
  return intro ? [INTRO, ...cards] : cards
}
