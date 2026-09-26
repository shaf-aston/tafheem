import { describe, expect, it } from 'vitest'

import { loadUnit, shown, unitIds } from './units'

describe('unit loading', () => {
  it('lists units from the folder, sorted', () => {
    const ids = unitIds()
    expect(ids).toEqual([...ids].sort())
  })

  it('loads the first supplied unit, valid', async (ctx) => {
    const [first] = unitIds()
    if (!first) return ctx.skip('no unit files in src/data/colloquial/ yet')
    const loaded = await loadUnit(first)
    expect(loaded.problems ?? []).toEqual([])
    expect(loaded.unit.unit).toBe(first)
  })

  it('returns problems, not a unit, for an invalid file', async () => {
    const loaded = await loadUnit('bad', { bad: async () => ({ unit: 'bad' }) })
    expect(loaded.unit).toBeUndefined()
    expect(loaded.problems.length).toBeGreaterThan(0)
  })

  it('hides an invalid unit in production, shows it in dev', () => {
    expect(shown({ problems: [1] }, false)).toBe(false)
    expect(shown({ problems: [1] }, true)).toBe(true)
    expect(shown({ unit: {} }, false)).toBe(true)
  })
})
