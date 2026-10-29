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
 * A marker's `pool` is the forms it is told apart from (keys of lib/grow/wordForms.js tables, `{p}` the person drawn; `toEnglish`, if
 * given, the ones for the English direction);
 * the pickers there leave out any that could mean the same. The order of the path: `path` in public/grow/basics.json.
 */
import { INTRO, MODULE, english, plain, teachWord, wordAsks } from './alifLam'
import { weave } from './lesson'
import { ADDRESSED, PERSONS, arabicOptions, englishOptions, joinedTable, peopleTable, pointingTable, possessiveTable, verbTable } from './wordForms'

const EVERYONE = PERSONS.map((person) => person.id)
// Taught whole; asked on a word with no ة, the ة half is left off (ruleFor).
const TA_CLAUSE = ', and a final ة is written ت before it.'
const MINE_TAIL = `A word with an ending never takes ال as well${TA_CLAUSE}`
// What a misspelt form (wordForms.js `wrong:<kind>:*`) got wrong.
export const MISSPELT = {
  al: 'A word with an ending never takes ال as well.',
  ta: 'A final ة is written ت before an ending.',
  'sa-past': 'سَ goes only on the present, never on the past.',
  'sa-apart': 'سَ is one letter, so it is joined to the verb, never written apart.',
  'sawfa-past': 'سَوْفَ goes only before the present, never before the past.',
  'lam-past': 'لَمْ goes before the present, never the past: for the past it is مَا.',
  'lan-past': 'لَنْ goes before the present, never the past.',
  apart: 'A one-letter word is joined to the word after it, never written apart.',
  alif: 'After لِـ the ا of ال is dropped: لِلْـ.',
  gender: 'هٰذَا and ذٰلِكَ go with a masculine word; هٰذِهِ and تِلْكَ with a feminine one, as most with ة are.',
}

const own = (id, end, said, pool, to = '') => ({
  id, key: `mine:${id}`, base: 'bare', persons: [null], pool: [...pool.map((one) => `mine:${one}`), `wrong:al:${id}`, `wrong:ta:${id}`],
  rule: `${end} on the end means “${said}”${to}. ${MINE_TAIL}`,
})
const fixed = (tense, person, base, rule, pool) => ({ id: person, key: `${tense}:${person}`, base, persons: [person], rule, pool })
const particle = (id, persons, base, rule, pool, toEnglish) => ({ id, key: `${id}:{p}`, base, persons, rule, pool, ...(toEnglish && { toEnglish }) })
// A noun skill's marker: no person, the form it is set beside, the forms it is told apart from.
const noun = (id, base, rule, pool) => ({ id, key: id, base, persons: [null], rule, pool })

