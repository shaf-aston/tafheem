import { describe, expect, it } from 'vitest'

import { makeRandom } from './quiz'
import { wordCards } from './wordLesson'

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
