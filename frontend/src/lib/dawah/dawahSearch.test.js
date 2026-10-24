import { describe, expect, it } from 'vitest'

import { matches } from './dawahSearch'

const question = { q: 'What does Islam say about الصَّبْر?', short: '', points: [], id: 'patience-in-islam' }
const topic = { title: 'Character' }

describe('dawah search', () => {
  it('finds vowelled Arabic from the bare word a keyboard types', () => {
    expect(matches('الصبر', topic, question)).toBe(true)
  })

  it('still needs every typed word', () => {
    expect(matches('patience', topic, question)).toBe(true)
    expect(matches('patience fasting', topic, question)).toBe(false)
  })
})
