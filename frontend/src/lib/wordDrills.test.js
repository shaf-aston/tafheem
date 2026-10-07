import { describe, expect, it } from 'vitest'

import { judge } from './colloquialAnswer'
import { WORDS_MODULE, wordDrills, wordKey } from './wordDrills'

const w = (arabic, english) => ({ arabic, english, transliteration: english })
const words = [w('سلام', 'peace'), w('اسم', 'name'), w('بيت', 'house'), w('باب', 'door'), w('قلم', 'pen')]

describe('wordDrills', () => {
  it('gives every word one drill, the kinds taking turns', () => {
    const drills = wordDrills(words, 'l1')
    expect(drills.map((d) => d.id.split('.').at(-1))).toEqual(['pick', 'listen', 'write', 'pick', 'listen'])
    expect(new Set(drills.map((d) => d.id)).size).toBe(words.length)
    expect(drills[1].say).toBe('اسم')
  })

  it('offers the answer among up to three other words, no repeats', () => {
    for (const d of wordDrills(words, 'l1').filter((x) => x.type === 'choose')) {
      expect(d.options).toContain(d.answer)
      expect(d.options).toHaveLength(4)
      expect(new Set(d.options).size).toBe(4)
    }
  })

  it('marks the Arabic or its sound right, and a lone word is written', () => {
    const [write] = wordDrills(words, 'l1').filter((d) => d.type === 'translate_to_arabic')
    expect(judge(write, 'بيت')).toBe(true)
    expect(judge(write, 'house')).toBe(true)
    expect(wordDrills([words[0]], 'l1')[0].type).toBe('translate_to_arabic')
  })

  it('files each drill under its word, and draws wrong options from the pool', () => {
    const [one] = wordDrills([words[3]], 'r', { pool: words, dialect: 'fusha' })
    expect(one.progress).toEqual({ module: WORDS_MODULE, item: wordKey('fusha', words[3]) })
    expect(one.type).toBe('choose')
    expect(one.options).toHaveLength(4)
    expect(wordDrills(words, 'l1')[0].progress).toBeUndefined()
  })
})
