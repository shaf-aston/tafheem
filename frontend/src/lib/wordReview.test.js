import { describe, expect, it } from 'vitest'

import { wordKey } from './wordDrills'
import { reviewOf, reviewQuestions } from './wordReview'

const w = (arabic) => ({ arabic, english: arabic, transliteration: arabic })
const words = [w('a'), w('b'), w('c'), w('d')]
const row = (word, due, dueAt) => ({ item: wordKey('fusha', word), due, dueAt })

describe('reviewOf', () => {
  it('asks the due words first, longest waiting first, then the new ones', () => {
    const rows = [row(words[0], false, '2026-12-01'), row(words[1], true, '2026-10-05'), row(words[3], true, '2026-10-01')]
    const r = reviewOf(words, rows, 'fusha')
    expect(r.session.map((x) => x.arabic)).toEqual(['d', 'b', 'c'])
    expect([r.due, r.fresh, r.later, r.next]).toEqual([2, 1, 1, '2026-12-01'])
  })

  it('treats a word as the same word only in the same dialect', () => {
    expect(reviewOf(words, [row(words[0], false, 'x')], 'egyptian').fresh).toBe(4)
  })

  it('puts a whole topic in the session, not a slice of it', () => {
    const many = Array.from({ length: 30 }, (_, i) => w(String(i)))
    expect(reviewOf(many, [], 'fusha').session).toHaveLength(30)
  })
})

describe('reviewQuestions', () => {
  const topic = Array.from({ length: 9 }, (_, i) => ({ arabic: `ar${i}`, english: `meaning ${i}`, transliteration: '' }))

  it('asks each session word in turn, by sound on every third, with distinct options holding the answer', () => {
    const qs = reviewQuestions(topic, topic, 'fusha')
    expect(qs.map((q) => q.answerId)).toEqual(topic.map((x) => wordKey('fusha', x)))
    expect(qs.map((q) => q.direction)).toEqual(topic.map((_, i) => (i % 3 === 0 ? 'ar-en' : 'en-ar')))
    expect(qs.map((q) => Boolean(q.listen))).toEqual(topic.map((_, i) => i % 3 === 2))
    qs.forEach((q, i) => {
      const ids = q.options.map((o) => o.id)
      expect(new Set(ids).size).toBe(ids.length)
      expect(ids).toContain(q.answerId)
      if (q.listen) expect([q.say, q.prompt, q.answerLang]).toEqual([topic[i].arabic, topic[i].english, 'ar'])
    })
  })

  it('asks a word the topic lists twice once, and never offers it twice', () => {
    const twice = [...topic, topic[0], { ...topic[1], english: 'another meaning' }]
    const { session } = reviewOf(twice, [], 'fusha')
    expect(session).toHaveLength(topic.length)
    for (const q of reviewQuestions(session, twice, 'fusha')) {
      const ids = q.options.map((o) => o.id)
      expect(new Set(ids).size).toBe(ids.length)
    }
  })
})
