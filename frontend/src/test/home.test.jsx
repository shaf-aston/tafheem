// @vitest-environment happy-dom
// Home offers where you stopped and the recent tabs from the journey, a first-visit
// start when there is no path, and every tab in view under its group.
import { describe, expect, it, vi } from 'vitest'
import { act, fireEvent, screen, within } from '@testing-library/react'

import { renderScreen } from './render'
import HomePanel from '../components/home/HomePanel'
import { visit } from '../lib/journey'
import { FIXED, HOME, LISTED } from '../lib/tabs'

const FIRST = LISTED.find((tab) => tab.id === FIXED.find((id) => id !== HOME))

describe('Home', () => {
  it('on a first visit offers the first fixed tab, and opens it on a tap', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    fireEvent.click(await screen.findByRole('button', { name: /Begin/ }))
    expect(onGo).toHaveBeenCalledWith(FIRST.id, undefined)
  })

  it('shows every other tab without opening anything', async () => {
    const onGo = vi.fn()
    const { container } = renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    expect(container.querySelector('details')).toBeNull()
    const others = LISTED.filter((tab) => tab.id !== HOME)
    // Each tab once in the list; the first-lesson card above is the only other place one shows.
    const list = screen.getByRole('region', { name: /All sections/ })
    for (const tab of others) {
      expect(within(list).getAllByText(tab.blurb), tab.id).toHaveLength(1)
    }
  })

  it('carries on where you stopped, with the word', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    act(() => { visit('dict', 'كتب') })
    fireEvent.click(await screen.findByRole('button', { name: /Continue/ }))
    expect(onGo).toHaveBeenCalledWith('dict', 'كتب')
  })
})