export const SKILLS = {
  mine: {
    title: 'My, his, her',
    table: 'nouns',
    markers: [
      { ...own('my', 'ـِي', 'my', ['his', 'our', 'your']), rule: `ـِي on the end means “my”. English puts “my” before the word; Arabic adds it to the end. ${MINE_TAIL}` },
      own('his', 'ـهُ', 'his', ['my', 'her', 'their']),
      own('her', 'ـهَا', 'her', ['his', 'my', 'our']),
      own('our', 'ـنَا', 'our', ['my', 'her', 'their']),
      own('their', 'ـهُمْ', 'their', ['his', 'her', 'our']),
      own('your', 'ـكَ', 'your', ['my', 'his', 'your-all'], ', said to one man'),
      own('your-all', 'ـكُمْ', 'your', ['your', 'their', 'our'], ', said to a group'),
    ],
  },
  people: {
    title: 'One and many',
    table: 'people',
    markers: [
      noun('woman', 'man', 'ة on the end makes a word for a man a word for a woman: مُسْلِمَة a Muslim woman. English mostly uses one word for both.',
        ['man', 'men', 'women']),
      noun('men', 'man', 'ـُونَ on the end = more than two men, or men and women together. You will also see it as ـِينَ (مُسْلِمِينَ): the same plural, in another place in the sentence.',
        ['man', 'woman', 'women']),
      noun('women', 'woman', 'ـَات on the end = more than two women: the ة goes, and ـَات takes its place. English adds -s for both.',
        ['woman', 'men', 'man']),
    ],
  },
  joined: {
    title: 'And, with, for, like',
    table: 'joined',
    markers: [
      noun('and', 'the', 'وَ = and. It is one letter, so it is joined to the word after it: وَالْكِتَاب and the book.',
        ['the', 'with', 'like', 'wrong:apart:and']),
      noun('with', 'the', 'بِـ = with (or by, or in), joined to the front of the word. English writes “with” as a word of its own.',
        ['and', 'for', 'like', 'wrong:apart:with']),
      noun('for', 'the', 'لِـ = for (or to), joined to the front. Before ال the ا is dropped, so لِ and الْكِتَاب make لِلْكِتَاب.',
        ['with', 'like', 'wrong:alif:for', 'wrong:apart:for']),
      noun('like', 'the', 'كَـ = like, joined to the front: كَالْقَمَر like the moon.',
        ['and', 'with', 'for', 'wrong:apart:like']),
    ],
  },
  this: {
    title: 'This, that',
    table: 'pointing',
    markers: [
      noun('this-is', null, 'هٰذَا before a word without ال = “this is a …”: هٰذَا كِتَاب this is a book. Arabic needs no word for “is”. For a feminine word, most with ة, it is هٰذِهِ.',
        ['this', 'that-is', 'wrong:gender:this-is']),
      noun('this', 'this-is', 'With ال, هٰذَا (or هٰذِهِ) is only “this”: هٰذَا الْكِتَاب this book. So ال tells you: a whole sentence, or one thing named.',
        ['this-is', 'that', 'wrong:gender:this']),
      noun('that-is', 'this-is', 'ذٰلِكَ = that, said the same way: ذٰلِكَ قَلَم that is a pen. For a feminine word it is تِلْكَ.',
        ['that', 'this-is', 'wrong:gender:that-is']),
      noun('that', 'that-is', 'With ال, ذٰلِكَ (or تِلْكَ) is only “that”: ذٰلِكَ الْقَلَم that pen.',
        ['that-is', 'this', 'wrong:gender:that']),
    ],
  },
  past: {
    title: 'The past',
    table: 'verbs',
    markers: [
      fixed('past', 'he', null, 'The past for “he” is the verb as it is: كَتَبَ he wrote. English adds -ed (or changes the word); Arabic adds an ending for who did it.', ['past:they', 'past:I', 'past:we', 'present:he']),
      fixed('past', 'they', 'past:he', 'ـُوا on the end = they did it. The ا is written, not said.', ['past:he', 'past:we', 'past:I', 'present:they']),
      fixed('past', 'I', 'past:he', 'ـْتُ on the end = I did it.', ['past:he', 'past:they', 'past:we', 'present:I']),
      fixed('past', 'we', 'past:he', 'ـْنَا on the end = we did it.', ['past:he', 'past:they', 'past:I', 'present:we']),
      fixed('past', 'you', 'past:he', 'ـْتَ on the end = you did it, said to one man.', ['past:he', 'past:we', 'past:they', 'past:you-all', 'present:you']),
      fixed('past', 'you-all', 'past:you', 'ـْتُمْ on the end = you all did it.', ['past:you', 'past:they', 'past:we', 'present:you-all']),
      fixed('past', 'she', 'past:he', 'ـَتْ on the end = she did it. Watch the marks: ـَتْ she, ـْتَ you, ـْتُ I.', ['past:he', 'past:you', 'past:I', 'present:she']),
    ],
  },
  present: {
    title: 'The present',
    table: 'verbs',
    markers: [
      fixed('present', 'he', 'past:he', 'The present adds a letter in front: يَـ = he. English adds -s: he writes.', ['present:they', 'present:I', 'present:we', 'past:he']),
      fixed('present', 'she', 'present:he', 'تَـ in front = she.', ['present:he', 'present:I', 'present:we', 'past:she']),
      fixed('present', 'they', 'present:he', 'يَـ in front and ـُونَ on the end = they.', ['present:he', 'present:we', 'present:you-all', 'past:they']),
      fixed('present', 'I', 'present:he', 'أَ in front = I.', ['present:he', 'present:we', 'present:she', 'past:I']),
      fixed('present', 'we', 'present:I', 'نَ in front = we.', ['present:I', 'present:he', 'present:they', 'past:we']),
      fixed('present', 'you', 'present:he', 'تَـ in front = you, said to one man: the same as “she”, and the sentence tells you which.', ['present:he', 'present:I', 'present:you-all', 'past:you']),
      fixed('present', 'you-all', 'present:they', 'تَـ in front and ـُونَ on the end = you all.', ['present:they', 'present:you', 'present:we', 'past:you-all']),
    ],
  },
  negation: {
    title: 'Not',
    table: 'verbs',
    markers: [
      // لَا + present can mean “won’t” too (لَا يُؤْمِنُونَ, they will not believe), so it is never set beside لَنْ.
      particle('not', EVERYONE, 'present:{p}', 'لَا before the present = not: “doesn’t” or “don’t” (in the Qur’an often “won’t”). English adds a word in front too.', ['present:{p}', 'not-past:{p}']),
      particle('not-past', EVERYONE, 'present:{p}', 'لَمْ before the present = didn’t. The last ـُ becomes ـْ, and ـُونَ becomes ـُوا.', ['not:{p}', 'not-future:{p}', 'past:{p}', 'wrong:lam-past:{p}']),
      particle('not-future', EVERYONE, 'future:{p}', 'لَنْ before the present = won’t. The last ـُ becomes ـَ, and ـُونَ becomes ـُوا.', ['future:{p}', 'not-past:{p}', 'wrong:lan-past:{p}']),
      particle('not-past-ma', EVERYONE, 'past:{p}', 'مَا before the past can say didn’t too, like لَمْ before the present. (مَا has other jobs as well, such as “what”.)', ['not:{p}', 'not-future:{p}', 'past:{p}']),
    ],
  },
  command: {
    title: 'Do! Don’t!',
    table: 'verbs',
    markers: [
      particle('command', ADDRESSED, 'present:{p}', 'A command is the present without its front letter: it ends in ـْ (to a group, ـُوا) and starts with ا, said اُ when the present has ـُ in the middle (اُكْتُبْ), else اِ (اِجْلِسْ). English drops “you” the same way.', ['present:{p}', 'past:{p}', 'prohibit:{p}']),
      particle('prohibit', ADDRESSED, 'command:{p}', 'لَا before the “you” present, ending in ـْ (to a group, ـُوا) = “Don’t …!”', ['command:{p}', 'present:{p}', 'past:{p}', 'future:{p}']),
    ],
  },
  future: {
    title: 'Will',
    table: 'verbs',
    markers: [
      // The bare present can mean "will" too (يَكْتُبُ, he will write), so it is no wrong answer to "he will write";
      // shown سَيَكْتُبُ, though, "he writes" is a wrong meaning, so it stays in the English direction.
      particle('future', EVERYONE, 'present:{p}', 'سَ joined to the front of the present = will. English adds a word; Arabic adds one letter.',
        ['past:{p}', 'not-future:{p}', 'wrong:sa-past:{p}', 'wrong:sa-apart:{p}'], ['present:{p}', 'past:{p}', 'not-future:{p}']),
      particle('future-sawfa', EVERYONE, 'future:{p}', 'سَوْفَ, a word of its own before the present, = will too.',
        ['past:{p}', 'not-future:{p}', 'wrong:sawfa-past:{p}'], ['present:{p}', 'past:{p}', 'not-future:{p}']),
    ],
  },
}

