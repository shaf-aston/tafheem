import { describe, expect, it } from 'vitest'

import data from '../../public/grow/basics.json'
import verbsData from '../../public/grow/basics-verbs.json'
import worlds from '../config/worlds.json'
import { INTRO, definite, keyOfBasic } from './alifLam'
import { OWNED, SKILLS, basicsCards, markerAsks, pathItems, teachMarker } from './basicsSkills'
import { makeRandom } from './quiz'
import { canPossess, meanings, possessiveTable, verbTable } from './wordForms'

const nfc = (text) => text.normalize('NFC')
const letters = (text) => text.replace(/[ً-ْٰ\s]/g, '')
const { words, path } = data
const { verbs } = verbsData
const items = pathItems(words, { verbs, path })
const itemOf = (id) => items.find((item) => item.id === id)
const markers = items.filter((item) => item.marker)
const book = words.find((word) => word.id === 'book')
const sun = words.find((word) => word.id === 'sun')

describe('pathItems', () => {
  it('keeps every word, once, in its order, with the id it always had', () => {
    const wordItems = items.filter((item) => !item.marker)
    expect(wordItems).toEqual(words)
    expect(new Set(items.map(keyOfBasic)).size).toBe(items.length)
  })

  it('sets the skills between the words as the path says', () => {
    const skillAt = (id) => items.findIndex((item) => item.skill === id)
    expect(skillAt('mine')).toBe(10)
    expect(skillAt('past')).toBe(10 + 7 + 10)
    expect(skillAt('present')).toBe(10 + 7 + 10 + 7 + 10)
    expect(items.slice(skillAt('past'), skillAt('past') + 7).map((item) => item.id)).toEqual(
      ['past:he', 'past:they', 'past:I', 'past:we', 'past:you', 'past:you-all', 'past:she'],
    )
    expect(items.slice(-words.length + 50).every((item) => !item.marker)).toBe(true)
    const order = [...new Set(markers.map((item) => item.skill))]
    expect(order).toEqual(['mine', 'past', 'present', 'negation', 'command', 'future'])
    expect(markers).toHaveLength(Object.values(SKILLS).reduce((sum, skill) => sum + skill.markers.length, 0))
  })

  it('gives a marker what its questions draw from', () => {
    expect(itemOf('past:she').words).toBe(verbs)
    expect(itemOf('mine:his').words.map((word) => word.id)).toEqual(OWNED)
  })

  it('puts the words left over at the end, and a path of words only is the old list', () => {
    expect(pathItems(words, { verbs, path: [] })).toEqual(words)
    expect(pathItems(words, { verbs, path: [{ words: 2 }, { skill: 'command' }] }).map((item) => item.id).slice(0, 5)).toEqual(
      ['book', 'sun', 'command:command', 'command:prohibit', 'house'],
    )
  })

  it('still gives every word when the verbs or the path did not load (an older cached file, or offline)', () => {
    const noVerbs = pathItems(words, { verbs: null, path })
    expect(noVerbs.filter((item) => !item.marker)).toEqual(words)
    expect(new Set(noVerbs.filter((item) => item.marker).map((item) => item.skill))).toEqual(new Set(['mine']))
    expect(pathItems(words, { verbs })).toEqual(words)
    expect(pathItems(words, { verbs, path: [{ skill: 'gone' }] })).toEqual(words)
  })

  it('is as long as the last stage asks for', () => {
    const { stages } = worlds.worlds.find((world) => world.id === 'basics')
    expect(stages.at(-1)).toBe(items.length)
  })

  it('draws possessives only from nouns that take the endings plainly', () => {
    for (const id of OWNED) expect(canPossess(words.find((word) => word.id === id)), id).toBe(true)
  })
})

