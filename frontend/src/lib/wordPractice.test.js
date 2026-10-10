import { describe, expect, it } from 'vitest'

import { exerciseOf } from '../components/colloquial/exercises/registry'
import { WORDS_MODULE, reviewOf, reviewQuestions, wordDrills, wordKey } from './wordPractice'

const w = (arabic, english = arabic) => ({ arabic, english, transliteration: english })

describe('wordDrills', () => {
  const words = [w('سلام', 'peace'), w('اسم', 'name'), w('بيت', 'house'), w('باب', 'door'), w('قلم', 'pen')]

  it('gives every word one drill, the kinds taking turns', () => {
    const drills = wordDrills(words, 'l1')
    expect(drills.map((d) => d.id.split('.').at(-1))).toEqual(['pick', 'listen', 'write', 'pick', 'listen'])
    expect(new Set(drills.map((d) => d.id)).size).toBe(words.length)
    expect(drills[1].say).toBe('اسم')
  })

  it('offers the answer among three other words, no repeats', () => {
    for (const d of wordDrills(words, 'l1').filter((x) => x.type === 'choose')) {
      expect(d.options).toContain(d.answer)
      expect(d.options).toHaveLength(4)
      expect(new Set(d.options).size).toBe(4)
    }
  })

  it('never offers a synonym of the answer, or a word the topic lists twice', () => {
    const topic = [w('كبير', 'big, large'), w('ضخم', 'large'), w('صغير', 'small'), w('طويل', 'tall'), w('قصير', 'short'), w('صغير', 'small')]
    const [pick] = wordDrills(topic, 'l1')
    expect(pick.options).not.toContain('ضخم')
    expect(new Set(pick.options).size).toBe(pick.options.length)
  })

  it('marks the Arabic or its sound right, and a lone word is written', () => {
    const [write] = wordDrills(words, 'l1').filter((d) => d.type === 'translate_to_arabic')
    expect(exerciseOf(write.type).judge(write, 'بيت')).toBe(true)
    expect(exerciseOf(write.type).judge(write, 'house')).toBe(true)
    expect(wordDrills([words[0]], 'l1')[0].type).toBe('translate_to_arabic')
  })

  it('files each drill under its word when a dialect is given', () => {
    expect(wordDrills(words, 'l1', { dialect: 'fusha' })[3].progress).toEqual({ module: WORDS_MODULE, item: wordKey('fusha', words[3]) })
    expect(wordDrills(words, 'l1')[0].progress).toBeUndefined()
  })
})

describe('reviewOf', () => {
  const words = [w('a'), w('b'), w('c'), w('d')]
  const row = (word, due, dueAt) => ({ item: wordKey('fusha', word), due, dueAt })

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