/**
 * The nouns the possessive skill draws: things a person has, every one taking the endings plainly (wordForms canPossess).
 * Not the body (or a shirt): “their heart”, “our face” are said with the plural in Arabic (قُلُوبُهُمْ), which is not taught yet.
 */
export const OWNED = [
  'book', 'house', 'pen', 'car', 'school', 'notebook', 'teacher', 'room', 'bed', 'key', 'cup', 'phone', 'bag', 'friend',
  'sister', 'doctor', 'family', 'garden', 'city', 'village', 'picture',
  'ball', 'horse', 'cat', 'dog', 'camel', 'lesson', 'question', 'word', 'language', 'door', 'table', 'shop', 'ticket', 'neighbour',
]

/** Things “with the …”, “for the …” and “like the …” all fit; none starts with ل, which لِـ would spell otherwise (لِلَّيْل). */
export const JOINED = ['book', 'pen', 'key', 'car', 'phone', 'bag', 'cup', 'spoon', 'knife', 'ball', 'notebook', 'ticket', 'box', 'candle', 'picture', 'bottle']

/** Things whose gender the ة shows: masculine without it, feminine with it (not شَمْس or يَد, feminine with none). */
export const POINTED = [
  'book', 'car', 'pen', 'school', 'house', 'room', 'door', 'key', 'bag', 'phone', 'notebook', 'cup', 'city', 'garden',
  'picture', 'ball', 'tree', 'mosque', 'ticket', 'window', 'table', 'bed', 'street', 'ship', 'box', 'cat',
]

/** Every form of `word` for a skill's table. */
export const TABLES = { verbs: verbTable, nouns: possessiveTable, people: peopleTable, joined: joinedTable, pointing: pointingTable }

/**
 * The path as items: `path` steps in order, `{ words: n }` the next n ال words, `{ skill }` that skill's markers;
 * words the path does not name are left out (a path that names none gives every word). A marker item carries what its
 * questions draw from (`words`). A skill whose list did not load (`verbs` or `people` null: an older cached file, or
 * offline) is left out, and the words still come.
 */
export function pathItems(words, { verbs, people, path = [] }) {
  const named = (ids) => ids.map((id) => words.find((word) => word.id === id)).filter(Boolean)
  const draws = { verbs: verbs ?? [], nouns: named(OWNED), people: people ?? [], joined: named(JOINED), pointing: named(POINTED) }
  const items = []
  let next = 0
  for (const step of path) {
    if (step.words) {
      items.push(...words.slice(next, next + step.words))
      next += step.words
    } else {
      const skill = SKILLS[step.skill]
      if (!skill || !draws[skill.table].length) continue
      for (const marker of skill.markers) items.push({ id: `${step.skill}:${marker.id}`, skill: step.skill, marker, words: draws[skill.table] })
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
    const said = `${asked.ar} = ${asked.en}.`
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

/**
 * A lesson's cards: a new item is taught, then asked both ways; a review is asked both ways.
 * A learner's first lesson (`intro`) opens on what ال is.
 */
export function basicsCards(picked, random = Math.random, intro = false) {
  const cards = weave(picked, {
    teach: (item) => (item.marker ? teachMarker(item) : teachWord(item)),
    asks: (item, isNew) => (item.marker ? markerAsks(item, isNew, random) : wordAsks(item, isNew, random)),
  })
  return intro ? [INTRO, ...cards] : cards
}
