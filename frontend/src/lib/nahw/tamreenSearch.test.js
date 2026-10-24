import { describe, expect, it } from 'vitest'

import { matchTag, tagMatches } from './tamreenSearch'

const haal = { key: 'haal', ar: 'حَال', en: 'Haal (State)', meaning: 'Describes the condition at the moment of the action.' }
const wawHaaliyya = { key: 'waw-haaliyya', ar: 'وَاو حَالِيَّة', en: 'Haal Waw', meaning: 'The waw that marks a state.' }

describe('tagMatches: exact/substring', () => {
  it('finds by English, any case', () => {
    expect(tagMatches(haal, 'STATE')).toBe(true)
  })

  it('finds by Arabic with every vowel mark on it', () => {
    expect(tagMatches(haal, 'حَال')).toBe(true)
  })

  it('finds by Arabic typed with no vowel marks', () => {
    expect(tagMatches(haal, 'حال')).toBe(true)
  })

  it('finds by the key', () => {
    expect(tagMatches(haal, 'haal')).toBe(true)
  })

  it('finds by a word inside the meaning', () => {
    expect(tagMatches(haal, 'condition')).toBe(true)
  })

  it('matches everything on an empty query', () => {
    expect(tagMatches(haal, '')).toBe(true)
    expect(tagMatches(haal, '   ')).toBe(true)
  })

  it('finds nothing when the words are not there', () => {
    expect(tagMatches(haal, 'donkey')).toBe(false)
  })
})

describe('tagMatches: typo tolerance', () => {
  it('tolerates a one-letter typo on a short word (key "haal", 4 letters)', () => {
    expect(tagMatches(haal, 'haap')).toBe(true) // distance 1
  })

  it('rejects a typo past the allowed distance for a short word', () => {
    expect(tagMatches(haal, 'haxp')).toBe(false) // distance 2 from "haal", short word cap is 1
  })

  it('tolerates a two-letter typo on a longer word', () => {
    expect(tagMatches(wawHaaliyya, 'haaliyah')).toBe(true) // haaliyya (8) vs haaliyah, distance 2
  })

  it('reports a fuzzy hit as not exact, so the caller can label it a close match', () => {
    expect(matchTag(haal, 'haap')).toEqual({ hit: true, exact: false })
    expect(matchTag(haal, 'haal')).toEqual({ hit: true, exact: true })
  })
})

describe('an exact-duplicate tag', () => {
  const duplicate = { ...haal }

  it('two identical tags both match the same query the same way', () => {
    expect(tagMatches(haal, 'state')).toBe(tagMatches(duplicate, 'state'))
    expect(matchTag(haal, 'state')).toEqual(matchTag(duplicate, 'state'))
  })
})