describe('teachMarker', () => {
  it('shows the form on كَتَبَ, the form it changes, and the rule', () => {
    expect(teachMarker(itemOf('past:she'))).toEqual({
      kind: 'teach', id: 'teach:past:she', tag: 'The past', ar: nfc('كَتَبَتْ'), en: 'she wrote',
      also: { ar: nfc('كَتَبَ'), en: 'he wrote' }, note: SKILLS.past.markers.find((one) => one.id === 'she').rule,
    })
    expect(teachMarker(itemOf('negation:not-past'))).toMatchObject({ ar: nfc('لَمْ يَكْتُبْ'), en: 'he didn’t write', also: { ar: nfc('يَكْتُبُ') } })
    expect(teachMarker(itemOf('command:prohibit'))).toMatchObject({ ar: nfc('لَا تَكْتُبْ'), en: 'Don’t write! (one man)', also: { ar: nfc('اُكْتُبْ') } })
  })
  it('sets the bare noun beside a possessive', () => {
    expect(teachMarker(itemOf('mine:my'))).toMatchObject({ ar: nfc('كِتَابِي'), en: 'my book', also: { ar: nfc('كِتَاب'), en: 'a book' } })
  })
  it('has nothing beside the past for “he”, the form the others grow from', () => {
    const card = teachMarker(itemOf('past:he'))
    expect(card.also).toBeUndefined()
    expect(card).toMatchObject({ ar: nfc('كَتَبَ'), en: 'he wrote' })
  })
})

describe('markerAsks', () => {
  it('asks a marker both ways, each on a verb and person of its own', () => {
    const [toArabic, toEnglish] = markerAsks(itemOf('past:she'), true, makeRandom(3))
    expect(toArabic).toMatchObject({ kind: 'choose', id: 'pick:past:she', tag: 'New form', arabic: true, answer: 'right' })
    expect(toArabic.ask).toMatch(/^Which one is “she .+”\?$/)
    expect(toArabic.options).toHaveLength(3)
    expect(toEnglish).toMatchObject({ id: 'read:past:she', ask: 'What does it mean?', answer: 'right' })
    expect(toEnglish.ar).toMatch(/تْ$/)
    expect(toEnglish.options.find((option) => option.id === 'right').text).toMatch(/^she /)
    expect(toArabic.record).toMatchObject({ module: 'basics', item: 'past:she', context: { world: 'basics', skill: 'past', direction: 'to-arabic' } })
    expect(toEnglish.record.context.direction).toBe('to-english')
    expect(toEnglish.record.context.word).toBe(toEnglish.ar)
    // Which verb and person were asked, so a later review can tell what a learner keeps missing.
    expect(verbs.map((verb) => verb.id)).toContain(toArabic.record.context.from)
    expect(toArabic.record.context.person).toBe('she')
    const [mine] = markerAsks(itemOf('mine:his'), true, makeRandom(3))
    expect(OWNED).toContain(mine.record.context.from)
    expect(mine.record.context).not.toHaveProperty('person')
    expect(markerAsks(itemOf('past:she'), false, makeRandom(3))[0].tag).toBe('Review')
  })

  it('says why: the right pair, then the rule', () => {
    const [card] = markerAsks(itemOf('future:future'), true, makeRandom(1))
    const right = card.options.find((option) => option.id === 'right').text
    expect(card.why).toBe(`${right} = ${card.ask.match(/“(.+)”/)[1]}. ${SKILLS.future.markers[0].rule}`)
  })

  it('draws different verbs and persons across lessons (the addition is learnt, not one word)', () => {
    const asked = new Set()
    const persons = new Set()
    for (let seed = 1; seed <= 40; seed += 1) {
      const [card] = markerAsks(itemOf('negation:not-past'), true, makeRandom(seed))
      asked.add(letters(card.options.find((option) => option.id === 'right').text))
      persons.add(card.ask.match(/“(\S+)/)[1])
    }
    expect(asked.size).toBeGreaterThan(15)
    expect(persons.size).toBeGreaterThanOrEqual(5)
  })

  it('never offers the plain present as wrong for “will”, since it can say will too, but does for reading سَ', () => {
    for (const id of ['future:future', 'future:future-sawfa']) {
      for (let seed = 1; seed <= 40; seed += 1) {
        const [toArabic, toEnglish] = markerAsks(itemOf(id), true, makeRandom(seed))
        const word = verbs.find((verb) => verb.id === toArabic.record.context.from)
        const table = verbTable(word)
        const presents = new Set(table.filter((entry) => entry.key.startsWith('present:')).map((entry) => entry.ar))
        for (const option of toArabic.options) expect(presents.has(option.text), `${id} ${option.text}`).toBe(false)
        expect(toEnglish.options.length).toBe(3)
      }
    }
    const offered = new Set()
    for (let seed = 1; seed <= 40; seed += 1) for (const option of markerAsks(itemOf('future:future'), true, makeRandom(seed))[1].options) offered.add(option.id.split(':')[0])
    expect(offered).toContain('present')
  })

  it('asks a command of the two “you” persons only', () => {
    for (let seed = 1; seed <= 20; seed += 1) {
      const [, card] = markerAsks(itemOf('command:command'), true, makeRandom(seed))
      expect(card.options.find((option) => option.id === 'right').text).toMatch(/!\s\((one man|all of you)\)$/)
    }
  })
})

