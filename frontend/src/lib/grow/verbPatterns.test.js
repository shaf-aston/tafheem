import { describe, expect, it } from 'vitest'

import data from '../../../public/grow/basics-verbs.json'
import { makeRandom } from '../quiz/quiz'
import { PATTERNS, familyTable, patternAsks } from './verbPatterns'

const nfc = (text) => text.normalize('NFC')
const { families } = data
const familyOf = (id) => families.find((family) => family.id === id)
const itemFor = (form) => ({
  id: `patterns:${form}`, skill: 'patterns', marker: { id: form, key: form, base: 'I', rule: `${PATTERNS[form].shape}: the rule.` },
  words: families.filter((family) => family.forms[form]),
})

describe('familyTable', () => {
  it('is the family’s verbs, form I first', () => {
    expect(familyTable(familyOf('know'))).toEqual([
      { key: 'I', ar: nfc('عَلِمَ'), en: 'he knew' }, { key: 'II', ar: nfc('عَلَّمَ'), en: 'he taught' },
      { key: 'V', ar: nfc('تَعَلَّمَ'), en: 'he learnt' }, { key: 'X', ar: nfc('اِسْتَعْلَمَ'), en: 'he asked to know' },
    ])
    expect(familyTable(familyOf('write')).find((entry) => entry.key === 'VI').ar).toBe(nfc('تَكَاتَبُوا'))
  })
})

describe('patternAsks', () => {
  it.each(Object.keys(PATTERNS))('%s: asks what the pattern adds, never beside one that adds nearly the same', (form) => {
    for (let seed = 1; seed <= 30; seed += 1) {
      const [adds] = patternAsks(itemFor(form), true, makeRandom(seed))
      expect(adds).toMatchObject({ kind: 'choose', id: `adds:patterns:${form}`, answer: 'right', tag: 'New form' })
      expect(adds.ask).toContain(PATTERNS[form].shape)
      expect(adds.options).toHaveLength(3)
      expect(adds.options.find((one) => one.id === 'right').text).toBe(PATTERNS[form].adds)
      for (const option of adds.options.filter((one) => one.id !== 'right')) {
        expect(PATTERNS[form].near, `${form} beside ${option.id}`).not.toContain(option.id)
        expect(adds.wrong[option.id]).toContain(PATTERNS[option.id].adds)
      }
      expect(itemFor(form).words.some((family) => family.forms[form].ar === adds.ar)).toBe(true)
    }
  })

  it.each(Object.keys(PATTERNS))('%s: asks what one verb on it means, beside its form I, against its family’s others', (form) => {
    for (let seed = 1; seed <= 30; seed += 1) {
      const [, read] = patternAsks(itemFor(form), true, makeRandom(seed))
      const family = families.find((one) => one.forms[form]?.ar === read.ar)
      expect(read.ask).toBe(`${family.forms.I.ar} is “${family.forms.I.en}”. What does this one mean?`)
      expect(read.options).toHaveLength(3)
      expect(read.options.find((one) => one.id === 'right').text).toBe(family.forms[form].en)
      const meanings = Object.values(family.forms).map((one) => one.en)
      for (const option of read.options) expect(meanings).toContain(option.text)
      expect(read.why).toBe(`${read.ar} = ${family.forms[form].en}. ${PATTERNS[form].shape} often adds ${PATTERNS[form].adds}.`)
      for (const line of Object.values(read.wrong)) expect(line.endsWith(`${PATTERNS[form].shape} often adds ${PATTERNS[form].adds}.`)).toBe(true)
      expect(read.record).toMatchObject({ module: 'basics', item: `patterns:${form}`, context: { skill: 'patterns', from: family.id, word: read.ar } })
    }
  })

  it('reviews with the same two cards', () => {
    expect(patternAsks(itemFor('X'), false, makeRandom(4)).map((card) => card.tag)).toEqual(['Review', 'Review'])
  })

  it('names every pattern near another both ways', () => {
    for (const [form, { near }] of Object.entries(PATTERNS)) for (const one of near) expect(PATTERNS[one].near).toContain(form)
  })
})
