import { describe, expect, it } from 'vitest'

import { quizNote } from './quizNote'

const say = (text, values = {}) => text.replace(/\{(\w+)\}/g, (_, key) => values[key])
const note = (word, setup = {}) => quizNote(word, { language: 'ur', dialect: null, say, ...setup })?.text ?? null

describe('quizNote', () => {
  it('warns of an Urdu false friend first, with its Urdu sense', () => {
    const word = { urdu: { kind: 'false-friend', sense: 'a letter' }, attached: true }
    expect(note(word, { dialect: 'Levantine' })).toBe('not what it looks like')
    expect(quizNote(word, { language: 'ur', say }).why).toContain('a letter')
  })

  it('says an Urdu word that means the same is known', () => {
    expect(note({ urdu: { kind: 'same' }, attached: true })).toBe('you know this one')
  })

  it('says nothing of Urdu in an English round', () => {
    expect(note({ urdu: { kind: 'same' } }, { language: 'en' })).toBeNull()
  })

  it('names a word only ever seen attached before the dialect', () => {
    expect(note({ attached: true }, { dialect: 'Levantine' })).toBe('from a phrase')
  })

  it('falls back to the dialect, then to nothing', () => {
    expect(note({}, { dialect: 'Levantine' })).toBe('Levantine')
    expect(note({})).toBeNull()
    expect(note(null)).toBeNull()
  })
})