describe('every marker, on every verb or noun and person (F2–F4)', () => {
  const tableFor = (item, word) => (SKILLS[item.skill].table === 'verbs' ? verbTable(word) : possessiveTable(word))

  it.each(markers.map((item) => [item.id, item]))('%s: three options, one right, none of the wrong ones right too', (_, item) => {
    for (let seed = 1; seed <= 25; seed += 1) {
      for (const card of markerAsks(item, true, makeRandom(seed))) {
        const texts = card.options.map((option) => option.text)
        expect(card.options, card.id).toHaveLength(3)
        expect(new Set(texts).size).toBe(3)
        expect(card.options.filter((option) => option.id === 'right')).toHaveLength(1)
        const right = card.options.find((option) => option.id === 'right').text
        // Every option is the same word: its root letters (or the noun's) are in each.
        const word = item.words.find((one) => {
          const table = tableFor(item, one)
          return table.some((entry) => entry.ar === (card.arabic ? right : card.ar))
        })
        expect(word, card.id).toBeTruthy()
        const table = tableFor(item, word)
        const byAr = meanings(table)
        if (card.arabic) {
          const core = item.skill === 'mine' ? letters(word.ar).replace(/ة$/, '') : null
          for (const option of card.options) {
            if (core) expect(letters(option.text)).toContain(core)
            else expect(letters(option.text)).toMatch(new RegExp([...word.root].join('.*')))
            if (option.id !== 'right') expect(byAr.get(option.text).has(card.ask.match(/“(.+)”/)[1])).toBe(false)
          }
        } else {
          for (const option of card.options) if (option.id !== 'right') expect(byAr.get(card.ar).has(option.text)).toBe(false)
        }
      }
    }
  })

  it('never sets the prohibition for one man beside لا with the plain present', () => {
    const not = verbTable(verbs[0]).find((entry) => entry.key === 'not:you')
    for (let seed = 1; seed <= 25; seed += 1) {
      for (const card of markerAsks(itemOf('command:prohibit'), true, makeRandom(seed))) {
        expect(card.options.map((option) => option.text)).not.toContain(not.ar)
        expect(card.options.map((option) => option.text)).not.toContain(not.en)
      }
    }
  })
})

