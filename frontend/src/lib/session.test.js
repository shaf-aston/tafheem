import { describe, expect, it } from 'vitest'

import { parseSession, serialise } from './session'

const TABS = ['dict', 'daleel', 'quran']
const NOW = 1_000_000_000
const HOUR = 60 * 60 * 1000
const GOOD = { steps: [{ tab: 'dict', value: null }, { tab: 'dict', value: 'كتب' }], at: 1 }

describe('parseSession', () => {
  it('reads back what serialise wrote', () => {
    expect(parseSession(serialise(GOOD, NOW), TABS, NOW)).toEqual(GOOD)
  })

  it('keeps a record inside its shelf life, drops one past it', () => {
    expect(parseSession(serialise(GOOD, NOW), TABS, NOW + 11 * HOUR)).toEqual(GOOD)
    expect(parseSession(serialise(GOOD, NOW), TABS, NOW + 13 * HOUR)).toBe(null)
  })

  it('drops a record from the future, a clock that moved is not a path', () => {
    expect(parseSession(serialise(GOOD, NOW + HOUR), TABS, NOW)).toBe(null)
  })

  it('drops another version of the record rather than repairing it', () => {
    const other = JSON.stringify({ ...JSON.parse(serialise(GOOD, NOW)), v: 99 })
    expect(parseSession(other, TABS, NOW)).toBe(null)
  })

  it('drops junk: nothing, not JSON, not an object, no steps', () => {
    for (const raw of ['', 'nope', '42', 'null', JSON.stringify({ v: 1, saved: NOW, steps: [], at: 0 })]) {
      expect(parseSession(raw, TABS, NOW)).toBe(null)
    }
  })

  it('drops a step on a tab this build does not have', () => {
    const gone = { steps: [{ tab: 'iraab', value: 'x' }], at: 0 }
    expect(parseSession(serialise(gone, NOW), TABS, NOW)).toBe(null)
  })

  it('drops an index that points outside the steps', () => {
    for (const at of [-1, 2, 1.5, '1']) {
      expect(parseSession(serialise({ ...GOOD, at }, NOW), TABS, NOW)).toBe(null)
    }
  })

  it('drops a value that is not text', () => {
    const odd = { steps: [{ tab: 'dict', value: 7 }], at: 0 }
    expect(parseSession(serialise(odd, NOW), TABS, NOW)).toBe(null)
  })

  it('drops a record with no version at all', () => {
    expect(parseSession(JSON.stringify({ saved: NOW, steps: GOOD.steps, at: 1 }), TABS, NOW)).toBe(null)
  })

  it('drops a step repeated straight after itself, the app never records one', () => {
    const twice = { steps: [{ tab: 'dict', value: 'a' }, { tab: 'dict', value: 'a' }], at: 1 }
    expect(parseSession(serialise(twice, NOW), TABS, NOW)).toBe(null)
    // The same word later on, after somewhere else, is a real return to it.
    const again = { steps: [{ tab: 'dict', value: 'a' }, { tab: 'dict', value: 'b' }, { tab: 'dict', value: 'a' }], at: 2 }
    expect(parseSession(serialise(again, NOW), TABS, NOW)).toEqual(again)
  })

  it('drops a path longer than the store allows, or a word longer', () => {
    const steps = Array.from({ length: 1001 }, (_, i) => ({ tab: 'dict', value: `w${i}` }))
    expect(parseSession(serialise({ steps, at: 0 }, NOW), TABS, NOW)).toBe(null)
    expect(parseSession(serialise({ steps: steps.slice(0, 1000), at: 0 }, NOW), TABS, NOW)).not.toBe(null)
    const long = { steps: [{ tab: 'dict', value: 'x'.repeat(1001) }], at: 0 }
    expect(parseSession(serialise(long, NOW), TABS, NOW)).toBe(null)
  })

  it('keeps only tab and value of each step, whatever else was in the file', () => {
    const fat = JSON.stringify({ v: 1, saved: NOW, steps: [{ tab: 'dict', value: 'a', extra: 1 }], at: 0 })
    expect(parseSession(fat, TABS, NOW)).toEqual({ steps: [{ tab: 'dict', value: 'a' }], at: 0 })
  })
})
