// @vitest-environment happy-dom
// A deep chart shows its first rows and folds the widest joins behind one
// button; the larger view draws every row.
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import TarkeebDiagram from '../components/grammar/tarkeeb/TarkeebDiagram'

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

  it('hands a tapped word, its place among the written words and itself to the caller', () => {
    const onWord = vi.fn()
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} onWord={onWord} />)
    const word = container.querySelectorAll('.tk-word')[2]
    fireEvent.click(word)
    expect(onWord).toHaveBeenCalledWith('ت', 2, word)
  })

  it('shows only a word\'s English on hover, from the caller, by its place', () => {
    const { container } = renderScreen(
      <TarkeebDiagram tarkeeb={TARKEEB} onWord={() => {}} glossOf={(n, text) => `${n}:${text}`} />)
    expect(container.querySelectorAll('.tk-word')[2].dataset.gloss).toBe('2:ت')
  })

  it('says a tap opens the meaning while no English is in', () => {
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} onWord={() => {}} />)
    expect(container.querySelectorAll('.tk-word')[2].dataset.gloss).toBe('tap for its meaning')
  })

  it('draws every row in the larger view', () => {
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} whole />)
    expect(rowsDrawn(container)).toBe(5)
    expect(screen.queryByRole('button', { name: /more row/ })).toBeNull()
  })

  it('hangs every name under its own brace, with no "=" or "+" saying the join again', () => {
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={TARKEEB} whole />)
    const names = [...container.querySelectorAll('.tk-name')]
    expect(names).toHaveLength(5)
    names.forEach((name) => expect(name.previousElementSibling.classList).toContain('tk-brace'))
    expect(container.querySelector('.tk-grid').textContent).not.toMatch(/[=+]/)
  })

  it('writes the open mark under a word no rule named, as the copied text does', () => {
    const tarkeeb = { words: ['أ', 'ب'], tree: { label: 'جُمْلَةٌ', parts: [], children: [
      { word: 0, role: 'مُبْتَدَأٌ', children: [], parts: [] }, { word: 1, role: null, gap: true, children: [], parts: [] }] } }
    const { container } = renderScreen(<TarkeebDiagram tarkeeb={tarkeeb} />)
    expect(container.querySelector('.tk-gap').textContent).toBe('؟')
  })
})
