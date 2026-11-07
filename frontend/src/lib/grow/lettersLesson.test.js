import { describe, expect, it } from 'vitest'

import data from '../../../public/grow/letters.json'
import { formsOf, lettersCards, MODULE } from './lettersLesson'

const { letters } = data
const byId = Object.fromEntries(letters.map((letter) => [letter.id, letter]))
const fixed = () => 0.3

describe('letters.json', () => {
  it('has the 28 letters once each, with a name, a sound and a shape family', () => {
    expect(letters).toHaveLength(28)
    expect(new Set(letters.map((one) => one.letter)).size).toBe(28)
    expect(new Set(letters.map((one) => one.id)).size).toBe(28)
    for (const one of letters) expect(one.name && one.ar && one.sound && one.family, one.id).toBeTruthy()
  })

  it('marks the six that never join the next letter', () => {
    expect(letters.filter((one) => !one.joins).map((one) => one.letter).sort()).toEqual(['ا', 'د', 'ذ', 'ر', 'ز', 'و'].sort())
  })
})

describe('lettersCards', () => {
  it('teaches a new letter, then asks it both ways, filed under the letters record', () => {
    const cards = lettersCards({ fresh: [byId.ba], reviews: [] }, letters, fixed)
    expect(cards.map((card) => card.kind)).toEqual(['teach', 'choose', 'choose'])
    expect(cards[0]).toMatchObject({ ar: 'ب', en: 'bā’ · b, as in book' })
    expect(cards[1]).toMatchObject({ ask: 'Which one is bā’?', arabic: true, answer: 'ba', record: { module: MODULE, item: 'ba' } })
    expect(cards[2]).toMatchObject({ ask: 'What is this letter?', ar: 'ب', answer: 'ba' })
  })

  it('offers look-alikes first: bā’ among its own shape, told apart by the dots', () => {
    const [, which] = lettersCards({ fresh: [byId.ba], reviews: [] }, letters, fixed)
    const ids = which.options.map((option) => option.id)
    expect(ids).toContain('ba')
    expect(ids.every((id) => byId[id].family === 'ba')).toBe(true)
  })

  it('marks every card a letter card, so the letter is drawn large', () => {
    const cards = lettersCards({ fresh: [byId.ba], reviews: [byId.mim] }, letters, fixed)
    expect(cards.every((card) => card.glyph)).toBe(true)
  })

  it('asks a review once', () => {
    expect(lettersCards({ fresh: [], reviews: [byId.mim] }, letters, fixed)).toHaveLength(1)
  })

  it('writes each form with the joining stroke, and a non-joiner the same at the start', () => {
    expect(formsOf(byId.ba)).toEqual(['بـ', 'ـبـ', 'ـب'])
    expect(formsOf(byId.dal)).toEqual(['د', 'ـد', 'ـد'])
  })
})
