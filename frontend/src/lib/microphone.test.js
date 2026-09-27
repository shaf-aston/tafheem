import { describe, expect, it } from 'vitest'

import { refusal } from './microphone'

describe('refusal', () => {
  it('tells the reader what they can do about each way the microphone is refused', () => {
    const say = (name) => refusal(Object.assign(new Error('x'), { name }))
    expect(say('NotAllowedError')).toBe('The microphone was not allowed.')
    expect(say('SecurityError')).toBe('The microphone was not allowed.')
    expect(say('NotFoundError')).toBe('No microphone was found.')
    expect(say('OverconstrainedError')).toBe('No microphone was found.')
    expect(say('NotReadableError')).toBe('The microphone is in use by another app.')
    expect(say('AbortError')).toBe('The microphone could not be opened.')
    expect(refusal(undefined)).toBe('The microphone could not be opened.')
  })
})
