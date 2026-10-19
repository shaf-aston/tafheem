import { describe, expect, it } from 'vitest'

import { labelOf, progressByTab, tabOf } from './moduleTab'

describe('which tab a module belongs to', () => {
  it('reads the part before the colon, and the names a tab files under', () => {
    expect(tabOf('quiz:ur').id).toBe('quiz')
    expect(tabOf('words').id).toBe('colloq')
    expect(tabOf('nawawi40').id).toBe('grow')
    expect(tabOf('quran-ayat').id).toBe('grow')
    expect(tabOf('quduri').id).toBe('grow')
    expect(tabOf('nothing')).toBeNull()
  })

  it('labels a row the way the profile always has', () => {
    expect(labelOf('quiz')).toBe('Quiz')
    expect(labelOf('quiz:ur')).toBe('Quiz · Urdu')
    expect(labelOf('words')).toBe('Colloquial · words')
    expect(labelOf('nothing')).toBe('nothing')
  })

  it('sums a tab\'s modules and keeps the latest day', () => {
    const sums = progressByTab([
      { module: 'quiz', learnt: 1, attempts: 3, lastAt: '2026-02-01' },
      { module: 'quiz:ur', learnt: 2, attempts: 5, lastAt: '2026-01-01' },
      { module: 'nothing', learnt: 9, attempts: 9, lastAt: '2026-03-01' },
    ])
    expect(sums).toEqual({ quiz: { learnt: 3, attempts: 8, lastAt: '2026-02-01' } })
  })
})
