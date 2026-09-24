import { describe, expect, it } from 'vitest'

import { synonymGloss } from './synonymGloss'

describe('synonymGloss', () => {
  it('keeps only the form of a verbal noun', () => {
    expect(synonymGloss('verbal noun of عَرَفَ (ʕarafa) (form I)')).toBe('form I')
    expect(synonymGloss('verbal noun of اِطَّلَعَ (ittalaʕa) (form VIII)')).toBe('form VIII')
  })

  it('survives a bracketed meaning inside the sentence', () => {
    expect(synonymGloss('verbal noun of أَبَّ (ʔabba, “to long for”) (form I)')).toBe('form I')
  })

  it('leaves a verbal noun with no form stated whole', () => {
    expect(synonymGloss('verbal noun of أَبَّ (ʔabba)')).toBe('verbal noun of أَبَّ (ʔabba)')
  })

  it('leaves every other gloss alone', () => {
    expect(synonymGloss('active participle of كَتَبَ (form I)')).toBe('active participle of كَتَبَ (form I)')
    expect(synonymGloss('knowledge')).toBe('knowledge')
    expect(synonymGloss('')).toBe('')
    expect(synonymGloss(undefined)).toBe(undefined)
  })
})
