/**
 * The translation file, checked against the code it translates.
 *
 * Using the English sentence as the key buys one file instead of two and a safe
 * fallback, and costs exactly one thing: rewording the English orphans its
 * translation silently, and the screen quietly goes back to English. So the
 * check is that every key still exists in the source, and that a sentence's
 * slots survive translation, which is what stopped "Keys 1–{k} answer" shipping
 * with the 4 written into the Urdu by hand.
 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

import ur from '../lang/ur.json'
import { fillIn, sayIn } from './say'

// quizBanks is in here because the set and cut names are interface words the
// panel renders through say(), even though they are declared beside the data.
const SOURCES = [
  '../components/QuizPanel.jsx',
  '../components/QuizInsights.jsx',
  '../components/ui/AutoAdvanceToggle.jsx',
  './quizBanks.js',
]
const code = SOURCES.map((path) => readFileSync(new URL(path, import.meta.url), 'utf8')).join('\n')

// Keys starting with _ are notes to whoever edits the file, not sentences.
const sentences = Object.entries(ur).filter(([key]) => !key.startsWith('_'))
const slotsIn = (text) => (text.match(/\{\w+\}/g) ?? []).sort()

describe('the Urdu file', () => {
  it.each(sentences)('translates "%s", which is still in the code', (key) => {
    // A long sentence is written across two source lines joined with +, so the
    // code is compared with those joins and its indentation flattened away.
    const flat = code.replace(/['"]\s*\+\s*['"]/g, '').replace(/\s+/g, ' ')
    expect(flat).toContain(key.replace(/\s+/g, ' '))
  })

  it.each(sentences)('keeps every slot of "%s"', (key, value) => {
    expect(slotsIn(value)).toEqual(slotsIn(key))
  })
})

describe('say', () => {
  it('falls back to the English when nothing has been translated', () => {
    expect(sayIn('en')('Next word')).toBe('Next word')
    expect(sayIn('ur')('A sentence nobody has translated')).toBe('A sentence nobody has translated')
  })

  it('fills slots with text', () => {
    expect(sayIn('en')('{a} of {b} seen', { a: 3, b: 9 })).toBe('3 of 9 seen')
  })

  it('leaves a slot alone when the caller has no value for it', () => {
    expect(sayIn('en')('{a} of {b} seen', { a: 3 })).toBe('3 of {b} seen')
  })

  it('puts the two halves where the language puts them, not where English does', () => {
    // The whole reason the correction line is one key: English sets its verb
    // between the pair, Urdu wraps around them.
    const english = fillIn('en')('{word} means {meaning}', { word: 'A', meaning: 'B' })
    const urdu = fillIn('ur')('{word} means {meaning}', { word: 'A', meaning: 'B' })
    expect(english.filter((piece) => typeof piece === 'string').join('')).toBe(' means ')
    expect(urdu.filter((piece) => typeof piece === 'string').join('')).not.toBe(' means ')
    // Both still hand back the same two elements, in the order written.
    expect(english).toHaveLength(urdu.length)
  })
})
