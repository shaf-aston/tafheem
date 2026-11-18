// @vitest-environment happy-dom
// One pattern for every board: a tapped place's word stands in the picture's rail, level with it, with its speaker.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import spine from '../../../../../../backend/data/colloquial/spine.json'
import { RAIL } from '../../../../lib/colloquial/labelRail'
import { pictureBoards } from '../../../../lib/colloquial/wordPictures'
import WordPicture from './WordPicture'

vi.mock('../../../../lib/speech/speak', () => ({ speak: vi.fn(), prepare: vi.fn(), stop: vi.fn() }))

const word = (id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'things' })
const body = spine.units.flatMap((u) => u.lessons).find((l) => l.title === 'The Body, Head to Toe').words.map(word)
const at = (search = '') => { window.history.replaceState({}, '', `/colloq/fusha/unit-23/lesson-01/words${search}`); return render(<WordPicture words={body} />) }
const dots = (container) => [...container.querySelectorAll('circle[data-key]')]
const label = (container) => container.querySelector('[data-callout]')
// The drawing's share of the picture's width: the rail is the rest.
const DRAWING = 100 / (1 + RAIL)

beforeEach(() => { globalThis.scrollTo = vi.fn() })
afterEach(cleanup)

<<<<<<< HEAD
describe('a picture board says a tapped place’s word beside it, the same on every board', () => {
  it('before a tap there is no label, and the card invites one', () => {
    const { container } = at()
    expect(label(container)).toBeNull()
    expect(screen.getByText('Tap any place to hear its name')).toBeTruthy()
  })

  it('a tap stands the word in the rail, beyond the drawing, with its speaker; the card gives way to it', () => {
    const { container } = at()
    fireEvent.click(dots(container)[0])
    const shown = label(container)
    expect(shown).not.toBeNull()
    expect(parseFloat(shown.style.left)).toBeGreaterThan(DRAWING)                   // never on the drawing
    expect(parseFloat(shown.style.left) + parseFloat(shown.style.width)).toBeLessThanOrEqual(100)
    expect(shown.getAttribute('aria-live')).toBe('polite')
    expect(screen.getAllByRole('button', { name: 'Say it aloud' })).toHaveLength(1)  // its speaker, the only one
    expect(screen.queryByText('Tap any place to hear its name')).toBeNull()
    expect(container.querySelector(`svg line[stroke="var(--primary)"]`)).not.toBeNull()   // joined to its place
=======
describe('Callout: the tapped dot’s word stands in the margin beside it', () => {
  it('stands against the drawing, outside it, inside the picture, and says its word', () => {
    // The drawing runs 60 to 180 across a 240-unit view: 120px to 360px of 480, 120px of margin each side.
    lay({ x: 60, y: 10, width: 120, height: 280 })
    const { container } = explore()
    tap(container)
    const label = callout(container)
    expect(label).not.toBeNull()
    expect(label.getAttribute('aria-live')).toBe('polite')   // the word's one place: heard here too
    expect(label.textContent).toMatch(/\S/)
    const left = parseFloat(label.style.left)
    const width = parseFloat(label.style.width)
    expect(left >= 360 || left + width <= 120).toBe(true)   // not on the drawing
    expect(left).toBeGreaterThanOrEqual(0)
    expect(left + width).toBeLessThanOrEqual(480)           // not outside the picture
    expect(container.querySelector('svg line[stroke="var(--primary)"]')).not.toBeNull()   // joined to its dot
  })

  it('takes the place of the card: the word and its speaker are beside the dot, and the card above is gone', async () => {
    lay({ x: 60, y: 10, width: 120, height: 280 })
    const { container } = explore()
    expect(container.querySelector('[aria-live="polite"]:not([data-callout])').textContent).toMatch(/Tap any place/)
    tap(container)
    const label = callout(container)
    expect(label.querySelector('button[aria-label="Say it aloud"]')).not.toBeNull()   // it speaks there
    expect(screen.getAllByRole('button', { name: 'Say it aloud' })).toHaveLength(1)    // and only there
    expect(screen.queryByText(/Tap any place/)).toBeNull()                               // the card is not shown
>>>>>>> origin/master
  })

  it('every place on the board gets its label, not only those with room beside them', () => {
    const { container } = at()
    for (const dot of dots(container)) {
      fireEvent.click(dot)
      expect(label(container)?.textContent).toContain(dot.getAttribute('aria-label').split(',')[0])
    }
  })

  it('the picture is the board widened by its rail on the right', () => {
    const { container } = at()
    const [x, y, w, h] = container.querySelector('svg[role=group]').getAttribute('viewBox').split(' ').map(Number)
    const board = pictureBoards(body)[0]
    expect([x, y, h]).toEqual([board.view[0], board.view[1], board.view[3]])
    expect(w).toBeCloseTo(board.view[2] * (1 + RAIL))
  })

  it('in Test, a right tap shows nothing beside the dot; a wrong one shows the word tapped, in red', () => {
    const { container } = at('?step=test')
    const board = pictureBoards(body)[0]
    const asked = () => {
      const arabic = container.querySelector('[aria-live="polite"] [lang="ar"]').textContent
      return board.spots.find((spot) => spot.words.some((w) => w.arabic === arabic)).key
    }
    const dot = (key) => container.querySelector(`circle[data-key="${key}"]`)
    expect(label(container)).toBeNull()
    const wrongKey = board.spots.map((s) => s.key).find((k) => k !== asked())
    fireEvent.click(dot(wrongKey))
    expect(label(container).style.borderColor).toBe('var(--danger)')
    expect(label(container).textContent).toContain(board.spots.find((s) => s.key === wrongKey).words[0].english)
    fireEvent.click(dot(asked()))
    expect(label(container)).toBeNull()
  })

  it('is one Tab stop: the arrow keys go from place to place, in reading order, and the stop follows', () => {
    const { container } = at()
    const places = () => [...container.querySelectorAll('[role="button"][data-key]')]
    expect(places().filter((e) => e.getAttribute('tabindex') === '0')).toHaveLength(1)
    const first = places().find((e) => e.getAttribute('tabindex') === '0')
    first.focus()
    fireEvent.keyDown(first, { key: 'ArrowRight' })
    const second = document.activeElement
    expect(second).not.toBe(first)
    expect(second.getAttribute('tabindex')).toBe('0')
    fireEvent.keyDown(second, { key: 'ArrowLeft' })
    expect(document.activeElement).toBe(first)
    fireEvent.keyDown(first, { key: 'End' })
    const last = document.activeElement
    fireEvent.keyDown(last, { key: 'Home' })
    expect(document.activeElement).toBe(first)
    fireEvent.keyDown(first, { key: 'Enter' })
    expect(label(container)).not.toBeNull()   // Enter says it, beside it
  })
})
