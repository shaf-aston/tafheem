import { describe, expect, it } from 'vitest'

import { bare, gapOf } from './gap'
import { makeRandom } from './quiz'

const LINES = ['قُلْ هُوَ ٱللَّهُ أَحَدٌ', 'ٱللَّهُ ٱلصَّمَدُ', 'لَمْ يَلِدْ وَلَمْ يُولَدْ', 'وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ']

describe('bare', () => {
  it('drops harakat, Uthmani marks, tatweel and trailing punctuation', () => {
    expect(bare('ٱللَّهُ')).toBe('ٱلله')
    expect(bare('لَّهُۥ')).toBe('له')
    expect(bare('كـتاب،')).toBe('كتاب')
    expect(bare('رَحِيمٌۗ')).toBe('رحيم')
  })
})

describe('gapOf', () => {
  it('blanks the longest word and offers it among three others, none the same word', () => {
    const gap = gapOf(LINES[0], LINES.slice(1), makeRandom(1))
    expect(gap.answer).toBe('ٱللَّهُ')
    expect(gap.words[gap.at]).toBe(gap.answer)
    expect(gap.options).toHaveLength(4)
    expect(new Set(gap.options.map((o) => bare(o.text))).size).toBe(4)
  })

  it('keeps punctuation after the blank as the tail', () => {
    const gap = gapOf('قل هو الله، أحد', LINES, makeRandom(1))
    expect(gap).toMatchObject({ answer: 'الله', tail: '،' })
  })

  it('ignores an ayah number and end mark at the end', () => {
    const gap = gapOf('وَٱلْعَصْرِ ۝١', LINES, makeRandom(1))
    expect(gap.words).toEqual(['وَٱلْعَصْرِ'])
    expect(gap.answer).toBe('وَٱلْعَصْرِ')
  })
})
