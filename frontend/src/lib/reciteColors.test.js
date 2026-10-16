import { describe, expect, it } from 'vitest'

import { CHECK, MISSED, SAID, WRONG } from './follow'
import { verdictOf } from './reciteColors'

describe('how a whole ayah went', () => {
  it('is wrong when any word was wrong or not said, whatever the rest were', () => {
    expect(verdictOf([SAID, WRONG, SAID])).toBe(WRONG)
    expect(verdictOf([SAID, MISSED])).toBe(WRONG)
    // A doubtful word does not soften a mistake elsewhere.
    expect(verdictOf([CHECK, MISSED, CHECK])).toBe(WRONG)
  })

  it('is not sure when a word was doubtful and none was wrong', () => {
    expect(verdictOf([SAID, CHECK, SAID])).toBe(CHECK)
    expect(verdictOf([CHECK])).toBe(CHECK)
  })

  it('is right only when every word was said', () => {
    expect(verdictOf([SAID, SAID, SAID])).toBe(SAID)
  })

  it('says nothing for an ayah with no words, rather than calling it right', () => {
    expect(verdictOf([])).toBe(null)
  })
})
