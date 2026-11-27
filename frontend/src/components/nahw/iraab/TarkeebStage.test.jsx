// @vitest-environment happy-dom
// The tarkeeb card: a list on an upright phone, the fitted chart elsewhere, a
// tapped word answered beside or under it, and a full screen that zooms.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'

import TarkeebStage from './TarkeebStage'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

// upright: a phone held upright; wide: room for the side panel
const media = ({ upright = false, wide = false }) => vi.stubGlobal('matchMedia', (q) => ({
  matches: q.includes('portrait') ? upright : q.includes('min-width: 64rem') ? wide : false,
  addEventListener() {}, removeEventListener() {},
}))

const word = (w, role) => ({ word: w, role, role_key: 'mubtada', name: null, case: "raf'", sign: 'ضمة', reason: 'لأنه في أول الكلام. القاعدة: المبتدأ مرفوع', governor: null, follows: null })
const leaf = (role, i) => ({ role, word: i, children: [], parts: [] })
const data = (a, b) => ({
  words: [word(a, 'مبتدأ'), word(b, 'خبر')],
  tree: { words: [a, b], tree: { label: 'جُمْلَةٌ اِسْمِيَّةٌ', children: [leaf('مبتدأ', 0), leaf('خبر', 1)], parts: [] } },
})
const BOOK = data('الكِتَابُ', 'مُفِيدٌ')
const glosses = [{ arabic: 'الكِتَابُ', english: 'the book' }, { arabic: 'مُفِيدٌ', english: 'useful' }]
const stage = (d = BOOK) => <TarkeebStage data={d} kind="nominal" glosses={glosses} onMore={() => {}} foot={<p>foot</p>} />

describe('TarkeebStage', () => {
  it('reads down as a list on an upright phone, with the chart one tap away', () => {
    media({ upright: true })
    render(stage())
    expect(screen.getByRole('list', { name: 'Tarkeeb, as a list' })).toBeTruthy()
    expect(screen.queryByRole('group', { name: /^Tarkeeb of/ })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Chart' }))
    expect(screen.getByRole('group', { name: 'Tarkeeb of الكِتَابُ مُفِيدٌ' })).toBeTruthy()
    expect(screen.getByText(/turn your phone sideways/)).toBeTruthy()
  })

  it('opens a tapped word under its own line in the list', () => {
    media({ upright: true })
    render(stage())
    const row = screen.getAllByRole('button', { expanded: false })[0]
    fireEvent.click(row)
    const item = row.closest('li')
    expect(within(item).getByText('the book')).toBeTruthy()
    expect(within(item).getByText(/القاعدة: المبتدأ مرفوع/)).toBeTruthy()
  })

  it('answers a tapped word in the side panel on a wide screen, and a second tap closes it', () => {
    media({ wide: true })
    render(stage())
    expect(screen.queryByRole('list', { name: 'Tarkeeb, as a list' })).toBeNull()
    expect(screen.getByText(/Tap any word in the chart/)).toBeTruthy()
    const book = screen.getByRole('button', { name: 'الكِتَابُ' })
    fireEvent.click(book)
    const panel = document.querySelector('aside[aria-live]')
    expect(within(panel).getByText('the book')).toBeTruthy()
    expect(book.getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(book)
    expect(within(panel).queryByText('the book')).toBeNull()
  })

  it('finds a tapped word\'s card by its place when the card spells it otherwise', () => {
    media({ wide: true })
    const spelt = { ...BOOK, words: [{ ...BOOK.words[0], word: 'كِتَابٌ' }, BOOK.words[1]] }
    render(stage(spelt))
    fireEvent.click(screen.getByRole('button', { name: 'الكِتَابُ' }))
    expect(within(document.querySelector('aside[aria-live]')).getByText(/القاعدة: المبتدأ مرفوع/)).toBeTruthy()
  })

  it('lets a card opened on top take Esc, leaving full screen open', () => {
    media({ wide: true })
    render(stage())
    fireEvent.click(screen.getByRole('button', { name: /Full screen/ }))
    const sheet = document.createElement('dialog'); sheet.setAttribute('open', ''); document.body.append(sheet)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.getByRole('dialog', { name: 'Tarkeeb, full screen' })).toBeTruthy()
    sheet.remove()
  })

  it('names a word\'s own job in the list when its pieces make up another', () => {
    media({ upright: true })
    const tree = { words: ['زَيْدٌ', 'فِيهِ'], tree: { label: 'جُمْلَةٌ اِسْمِيَّةٌ', children: [leaf('مبتدأ', 0),
      { role: 'خبر', word: 1, children: [], parts: [{ role: 'حرف جر' }, { role: 'مجرور' }] }], parts: [] } }
    render(stage({ words: [word('زَيْدٌ', 'مبتدأ'), word('فِيهِ', 'خبر')], tree }))
    const row = screen.getAllByRole('button', { expanded: false })[1]
    expect(row.textContent).toMatch(/خبر.*حرف جر.*مجرور/)
  })

  it('forgets the tapped word when a new sentence comes', () => {
    media({ wide: true })
    const { rerender } = render(stage())
    fireEvent.click(screen.getByRole('button', { name: 'الكِتَابُ' }))
    // the same first word, so only the new sentence can clear it
    rerender(stage(data('الكِتَابُ', 'نُورٌ')))
    expect(screen.getByText(/Tap any word in the chart/)).toBeTruthy()
  })

  it('keeps the foot inside the card', () => {
    media({ wide: true })
    render(stage())
    expect(screen.getByRole('region', { name: 'Tarkeeb' }).contains(screen.getByText('foot'))).toBe(true)
  })

  it('fills the screen, zooms in steps and closes on Escape', () => {
    media({ wide: true })
    render(stage())
    fireEvent.click(screen.getByRole('button', { name: /Full screen/ }))
    const full = screen.getByRole('dialog', { name: 'Tarkeeb, full screen' })
    const out = within(full).getByRole('button', { name: 'Zoom out' })
    const fit = within(full).getByRole('button', { name: 'Fit the whole chart' })
    const zoomIn = within(full).getByRole('button', { name: 'Zoom in' })
    expect(out.disabled).toBe(true)
    expect(fit.getAttribute('aria-pressed')).toBe('true')
    expect(full.querySelector('.tkc.tkc-fill.tkc-zoomed')).toBeNull()

    fireEvent.click(zoomIn)
    expect(out.disabled).toBe(false)
    expect(fit.getAttribute('aria-pressed')).toBe('false')
    expect(full.querySelector('.tkc.tkc-fill.tkc-zoomed')).not.toBeNull()
    fireEvent.click(zoomIn)
    fireEvent.click(zoomIn)
    expect(zoomIn.disabled).toBe(true)
    fireEvent.click(fit)
    expect(full.querySelector('.tkc-zoomed')).toBeNull()

    expect(document.activeElement).toBe(within(full).getByRole('button', { name: 'Close full screen' }))
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(screen.getByRole('button', { name: /Full screen/ }))
  })

  it('opens full screen at the fitted size again after a zoom', () => {
    media({ wide: true })
    render(stage())
    fireEvent.click(screen.getByRole('button', { name: /Full screen/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Close full screen' }))
    fireEvent.click(screen.getByRole('button', { name: /Full screen/ }))
    expect(screen.getByRole('button', { name: 'Fit the whole chart' }).getAttribute('aria-pressed')).toBe('true')
  })
})
