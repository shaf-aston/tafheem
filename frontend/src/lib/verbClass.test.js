import { describe, expect, it } from 'vitest'

import { verbClass } from './verbClass'

describe('verbClass', () => {
  // The app's data, an AI and a preset each write the mark differently, and the
  // split silently stops happening for whichever one is not covered.
  it.each([':', '—', '–', '-'])('splits the name from its meaning across a %s', (mark) => {
    const { value, gloss, arabic } = verbClass(`صحيح سالم ${mark} no weak letter, no hamzah`)
    expect(value).toBe('صحيح سالم')
    expect(gloss).toBe('no weak letter, no hamzah')
    expect(arabic).toBe(true)
  })

  it('keeps an explanation that runs onto another line', () => {
    expect(verbClass('صحيح: no weak letter,\nno hamzah').gloss).toBe('no weak letter,\nno hamzah')
  })

  // Better a plain label than a wrong split.
  it('passes through a class with no Arabic name', () => {
    expect(verbClass('Form II')).toEqual({ value: 'Form II' })
  })

  it('passes through nothing at all without throwing', () => {
    for (const nothing of ['', null, undefined]) {
      expect(verbClass(nothing)).toEqual({ value: nothing })
    }
  })
})
