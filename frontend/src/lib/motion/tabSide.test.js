import { describe, expect, it } from 'vitest'

import { sideOf } from './tabSide'

describe('sideOf', () => {
  const bar = ['home', 'quran', 'dict', 'quiz']
  it('a tab to the right comes in from the right', () => expect(sideOf(bar, 'quran', 'quiz')).toBe('next'))
  it('a tab to the left comes in from the left', () => expect(sideOf(bar, 'quiz', 'home')).toBe('prev'))
  it('a tab behind More sits at the far end', () => expect(sideOf(bar, 'dict', 'map')).toBe('next'))
  it('More to More, or the first tab, has no side', () => {
    expect(sideOf(bar, 'map', 'kit')).toBeNull()
    expect(sideOf(bar, null, 'home')).toBeNull()
    expect(sideOf(bar, 'home', 'home')).toBeNull()
  })
})
