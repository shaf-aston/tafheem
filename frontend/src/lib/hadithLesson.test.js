import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

import { bare, gapOf, hadithCards } from './hadithLesson'
import { makeRandom } from './quiz'

const { hadiths } = JSON.parse(readFileSync(new URL('../../public/grow/nawawi40.json', import.meta.url), 'utf8'))

describe('the built file', () => {
  it('holds all 42, each with a key line in both languages', () => {
    expect(hadiths.map((h) => h.n)).toEqual(Array.from({ length: 42 }, (_, i) => i + 1))
    for (const h of hadiths) expect(h.key.ar && h.key.en).toBeTruthy()
  })
})

describe('gapOf', () => {
  it('blanks a word of the key line, offers it among three others, none the same word', () => {
    for (const h of hadiths) {
      const gap = gapOf(h, hadiths, makeRandom(h.n))
      expect(gap.words[gap.at].startsWith(gap.answer)).toBe(true)
      expect(gap.options.map((o) => o.text)).toContain(gap.answer)
      expect(gap.options).toHaveLength(4)
      expect(new Set(gap.options.map((o) => bare(o.text))).size).toBe(4)
    }
  })
})

describe('hadithCards', () => {
  it('teaches a new hadith, then asks its meaning and its missing word', () => {
    const cards = hadithCards({ fresh: [hadiths[0]], reviews: [] }, hadiths, makeRandom(1))
    expect(cards.map((c) => c.kind)).toEqual(['hadith', 'meaning', 'gap'])
    const meaning = cards[1]
    expect(meaning.question.options.map((o) => o.id)).toContain('1')
    expect(new Set(meaning.question.options.map((o) => o.id)).size).toBe(4)
    expect(meaning.record).toMatchObject({ module: 'nawawi40', item: '1' })
  })

  it('asks a review one way only', () => {
    const cards = hadithCards({ fresh: [], reviews: [hadiths[4]] }, hadiths, makeRandom(2))
    expect(cards).toHaveLength(1)
    expect(['meaning', 'gap']).toContain(cards[0].kind)
  })
})
