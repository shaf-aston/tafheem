// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import spine from '../../../../../../backend/data/colloquial/spine.json'
import WordPicture from './WordPicture'

vi.mock('../../../../lib/speech/speak', () => ({ speak: vi.fn(), prepare: vi.fn(), stop: vi.fn() }))

const word = (id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'things' })
const body = spine.units.flatMap((u) => u.lessons).find((l) => l.title === 'The Body, Head to Toe').words.map(word)

// Nothing is laid out here, so the picture is given a size by hand: a 480 x 600 box showing the board's
// view at 2px a unit, and a drawing whose extent the test chooses.
const BOX = { left: 0, top: 0, width: 480, height: 600, right: 480, bottom: 600 }
const tags = ['Element', 'SVGElement', 'SVGGraphicsElement', 'SVGSVGElement', 'SVGGElement']
const saved = []
const stub = (name, make) => {
  for (const tag of tags) {
    const proto = window[tag]?.prototype
    if (!proto) continue
    saved.push([proto, name, Object.getOwnPropertyDescriptor(proto, name)])
    Object.defineProperty(proto, name, { configurable: true, writable: true, value: make })
  }
}
const lay = (art) => {
  stub('getScreenCTM', () => ({ a: 2, d: 2, e: 0, f: 0 }))
  stub('getBBox', () => art)
  // The picture's own box is 480 x 600; the label, a small thing, is 40 tall.
  stub('getBoundingClientRect', function rect() { return this.tagName?.toLowerCase() === 'svg' ? BOX : { ...BOX, width: 100, height: 40 } })
}

const explore = () => { window.history.replaceState({}, '', '/colloq/fusha/unit-23/lesson-01/words'); return render(<WordPicture words={body} />) }
const tap = (container) => fireEvent.click(container.querySelector('circle[data-key]'))
const callout = (container) => container.querySelector('[data-callout]')

beforeEach(() => { globalThis.scrollTo = vi.fn() })
afterEach(() => {
  cleanup()
  while (saved.length) {
    const [proto, name, was] = saved.pop()
    if (was) Object.defineProperty(proto, name, was); else delete proto[name]
  }
})

describe('Callout: the tapped dot’s word stands in the margin beside it', () => {
  it('stands against the drawing, outside it, inside the picture, and says its word', () => {
    // The drawing runs 60 to 180 across a 240-unit view: 120px to 360px of 480, 120px of margin each side.
    lay({ x: 60, y: 10, width: 120, height: 280 })
    const { container } = explore()
    tap(container)
    const label = callout(container)
    expect(label).not.toBeNull()
    expect(label.getAttribute('aria-hidden')).toBe('true')   // the card is the live region; this is for the eye
    expect(label.textContent).toMatch(/\S/)
    const left = parseFloat(label.style.left)
    const width = parseFloat(label.style.width)
    expect(left >= 360 || left + width <= 120).toBe(true)   // not on the drawing
    expect(left).toBeGreaterThanOrEqual(0)
    expect(left + width).toBeLessThanOrEqual(480)           // not outside the picture
    expect(container.querySelector('svg line[stroke="var(--primary)"]')).not.toBeNull()   // joined to its dot
  })

  it('says the same word as the card, which keeps saying it', () => {
    lay({ x: 60, y: 10, width: 120, height: 280 })
    const { container } = explore()
    tap(container)
    const card = container.querySelector('[aria-live="polite"]')
    expect(card.textContent).toMatch(/\S/)
    expect(screen.getByRole('button', { name: 'Say it aloud' })).toBeTruthy()
    const english = callout(container).querySelector('p:last-child').textContent
    expect(card.textContent).toContain(english)
  })

  it('stays away where the drawing fills its picture: no margin, so the card alone says the word', () => {
    lay({ x: 0, y: 0, width: 240, height: 300 })
    const { container } = explore()
    tap(container)
    expect(callout(container)).toBeNull()
    expect(container.querySelector('svg line[stroke="var(--primary)"]')).toBeNull()
    expect(container.querySelector('[aria-live="polite"]').textContent).toMatch(/\S/)
  })

  it('stays away in Test, where the word is the question', () => {
    lay({ x: 60, y: 10, width: 120, height: 280 })
    window.history.replaceState({}, '', '/colloq/fusha/unit-23/lesson-01/words?step=test')
    const { container } = render(<WordPicture words={body} />)
    tap(container)
    expect(callout(container)).toBeNull()
  })

  it('is not there before a tap, and stays away where nothing can be measured', () => {
    lay({ x: 60, y: 10, width: 120, height: 280 })
    const first = explore()
    expect(callout(first.container)).toBeNull()
    cleanup()
    while (saved.length) {
      const [proto, name, was] = saved.pop()
      if (was) Object.defineProperty(proto, name, was); else delete proto[name]
    }
    const { container } = explore()
    tap(container)
    expect(callout(container)).toBeNull()
  })
})
