import { describe, expect, it } from 'vitest'

import { nextSpot } from './keyHint'

const tab = (offsetLeft, offsetWidth) => ({ offsetLeft, offsetWidth })

describe('nextSpot', () => {
  const strip = [tab(0, 100), tab(100, 0), tab(200, 50)]

  it('keys a tab by its place in the strip and aims at its middle', () => {
    expect(nextSpot(strip, 0)).toEqual({ n: 1, x: 50, last: false })
  })

  it('skips a tab a narrow screen hides, without renumbering the rest', () => {
    expect(nextSpot(strip, 1)).toEqual({ n: 3, x: 225, last: true })
  })

  it('starts the pass again after the last tab', () => {
    expect(nextSpot(strip, 3).n).toBe(1)
  })

  it('has nowhere to go when no tab is on show', () => {
    expect(nextSpot([tab(0, 0)], 0)).toBeNull()
  })
})
