import { describe, expect, it } from 'vitest'

import { entrySpan } from './entrySpan'

const light = { definitions: ['to inquire'], synonyms: [[]] }

describe('entrySpan', () => {
  it('gives a light word one column', () => {
    expect(entrySpan(light)).toBe(1)
    expect(entrySpan({})).toBe(1)
  })

  it('widens a word with many senses', () => {
    expect(entrySpan({ definitions: ['a', 'b', 'c', 'd'] })).toBe(2)
    expect(entrySpan({ definitions: ['a', 'b', 'c'] })).toBe(1)
  })

  it('widens a word whose senses run long even when few', () => {
    expect(entrySpan({ definitions: ['x'.repeat(60), 'y'.repeat(60)] })).toBe(2)
  })

  it('widens a word that carries synonyms, since the band needs the room', () => {
    expect(entrySpan({ definitions: ['a'], synonyms: [[{ word: 'ب', meaning: '' }]] })).toBe(2)
  })
})
