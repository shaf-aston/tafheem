import { describe, expect, it } from 'vitest'

import data from '../../public/grow/basics.json'
import verbsData from '../../public/grow/basics-verbs.json'
import worlds from '../worlds.json'
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
