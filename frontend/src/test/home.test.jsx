// @vitest-environment happy-dom
// Home offers where you stopped and the recent tabs from the journey, a first-visit
// start when there is no path, and every tab behind All sections.
import { describe, expect, it, vi } from 'vitest'
import { act, fireEvent, screen } from '@testing-library/react'

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

  it('lists every other tab behind All sections', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    const others = LISTED.filter((tab) => tab.id !== HOME)
    for (const tab of others) {
      expect(screen.getByText(tab.blurb), tab.id).toBeTruthy()
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
