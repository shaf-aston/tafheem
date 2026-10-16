// @vitest-environment happy-dom
// A deep chart shows its first rows and folds the widest joins behind one
// button; the larger view draws every row.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import TarkeebDiagram from '../components/TarkeebDiagram'

// Six words, each joined to the rest one level further down: five rows.
const deep = (word, last) => (word === last
  ? { word, role: 'خَبَرٌ', children: [], parts: [] }
  : { label: 'جُمْلَةٌ', children: [{ word, role: 'مُبْتَدَأٌ', children: [], parts: [] }, deep(word + 1, last)], parts: [] })
const TARKEEB = { words: ['أ', 'ب', 'ت', 'ث', 'ج', 'ح'], tree: deep(0, 5) }
const rowsDrawn = (container) => new Set([...container.querySelectorAll('.tk-group')].map((group) => group.style.gridRow)).size

describe('tarkeeb chart', () => {
  it('folds the rows past the first four, and opens them on a tap', () => {
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} />)
    expect(rowsDrawn(container)).toBe(4)
    fireEvent.click(screen.getByRole('button', { name: /1 more row/ }))
    expect(rowsDrawn(container)).toBe(5)
    expect(screen.queryByRole('button', { name: /more row/ })).toBeNull()
  })

  it('draws every row in the larger view', () => {
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} whole />)
    expect(rowsDrawn(container)).toBe(5)
    expect(screen.queryByRole('button', { name: /more row/ })).toBeNull()
  })
})
