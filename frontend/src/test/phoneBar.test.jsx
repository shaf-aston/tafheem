// @vitest-environment happy-dom
// The phone bar: two docked tabs, Ask in the middle, Learn for every other tab, Me.
// Ask opens one box that routes anything to the tab that answers it; focus mode
// (a lesson running) is one counted flag on <html>.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, renderHook, screen } from '@testing-library/react'

import BottomNav from '../components/shell/BottomNav'
import AskSheet from '../components/shell/AskSheet'
import { DOCK, LISTED, accentOf } from '../lib/nav/tabs'
import { useFocusMode } from '../lib/shell/focus'

afterEach(cleanup)

const bar = (active, more = {}) => render(
  <BottomNav tabs={LISTED} dock={DOCK} active={active} colorOf={accentOf} onSelect={() => {}} onAll={() => {}} onAsk={() => {}} onMe={() => {}} {...more} />,
)

describe('phone bar', () => {
  it('is Home, Quran, Ask, Learn, Me, with Ask in the middle', () => {
    bar('home')
    const names = screen.getAllByRole('button').map((b) => b.getAttribute('aria-label') ?? b.textContent)
    expect(names).toEqual(['Home', 'Quran', 'Ask: a word, root, ayah or sentence', 'Learn: all sections', 'Me: your progress and account'])
  })

  it('lights Learn, named for the tab, when the open tab is not on the bar', () => {
    bar('nahw')
    expect(screen.getByRole('button', { name: 'All sections, now on Nahw' }).getAttribute('aria-current')).toBe('page')
  })

  it('opens Ask and Me', () => {
    const onAsk = vi.fn()
    const onMe = vi.fn()
    bar('home', { onAsk, onMe })
    fireEvent.click(screen.getByRole('button', { name: /^Ask/ }))
    fireEvent.click(screen.getByRole('button', { name: /^Me/ }))
    expect(onAsk).toHaveBeenCalledOnce()
    expect(onMe).toHaveBeenCalledOnce()
  })
})

describe('Ask', () => {
  it('sends an ayah number to the Quran tab and closes', () => {
    const onGo = vi.fn()
    const onClose = vi.fn()
    render(<AskSheet tabs={LISTED} colorOf={accentOf} onGo={onGo} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: '2:255' }))
    fireEvent.keyDown(screen.getByRole('combobox'), { key: 'Enter' })
    expect(onClose).toHaveBeenCalled()
    expect(onGo).toHaveBeenCalledWith('quran', '2:255')
  })
})

describe('focus mode', () => {
  it('holds while any lesson holds it, and lets go after the last', () => {
    const one = renderHook(() => useFocusMode(true))
    const two = renderHook(() => useFocusMode(true))
    expect(document.documentElement.dataset.focus).toBe('lesson')
    one.unmount()
    expect(document.documentElement.dataset.focus).toBe('lesson')
    two.unmount()
    expect(document.documentElement.dataset.focus).toBeUndefined()
  })
})
