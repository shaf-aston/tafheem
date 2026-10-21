import { describe, expect, it } from 'vitest'

import { makeRandom } from './quiz'
import { optionPool, wordCards } from './wordLesson'

const word = (id) => ({ meaningKey: id, ar: `ar-${id}`, en: id, wordType: 'noun' })
const ALL = ['a', 'b', 'c', 'd', 'e'].map(word)

describe('wordCards', () => {
  it('teaches a new word, then asks the quiz’s own question filed under the quiz', () => {
    const [teach, ask] = wordCards({ fresh: [ALL[0]], reviews: [] }, ALL, makeRandom(3))
    expect(teach).toMatchObject({ kind: 'teach', ar: 'ar-a', en: 'a' })
    expect(ask.question.answerId).toBe('a')
    expect(ask.record).toMatchObject({ module: 'quiz', item: 'a' })
    expect(ask.answerText).toBe('a')
  })
})

describe('optionPool', () => {
  const inTopic = (id, groups, wordType = 'noun') => ({ ...word(id), groups, wordType })
  const travel = ['t1', 't2', 't3', 't4', 't5', 't6'].map((id) => inTopic(id, ['everyday:travel']))
  const others = ['x1', 'x2', 'x3'].map((id) => inTopic(id, ['everyday:food']))

  it('keeps wrong options to the answer’s own topic and type when it has company there', () => {
    const pool = optionPool(travel[0], [...travel, ...others, inTopic('v1', ['everyday:travel'], 'verb')])
    expect(pool.map((w) => w.meaningKey)).toEqual(travel.map((w) => w.meaningKey))
  })

  it('falls back to every word when the topic is thin or the word has none', () => {
    const all = [...travel.slice(0, 3), ...others]
    expect(optionPool(travel[0], all)).toBe(all)
    expect(optionPool(word('plain'), all)).toBe(all)
  })

  it('deals a question whose wrong options all share the answer’s topic', () => {
    const [, ask] = wordCards({ fresh: [travel[0]], reviews: [] }, [...travel, ...others], makeRandom(5))
    const topic = new Set(travel.map((w) => w.meaningKey))
    for (const option of ask.question.options) expect(topic.has(option.id)).toBe(true)
  })
})
