import { describe, expect, it } from 'vitest'

import { isCentred, pageFontPx, wordsOf } from './mushafFit'

describe('pageFontPx', () => {
  const knobs = { measure: 40, fill: 1 }
  it('takes the size at which the widest line just fits', () => {
    expect(pageFontPx([400, 800], 400, knobs)).toBe(20)
  })
  it('spreads a short centred line over only part of the width', () => {
    expect(pageFontPx([200], 400, { measure: 40, fill: 0.5 })).toBe(40)
  })
  it('waits while nothing is measured', () => {
    expect(pageFontPx([], 400, knobs)).toBeNull()
    expect(pageFontPx([300], 0, knobs)).toBeNull()
  })
})

describe('the print', () => {
  it('centres only the first two pages', () => {
    expect([1, 2, 3].map(isCentred)).toEqual([true, true, false])
  })
  it('keeps the end mark as its own word', () => {
    expect(wordsOf('ٱلۡحَمۡدُ لِلَّهِ ٢')).toEqual(['ٱلۡحَمۡدُ', 'لِلَّهِ', '٢'])
  })
})