describe('SKILLS', () => {
  it('names each skill as its teach cards show it, in path order', () => {
    expect(Object.entries(SKILLS).map(([id, skill]) => [id, skill.title, skill.table])).toEqual([
      ['mine', 'My, his, her', 'nouns'], ['past', 'The past', 'verbs'], ['present', 'The present', 'verbs'],
      ['negation', 'Not', 'verbs'], ['command', 'Do! Don’t!', 'verbs'], ['future', 'Will', 'verbs'],
    ])
  })

  // Every key a marker names (its own, its base, its pools) is a form the table has, for every person it draws.
  it.each(markers.map((item) => [item.id, item]))('%s: every form it names is in the table', (_, item) => {
    const { table, markers: all } = SKILLS[item.skill]
    const word = item.words[0]
    const keys = new Set((table === 'verbs' ? verbTable(word) : possessiveTable({ ...word, ar: 'مَدْرَسَة' })).map((entry) => entry.key))
    const { key, base, persons, pool, toEnglish = [] } = item.marker
    expect(all).toContain(item.marker)
    for (const person of persons) {
      const at = (one) => one.replace('{p}', person)
      for (const one of [key, ...pool, ...toEnglish]) expect(keys.has(at(one)), `${at(one)}`).toBe(true)
      if (base && base !== 'bare') expect(keys.has(at(base)), at(base)).toBe(true)
      expect(pool.filter((one) => keys.has(at(one)) && at(one) !== at(key)).length).toBeGreaterThanOrEqual(2)
    }
  })

  it('says “my, his, her” on nouns for anyone, and each verb marker for the persons it is said by', () => {
    expect(SKILLS.mine.markers.every((marker) => marker.persons.length === 1 && marker.persons[0] === null && marker.base === 'bare')).toBe(true)
    expect(SKILLS.past.markers.map((marker) => marker.persons)).toEqual([['he'], ['they'], ['I'], ['we'], ['you'], ['you-all'], ['she']])
    expect(SKILLS.command.markers.map((marker) => marker.persons)).toEqual([['you', 'you-all'], ['you', 'you-all']])
    for (const skill of ['negation', 'future']) for (const marker of SKILLS[skill].markers) expect(marker.persons).toEqual(['he', 'she', 'they', 'you', 'you-all', 'I', 'we'])
  })

  // What each rule teaches: the addition, then what it says in English.
  const TAUGHT = {
    'mine:my': ['ـِي', '“my”'], 'mine:his': ['ـهُ', '“his”'], 'mine:her': ['ـهَا', '“her”'], 'mine:our': ['ـنَا', '“our”'],
    'mine:their': ['ـهُمْ', '“their”'], 'mine:your': ['ـكَ', 'one man'], 'mine:your-all': ['ـكُمْ', 'a group'],
    'past:he': ['كَتَبَ', 'he wrote'], 'past:they': ['ـُوا', 'they did'], 'past:I': ['ـْتُ', 'I did'], 'past:we': ['ـْنَا', 'we did'],
    'past:you': ['ـْتَ', 'one man'], 'past:you-all': ['ـْتُمْ', 'you all did'], 'past:she': ['ـَتْ', 'she did'],
    'present:he': ['يَـ', 'he writes'], 'present:she': ['تَـ', 'she'], 'present:they': ['ـُونَ', 'they'], 'present:I': ['أَ', 'I'],
    'present:we': ['نَ', 'we'], 'present:you': ['تَـ', 'one man'], 'present:you-all': ['ـُونَ', 'you all'],
    'negation:not': ['لَا', 'doesn’t'], 'negation:not-past': ['لَمْ', 'didn’t'], 'negation:not-future': ['لَنْ', 'won’t'],
    'negation:not-past-ma': ['مَا', 'didn’t'], 'command:command': ['اُكْتُبْ', 'drops “you”'], 'command:prohibit': ['لَا', 'Don’t'],
    'future:future': ['سَ', 'will'], 'future:future-sawfa': ['سَوْفَ', 'will'],
  }
  it('teaches every marker, and no other', () => expect(markers.map((item) => item.id).sort()).toEqual(Object.keys(TAUGHT).sort()))
  it.each(Object.entries(TAUGHT))('%s: its rule names the addition and what it says', (id, said) => {
    const { rule } = itemOf(id).marker
    for (const one of said) expect(rule).toContain(one)
    if (id.startsWith('mine:')) expect(rule).toMatch(/never takes ال as well, and a final ة is written ت before it\.$/)
  })
})

describe('rules', () => {
  // A vowel mark alone, after a space or quote, draws on a dotted circle or on the letter before it: it sits on ـ.
  it.each(markers.map((item) => [item.id, item.marker.rule]))('%s: no mark stands alone', (_, rule) => {
    expect(rule).not.toMatch(/(?:^|[\s"“‘(,.])[\u064B-\u0652]/)
  })
})

describe('basicsCards', () => {
  it('opens a first lesson on what ال is, then teaches each new item and asks it both ways', () => {
    const cards = basicsCards({ fresh: [book, itemOf('mine:my')], reviews: [] }, makeRandom(2), true)
    expect(cards.map((card) => card.id)).toEqual(['teach:al', 'teach:book', 'the:book', 'means:book', 'teach:mine:my', 'pick:mine:my', 'read:mine:my'])
    expect(cards[0]).toBe(INTRO)
    expect(cards[1]).toMatchObject({ ar: definite('كِتَاب'), en: 'the book' })
  })
  it('does not open a later lesson on it, and asks a review with no teach card', () => {
    const cards = basicsCards({ fresh: [sun], reviews: [itemOf('past:I')] }, makeRandom(2))
    expect(cards.map((card) => card.id)).toEqual(['teach:sun', 'the:sun', 'means:sun', 'pick:past:I', 'read:past:I'])
    expect(cards.at(-1).tag).toBe('Review')
  })
})
